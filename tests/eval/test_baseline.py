"""Degree baseline and precision@k. No threshold is fit on a held-out split."""

import math

import pytest

from d1_eval.baseline import (
    DegreeBaseline,
    disease_retrieval,
    is_hit,
    packet_retrieval,
    phenotype_profiles,
    precision_at_k,
)
from d1_eval.harness import DiseaseScore, EvalCase, rank_case, rank_diseases
from scoring.catalogue import catalogue_score, prepare_catalogue, rank_products


def test_degree_score_is_the_sum_of_negative_log_frequencies() -> None:
    profiles = {
        "OMIM:1": {"HP:1", "HP:2"},
        "OMIM:2": {"HP:1"},
    }
    scorer = DegreeBaseline(profiles)
    assert scorer.weights["HP:1"] == pytest.approx(-math.log(1))
    assert scorer.weights["HP:2"] == pytest.approx(-math.log(0.5))
    scored = {item.disease_id: item.score for item in scorer.score(["HP:1", "HP:2", "HP:missing"])}
    assert scored["OMIM:1"] == pytest.approx(-math.log(0.5))
    assert scored["OMIM:2"] == pytest.approx(0.0)
    assert "gene" not in DegreeBaseline.score.__code__.co_varnames


def test_an_excluded_bin_does_not_count_toward_degree() -> None:
    rows = [
        {"orphanet_id": "ORPHA:1", "hpo_id": "HP:1", "bin": "frequent"},
        {"orphanet_id": "ORPHA:1", "hpo_id": "HP:2", "bin": "excluded"},
        {"orphanet_id": "ORPHA:9", "hpo_id": "HP:1", "bin": "frequent", "corpus_only": True},
    ]
    profiles = phenotype_profiles(rows, {"ORPHA:1": "OMIM:1"}, {"OMIM:1", "OMIM:2"})
    assert profiles == {"OMIM:1": {"HP:1"}, "OMIM:2": set()}


def test_precision_keeps_denominator_k_when_the_list_is_shorter() -> None:
    assert precision_at_k(1, False, 5, list_length=2) == pytest.approx(0.2)
    assert precision_at_k(6, False, 5, list_length=9) == 0.0
    assert precision_at_k(None, True, 5, list_length=0) == 0.0
    assert is_hit(1, False, 1) is True
    assert is_hit(2, False, 1) is False
    assert is_hit(1, True, 1) is False


def test_ties_take_the_worst_rank_before_precision() -> None:
    ranks = rank_diseases([DiseaseScore("A", 3.0), DiseaseScore("B", 3.0), DiseaseScore("C", 1.0)])
    assert ranks["A"] == 2
    assert precision_at_k(ranks["A"], False, 1, list_length=3) == 0.0
    assert precision_at_k(ranks["A"], False, 5, list_length=3) == pytest.approx(0.2)


def test_packet_and_disease_denominators_count_abstention_as_a_miss() -> None:
    queries = [(1, False), (None, True), (4, False)]
    hits, count, percentage, precision = packet_retrieval(queries, 1)
    assert (hits, count) == (1, 3)
    assert percentage == pytest.approx(1 / 3)
    assert precision == pytest.approx(1 / 3)
    hits5, count5, percentage5, precision5 = packet_retrieval(queries, 5)
    assert (hits5, count5) == (2, 3)
    assert percentage5 == pytest.approx(2 / 3)
    assert precision5 == pytest.approx((1 / 5 + 1 / 5) / 3)
    percentage_d, precision_d, n_diseases, empty = disease_retrieval(
        {"OMIM:1": [(1, False), (None, True)], "OMIM:2": []},
        ["OMIM:1", "OMIM:2", "OMIM:3"],
        1,
    )
    assert n_diseases == 3
    assert empty == 2
    assert percentage_d == pytest.approx((0.5 + 0.0 + 0.0) / 3)
    assert precision_d == pytest.approx((0.5 + 0.0 + 0.0) / 3)


def test_rank_products_matches_the_catalogue_report() -> None:
    rows = [
        {
            "id": "00000000-0000-4000-8000-000000000001",
            "source": "Orphanet",
            "version": "fixture",
            "orphanet_id": "ORPHA:9000001",
            "mondo_id": "MONDO:1",
            "hpo_id": "HP:0001166",
            "bin": "obligate",
        },
        {
            "id": "00000000-0000-4000-8000-000000000002",
            "source": "Orphanet",
            "version": "fixture",
            "orphanet_id": "ORPHA:9000002",
            "mondo_id": "MONDO:2",
            "hpo_id": "HP:0001166",
            "bin": "obligate",
        },
    ]
    accepted = [("HP:0001166", "present")]
    report = catalogue_score(accepted, rows)
    products, confident = rank_products(accepted, prepare_catalogue(rows))
    assert confident is report.confident
    assert [(item.orphanet_id, item.lower_ratio) for item in products] == [
        (disease.orphanet_id, pytest.approx(disease.lower_ratio)) for disease in report.diseases
    ]


def test_degree_baseline_abstains_when_ten_diseases_tie_for_best() -> None:
    profiles = {f"OMIM:{index}": {"HP:rare"} for index in range(10)}
    profiles["OMIM:other"] = set()
    scorer = DegreeBaseline(profiles)

    class _Term:
        hpo_id = "HP:rare"
        presence = "present"

    class _Pipeline:
        accepted_terms = [_Term()]

    case = EvalCase(
        pipeline=_Pipeline(),
        truth_disease_id="OMIM:0",
        truth_genes=(),
        created=None,
        packet_id="packet",
        source={},
    )
    ranked = rank_case(case, scorer, set(profiles), tied_at_best=10)
    assert ranked.no_confident is True
    assert ranked.scored is True
    assert scorer.weights["HP:rare"] > 0
