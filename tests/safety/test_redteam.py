"""Red-team prompts and rows. A forbidden sentence must not come back."""

import tomllib
from pathlib import Path

import pytest
from d1_safety.redflag import stop_screen
from d1_safety.render import SafetyError, render


@pytest.fixture(autouse=True)
def _united_kingdom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("D1_COUNTRY", "gb")


_CASES = tomllib.loads((Path(__file__).parent / "redteam.toml").read_text())["case"]
_ROW_KEYS = (
    "label",
    "hpo_id",
    "presence",
    "source",
    "version",
    "subject_key",
    "previous_text",
    "current_text",
    "report_date",
    "gene_symbol",
    "lab_words",
    "confirmed_count",
    "prompt",
    "speaker",
)


def _row(case: dict) -> dict:
    return {key: case[key] for key in _ROW_KEYS if key in case}


@pytest.mark.parametrize("case", _CASES, ids=[case["id"] for case in _CASES])
def test_redteam_case(case: dict) -> None:
    kind = case["kind"]
    if kind == "reject":
        with pytest.raises(ValueError):
            render(case["template"], _row(case))
        return
    if kind == "block":
        with pytest.raises(SafetyError) as caught:
            render(case["template"], _row(case))
        assert case["rule"] in caught.value.rules
        return
    if kind == "allow":
        text, _quotes = render(case["template"], _row(case))
        assert case["must_contain"] in text
        return
    if kind == "stop":
        screen = stop_screen(case["text"])
        assert screen is not None
        for word in case["forbid"]:
            assert word not in screen["body"]
        return
    raise AssertionError(f"unknown kind {kind}")
