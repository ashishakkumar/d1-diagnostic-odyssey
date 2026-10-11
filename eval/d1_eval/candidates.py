"""Candidate rankers. Chosen on train and validation. The test split is not an input.

Information content uses the 249 unique-map diseases. A disease annotated with a
term counts for that term and its ancestors. phenotype.hpoa is not read.
en_product6 is not read. No scorer takes a gene symbol.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

from d1_eval.harness import DiseaseScore
from scoring.catalogue import BINS

ROOTS = frozenset({"HP:0000001", "HP:0000118"})
# Robertson BM25 defaults. Not fit on the store.
BM25_K1 = 1.2
BM25_B = 0.75


def all_parents(path: Path) -> dict[str, tuple[str, ...]]:
    """Every is_a parent. Obsolete terms are dropped."""
    parents: dict[str, list[str]] = {}
    obsolete: set[str] = set()
    current: str | None = None
    for line in path.read_text().splitlines():
        if line == "[Term]" or (line.startswith("[") and line.endswith("]")):
            current = None
            continue
        if line.startswith("id: HP:"):
            current = line.removeprefix("id: ").strip()
            parents.setdefault(current, [])
            continue
        if current is None:
            continue
        if line.startswith("is_obsolete: true"):
            obsolete.add(current)
        elif line.startswith("is_a: HP:"):
            parent = line.removeprefix("is_a: ").split("!", 1)[0].strip()
            parents[current].append(parent)
    return {term: tuple(chain) for term, chain in parents.items() if term not in obsolete}


def bin_lowers(
    rows: Sequence[Mapping],
    orpha_to_disease: Mapping[str, str],
    diseases: set[str],
) -> dict[str, dict[str, float]]:
    """Strongest non-excluded bin lower bound for each disease and term."""
    found = {disease: {} for disease in diseases}
    for row in rows:
        if row.get("corpus_only"):
            continue
        bin_name = str(row.get("bin") or "")
        if bin_name == "excluded" or bin_name not in BINS:
            continue
        disease = orpha_to_disease.get(str(row.get("orphanet_id") or ""))
        hpo_id = str(row.get("hpo_id") or "")
        if disease not in found or not hpo_id:
            continue
        lower = BINS[bin_name][0]
        previous = found[disease].get(hpo_id)
        if previous is None or lower > previous:
            found[disease][hpo_id] = lower
    return found


class _Index:
    def __init__(
        self,
        profiles: Mapping[str, set[str]],
        parents: Mapping[str, Sequence[str]],
    ) -> None:
        self.profiles = {disease: set(terms) for disease, terms in profiles.items()}
        self.parents = {term: tuple(chain) for term, chain in parents.items()}
        self._ancestors: dict[str, tuple[str, ...]] = {}
        self.closure = {disease: self._close(terms) for disease, terms in self.profiles.items()}
        counts: Counter[str] = Counter()
        for closed in self.closure.values():
            counts.update(closed)
        n_diseases = len(self.profiles)
        self.ic = {
            term: -math.log(count / n_diseases)
            for term, count in counts.items()
            if n_diseases and 0 < count < n_diseases
        }

    def ancestors(self, term: str) -> tuple[str, ...]:
        cached = self._ancestors.get(term)
        if cached is not None:
            return cached
        found: list[str] = []
        seen: set[str] = set()
        stack = [term]
        while stack:
            current = stack.pop()
            if not current or current in seen or current in ROOTS:
                continue
            seen.add(current)
            found.append(current)
            stack.extend(self.parents.get(current, ()))
        cached = tuple(found)
        self._ancestors[term] = cached
        return cached

    def _close(self, terms: set[str]) -> set[str]:
        closed: set[str] = set()
        for term in terms:
            closed.update(self.ancestors(term))
        return closed

    def best(self, term: str, closure: set[str]) -> float:
        best_ic = 0.0
        for ancestor in self.ancestors(term):
            if ancestor not in closure:
                continue
            information = self.ic.get(ancestor, 0.0)
            if information > best_ic:
                best_ic = information
        return best_ic


class InformationContentOverlap:
    """Sum of IC over the shared ancestor closure. Higher is better."""

    def __init__(self, index: _Index) -> None:
        self._index = index

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        query_closure: set[str] = set()
        for term in hpo_ids:
            query_closure.update(self._index.ancestors(term))
        found: list[DiseaseScore] = []
        for disease, closure in self._index.closure.items():
            total = sum(self._index.ic.get(term, 0.0) for term in query_closure & closure)
            found.append(DiseaseScore(disease, total))
        return found


class ResnikBestMatch:
    """Symmetric Resnik best-match average. Higher is better."""

    def __init__(self, index: _Index) -> None:
        self._index = index

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        query = list(dict.fromkeys(hpo_ids))
        query_closure: set[str] = set()
        for term in query:
            query_closure.update(self._index.ancestors(term))
        found: list[DiseaseScore] = []
        for disease, closure in self._index.closure.items():
            if not query:
                found.append(DiseaseScore(disease, 0.0))
                continue
            left = sum(self._index.best(term, closure) for term in query) / len(query)
            exact = self._index.profiles[disease]
            if exact:
                right = sum(self._index.best(term, query_closure) for term in exact) / len(exact)
            else:
                right = 0.0
            found.append(DiseaseScore(disease, 0.5 * (left + right)))
        return found


class PhenomizerScore:
    """One-way mean of Resnik best matches from the query onto the disease."""

    def __init__(self, index: _Index) -> None:
        self._index = index

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        query = list(dict.fromkeys(hpo_ids))
        found: list[DiseaseScore] = []
        for disease, closure in self._index.closure.items():
            if not query:
                found.append(DiseaseScore(disease, 0.0))
                continue
            total = sum(self._index.best(term, closure) for term in query) / len(query)
            found.append(DiseaseScore(disease, total))
        return found


class Bm25Score:
    """BM25 over exact non-excluded disease annotations. tf is 1. Defaults are fixed."""

    def __init__(self, profiles: Mapping[str, set[str]]) -> None:
        self._profiles = {disease: set(terms) for disease, terms in profiles.items()}
        n_diseases = len(self._profiles)
        counts: Counter[str] = Counter()
        for terms in self._profiles.values():
            counts.update(terms)
        self.idf = {
            term: math.log((n_diseases - count + 0.5) / (count + 0.5))
            for term, count in counts.items()
            if n_diseases and count > 0
        }
        lengths = [len(terms) for terms in self._profiles.values()]
        self._avgdl = (sum(lengths) / len(lengths)) if lengths else 1.0

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        found: list[DiseaseScore] = []
        for disease, terms in self._profiles.items():
            length = len(terms)
            scale = self._avgdl if self._avgdl else 1.0
            normalizer = BM25_K1 * (1.0 - BM25_B + BM25_B * length / scale)
            factor = (BM25_K1 + 1.0) / (1.0 + normalizer)
            total = 0.0
            for term in hpo_ids:
                if term not in terms:
                    continue
                total += self.idf.get(term, 0.0) * factor
            found.append(DiseaseScore(disease, total))
        return found


class DegreeCorrectedFrequency:
    """Bin lower bound over the 249-disease prior. A listed term is not scored below zero.

    contribution = max(0, log(bin_lower / P(term))). Missing and excluded terms add 0,
    so one excluded annotation does not zero the disease.
    """

    def __init__(
        self,
        lowers: Mapping[str, Mapping[str, float]],
        profiles: Mapping[str, set[str]],
    ) -> None:
        self._lowers = {disease: dict(terms) for disease, terms in lowers.items()}
        n_diseases = len(profiles)
        counts: Counter[str] = Counter()
        for terms in profiles.values():
            counts.update(terms)
        self.idf = {
            term: -math.log(count / n_diseases)
            for term, count in counts.items()
            if n_diseases and 0 < count < n_diseases
        }

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        found: list[DiseaseScore] = []
        for disease, lowers in self._lowers.items():
            total = 0.0
            for term in hpo_ids:
                lower = lowers.get(term)
                weight = self.idf.get(term)
                if lower is None or weight is None or lower <= 0:
                    continue
                total += max(0.0, math.log(lower) + weight)
            found.append(DiseaseScore(disease, total))
        return found


def build_index(
    profiles: Mapping[str, set[str]],
    parents: Mapping[str, Sequence[str]],
) -> _Index:
    return _Index(profiles, parents)
