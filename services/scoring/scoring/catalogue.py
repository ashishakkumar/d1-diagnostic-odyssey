"""Orphanet frequency-bin likelihood ratios. Phenotype frequencies only."""

import math
from collections import defaultdict
from pathlib import Path
from typing import Literal, Mapping, Sequence

import phenopackets.schema.v2 as pps2
import pronto
from google.protobuf.json_format import ParseDict
from pydantic import BaseModel, ConfigDict

from d1_contracts import EvidenceRow

# ponytail: one background for every term, and 0.01 when a disease has no row.
# Upgrade path is the fraction of unique-map diseases that list the term.
BACKGROUND = 0.05
UNANNOTATED = 0.01
# Frozen before any store run. Refitting these fails the evaluation.
CLOSE_DISEASE_COUNT = 10
CLOSE_FACTOR = 2.0
NONSPECIFIC_HPO = frozenset({"HP:0001249", "HP:0001250"})
_FORBIDDEN = ("diagnosis", "pathogenic", "benign")
NOT_CONSIDERED = (
    "lab-reported variant",
    "ClinVar record",
    "gene symbol",
    "Orphanet gene file",
)

BINS: dict[str, tuple[float, float]] = {
    "obligate": (1.0, 1.0),
    "very_frequent": (0.80, 0.99),
    "frequent": (0.30, 0.79),
    "occasional": (0.05, 0.29),
    "very_rare": (0.01, 0.04),
    "excluded": (0.0, 0.0),
}

Relation = Literal["supports", "does_not_support"]
Presence = Literal["present", "excluded"]


class TermEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hpo_id: str
    relation: Relation
    source: str
    version: str
    lower_ratio: float
    upper_ratio: float


class DiseaseScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    orphanet_id: str
    mondo_id: str
    lower_ratio: float
    upper_ratio: float
    terms: list[TermEvidence]


class CitedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    version: str


class GeneFit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gene_symbol: str
    explained_hpo_ids: list[str]
    unexplained_hpo_ids: list[str]
    sources: list[CitedSource]


class ScoreReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diseases: list[DiseaseScore]
    confident: bool
    abstain_reason: (
        Literal[
            "many_within_factor",
            "top_flips_between_bounds",
            "tied_for_first",
            "no_scoreable_disease",
        ]
        | None
    )
    leading_orphanet_id: str | None
    margin: float | None
    excluded_disease_count: int


def _ratio(presence: str, bound: float) -> float:
    if presence == "present":
        return bound / BACKGROUND
    if presence == "excluded":
        return (1.0 - bound) / (1.0 - BACKGROUND)
    raise ValueError(presence)


def _relation(presence: str, bin_name: str) -> Relation:
    if presence == "present":
        return "does_not_support" if bin_name == "excluded" else "supports"
    if presence == "excluded":
        return "supports" if bin_name == "excluded" else "does_not_support"
    raise ValueError(presence)


def _partition(
    rows: Sequence[Mapping],
) -> tuple[dict[str, list[Mapping]], list[str], int]:
    grouped: dict[str, list[Mapping]] = defaultdict(list)
    mondos_for: dict[str, set[str]] = defaultdict(set)
    orphanets_for: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        citation = EvidenceRow.model_validate(
            {
                "id": row["id"],
                "source": row["source"],
                "version": row["version"],
                "subject_key": row.get("subject_key"),
            }
        )
        if "clinvar" in citation.source.casefold():
            continue
        orphanet_id = str(row["orphanet_id"])
        mondo_id = str(row["mondo_id"])
        grouped[orphanet_id].append(row)
        mondos_for[orphanet_id].add(mondo_id)
        orphanets_for[mondo_id].add(orphanet_id)

    scoreable: list[str] = []
    excluded = 0
    for orphanet_id, mondos in mondos_for.items():
        mondo_id = next(iter(mondos))
        if len(mondos) == 1 and len(orphanets_for[mondo_id]) == 1:
            scoreable.append(orphanet_id)
        else:
            excluded += 1
    return grouped, scoreable, excluded


def _blocked(hpo_id: str, ontology: pronto.Ontology | None) -> bool:
    if hpo_id in NONSPECIFIC_HPO:
        return True
    if ontology is None or hpo_id not in ontology:
        return False
    parents = ontology[hpo_id].superclasses(with_self=False)
    return any(parent.id in NONSPECIFIC_HPO for parent in parents)


def _curve_ok(curve: Sequence[Mapping] | None) -> bool:
    if curve is None or len(curve) < 2:
        return False
    for point in curve:
        predicted = float(point["predicted"])
        observed = float(point["observed"])
        if not 0 <= predicted <= 1 or not 0 <= observed <= 1:
            return False
    return True


def _guard(value: object) -> None:
    if isinstance(value, str):
        lowered = value.casefold()
        if any(word in lowered for word in _FORBIDDEN):
            raise ValueError("output contains a forbidden word")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _guard(key)
            _guard(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _guard(item)


def to_public(
    report: ScoreReport,
    *,
    probability: float | None = None,
    reliability_curve: Sequence[Mapping] | None = None,
    questions: Sequence[str] | None = None,
    ontology_path: Path | None = None,
) -> dict:
    """Evidence and margin. A probability is included only with a reliability curve."""
    ontology = pronto.Ontology(ontology_path) if ontology_path is not None else None
    asked = [hpo_id for hpo_id in (questions or []) if not _blocked(hpo_id, ontology)]
    terms = []
    for disease in report.diseases:
        for term in disease.terms:
            item = term.model_dump()
            item["orphanet_id"] = disease.orphanet_id
            terms.append(item)
    payload: dict = {
        "evidence": {
            "rule": "orphanet-frequency-bin-likelihood-ratio",
            "terms": terms,
            "diseases": [
                {
                    "orphanet_id": disease.orphanet_id,
                    "mondo_id": disease.mondo_id,
                    "lower_ratio": disease.lower_ratio,
                    "upper_ratio": disease.upper_ratio,
                }
                for disease in report.diseases
            ],
            "confident": report.confident,
            "abstain_reason": report.abstain_reason,
            "leading_orphanet_id": report.leading_orphanet_id,
            "excluded_disease_count": report.excluded_disease_count,
            "not_considered": list(NOT_CONSIDERED),
            "questions": asked,
        },
        "margin": report.margin,
    }
    if probability is not None and _curve_ok(reliability_curve):
        payload["probability"] = probability
        payload["reliability_curve"] = [dict(point) for point in reliability_curve or []]
    _guard(payload)
    return payload


def hpo_from_phenopacket(payload: Mapping) -> list[tuple[str, Presence]]:
    message = ParseDict(dict(payload), pps2.Phenopacket())
    found: list[tuple[str, Presence]] = []
    for feature in message.phenotypic_features:
        presence: Presence = "excluded" if feature.excluded else "present"
        found.append((feature.type.id, presence))
    return found


def gene_fit(
    accepted_hpo_ids: Sequence[str],
    gene_symbol: str,
    associations: Sequence[Mapping],
) -> GeneFit:
    usable: list[Mapping] = []
    sources: list[CitedSource] = []
    seen: set[tuple[str, str]] = set()
    for row in associations:
        EvidenceRow.model_validate(
            {
                "id": row["id"],
                "source": row["source"],
                "version": row["version"],
                "subject_key": row.get("subject_key"),
            }
        )
        if "clinvar" in str(row["source"]).casefold():
            continue
        usable.append(row)
        pair = (str(row["source"]), str(row["version"]))
        if pair not in seen:
            seen.add(pair)
            sources.append(CitedSource(source=pair[0], version=pair[1]))
    explained_ids = {str(row["hpo_id"]) for row in usable if str(row["gene_symbol"]) == gene_symbol}
    explained = [hpo_id for hpo_id in accepted_hpo_ids if hpo_id in explained_ids]
    unexplained = [hpo_id for hpo_id in accepted_hpo_ids if hpo_id not in explained_ids]
    return GeneFit(
        gene_symbol=gene_symbol,
        explained_hpo_ids=explained,
        unexplained_hpo_ids=unexplained,
        sources=sources,
    )


def suggest_questions(
    accepted_hpo_ids: Sequence[str],
    rows: Sequence[Mapping],
    *,
    enabled: bool = False,
    ontology_path: Path | None = None,
) -> list[str]:
    if not enabled:
        return []
    ontology = pronto.Ontology(ontology_path) if ontology_path is not None else None
    accepted = set(accepted_hpo_ids)
    grouped, scoreable, _excluded = _partition(rows)
    found: set[str] = set()
    for orphanet_id in scoreable:
        for row in grouped[orphanet_id]:
            hpo_id = str(row["hpo_id"])
            if hpo_id in accepted or _blocked(hpo_id, ontology):
                continue
            found.add(hpo_id)
    return sorted(found)


def catalogue_score(
    accepted_hpo: Sequence[tuple[str, Presence]],
    rows: Sequence[Mapping],
) -> ScoreReport:
    grouped, scoreable, excluded = _partition(rows)

    diseases: list[DiseaseScore] = []
    for orphanet_id in sorted(scoreable):
        disease_rows = grouped[orphanet_id]
        by_hpo = {str(row["hpo_id"]): row for row in disease_rows}
        terms: list[TermEvidence] = []
        lower = 1.0
        upper = 1.0
        for hpo_id, presence in accepted_hpo:
            row = by_hpo.get(hpo_id)
            if row is None:
                lower_ratio = _ratio(presence, UNANNOTATED)
                upper_ratio = _ratio(presence, UNANNOTATED)
                relation: Relation = "does_not_support"
                source = str(disease_rows[0]["source"])
                version = str(disease_rows[0]["version"])
            else:
                bin_name = str(row["bin"])
                lo, hi = BINS[bin_name]
                lower_ratio = _ratio(presence, lo)
                upper_ratio = _ratio(presence, hi)
                relation = _relation(presence, bin_name)
                source = str(row["source"])
                version = str(row["version"])
            lower *= lower_ratio
            upper *= upper_ratio
            terms.append(
                TermEvidence(
                    hpo_id=hpo_id,
                    relation=relation,
                    source=source,
                    version=version,
                    lower_ratio=lower_ratio,
                    upper_ratio=upper_ratio,
                )
            )
        diseases.append(
            DiseaseScore(
                orphanet_id=orphanet_id,
                mondo_id=str(disease_rows[0]["mondo_id"]),
                lower_ratio=lower,
                upper_ratio=upper,
                terms=terms,
            )
        )
    diseases.sort(key=lambda disease: (-disease.lower_ratio, disease.orphanet_id))
    leading, reason = _separate(diseases)
    return ScoreReport(
        diseases=diseases,
        confident=reason is None,
        abstain_reason=reason,
        leading_orphanet_id=leading,
        margin=_margin(diseases),
        excluded_disease_count=excluded,
    )


def _unique_leader(diseases: list[DiseaseScore], attr: str) -> str | None:
    if not diseases:
        return None
    best = max(getattr(disease, attr) for disease in diseases)
    leaders = [
        disease
        for disease in diseases
        if math.isclose(getattr(disease, attr), best, rel_tol=1e-9, abs_tol=1e-9)
    ]
    if len(leaders) != 1:
        return None
    return leaders[0].orphanet_id


def _separate(diseases: list[DiseaseScore]) -> tuple[str | None, str | None]:
    if not diseases:
        return None, "no_scoreable_disease"
    best = diseases[0].lower_ratio
    close = sum(1 for disease in diseases if disease.lower_ratio + 1e-12 >= best / CLOSE_FACTOR)
    lower_leader = _unique_leader(diseases, "lower_ratio")
    upper_leader = _unique_leader(diseases, "upper_ratio")
    if close >= CLOSE_DISEASE_COUNT:
        return None, "many_within_factor"
    if lower_leader is None or upper_leader is None:
        return None, "tied_for_first"
    if lower_leader != upper_leader:
        return None, "top_flips_between_bounds"
    return lower_leader, None


def _margin(diseases: list[DiseaseScore]) -> float | None:
    if len(diseases) < 2 or diseases[1].lower_ratio == 0:
        return None
    return diseases[0].lower_ratio / diseases[1].lower_ratio
