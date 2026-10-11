"""Formula checks for the candidate rankers. No store split is read."""

import math

import pytest

from d1_eval.candidates import (
    BM25_B,
    BM25_K1,
    Bm25Score,
    DegreeCorrectedFrequency,
    InformationContentOverlap,
    PhenomizerScore,
    ResnikBestMatch,
    build_index,
)
from d1_eval.harness import DiseaseScore


def _index():
    profiles = {"D1": {"HP:child"}, "D2": {"HP:other"}}
    parents = {
        "HP:child": ("HP:parent",),
        "HP:parent": ("HP:0000001",),
        "HP:other": ("HP:0000001",),
    }
    return build_index(profiles, parents)


def _by_id(scores: list[DiseaseScore]) -> dict[str, float]:
    return {item.disease_id: item.score for item in scores}


def test_resnik_and_overlap_prefer_the_annotated_disease() -> None:
    index = _index()
    information = -math.log(0.5)
    phenomizer = _by_id(PhenomizerScore(index).score(["HP:child"]))
    assert phenomizer["D1"] == pytest.approx(information)
    assert phenomizer["D2"] == pytest.approx(0.0)
    overlap = _by_id(InformationContentOverlap(index).score(["HP:child"]))
    assert overlap["D1"] > overlap["D2"]
    # A more specific patient term still matches through the parent.
    climbed = _by_id(PhenomizerScore(index).score(["HP:child"]))
    parent_query = _by_id(PhenomizerScore(index).score(["HP:parent"]))
    assert climbed["D1"] == pytest.approx(information)
    assert parent_query["D1"] == pytest.approx(information)


def test_best_match_average_uses_both_directions() -> None:
    index = _index()
    scores = _by_id(ResnikBestMatch(index).score(["HP:child"]))
    assert scores["D1"] > scores["D2"]
    assert "gene" not in PhenomizerScore.score.__code__.co_varnames
    assert "gene" not in ResnikBestMatch.score.__code__.co_varnames


def test_bm25_uses_the_fixed_defaults_and_the_rare_term() -> None:
    assert (BM25_K1, BM25_B) == (1.2, 0.75)
    scorer = Bm25Score({"D1": {"HP:rare"}, "D2": {"HP:common"}, "D3": {"HP:common"}})
    scores = _by_id(scorer.score(["HP:rare", "HP:common"]))
    assert scores["D1"] > scores["D2"]


def test_degree_corrected_frequency_matches_degree_on_obligate_and_does_not_go_negative() -> None:
    profiles = {"D1": {"HP:1"}, "D2": {"HP:1"}}
    scorer = DegreeCorrectedFrequency({"D1": {"HP:1": 1.0}, "D2": {"HP:1": 0.01}}, profiles)
    # P(HP:1) = 1, so -log(P) is 0 and both contributions stay 0.
    both = _by_id(scorer.score(["HP:1"]))
    assert both["D1"] == pytest.approx(0.0)
    assert both["D2"] == pytest.approx(0.0)
    rare = DegreeCorrectedFrequency(
        {"D1": {"HP:rare": 1.0}, "D2": {"HP:rare": 0.01}},
        {"D1": {"HP:rare"}, "D2": set()},
    )
    scored = _by_id(rare.score(["HP:rare"]))
    assert scored["D1"] == pytest.approx(-math.log(0.5))
    assert scored["D2"] == pytest.approx(0.0)
