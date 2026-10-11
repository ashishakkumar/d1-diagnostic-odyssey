"""Accept a drafted symptom term through the HTTP gate.

The body is an ApprovalRequest. The reviewer is the session cookie.
"""

import os

import psycopg
import pytest
from fastapi.testclient import TestClient
from support import wipe

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://d1:d1@127.0.0.1:5432/d1")
CASE_ID = "00000000-0000-4000-8000-0000000000a1"


@pytest.fixture
def client():
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def test_accept_stores_the_session_reviewer_and_one_observation(client: TestClient) -> None:
    drafted = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"},
    )
    assert drafted.status_code == 200
    draft = drafted.json()
    approval = {
        "draft_id": draft["draft_id"],
        "decision": "approve",
        "seen_hash": draft["seen_hash"],
    }
    assert draft["official_name"] == "Seizure"
    assert draft["plain_words"] == "seizures"
    assert "brain" in draft["explanation"]
    assert set(approval) == {"draft_id", "decision", "seen_hash"}

    missing = client.post(f"/cases/{CASE_ID}/approvals", json=approval)
    assert missing.status_code == 401

    session = client.post("/session", json={"name": "caregiver"})
    assert session.status_code == 200

    forged = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={**approval, "reviewer": "someone-else"},
    )
    assert forged.status_code == 422

    accepted = client.post(f"/cases/{CASE_ID}/approvals", json=approval)
    assert accepted.status_code == 200

    with psycopg.connect(DATABASE_URL) as connection:
        decision = connection.execute(
            """
            SELECT reviewer, decision, body_hash
            FROM app.decision WHERE draft_id = %s::uuid
            """,
            (draft["draft_id"],),
        ).fetchone()
        observation = connection.execute(
            "SELECT kind, body FROM app.observation WHERE draft_id = %s::uuid",
            (draft["draft_id"],),
        ).fetchone()
        status = connection.execute(
            "SELECT status FROM app.draft WHERE id = %s::uuid",
            (draft["draft_id"],),
        ).fetchone()
        snapshots = connection.execute(
            "SELECT count(*) FROM app.snapshot WHERE case_id = %s::uuid",
            (CASE_ID,),
        ).fetchone()
    assert decision == ("caregiver", "approve", draft["seen_hash"])
    assert status == ("approved",)
    assert snapshots == (1,)
    assert observation is not None
    assert observation[0] == "hpo_term"
    assert observation[1]["hpo_id"] == "HP:0001250"
    assert observation[1]["label"] == "Seizure"

    again = client.post(f"/cases/{CASE_ID}/approvals", json=approval)
    assert again.status_code == 409
    with psycopg.connect(DATABASE_URL) as connection:
        count = connection.execute(
            "SELECT count(*) FROM app.observation WHERE case_id = %s::uuid",
            (CASE_ID,),
        ).fetchone()
    assert count == (1,)


def test_uncertain_presence_cannot_be_approved(client: TestClient) -> None:
    drafted = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001252", "label": "Hypotonia", "presence": "uncertain"},
    )
    assert drafted.status_code == 200
    draft = drafted.json()
    assert draft["plain_words"] == "low muscle tone"
    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    refused = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert refused.status_code == 422
    with psycopg.connect(DATABASE_URL) as connection:
        status = connection.execute(
            "SELECT status FROM app.draft WHERE id = %s::uuid",
            (draft["draft_id"],),
        ).fetchone()
        observations = connection.execute(
            "SELECT count(*) FROM app.observation WHERE case_id = %s::uuid",
            (CASE_ID,),
        ).fetchone()
    assert status == ("pending",)
    assert observations == (0,)
