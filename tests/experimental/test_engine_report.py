"""Tool files become a pipeline report. Scores stay the tools' scores."""

import json
from pathlib import Path

import pytest
from d1_safety.scan import scan

from d1_contracts import parse_report
from d1_engine.gate import GRADE
from d1_engine.report import build_report, combine, sentences_of
from d1_engine.tools import parse_exomiser_genes, parse_lirical

ROOT = Path(__file__).resolve().parents[2]


def _rank(label: str, score: float, *, kind: str = "gene", tool: str = "exomiser") -> dict:
    version = "15.1.0" if tool == "exomiser" else "2.4.1"
    score_name = "EXOMISER_GENE_COMBINED_SCORE" if tool == "exomiser" else "compositeLR"
    return {
        "kind": kind,
        "label": label,
        "tool": tool,
        "tool_version": version,
        "score": score,
        "score_name": score_name,
    }


def test_the_pipeline_report_can_carry_tool_ranks() -> None:
    raw = {
        "evidence": [],
        "margin": 9.0,
        "abstained": False,
        "grade": GRADE,
        "ranks": [_rank("SYN1", 0.9)],
    }
    parsed = parse_report(raw)
    assert parsed.grade == GRADE
    assert parsed.ranks is not None
    assert parsed.ranks[0].label == "SYN1"
    assert parsed.probability is None
    assert parsed.reliability_curve is None


def test_a_report_uses_tool_scores_and_states_no_probability() -> None:
    report = build_report([_rank("SYN1", 0.9), _rank("DEC1", 0.1)])
    parsed = parse_report(report)
    assert parsed.grade == GRADE
    assert parsed.abstained is False
    assert parsed.probability is None
    assert "probability" not in report
    assert report["ranks"][0]["label"] == "SYN1"
    assert report["ranks"][0]["score"] == 0.9
    for sentence in sentences_of(report):
        assert scan(sentence) == []


def test_close_tool_scores_abstain() -> None:
    report = build_report([_rank("SYN1", 0.5), _rank("DEC1", 0.4)])
    parsed = parse_report(report)
    assert parsed.abstained is True
    assert parsed.margin is None
    assert parsed.probability is None
    for sentence in sentences_of(report):
        assert scan(sentence) == []


def test_phenotype_and_genotype_disagreement_abstains() -> None:
    report = combine(
        [_rank("SYN1", 0.9), _rank("DEC1", 0.1)],
        [_rank("DEC1", 0.8), _rank("SYN1", 0.2)],
    )
    assert report["abstained"] is True
    assert report["margin"] is None
    assert "probability" not in report
    for sentence in sentences_of(report):
        assert scan(sentence) == []


def test_a_sentence_the_scanner_rejects_is_not_returned() -> None:
    with pytest.raises(Exception):
        build_report([_rank("you have this", 0.9), _rank("DEC1", 0.1)])


def test_exomiser_tsv_keeps_the_tool_score_column() -> None:
    text = (
        "#RANK\tGENE_SYMBOL\tEXOMISER_GENE_COMBINED_SCORE\t"
        "EXOMISER_GENE_PHENO_SCORE\tEXOMISER_GENE_VARIANT_SCORE\n"
        "1\tSYN1\t0.90\t0.80\t0.70\n"
        "2\tDEC1\t0.10\t0.05\t0.20\n"
    )
    rows = parse_exomiser_genes(text, version="15.1.0")
    assert rows[0]["label"] == "SYN1"
    assert rows[0]["score_name"] == "EXOMISER_GENE_COMBINED_SCORE"
    assert rows[0]["score"] == 0.9
    assert rows[0]["tool"] == "exomiser"
    assert rows[0]["tool_version"] == "15.1.0"


def test_lirical_tsv_does_not_copy_the_post_test_column() -> None:
    text = (
        "rank\tdiseaseName\tdiseaseCurie\tpretestprob\tpostestprob\tcompositeLR\n"
        "1\tExample disease\tOMIM:1\t0.01\t0.8\t12.5\n"
        "2\tOther disease\tOMIM:2\t0.01\t0.2\t1.0\n"
    )
    rows = parse_lirical(text, version="2.4.1")
    blob = json.dumps(rows)
    assert rows[0]["kind"] == "disease"
    assert rows[0]["score_name"] == "compositeLR"
    assert rows[0]["score"] == 12.5
    assert rows[0]["label"] == "Example disease"
    assert "0.8" not in blob
    assert "postestprob" not in blob
    assert "pretestprob" not in blob
