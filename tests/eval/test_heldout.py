"""Locks for the one held-out look. These tests do not read the store."""

import pytest

from d1_eval.harness import _genes
from d1_eval.heldout import (
    LOCKED_ABSTAIN,
    LOCKED_BECAUSE,
    LOCKED_WINNER,
    mean_over_present,
    require_locked_choice,
    splice_results,
    with_decoy_gene,
)


def _choice() -> dict:
    return {
        "winner": LOCKED_WINNER,
        "shipped_because": LOCKED_BECAUSE,
        "test_scored": False,
        "candidates": {LOCKED_WINNER: {"abstain": LOCKED_ABSTAIN}},
    }


def test_locked_choice_accepts_the_validation_record() -> None:
    require_locked_choice(_choice())


def test_locked_choice_rejects_a_different_winner() -> None:
    payload = _choice()
    payload["winner"] = "degree_corrected"
    with pytest.raises(RuntimeError, match="winner"):
        require_locked_choice(payload)


def test_locked_choice_rejects_a_second_test_look() -> None:
    payload = _choice()
    payload["test_scored"] = True
    with pytest.raises(RuntimeError, match="already scored"):
        require_locked_choice(payload)


def test_decoy_gene_leaves_the_phenotype_rows() -> None:
    packet = {
        "id": "packet",
        "phenotypicFeatures": [{"type": {"id": "HP:0001250"}, "excluded": False}],
        "interpretations": [{"diagnosis": {"disease": {"id": "OMIM:1"}}}],
    }
    cloned = with_decoy_gene(packet)
    assert cloned["phenotypicFeatures"] == packet["phenotypicFeatures"]
    assert packet["interpretations"] == [{"diagnosis": {"disease": {"id": "OMIM:1"}}}]
    assert "DECOYGENE" in _genes(cloned)


def test_disease_mean_omits_a_disease_with_no_packet() -> None:
    grouped = {"D1": [(1, False)], "D2": [(None, True)]}
    percentage, precision, n_diseases = mean_over_present(grouped, 1)
    assert n_diseases == 2
    assert percentage == pytest.approx(0.5)
    assert precision == pytest.approx(0.5)


def test_results_splice_keeps_the_frequency_bin_curve(tmp_path) -> None:
    path = tmp_path / "RESULTS.md"
    path.write_text(
        "# Public\n\nfrequency comparison\n\n"
        "## Calibration\n\n| row |\n\n"
        "## Held-out split\n\n| full | train |\n\n"
        "# Public-case method results\n\nterm overlap\n"
    )
    section = "# Resnik best-match average, held-out once\n\nmeasured\n"
    splice_results(path, section)
    splice_results(path, section)
    text = path.read_text()
    marker = "# Resnik best-match average, held-out once"
    assert text.count(marker) == 1
    assert text.index("## Calibration") < text.index(marker)
    assert text.index("## Held-out split") < text.index(marker)
    assert text.index("measured") < text.index("# Public-case method results")
