"""Pending symptom drafts are what the accept form lists."""

import pytest
from fastapi.testclient import TestClient
from support import wipe

CASE_ID = "00000000-0000-4000-8000-0000000000a5"


@pytest.fixture
def client():
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def test_case_list_and_pending_terms(client: TestClient) -> None:
    assert client.get("/cases").json() == {"cases": []}
    assert client.get("/session").status_code == 401

    drafted = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"},
    )
    assert drafted.status_code == 200
    draft = drafted.json()

    cases = client.get("/cases").json()["cases"]
    assert cases == [CASE_ID]

    pending = client.get(f"/cases/{CASE_ID}/term-drafts").json()["drafts"]
    assert len(pending) == 1
    assert pending[0]["draft_id"] == draft["draft_id"]
    assert pending[0]["seen_hash"] == draft["seen_hash"]
    assert pending[0]["plain_words"] == "seizures"
    assert pending[0]["official_name"] == "Seizure"
    assert pending[0]["explanation"]

    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    assert client.get("/session").json() == {"name": "ashish"}
    accepted = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert accepted.status_code == 200
    assert client.get(f"/cases/{CASE_ID}/term-drafts").json()["drafts"] == []
