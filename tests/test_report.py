"""The shared contract carries a catalogue report and a plain-language explanation."""

import json
from pathlib import Path

import pytest

from d1_contracts import HpoTermDraft, Report, parse_report
from test_contract_roundtrip import sample_pipeline

ROOT = Path(__file__).resolve().parents[1]

CASE = "00000000-0000-4000-8000-000000000010"
TERM = {
    "hpo_id": "HP:0001250",
    "relation": "supports",
    "source": "orphanet-en_product4",
    "version": "2026-06-23-synthetic",
}


def _report(**extra: object) -> dict:
    body: dict = {
        "evidence": [TERM],
        "margin": 2.0,
        "abstained": False,
    }
    body.update(extra)
    return body


def test_hpo_term_draft_stores_a_plain_language_explanation() -> None:
    draft = HpoTermDraft.model_validate(
        {
            "id": "00000000-0000-4000-8000-000000000001",
            "case_id": CASE,
            "hpo_id": "HP:0001250",
            "label": "Seizure",
            "presence": "present",
            "explanation": (
                "A burst of brain activity that changes movement, awareness, or sensation."
            ),
        }
    )
    assert draft.explanation is not None
    assert "brain" in draft.explanation


def test_a_probability_is_valid_only_together_with_a_reliability_curve() -> None:
    parse_report(_report())
    curve = [
        {"predicted": 0.2, "observed": 0.1},
        {"predicted": 0.8, "observed": 0.7},
    ]
    parsed = parse_report(_report(probability=0.4, reliability_curve=curve))
    assert parsed.probability == 0.4
    assert isinstance(parsed, Report)
    with pytest.raises(Exception):
        parse_report(_report(probability=0.4))
    with pytest.raises(Exception):
        parse_report(_report(reliability_curve=curve))
    with pytest.raises(Exception):
        parse_report(
            _report(probability=0.4, reliability_curve=[{"predicted": 0.5, "observed": 0.5}])
        )


def test_the_schema_names_the_report_and_the_explanation() -> None:
    schema = json.loads((ROOT / "contracts" / "pipeline.schema.json").read_text())
    report = schema["$defs"]["Report"]
    assert {"evidence", "margin", "abstained"} <= set(report["required"])
    assert report["dependentRequired"]["probability"] == ["reliability_curve"]
    assert report["dependentRequired"]["reliability_curve"] == ["probability"]
    explanation = schema["$defs"]["HpoTermDraft"]["properties"]["explanation"]
    assert explanation["type"] == "string"
    raw = sample_pipeline()
    raw["report"] = _report()
    from d1_contracts import parse_pipeline

    assert parse_pipeline(raw).report is not None
    raw["report"] = _report(probability=0.4)
    with pytest.raises(Exception):
        parse_pipeline(raw)
