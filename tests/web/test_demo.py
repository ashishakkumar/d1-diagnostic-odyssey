"""Five synthetic cases through the API, including abstention and the stop screen."""

import pytest
from fastapi.testclient import TestClient
from support import wipe

from app.demo_cases import DEMO_CASES
from d1_contracts import parse_report

CASE_IDS = [str(case["case_id"]) for case in DEMO_CASES]


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


def _load(client: TestClient, slug: str) -> str:
    response = client.post(f"/demo/cases/{slug}/load")
    assert response.status_code == 200
    return str(response.json()["case_id"])


def test_five_demo_cases_score_without_a_dose_or_a_moved_comparison(client: TestClient) -> None:
    assert client.post("/session", json={"name": "ashish"}).status_code == 200
    listed = client.get("/demo/cases")
    assert listed.status_code == 200
    assert [item["slug"] for item in listed.json()["cases"]] == [
        "separated",
        "abstain",
        "stable",
        "variant",
        "limits",
    ]

    separated_id = _load(client, "separated")
    separated = parse_report(client.get(f"/cases/{separated_id}/report").json())
    assert separated.abstained is False
    assert separated.leading_orphanet_id == "ORPHA:9000001"
    assert separated.margin is None
    assert separated.margin_reason == "runner_up_ratio_is_zero"
    page = client.get(f"/cases/{separated_id}/summary")
    assert page.status_code == 200
    assert "ORPHA:9000001" in page.text
    assert "ratio of zero" in page.text
    assert "long for the hand" in page.text
    assert "does not choose a dose" in page.text
    assert "112" in page.text

    abstain_id = _load(client, "abstain")
    abstain = parse_report(client.get(f"/cases/{abstain_id}/report").json())
    assert abstain.abstained is True
    assert abstain.abstain_reason == "many_within_factor"
    abstain_page = client.get(f"/cases/{abstain_id}/summary")
    assert "did not separate a first row" in abstain_page.text
    assert "does not mean you are well" in abstain_page.text

    stable_id = _load(client, "stable")
    stable = parse_report(client.get(f"/cases/{stable_id}/report").json())
    assert stable.abstained is False
    assert stable.margin is not None and stable.margin > 1
    assert stable.margin_reason is None
    assert stable.leading_orphanet_id == "ORPHA:9000011"

    variant_id = _load(client, "variant")
    variant = parse_report(client.get(f"/cases/{variant_id}/report").json())
    assert variant.model_dump() == separated.model_dump()
    off = client.get(f"/cases/{variant_id}/population-prior")
    assert off.status_code == 200
    assert off.json()["opted_in"] is False
    assert off.json()["found"] is False
    on = client.get(f"/cases/{variant_id}/population-prior?opt_in=true")
    assert on.json()["found"] is True
    assert on.json()["experimental"] is True
    assert on.json()["allele_frequency"] == 0.00012
    assert "did not call gnomAD" in on.json()["limits"]
    again = parse_report(client.get(f"/cases/{variant_id}/report").json())
    assert again.model_dump() == separated.model_dump()

    limits_id = _load(client, "limits")
    limits_page = client.get(f"/cases/{limits_id}/summary")
    assert "does not choose a dose" in limits_page.text

    stopped = client.post(
        f"/cases/{separated_id}/variants",
        json={
            "gene_symbol": "FBN1",
            "variant": "NM_000138.5:c.1A>G",
            "lab_words": "Unconsciousness.",
            "report_date": "2024-03-01",
        },
    )
    assert stopped.status_code == 409
    assert "Stop" in stopped.json()["detail"]["body"]
    assert "probability" not in client.get(f"/cases/{separated_id}/report").json()
