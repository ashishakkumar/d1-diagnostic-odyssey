"""Precision and recall on a ranking. Absent tool output stays not-run."""

from pathlib import Path

from d1_engine.tools import parse_exomiser_genes


def precision_recall(ranked: list[str], truth: str, k: int) -> tuple[float, float]:
    hit = 1.0 if truth in ranked[:k] else 0.0
    precision = hit / k if k else 0.0
    return precision, hit


def evaluate(*, jar: Path, tool_output: Path | None, truth: str | None = None, k: int = 1) -> dict:
    if tool_output is None or not jar.is_file() or not tool_output.is_file():
        return {
            "status": "not-run",
            "ranks": [],
            "reason": "the tool jar or its output file is absent",
        }
    rows = parse_exomiser_genes(tool_output.read_text(encoding="utf-8"), version="15.1.0")
    result: dict = {"status": "parsed-output-file", "ranks": rows}
    if truth is not None:
        labels = [str(row["label"]) for row in rows]
        precision, recall = precision_recall(labels, truth, k)
        result["precision"] = precision
        result["recall"] = recall
    return result
