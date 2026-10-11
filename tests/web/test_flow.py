"""One synthetic case through the gate, the scorer, a change, and the scanned page."""

import os

import psycopg
import pytest
from d1_safety.scan import scan
from fastapi.testclient import TestClient
from support import DATABASE_URL, wipe

from d1_contracts import parse_report

CASE_ID = "00000000-0000-4000-8000-0000000000c1"
TERMS = (
    ("HP:0001166", "Arachnodactyly"),
    ("HP:0000272", "Malar flattening"),
)


def _pdf_text(data: bytes) -> str:
    chunks: list[str] = []
    for piece in data.split(b"Tj"):
        start = piece.rfind(b"(")
        end = piece.rfind(b")")
        if start < 0 or end < start:
            continue
        raw = piece[start + 1 : end]
        raw = raw.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
        chunks.append(raw.decode("cp1252", errors="replace"))
    return "\n".join(chunks)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("D1_COUNTRY", "in")
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def _accept(client: TestClient, draft: dict) -> None:
    accepted = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert accepted.status_code == 200


def test_a_synthetic_case_scores_a_change_and_scans_clean(client: TestClient) -> None:
    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    for hpo_id, label in TERMS:
        drafted = client.post(
            f"/cases/{CASE_ID}/term-drafts",
            json={"hpo_id": hpo_id, "label": label, "presence": "present"},
        )
        assert drafted.status_code == 200
        draft = drafted.json()
        assert draft["explanation"]
        _accept(client, draft)

    with psycopg.connect(DATABASE_URL) as connection:
        stored = connection.execute(
            """
            SELECT body->>'explanation'
            FROM app.draft
            WHERE case_id = %s::uuid AND kind = 'hpo_term'
            """,
            (CASE_ID,),
        ).fetchall()
    assert stored
    assert all(row[0] for row in stored)

    drafted = client.post(
        f"/cases/{CASE_ID}/variants",
        json={
            "gene_symbol": "FBN1",
            "variant": "NM_000138.5:c.1A>G",
            "lab_words": "the synthetic report's own words",
            "report_date": "2024-03-01",
        },
    )
    assert drafted.status_code == 200
    _accept(client, drafted.json())

    report = client.get(f"/cases/{CASE_ID}/report")
    assert report.status_code == 200
    body = report.json()
    parsed = parse_report(body)
    assert parsed.abstained is False
    leader = [item for item in parsed.evidence if item.orphanet_id == "ORPHA:9000001"]
    product = 1.0
    for item in leader:
        product *= item.lower_ratio
    assert product == pytest.approx(320)
    # The other disease's present term is in the excluded bin, so its lower
    # ratio is 0. The scorer leaves margin empty rather than dividing by zero.
    assert parsed.margin is None
    assert parsed.evidence
    assert "probability" not in body
    assert "reliability_curve" not in body

    page = client.get(f"/cases/{CASE_ID}/summary")
    assert page.status_code == 200
    text = page.text
    assert "ClinicalSignificance: ALPHA" in text
    assert "ClinicalSignificance: BETA" in text
    assert "112" in text
    assert scan(text) == []

    pdf = client.get(f"/cases/{CASE_ID}/summary.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    extracted = _pdf_text(pdf.content)
    assert "ClinicalSignificance: BETA" in extracted
    assert scan(extracted) == []


def test_a_red_flag_phrase_returns_the_stop_screen(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("D1_COUNTRY", "gb")
    stopped = client.post(
        f"/cases/{CASE_ID}/variants",
        json={
            "gene_symbol": "FBN1",
            "variant": "NM_000138.5:c.1A>G",
            "lab_words": "chest pain",
            "report_date": "2024-03-01",
        },
    )
    assert stopped.status_code == 409
    detail = stopped.json()["detail"]
    assert detail["matched"] == ["chest pain"]
    assert "chest pain" in detail["body"]
    assert scan(detail["body"]) == []
    assert scan(detail["footer"]) == []
    footer = client.get("/footer")
    assert footer.status_code == 200
    assert "999" in footer.json()["text"]
    assert scan(footer.json()["text"]) == []
    with psycopg.connect(os.environ.get("DATABASE_URL", DATABASE_URL)) as connection:
        count = connection.execute(
            "SELECT count(*) FROM app.draft WHERE case_id = %s::uuid",
            (CASE_ID,),
        ).fetchone()
    assert count == (0,)
