"""One-step reading of a synthetic note. Lexicon, then Resnik on the ten-row table."""

import os

import psycopg
import pytest
from fastapi.testclient import TestClient
from support import wipe

from app.demo_cases import DEMO_CASES
from app.pipeline import extract_terms, resnik_scores, synthetic_profiles

CASE_IDS = [str(case["case_id"]) for case in DEMO_CASES]
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://d1:d1@127.0.0.1:5432/d1")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("D1_COUNTRY", "in")
    for case_id in CASE_IDS:
        wipe(case_id)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    for case_id in CASE_IDS:
        wipe(case_id)


def _counts(case_id: str) -> tuple[int, int]:
    with psycopg.connect(DATABASE_URL) as connection:
        drafts = connection.execute(
            "SELECT count(*) FROM app.draft WHERE case_id = %s::uuid",
            (case_id,),
        ).fetchone()
        observations = connection.execute(
            "SELECT count(*) FROM app.observation WHERE case_id = %s::uuid",
            (case_id,),
        ).fetchone()
    assert drafts is not None and observations is not None
    return int(drafts[0]), int(observations[0])


def test_lexicon_keeps_the_longer_phrase_and_the_quote_span() -> None:
    note = "Synthetic note. There were seizures."
    terms = extract_terms(note)
    assert [term["hpo_id"] for term in terms] == ["HP:0001250"]
    assert terms[0]["quote"] == "seizures"
    assert note[int(terms[0]["start"]) : int(terms[0]["end"])] == "seizures"


def test_resnik_on_the_synthetic_table_separates_and_abstains() -> None:
    profiles = synthetic_profiles()
    separated = resnik_scores(["HP:0001166", "HP:0000272"], profiles)
    assert separated[0][0] == "ORPHA:9000001"
    assert separated[0][1] > separated[1][1]
    assert separated[0][1] > 0

    seizure = resnik_scores(["HP:0001250"], profiles)
    assert seizure[0][1] == 0

    stable = resnik_scores(["HP:0001251", "HP:0001252"], profiles)
    leaders = [item for item in stable if item[1] == stable[0][1]]
    assert {item[0] for item in leaders} == {"ORPHA:9000011", "ORPHA:9000012"}


def test_pipeline_labels_the_lexicon_and_does_not_write(client: TestClient) -> None:
    before = _counts(CASE_IDS[0])
    separated = client.post("/pipeline", json={"slug": "separated"})
    assert separated.status_code == 200
    body = separated.json()
    assert "No language model ran" in body["method"]
    assert "2026-10-12" in body["method"]
    assert [stage["label"] for stage in body["stages"]] == ["Read", "Map", "Match", "Rank"]
    assert body["abstained"] is False
    assert body["ranks"][0]["orphanet_id"] == "ORPHA:9000001"
    assert body["ranks"][0]["bar"] == 1
    assert "highest score" in body["ranks"][0]["reason"]
    assert [term["hpo_id"] for term in body["terms"]] == ["HP:0001166", "HP:0000272"]
    assert "Ask a doctor" in body["questions"][0]
    assert _counts(CASE_IDS[0]) == before

    abstain = client.post("/pipeline", json={"slug": "abstain"})
    assert abstain.status_code == 200
    assert abstain.json()["abstained"] is True
    assert "Not enough signal" in abstain.json()["abstain_text"]

    stable = client.post("/pipeline", json={"slug": "stable"})
    assert stable.json()["abstained"] is True
    tied = [row for row in stable.json()["ranks"] if row["bar"] == 1]
    assert {row["orphanet_id"] for row in tied} == {"ORPHA:9000011", "ORPHA:9000012"}

    variant = client.post("/pipeline", json={"slug": "variant"})
    assert "did not use it" in variant.json()["gene_line"]
    assert variant.json()["ranks"][0]["orphanet_id"] == "ORPHA:9000001"

    limits = client.post("/pipeline", json={"slug": "limits"})
    assert "does not choose a dose" in limits.json()["limit_line"]

    stopped = client.post("/pipeline", json={"note": "Unconsciousness."})
    assert stopped.status_code == 409
    assert stopped.json()["detail"]["title"] == "Stop"
    assert "Unconsciousness." in stopped.json()["detail"]["matched"]
    assert _counts(CASE_IDS[0]) == before

    assert client.post("/pipeline", json={"slug": "missing"}).status_code == 404
    assert client.post("/pipeline", json={}).status_code == 422
    assert client.post("/pipeline", json={"slug": "separated", "note": "x"}).status_code == 422


def test_confirm_is_the_only_write_and_uses_the_gate(client: TestClient) -> None:
    body = client.post("/pipeline", json={"slug": "separated"}).json()
    empty = client.post(
        "/pipeline/confirm",
        json={"case_id": body["case_id"], "terms": []},
    )
    assert empty.status_code == 422
    assert _counts(body["case_id"]) == (0, 0)

    flagged = client.post(
        "/pipeline/confirm",
        json={
            "case_id": body["case_id"],
            "terms": [{"hpo_id": "HP:0001250", "label": "Unconsciousness."}],
        },
    )
    assert flagged.status_code == 409
    assert _counts(body["case_id"]) == (0, 0)

    confirmed = client.post(
        "/pipeline/confirm",
        json={
            "case_id": body["case_id"],
            "terms": [{"hpo_id": term["hpo_id"], "label": term["label"]} for term in body["terms"]],
        },
    )
    assert confirmed.status_code == 200
    recorded = confirmed.json()
    assert recorded["reviewer"] == "synthetic-reader"
    assert len(recorded["recorded"]) == 2
    assert "Ask a doctor" in recorded["questions"][0]
    assert _counts(body["case_id"]) == (2, 2)

    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    named = client.post("/pipeline", json={"slug": "stable"}).json()
    with_name = client.post(
        "/pipeline/confirm",
        json={
            "case_id": named["case_id"],
            "terms": [
                {"hpo_id": term["hpo_id"], "label": term["label"]} for term in named["terms"]
            ],
        },
    )
    assert with_name.status_code == 200
    assert with_name.json()["reviewer"] == "ashish"
