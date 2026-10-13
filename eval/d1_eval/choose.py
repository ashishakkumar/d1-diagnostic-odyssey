"""Choose a ranker on fit and validation. This module does not score the test split.

Test packets are the existing held-out split: SHA-256(packet id) modulo 5, remainder 0.
Validation packets are the train packets whose SHA-256(packet id + newline + "validation")
modulo 4 is 0. Everything else in train is fit.

A candidate beats the degree baseline on validation when percentage@k and precision@k
at k=1 and k=5 are all strictly greater. Abstention settings are chosen on fit only,
because an abstention is a miss. The degree baseline keeps its published rule
(best score <= 0, or at least 10 diseases tied at the best score).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from d1_eval.baseline import DegreeBaseline, packet_retrieval, phenotype_profiles
from d1_eval.candidates import (
    Bm25Score,
    DegreeCorrectedFrequency,
    InformationContentOverlap,
    PhenomizerScore,
    ResnikBestMatch,
    all_parents,
    bin_lowers,
    build_index,
)
from d1_eval.frequency import frequency_table
from d1_eval.harness import (
    DiseaseScore,
    cohort_split,
    load_cases,
    load_pins,
    orphanet_from_mondo_nodes,
    present_hpo_ids,
    rank_diseases,
    unique_orphanet,
)

AbstainMode = Literal["raw", "tie10", "factor10"]
MODES: tuple[AbstainMode, ...] = ("raw", "tie10", "factor10")
FALLBACK = "degree_corrected"


def split_role(packet_id: str) -> Literal["fit", "validation", "test"]:
    if cohort_split(packet_id) == "test":
        return "test"
    digest = hashlib.sha256(f"{packet_id}\nvalidation".encode()).hexdigest()
    if int(digest[:8], 16) % 4 == 0:
        return "validation"
    return "fit"


def _abstained(mode: AbstainMode, best: float, ties: int, close: int) -> bool:
    if best <= 0:
        return True
    if mode == "raw":
        return False
    if mode == "tie10":
        return ties >= 10
    if mode == "factor10":
        return close >= 10
    raise ValueError(mode)


def _snapshot(
    scores: Sequence[DiseaseScore],
    truth: str,
) -> tuple[int | None, float, int, int]:
    if not scores:
        return None, 0.0, 0, 0
    ranks = rank_diseases(scores)
    best = max(item.score for item in scores)
    ties = sum(1 for item in scores if item.score == best)
    if best > 0:
        close = sum(1 for item in scores if item.score + 1e-12 >= best / 2.0)
    else:
        close = len(scores)
    return ranks.get(truth), best, ties, close


def _queries(
    rows: Sequence[tuple[str, tuple[int | None, float, int, int]]],
    role: str,
    mode: AbstainMode,
) -> list[tuple[int | None, bool]]:
    found = []
    for row_role, snapshot in rows:
        if row_role != role:
            continue
        rank, best, ties, close = snapshot
        found.append((rank, _abstained(mode, best, ties, close)))
    return found


def _metrics(
    rows: Sequence[tuple[str, tuple[int | None, float, int, int]]],
    role: str,
    mode: AbstainMode,
) -> dict[int, dict[str, float]]:
    queries = _queries(rows, role, mode)
    metrics: dict[int, dict[str, float]] = {}
    for k in (1, 5):
        hits, count, percentage, precision = packet_retrieval(queries, k)
        metrics[k] = {
            "hits": float(hits),
            "count": float(count),
            "percentage": percentage,
            "precision": precision,
        }
    return metrics


def _better(left: dict[int, dict[str, float]], right: dict[int, dict[str, float]]) -> bool:
    if left[1]["percentage"] != right[1]["percentage"]:
        return left[1]["percentage"] > right[1]["percentage"]
    return left[5]["percentage"] > right[5]["percentage"]


def _beats(candidate: dict[int, dict[str, float]], baseline: dict[int, dict[str, float]]) -> bool:
    for k in (1, 5):
        if candidate[k]["percentage"] <= baseline[k]["percentage"]:
            return False
        if candidate[k]["precision"] <= baseline[k]["precision"]:
            return False
    return True


def _mode_on_fit(
    rows: Sequence[tuple[str, tuple[int | None, float, int, int]]],
) -> AbstainMode:
    chosen: AbstainMode = "raw"
    best_metrics = _metrics(rows, "fit", chosen)
    for mode in MODES[1:]:
        metrics = _metrics(rows, "fit", mode)
        if _better(metrics, best_metrics):
            chosen = mode
            best_metrics = metrics
    return chosen


def choose(data: Path) -> dict:
    """Score fit and validation only. Test packets are skipped."""
    pins = load_pins()
    loaded = load_cases(data / "all_phenopackets.zip")
    mapping = orphanet_from_mondo_nodes(data / "mondo_nodes.tsv")
    unique, _excluded = unique_orphanet(loaded.disease_ids, mapping)
    kept = {disease: mapping[disease] for disease in unique}
    rows, orpha_to_disease = frequency_table(data / "en_product4.xml", kept)
    profiles = phenotype_profiles(rows, orpha_to_disease, unique)
    parents = all_parents(data / "hp.obo")
    index = build_index(profiles, parents)
    scorers: dict[str, Callable[[Sequence[str]], list[DiseaseScore]]] = {
        "degree": DegreeBaseline(profiles).score,
        "ic_overlap": InformationContentOverlap(index).score,
        "resnik_bma": ResnikBestMatch(index).score,
        "phenomizer": PhenomizerScore(index).score,
        "bm25": Bm25Score(profiles).score,
        "degree_corrected": DegreeCorrectedFrequency(
            bin_lowers(rows, orpha_to_disease, unique),
            profiles,
        ).score,
    }
    recorded: dict[str, list[tuple[str, tuple[int | None, float, int, int]]]] = {
        name: [] for name in scorers
    }
    seen = {"fit": 0, "validation": 0, "test_skipped": 0}
    for case in loaded.cases:
        if case.truth_disease_id not in unique:
            continue
        role = split_role(case.packet_id)
        if role == "test":
            seen["test_skipped"] += 1
            continue
        seen[role] += 1
        terms = present_hpo_ids(case)
        for name, score in scorers.items():
            snapshot = _snapshot(score(terms), case.truth_disease_id)
            recorded[name].append((role, snapshot))
        total = seen["fit"] + seen["validation"]
        if total % 500 == 0:
            print(f"scored_fit_and_validation={total}", flush=True)
    degree_validation = _metrics(recorded["degree"], "validation", "tie10")
    report: dict[str, dict] = {}
    beaters: list[str] = []
    for name, rows_for_name in recorded.items():
        if name == "degree":
            continue
        mode = _mode_on_fit(rows_for_name)
        validation = _metrics(rows_for_name, "validation", mode)
        fit = _metrics(rows_for_name, "fit", mode)
        did_beat = _beats(validation, degree_validation)
        report[name] = {"abstain": mode, "fit": fit, "validation": validation, "beats": did_beat}
        if did_beat:
            beaters.append(name)
    if beaters:
        winner = max(
            beaters,
            key=lambda name: (
                report[name]["validation"][1]["percentage"],
                report[name]["validation"][5]["percentage"],
            ),
        )
        shipped_because = "beats_degree_on_validation"
    else:
        winner = FALLBACK
        shipped_because = "none_beat_degree_on_validation"
    return {
        "store_sha256": pins.store_sha256,
        "counts": seen,
        "degree_validation_tie10": degree_validation,
        "candidates": report,
        "winner": winner,
        "shipped_because": shipped_because,
        "test_scored": False,
    }


def main(data: Path, out: Path) -> None:
    payload = choose(data)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    summary = {
        "winner": payload["winner"],
        "because": payload["shipped_because"],
        "counts": payload["counts"],
    }
    print(json.dumps(summary))
