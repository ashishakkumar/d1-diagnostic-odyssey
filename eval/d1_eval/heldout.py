"""One look at the held-out split for the ranker already chosen on validation.

This module does not choose a winner. It reads eval/choice.json, checks the locked
name and abstention, and scores that ranker on test packets only. Other candidates
are not scored here. A second call refuses once test_scored is true.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path

from d1_eval.baseline import DegreeBaseline, packet_retrieval, phenotype_profiles
from d1_eval.candidates import ResnikBestMatch, all_parents, build_index
from d1_eval.choose import _abstained, _snapshot, split_role
from d1_eval.frequency import FrequencyBinScorer, frequency_table
from d1_eval.harness import (
    DiseaseScore,
    _case_from_packet,
    _genes,
    load_cases,
    load_pins,
    orphanet_from_mondo_nodes,
    parents_from_obo,
    present_hpo_ids,
    unique_orphanet,
)
from scoring.catalogue import rank_products

LOCKED_WINNER = "resnik_bma"
LOCKED_BECAUSE = "beats_degree_on_validation"
LOCKED_ABSTAIN = "raw"
DEGREE_ABSTAIN = "tie10"
DECOY_GENE = "DECOYGENE"
MARKER = "# Resnik best-match average, held-out once"


def require_locked_choice(payload: Mapping) -> None:
    """Fail before any test packet is scored if the selection record moved."""
    if payload.get("test_scored") is True:
        raise RuntimeError("the test split was already scored")
    if payload.get("winner") != LOCKED_WINNER:
        raise RuntimeError("winner does not match the locked validation choice")
    if payload.get("shipped_because") != LOCKED_BECAUSE:
        raise RuntimeError("selection reason does not match the locked validation choice")
    candidate = payload.get("candidates", {}).get(LOCKED_WINNER, {})
    if candidate.get("abstain") != LOCKED_ABSTAIN:
        raise RuntimeError("abstention does not match the fit-split choice")


def with_decoy_gene(packet: dict) -> dict:
    """Copy a packet and add a gene symbol. Phenotype rows stay as they were."""
    cloned = deepcopy(packet)
    interpretations = list(cloned.get("interpretations") or [])
    if not interpretations:
        interpretations = [{}]
    current = dict(interpretations[0])
    diagnosis = dict(current.get("diagnosis") or {})
    genomics = list(diagnosis.get("genomicInterpretations") or [])
    genomics.append({"gene": {"symbol": DECOY_GENE}})
    diagnosis["genomicInterpretations"] = genomics
    current["diagnosis"] = diagnosis
    interpretations[0] = current
    cloned["interpretations"] = interpretations
    return cloned


def mean_over_present(
    packets_by_disease: Mapping[str, Sequence[tuple[int | None, bool]]],
    k: int,
) -> tuple[float, float, int]:
    """Unweighted mean over diseases that have a packet. Empty diseases are omitted."""
    diseases = sorted(packets_by_disease)
    if not diseases:
        return 0.0, 0.0, 0
    percentage_total = 0.0
    precision_total = 0.0
    for disease in diseases:
        _hits, _count, percentage, precision = packet_retrieval(packets_by_disease[disease], k)
        percentage_total += percentage
        precision_total += precision
    n_diseases = len(diseases)
    return percentage_total / n_diseases, precision_total / n_diseases, n_diseases


def _metrics(queries: Sequence[tuple[int | None, bool]]) -> dict[str, dict[str, float | int]]:
    found: dict[str, dict[str, float | int]] = {}
    for k in (1, 5):
        hits, count, percentage, precision = packet_retrieval(queries, k)
        found[str(k)] = {
            "hits": hits,
            "count": count,
            "percentage": percentage,
            "precision": precision,
        }
    return found


def _products(
    scorer: FrequencyBinScorer,
    hpo_ids: Sequence[str],
    parents: Mapping[str, str] | None,
) -> list:
    ranked, _confident = rank_products(
        [(hpo_id, "present") for hpo_id in hpo_ids],
        scorer._prepared,
        parents,
    )
    return ranked


def _disease_scores(
    ranked: Sequence,
    orpha_to_disease: Mapping[str, str],
) -> list[DiseaseScore]:
    found: list[DiseaseScore] = []
    for product in ranked:
        disease_id = orpha_to_disease.get(product.orphanet_id)
        if disease_id is None:
            continue
        found.append(DiseaseScore(disease_id, product.lower_ratio))
    return found


def _query(scores: Sequence[DiseaseScore], truth: str, abstained: bool) -> tuple[int | None, bool]:
    if abstained or not scores:
        return None, True
    rank, _best, _ties, _close = _snapshot(scores, truth)
    return rank, False


def _parent_ids(path: Path) -> dict[str, str]:
    return {term: parent for term, (parent, _label) in parents_from_obo(path).items()}


def _beats(candidate: Mapping, baseline: Mapping) -> bool:
    for k in ("1", "5"):
        if candidate[k]["percentage"] <= baseline[k]["percentage"]:
            return False
        if candidate[k]["precision"] <= baseline[k]["precision"]:
            return False
    return True


def _fmt(value: float) -> str:
    return f"{value:.6f}"


def _verb(left: float, right: float) -> str:
    if left > right:
        return "beats"
    return "does not beat"


def heldout_markdown(report: Mapping) -> str:
    """Plain record of the one test look. Numbers come from the report dict."""
    winner = report["winner"]
    test = report["test"]
    diseases = report["disease_mean_present"]
    diagnosis = report["diagnosis_train"]
    decoy = report["decoy"]
    comparison = "beats" if report["beats_degree_on_test"] else "does not beat"
    lines = [
        "# Resnik best-match average, held-out once",
        "",
        "For research use only. Not for use in diagnostic procedures.",
        "",
        "The public-case ranker was chosen on fit and validation before this file was written. "
        f"The winner is {winner}. Abstention is {report['abstain']}: a best score at or below "
        "zero abstains, and a positive tie does not. That mode was the fit-split choice. "
        "The degree baseline keeps its published rule: best score at or below zero, or at least "
        "10 diseases tied at the best score. Other candidates were not scored on this split. "
        "phenotype.hpoa was not loaded. en_product6 was not loaded.",
        "",
        "The synthetic notebook card stays the frequency-bin comparison. These rows do not "
        "replace that card. The five synthetic stories stay on that card.",
        "",
        f"store_sha256: {report['store_sha256']}",
        f"unique_map_diseases: {report['unique_map_diseases']}",
        f"test_packets: {report['test_packets']}",
        f"diseases_with_a_test_packet: {report['diseases_with_a_test_packet']}",
        "",
        "## Why frequency-bin loses to the degree baseline",
        "",
        "Measured on train packets only. Test packets were not in this loop. "
        "The shipped frequency-bin scorer does not receive a parent map. A missing row "
        "contributes a ratio of 1. A listed bin whose lower bound sits below the corpus "
        "background scores below a missing row. Abstentions are misses. Climbing to a parent "
        "inside that product was measured here on the train split and is not shipped.",
        "",
        "| train check | k | hits | denominator | percentage@k |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in (
        "frequency_with_abstention",
        "frequency_ranked_anyway",
        "frequency_parent_climb_ranked_anyway",
    ):
        for k in ("1", "5"):
            row = diagnosis[name][k]
            percentage = _fmt(float(row["percentage"]))
            lines.append(f"| {name} | {k} | {row['hits']} | {row['count']} | {percentage} |")
    lines.extend(
        [
            "",
            f"Train packets whose truth disease has lower ratio 0: "
            f"{diagnosis['truth_lower_ratio_zero']} / {diagnosis['train_packets']}.",
            f"Train query terms: {diagnosis['query_terms']}. "
            f"Exact annotation on the truth disease: {diagnosis['exact_on_truth']}. "
            f"Additional ancestor relation: {diagnosis['ancestor_on_truth']}.",
            "",
            "## Held-out packets",
            "",
            "percentage@k is hits over the test-packet denominator. Abstentions are misses. "
            "precision@k is the mean of 1/k on a hit and 0 on a miss. Ties take the worst rank.",
            "",
            "| tool | k | hits | denominator | percentage@k | precision@k |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for tool in (winner, "degree"):
        for k in ("1", "5"):
            row = test[tool][k]
            lines.append(
                "| "
                + " | ".join(
                    [
                        tool,
                        k,
                        str(row["hits"]),
                        str(row["count"]),
                        _fmt(float(row["percentage"])),
                        _fmt(float(row["precision"])),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "Disease rows are the unweighted mean of each disease's test-packet rate. "
            "A unique-map disease with no test packet is left out of this mean. "
            f"{report['diseases_with_a_test_packet']} of {report['unique_map_diseases']} "
            "unique-map diseases have a test packet.",
            "",
            "| tool | k | diseases_in_mean | percentage@k | precision@k |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for tool in (winner, "degree"):
        for k in ("1", "5"):
            row = diseases[tool][k]
            lines.append(
                f"| {tool} | {k} | {row['diseases']} | "
                f"{_fmt(float(row['percentage']))} | {_fmt(float(row['precision']))} |"
            )
    lines.extend(["", "## Comparison", ""])
    for k in ("1", "5"):
        left = test[winner][k]
        right = test["degree"][k]
        lines.append(
            f"On test packets at k={k}, {winner} percentage@k "
            f"{_verb(float(left['percentage']), float(right['percentage']))} the degree baseline "
            f"({_fmt(float(left['percentage']))} vs {_fmt(float(right['percentage']))}) and "
            f"precision@k {_verb(float(left['precision']), float(right['precision']))} it "
            f"({_fmt(float(left['precision']))} vs {_fmt(float(right['precision']))})."
        )
        disease_left = diseases[winner][k]
        disease_right = diseases["degree"][k]
        lines.append(
            f"On unique-map diseases with a test packet at k={k}, {winner} percentage@k "
            f"{_verb(float(disease_left['percentage']), float(disease_right['percentage']))} "
            f"the degree baseline ({_fmt(float(disease_left['percentage']))} vs "
            f"{_fmt(float(disease_right['percentage']))}) and precision@k "
            f"{_verb(float(disease_left['precision']), float(disease_right['precision']))} it "
            f"({_fmt(float(disease_left['precision']))} vs "
            f"{_fmt(float(disease_right['precision']))})."
        )
    lines.extend(
        [
            "",
            f"The held-out packet bar {comparison} the degree baseline at both k=1 and k=5 "
            "on percentage@k and precision@k.",
            "",
            "## Decoy gene",
            "",
            "A gene symbol was added to each test packet and the case was rebuilt. "
            "The ranker is called with present HPO ids only.",
            "",
            f"packets: {decoy['packets']}",
            f"hpo_unchanged: {decoy['hpo_unchanged']}",
            f"decoy_gene_recorded: {decoy['gene_recorded']}",
            f"scores_unchanged: {decoy['scores_unchanged']}",
            f"rebuild_failures: {decoy['rebuild_failures']}",
            "",
        ]
    )
    return "\n".join(lines)


def splice_results(path: Path, section: str) -> None:
    """Insert the held-out section in front of the calibration heading."""
    text = path.read_text()
    calibration = text.find("\n## Calibration\n")
    if calibration == -1:
        raise RuntimeError("calibration heading is missing")
    start = text.find(MARKER)
    block = section.rstrip() + "\n\n"
    if start == -1:
        updated = text[:calibration] + "\n" + block + text[calibration + 1 :]
    else:
        updated = text[:start] + block + text[calibration + 1 :]
    path.write_text(updated)


def _score_map(scores: Sequence[DiseaseScore]) -> dict[str, float]:
    return {item.disease_id: item.score for item in scores}


def evaluate_test(data: Path, choice_path: Path) -> dict:
    """Score the locked ranker on test packets. Train packets are used only for the diagnosis."""
    payload = json.loads(choice_path.read_text())
    require_locked_choice(payload)
    pins = load_pins()
    if payload.get("store_sha256") != pins.store_sha256:
        raise RuntimeError("choice store hash does not match the pins")
    loaded = load_cases(data / "all_phenopackets.zip")
    mapping = orphanet_from_mondo_nodes(data / "mondo_nodes.tsv")
    unique, _excluded = unique_orphanet(loaded.disease_ids, mapping)
    kept = {disease: mapping[disease] for disease in unique}
    rows, orpha_to_disease = frequency_table(data / "en_product4.xml", kept)
    profiles = phenotype_profiles(rows, orpha_to_disease, unique)
    index = build_index(profiles, all_parents(data / "hp.obo"))
    resnik: Callable[[Sequence[str]], list[DiseaseScore]] = ResnikBestMatch(index).score
    degree = DegreeBaseline(profiles).score
    frequency = FrequencyBinScorer(rows, orpha_to_disease)
    parent_ids = _parent_ids(data / "hp.obo")
    disease_to_orpha: dict[str, str] = {}
    for orpha, disease in orpha_to_disease.items():
        disease_to_orpha.setdefault(disease, orpha)

    diagnosis_queries: dict[str, list[tuple[int | None, bool]]] = {
        "frequency_with_abstention": [],
        "frequency_ranked_anyway": [],
        "frequency_parent_climb_ranked_anyway": [],
    }
    train_packets = 0
    truth_zero = 0
    query_terms = 0
    exact_on_truth = 0
    ancestor_on_truth = 0
    test_queries: dict[str, list[tuple[int | None, bool]]] = {"resnik_bma": [], "degree": []}
    by_disease: dict[str, dict[str, list[tuple[int | None, bool]]]] = {
        "resnik_bma": defaultdict(list),
        "degree": defaultdict(list),
    }
    decoy = {
        "packets": 0,
        "hpo_unchanged": 0,
        "gene_recorded": 0,
        "scores_unchanged": 0,
        "rebuild_failures": 0,
    }

    for case in loaded.cases:
        if case.truth_disease_id not in unique:
            continue
        role = split_role(case.packet_id)
        terms = present_hpo_ids(case)
        if role != "test":
            train_packets += 1
            abstained_scores = frequency.score(terms)
            diagnosis_queries["frequency_with_abstention"].append(
                _query(abstained_scores, case.truth_disease_id, not abstained_scores)
            )
            ranked = _products(frequency, terms, None)
            raw_scores = _disease_scores(ranked, orpha_to_disease)
            diagnosis_queries["frequency_ranked_anyway"].append(
                _query(raw_scores, case.truth_disease_id, False)
            )
            climbed = _products(frequency, terms, parent_ids)
            diagnosis_queries["frequency_parent_climb_ranked_anyway"].append(
                _query(_disease_scores(climbed, orpha_to_disease), case.truth_disease_id, False)
            )
            orpha = disease_to_orpha.get(case.truth_disease_id)
            for product in ranked:
                if product.orphanet_id == orpha and product.lower_ratio == 0:
                    truth_zero += 1
            closure = index.closure.get(case.truth_disease_id, set())
            profile = profiles.get(case.truth_disease_id, set())
            for term in terms:
                query_terms += 1
                if term in profile:
                    exact_on_truth += 1
                    continue
                ancestors = index.ancestors(term)
                if any(ancestor in closure and ancestor != term for ancestor in ancestors):
                    ancestor_on_truth += 1
            if train_packets % 500 == 0:
                print(f"diagnosed_train={train_packets}", flush=True)
            continue
        resnik_scores = resnik(terms)
        degree_scores = degree(terms)
        resnik_snapshot = _snapshot(resnik_scores, case.truth_disease_id)
        degree_snapshot = _snapshot(degree_scores, case.truth_disease_id)
        resnik_query = (
            resnik_snapshot[0],
            _abstained(LOCKED_ABSTAIN, resnik_snapshot[1], resnik_snapshot[2], resnik_snapshot[3]),
        )
        degree_query = (
            degree_snapshot[0],
            _abstained(DEGREE_ABSTAIN, degree_snapshot[1], degree_snapshot[2], degree_snapshot[3]),
        )
        test_queries["resnik_bma"].append(resnik_query)
        test_queries["degree"].append(degree_query)
        by_disease["resnik_bma"][case.truth_disease_id].append(resnik_query)
        by_disease["degree"][case.truth_disease_id].append(degree_query)
        decoy["packets"] += 1
        cloned = with_decoy_gene(case.source)
        try:
            rebuilt = _case_from_packet(cloned, pins.store_version)
        except Exception:
            rebuilt = None
        if rebuilt is None:
            decoy["rebuild_failures"] += 1
        else:
            decoy_terms = present_hpo_ids(rebuilt)
            if decoy_terms == terms:
                decoy["hpo_unchanged"] += 1
            if DECOY_GENE in _genes(cloned) and DECOY_GENE in rebuilt.truth_genes:
                decoy["gene_recorded"] += 1
            if _score_map(resnik(decoy_terms)) == _score_map(resnik_scores):
                decoy["scores_unchanged"] += 1
        if decoy["packets"] % 250 == 0:
            print(f"scored_test={decoy['packets']}", flush=True)

    test_metrics = {name: _metrics(queries) for name, queries in test_queries.items()}
    disease_mean: dict[str, dict[str, dict[str, float | int]]] = {}
    for name, grouped in by_disease.items():
        disease_mean[name] = {}
        for k in (1, 5):
            percentage, precision, n_diseases = mean_over_present(grouped, k)
            disease_mean[name][str(k)] = {
                "diseases": n_diseases,
                "percentage": percentage,
                "precision": precision,
            }
    report = {
        "winner": LOCKED_WINNER,
        "abstain": LOCKED_ABSTAIN,
        "degree_abstain": DEGREE_ABSTAIN,
        "shipped_because": LOCKED_BECAUSE,
        "store_sha256": pins.store_sha256,
        "unique_map_diseases": len(unique),
        "test_packets": len(test_queries["resnik_bma"]),
        "diseases_with_a_test_packet": len(by_disease["resnik_bma"]),
        "test_scored": True,
        "beats_degree_on_test": _beats(test_metrics["resnik_bma"], test_metrics["degree"]),
        "test": test_metrics,
        "disease_mean_present": disease_mean,
        "decoy": decoy,
        "diagnosis_train": {
            "train_packets": train_packets,
            "truth_lower_ratio_zero": truth_zero,
            "query_terms": query_terms,
            "exact_on_truth": exact_on_truth,
            "ancestor_on_truth": ancestor_on_truth,
            **{name: _metrics(queries) for name, queries in diagnosis_queries.items()},
        },
    }
    return report


def mark_choice_scored(choice_path: Path) -> None:
    """Flip the scored flag. The winner and the candidate table stay as they were."""
    payload = json.loads(choice_path.read_text())
    payload["test_scored"] = True
    choice_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(data: Path, choice_path: Path, out: Path, results: Path | None, record: Path) -> None:
    report = evaluate_test(data, choice_path)
    text = heldout_markdown(report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    record.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if results is not None:
        splice_results(results, text)
    mark_choice_scored(choice_path)
    print(
        json.dumps(
            {
                "winner": report["winner"],
                "beats_degree_on_test": report["beats_degree_on_test"],
                "test_packets": report["test_packets"],
                "diseases_with_a_test_packet": report["diseases_with_a_test_packet"],
            }
        ),
        flush=True,
    )
