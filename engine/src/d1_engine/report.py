"""Map upstream tool rows onto the pipeline report. No probability is added."""

from d1_safety.scan import scan

from d1_contracts import parse_report
from d1_engine.gate import BANNER, GRADE, GateError

# Same separation the catalogue uses: a first row within a factor of 2 of the next abstains.
# This is not a fitted cutoff and it is not a probability.
FACTOR = 2.0


def sentences_of(report: dict) -> list[str]:
    lines = [BANNER, GRADE]
    fact = report.get("margin_fact")
    if isinstance(fact, str):
        lines.append(fact)
    for row in report.get("ranks") or []:
        lines.append(str(row["label"]))
    return lines


def _clean(report: dict) -> None:
    for line in sentences_of(report):
        found = scan(line)
        if found:
            raise GateError(" ".join(found))


def _separate(scores: list[float]) -> tuple[bool, float | None, str]:
    if not scores:
        return True, None, "No tool output was read, so this report abstains."
    if len(scores) == 1:
        return True, None, "There is no second row, so this report abstains."
    best, runner = scores[0], scores[1]
    if runner <= 0 or best <= FACTOR * runner:
        return (
            True,
            None,
            (
                "The top score is not separated from the next score by a factor of 2, "
                "so this report abstains."
            ),
        )
    return (
        False,
        best / runner,
        ("The first row is ahead of the next by more than a factor of 2 on the tool score."),
    )


def build_report(ranks: list[dict]) -> dict:
    ordered = sorted(ranks, key=lambda row: float(row["score"]), reverse=True)
    abstained, margin, fact = _separate([float(row["score"]) for row in ordered])
    body: dict = {
        "evidence": [],
        "margin": margin,
        "margin_fact": fact,
        "abstained": abstained,
        "grade": GRADE,
        "ranks": ordered,
    }
    _clean(body)
    parse_report(body)
    return body


def _top(rows: list[dict]) -> str:
    return str(max(rows, key=lambda row: float(row["score"]))["label"])


def combine(phenotype: list[dict], genotype: list[dict]) -> dict:
    report = build_report([*phenotype, *genotype])
    if phenotype and genotype and _top(phenotype) != _top(genotype):
        report["abstained"] = True
        report["margin"] = None
        report["margin_fact"] = (
            "Phenotype-only and genotype-only name different first rows, so this report abstains."
        )
        _clean(report)
        parse_report(report)
    return report
