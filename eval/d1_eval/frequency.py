"""Orphanet frequency bins scored by the catalogue. Thresholds stay in the scorer."""

import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path

from d1_ingest.load import load_orphadata_phenotypes

from d1_eval.harness import DiseaseScore
from scoring import catalogue_score, to_public

# "very frequent" is checked before "frequent", and "very rare" before any shorter label.
_BIN_PREFIXES = (
    ("obligate", "obligate"),
    ("very frequent", "very_frequent"),
    ("very rare", "very_rare"),
    ("frequent", "frequent"),
    ("occasional", "occasional"),
    ("excluded", "excluded"),
)


def _bin(label: str) -> str | None:
    folded = label.casefold()
    for prefix, name in _BIN_PREFIXES:
        if folded.startswith(prefix):
            return name
    return None


def _mondo(disease_id: str) -> str:
    digits = "".join(character for character in disease_id if character.isdigit())
    return f"MONDO:{digits}"


def frequency_table(
    path: Path,
    omim_to_orpha: Mapping[str, set[str]],
) -> tuple[list[dict], dict[str, str]]:
    """Rows for Orphanet ids owned by exactly one disease in the map."""
    owners: dict[str, set[str]] = {}
    for disease_id, orphas in omim_to_orpha.items():
        for orpha in orphas:
            owners.setdefault(orpha, set()).add(disease_id)
    orpha_to_disease = {
        orpha: next(iter(diseases)) for orpha, diseases in owners.items() if len(diseases) == 1
    }
    rows: list[dict] = []
    for cited in load_orphadata_phenotypes(path):
        orpha, _sep, hpo_id = cited.subject_key.partition("|")
        disease_id = orpha_to_disease.get(orpha)
        bin_name = _bin(cited.text)
        if disease_id is None or not hpo_id or bin_name is None:
            continue
        rows.append(
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, cited.subject_key)),
                "source": cited.source,
                "version": cited.version,
                "subject_key": cited.subject_key,
                "orphanet_id": orpha,
                "mondo_id": _mondo(disease_id),
                "hpo_id": hpo_id,
                "bin": bin_name,
            }
        )
    return rows, orpha_to_disease


class FrequencyBinScorer:
    """Phenotype-only ranks. An abstention is an empty list, which the harness counts as a miss."""

    def __init__(
        self,
        rows: Sequence[Mapping],
        orpha_to_disease: Mapping[str, str],
        parents: Mapping[str, str] | None = None,
    ) -> None:
        self._rows = list(rows)
        self._orpha_to_disease = dict(orpha_to_disease)
        self._parents = dict(parents or {})

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        report = catalogue_score(
            [(hpo_id, "present") for hpo_id in hpo_ids],
            self._rows,
            self._parents,
        )
        public = to_public(report)
        if not public["evidence"]["confident"]:
            return []
        found: list[DiseaseScore] = []
        for disease in report.diseases:
            disease_id = self._orpha_to_disease.get(disease.orphanet_id)
            if disease_id is None:
                continue
            found.append(DiseaseScore(disease_id, disease.lower_ratio))
        return found
