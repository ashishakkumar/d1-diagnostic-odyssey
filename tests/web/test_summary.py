"""The doctor summary is a fixed template filled from accepted rows."""

import psycopg
import pytest
from fastapi.testclient import TestClient
from support import DATABASE_URL, wipe

CASE_ID = "00000000-0000-4000-8000-0000000000a4"
NOTICE = "Not for use in diagnostic procedures"


def page_count(data: bytes) -> int:
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


@pytest.fixture
def client():
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def _approve_term(client: TestClient) -> None:
    drafted = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"},
    )
    assert drafted.status_code == 200
    draft = drafted.json()
    accepted = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert accepted.status_code == 200


def _approve_variant(client: TestClient) -> None:
    drafted = client.post(
        f"/cases/{CASE_ID}/variants",
        json={
            "gene_symbol": "EXAMPLE1",
            "variant": "c.1A>G",
            "lab_words": "the synthetic report's own words",
            "report_date": "2024-03-01",
        },
    )
    assert drafted.status_code == 200
    draft = drafted.json()
    accepted = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert accepted.status_code == 200


def test_summary_pdf_is_filled_from_accepted_rows(client: TestClient) -> None:
    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    _approve_term(client)
    _approve_variant(client)

    text = client.get(f"/cases/{CASE_ID}/summary")
    assert text.status_code == 200
    page = text.text
    assert "Seizure" in page
    assert "HP:0001250" in page
    assert "EXAMPLE1" in page
    assert "c.1A>G" in page
    assert "the synthetic report's own words" in page
    assert "2024-03-01" in page
    assert "Questions to take to a doctor" in page
    assert NOTICE in page
    assert "Not a medical document" in page

    pdf = client.get(f"/cases/{CASE_ID}/summary.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")
    assert 1 <= page_count(pdf.content) <= 2
    assert b"Seizure" in pdf.content
    assert b"EXAMPLE1" in pdf.content
    assert b"Questions to take to a doctor" in pdf.content
    assert NOTICE.encode() in pdf.content

    with psycopg.connect(DATABASE_URL) as connection:
        kinds = {
            row[0]
            for row in connection.execute(
                "SELECT kind FROM app.observation WHERE case_id = %s::uuid",
                (CASE_ID,),
            ).fetchall()
        }
    assert kinds == {"hpo_term", "lab_reported_variant"}


def test_summary_pdf_stays_within_two_pages() -> None:
    from app.routes.summary import text_to_pdf

    text = "\n".join(f"Question {index} about a saved row." for index in range(400))
    pdf = text_to_pdf(text)
    assert pdf.startswith(b"%PDF")
    assert page_count(pdf) == 2
    assert b"timeline" in pdf
