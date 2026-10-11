"""A lab-reported variant is typed, then accepted through the same gate."""

import psycopg
import pytest
from fastapi.testclient import TestClient
from support import DATABASE_URL, wipe

CASE_ID = "00000000-0000-4000-8000-0000000000a3"
VARIANT = {
    "gene_symbol": "EXAMPLE1",
    "variant": "c.1A>G",
    "lab_words": "the synthetic report's own words",
    "report_date": "2024-03-01",
}


@pytest.fixture
def client():
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def test_typed_variant_is_pending_until_the_session_accepts_it(client: TestClient) -> None:
    created = client.post(f"/cases/{CASE_ID}/variants", json=VARIANT)
    assert created.status_code == 200
    draft = created.json()
    assert draft["gene_symbol"] == "EXAMPLE1"
    assert draft["variant"] == "c.1A>G"
    assert draft["lab_words"] == VARIANT["lab_words"]
    assert draft["report_date"] == "2024-03-01"
    assert "classification" not in draft

    with psycopg.connect(DATABASE_URL) as connection:
        pending = connection.execute(
            "SELECT status, kind FROM app.draft WHERE id = %s::uuid",
            (draft["draft_id"],),
        ).fetchone()
        observations = connection.execute(
            "SELECT count(*) FROM app.observation WHERE case_id = %s::uuid",
            (CASE_ID,),
        ).fetchone()
    assert pending == ("pending", "lab_reported_variant")
    assert observations == (0,)

    assert client.post("/session", json={"name": "caregiver"}).status_code == 200
    accepted = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert accepted.status_code == 200
    with psycopg.connect(DATABASE_URL) as connection:
        stored = connection.execute(
            """
            SELECT o.body, d.reviewer
            FROM app.observation o
            JOIN app.decision d ON d.draft_id = o.draft_id
            WHERE o.draft_id = %s::uuid
            """,
            (draft["draft_id"],),
        ).fetchone()
    assert stored is not None
    body, reviewer = stored
    assert reviewer == "caregiver"
    assert body["gene_symbol"] == "EXAMPLE1"
    assert body["lab_words"] == VARIANT["lab_words"]
    assert body["report_date"] == "2024-03-01"
    assert body["variation"]["expressions"][0]["value"] == "c.1A>G"
    assert "classification" not in body


def test_variant_fields_are_required(client: TestClient) -> None:
    response = client.post(
        f"/cases/{CASE_ID}/variants",
        json={"gene_symbol": "EXAMPLE1", "variant": "c.1A>G", "report_date": "2024-03-01"},
    )
    assert response.status_code == 422
