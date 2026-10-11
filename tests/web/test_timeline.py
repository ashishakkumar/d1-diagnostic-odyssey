"""The case timeline is the accepted facts, newest first."""

import pytest
from fastapi.testclient import TestClient
from support import wipe

CASE_ID = "00000000-0000-4000-8000-0000000000a2"


@pytest.fixture
def client():
    wipe(CASE_ID)
    from app.routes.notebook import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    wipe(CASE_ID)


def _approve(client: TestClient, draft: dict) -> None:
    response = client.post(
        f"/cases/{CASE_ID}/approvals",
        json={
            "draft_id": draft["draft_id"],
            "decision": "approve",
            "seen_hash": draft["seen_hash"],
        },
    )
    assert response.status_code == 200


def test_timeline_is_empty_until_something_is_accepted(client: TestClient) -> None:
    response = client.get(f"/cases/{CASE_ID}/timeline")
    assert response.status_code == 200
    assert response.json() == {"case_id": CASE_ID, "events": []}


def test_timeline_lists_accepted_facts_newest_first(client: TestClient) -> None:
    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    first = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"},
    ).json()
    _approve(client, first)
    second = client.post(
        f"/cases/{CASE_ID}/term-drafts",
        json={"hpo_id": "HP:0001252", "label": "Hypotonia", "presence": "present"},
    ).json()
    _approve(client, second)

    events = client.get(f"/cases/{CASE_ID}/timeline").json()["events"]
    assert [event["body"]["label"] for event in events] == ["Hypotonia", "Seizure"]
    assert events[0]["at"] >= events[1]["at"]
    assert events[0]["kind"] == "hpo_term"
