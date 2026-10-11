"""Degree baseline and retrieval at k. Thresholds are not fit here.

The degree frequency of a term is the fraction of the unique-map diseases whose
Orphanet phenotype rows list that term outside the excluded bin. The score is
the sum of the negative natural log of those frequencies. A term no unique-map
disease lists adds nothing. phenotype.hpoa is not read. en_product6 is not read.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from d1_eval.harness import DiseaseScore


def phenotype_profiles(
    rows: Sequence[Mapping],
    orpha_to_disease: Mapping[str, str],
    diseases: set[str],
) -> dict[str, set[str]]:
    """Non-excluded HPO ids on each unique-map disease. Corpus-only rows are not ranked."""
    profiles = {disease: set() for disease in diseases}
    for row in rows:
        if row.get("corpus_only"):
            continue
        if str(row.get("bin") or "") == "excluded":
            continue
        disease = orpha_to_disease.get(str(row.get("orphanet_id") or ""))
        hpo_id = str(row.get("hpo_id") or "")
        if disease in profiles and hpo_id:
            profiles[disease].add(hpo_id)
    return profiles


class DegreeBaseline:
    """Rank unique-map diseases by inverse-frequency degree. Higher is better."""

    def __init__(self, profiles: Mapping[str, set[str]]) -> None:
        self._profiles = {disease: set(terms) for disease, terms in profiles.items()}
        n_diseases = len(self._profiles)
        counts: dict[str, int] = {}
        for terms in self._profiles.values():
            for term in terms:
                counts[term] = counts.get(term, 0) + 1
        self.weights: dict[str, float] = {}
        if n_diseases:
            for term, count in counts.items():
                if count > 0:
                    self.weights[term] = -math.log(count / n_diseases)

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        query = [term for term in hpo_ids if term in self.weights]
        found: list[DiseaseScore] = []
        for disease, terms in self._profiles.items():
            total = sum(self.weights[term] for term in query if term in terms)
            found.append(DiseaseScore(disease, total))
        return found


def is_hit(rank: int | None, abstained: bool, k: int) -> bool:
    return (not abstained) and rank is not None and rank <= k


def precision_at_k(
    rank: int | None,
    abstained: bool,
    k: int,
    list_length: int,
) -> float:
    """One relevant disease. The denominator stays k when the list is shorter than k."""
    if k <= 0:
        raise ValueError("k must be positive")
    if list_length < 0:
        raise ValueError("list_length must be non-negative")
    if not is_hit(rank, abstained, k):
        return 0.0
    return 1.0 / k


def packet_retrieval(
    queries: Sequence[tuple[int | None, bool]],
    k: int,
) -> tuple[int, int, float, float]:
    """Hits, packet count, percentage@k, and mean precision@k. Abstentions are misses."""
    hits = 0
    precision_total = 0.0
    for rank, abstained in queries:
        if is_hit(rank, abstained, k):
            hits += 1
            precision_total += 1.0 / k
    count = len(queries)
    if count == 0:
        return 0, 0, 0.0, 0.0
    return hits, count, hits / count, precision_total / count


def disease_retrieval(
    packets_by_disease: Mapping[str, Sequence[tuple[int | None, bool]]],
    diseases: Sequence[str],
    k: int,
) -> tuple[float, float, int, int]:
    """Unweighted mean over every unique-map disease. A disease with no packet is a miss."""
    if not diseases:
        return 0.0, 0.0, 0, 0
    percentage_total = 0.0
    precision_total = 0.0
    empty = 0
    for disease in diseases:
        packets = list(packets_by_disease.get(disease, ()))
        if not packets:
            empty += 1
            continue
        hits, count, percentage, precision = packet_retrieval(packets, k)
        if count != len(packets) or hits < 0:
            raise RuntimeError("packet retrieval drifted")
        percentage_total += percentage
        precision_total += precision
    n_diseases = len(diseases)
    return percentage_total / n_diseases, precision_total / n_diseases, n_diseases, empty
