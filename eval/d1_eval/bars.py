"""Degree baseline and precision@k on the shipped frequency-bin scorer.

The held-out split is SHA-256 of the packet id, modulo 5, remainder 0 = test.
Nothing in this module chooses a threshold from that split.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from d1_eval.baseline import DegreeBaseline, disease_retrieval, packet_retrieval, phenotype_profiles
from d1_eval.frequency import FrequencyBinScorer, frequency_table
from d1_eval.harness import (
    CaseRank,
    cohort_split,
    degrade,
    load_cases,
    load_pins,
    orphanet_from_mondo_nodes,
    rank_case,
    unique_orphanet,
)

KS = (1, 5)


def measure_bars(data: Path) -> str:
    pins = load_pins()
    loaded = load_cases(data / "all_phenopackets.zip")
    mapping = orphanet_from_mondo_nodes(data / "mondo_nodes.tsv")
    unique, excluded = unique_orphanet(loaded.disease_ids, mapping)
    kept = {disease: mapping[disease] for disease in unique}
    rows, orpha_to_disease = frequency_table(data / "en_product4.xml", kept)
    frequency = FrequencyBinScorer(rows, orpha_to_disease)
    degree = DegreeBaseline(phenotype_profiles(rows, orpha_to_disease, unique))
    by_tool: dict[str, list[tuple[str, str, CaseRank]]] = {
        "frequency-bin": [],
        "degree-baseline": [],
    }
    scorers = (("frequency-bin", frequency), ("degree-baseline", degree))
    print(f"unique_diseases={len(unique)} excluded_diseases={excluded}", flush=True)
    for index, case in enumerate(loaded.cases, start=1):
        if case.truth_disease_id not in unique:
            continue
        full = degrade(case, "full", {}, pins.keep_fraction)
        for name, scorer in scorers:
            ranked = rank_case(full, scorer, unique, pins.tied_at_best)
            by_tool[name].append((case.truth_disease_id, case.packet_id, ranked))
        if index % 250 == 0:
            print(f"packets_seen={index}", flush=True)
    return _document(
        by_tool,
        sorted(unique),
        excluded=excluded,
        rows=len(rows),
        store_sha=pins.store_sha256,
    )


def _queries(
    rows: list[tuple[str, str, CaseRank]],
    cohort: str | None,
) -> list[tuple[int | None, bool]]:
    found = []
    for _disease, packet_id, ranked in rows:
        if cohort is not None and cohort_split(packet_id) != cohort:
            continue
        if not ranked.scored:
            continue
        found.append((ranked.rank, ranked.no_confident))
    return found


def _by_disease(
    rows: list[tuple[str, str, CaseRank]],
) -> dict[str, list[tuple[int | None, bool]]]:
    grouped: dict[str, list[tuple[int | None, bool]]] = defaultdict(list)
    for disease, _packet_id, ranked in rows:
        if ranked.scored:
            grouped[disease].append((ranked.rank, ranked.no_confident))
    return grouped


def _beats(left: float, right: float) -> str:
    if left > right:
        return "beats"
    return "does not beat"


def _document(
    by_tool: dict[str, list[tuple[str, str, CaseRank]]],
    diseases: list[str],
    *,
    excluded: int,
    rows: int,
    store_sha: str,
) -> str:
    lines = [
        "# Degree baseline and precision@k",
        "",
        "For research use only. Not for use in diagnostic procedures.",
        "",
        "Shipped scorer: frequency-bin 0.0.2. No parent map. "
        "CLOSE_DISEASE_COUNT stays 10 and CLOSE_FACTOR stays 2.0. They were not refit. "
        "The degree baseline scores each unique-map disease by the sum of -log(frequency) "
        "over present terms that disease lists outside the excluded bin. "
        "Frequency is the fraction of unique-map diseases that list the term. "
        "A term no unique-map disease lists adds nothing. "
        "phenotype.hpoa was not loaded. en_product6 was not loaded.",
        "",
        "percentage@k is hits over the stated denominator. Abstentions are misses. "
        "precision@k is the mean of 1/k when the truth disease's worst rank is at most k, "
        "and 0 otherwise. The denominator stays k when the returned list is shorter than k. "
        "Ties take the worst rank. The held-out split is SHA-256 of the packet id, modulo 5, "
        "remainder 0 = test. That split was not used to choose a threshold, a background, "
        "or a bin edge.",
        "",
        f"unique_map_diseases: {len(diseases)}",
        f"excluded_diseases: {excluded}",
        f"en_product4_rows: {rows}",
        f"store_sha256: {store_sha}",
        "",
        "| cohort | tool | k | hits | denominator | percentage@k | precision@k |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    summaries: dict[tuple[str, str, int], tuple[float, float]] = {}
    for cohort in ("all", "train", "test"):
        for tool, tool_rows in by_tool.items():
            cohort_name = None if cohort == "all" else cohort
            queries = _queries(tool_rows, cohort_name)
            for k in KS:
                hits, count, percentage, precision = packet_retrieval(queries, k)
                summaries[(cohort, tool, k)] = (percentage, precision)
                lines.append(
                    f"| {cohort} packets | {tool} | {k} | {hits} | {count} | "
                    f"{percentage:.6f} | {precision:.6f} |"
                )
    lines.extend(
        [
            "",
            "Disease rows are the unweighted mean of each disease's packet rate. "
            "A unique-map disease with no scored packet is a miss and stays in the denominator.",
            "",
            "| tool | k | diseases | diseases_with_no_packet | percentage@k | precision@k |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for tool, tool_rows in by_tool.items():
        grouped = _by_disease(tool_rows)
        for k in KS:
            percentage, precision, n_diseases, empty = disease_retrieval(grouped, diseases, k)
            summaries[("diseases", tool, k)] = (percentage, precision)
            lines.append(
                f"| {tool} | {k} | {n_diseases} | {empty} | {percentage:.6f} | {precision:.6f} |"
            )
    lines.extend(["", "## Comparison", ""])
    for cohort in ("all", "train", "test", "diseases"):
        label = "unique-map diseases" if cohort == "diseases" else f"{cohort} packets"
        for k in KS:
            freq = summaries[(cohort, "frequency-bin", k)]
            base = summaries[(cohort, "degree-baseline", k)]
            lines.append(
                f"On {label} at k={k}, frequency-bin percentage@k "
                f"{_beats(freq[0], base[0])} the degree baseline "
                f"({freq[0]:.6f} vs {base[0]:.6f}) and precision@k "
                f"{_beats(freq[1], base[1])} it ({freq[1]:.6f} vs {base[1]:.6f})."
            )
    lines.append("")
    return "\n".join(lines)
