"""The harness ranks with the frequency-bin scorer, not the term-overlap stand-in."""

import inspect
import json
from pathlib import Path

import pytest

from d1_eval.frequency import FrequencyBinScorer, frequency_table
from d1_eval.harness import DiseaseScore
from scoring import catalogue_score, to_public

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "scoring" / "fixtures"
ORPHA = (
    Path(__file__).resolve().parents[2] / "tests" / "ingest" / "fixtures" / "en_product4_mini.xml"
)


def test_diseases_outside_the_unique_map_remain_in_the_corpus() -> None:
    rows, orpha_to_disease = frequency_table(ORPHA, {})
    assert orpha_to_disease == {}
    assert rows
    assert {row["hpo_id"] for row in rows} == {"HP:0001250", "HP:0001251"}
    assert all(row["corpus_only"] is True for row in rows)


def test_frequency_rows_follow_the_orphanet_bin_names() -> None:
    rows, orpha_to_disease = frequency_table(ORPHA, {"OMIM:1": {"ORPHA:999999"}})
    assert orpha_to_disease == {"ORPHA:999999": "OMIM:1"}
    by_hpo = {row["hpo_id"]: row["bin"] for row in rows}
    assert by_hpo == {"HP:0001250": "very_frequent", "HP:0001251": "occasional"}
    shared = {"OMIM:1": {"ORPHA:999999"}, "OMIM:2": {"ORPHA:999999"}}
    shared_rows, shared_map = frequency_table(ORPHA, shared)
    assert shared_map == {}
    assert shared_rows
    assert all(row["corpus_only"] is True for row in shared_rows)


def test_the_harness_scorer_calls_the_real_catalogue_and_has_no_gene_argument() -> None:
    rows = json.loads((FIXTURES / "frequencies.json").read_text())
    mapping = {"ORPHA:9000001": "OMIM:111", "ORPHA:9000002": "OMIM:222"}
    scorer = FrequencyBinScorer(rows, mapping)
    assert "gene" not in inspect.signature(scorer.score).parameters

    separated = scorer.score(["HP:0001166", "HP:0000272"])
    public = to_public(
        catalogue_score(
            [("HP:0001166", "present"), ("HP:0000272", "present")],
            rows,
        )
    )
    assert public["evidence"]["confident"] is True
    assert separated[0] == DiseaseScore("OMIM:111", pytest.approx(3.6))

    tied = scorer.score(["HP:0001250"])
    assert tied == []
