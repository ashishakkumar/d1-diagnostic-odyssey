"""Load public packets, rank diseases from HPO terms, and write the method table.

The disease scorer sees HPO ids only. Gene symbols stay on the case for an
evaluation-only check and are never an argument to score().
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import tomllib
import uuid
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal, NamedTuple, Never, Protocol

from d1_contracts.canonical import body_hash
from d1_contracts.validate import parse_pipeline

PIN_PATH = Path(__file__).resolve().parents[1] / "pins.toml"
_OMIM = re.compile(r"OMIM(?:PS)?:(\d+)")
_ORPHA = re.compile(r"(?:Orphanet|ORPHA):(\d+)")


class DiseaseScore(NamedTuple):
    """A disease id and a phenotype-only score. Higher is better."""

    disease_id: str
    score: float


class PhenotypeScorer(Protocol):
    def score(self, hpo_ids: Sequence[str]) -> Sequence[DiseaseScore]:
        """Rank diseases from present HPO ids. There is no gene argument."""


@dataclass(frozen=True)
class Pins:
    store_version: str
    store_bytes: int
    store_sha256: str
    store_doi: str
    store_url: str
    mondo_version: str
    mondo_url: str
    hpo_version: str
    hpo_url: str
    ks: tuple[int, ...]
    tied_at_best: int
    keep_fraction: float
    knowledge_cutoff: date
    tool_name: str
    tool_version: str


@dataclass(frozen=True)
class EvalCase:
    pipeline: object
    truth_disease_id: str
    truth_genes: tuple[str, ...]
    created: datetime | None
    packet_id: str
    source: dict


@dataclass(frozen=True)
class StoreLoad:
    cases: tuple[EvalCase, ...]
    disease_ids: tuple[str, ...]
    skipped: int


@dataclass(frozen=True)
class CaseRank:
    packet_id: str
    rank: int | None
    no_confident: bool
    top_score: float | None
    scored: bool


@dataclass(frozen=True)
class RunResult:
    cases: tuple[CaseRank, ...]
    hits: dict[int, int]
    packets_scored: int
    packets_not_unique: int
    excluded_diseases: int
    no_confident: int
    confident: tuple[tuple[float, bool], ...]

    @property
    def no_confident_rate(self) -> float:
        if self.packets_scored == 0:
            return 0.0
        return self.no_confident / self.packets_scored


@dataclass(frozen=True)
class CalibrationBin:
    score: float
    n: int
    hits: int

    @property
    def hit_rate(self) -> float:
        return self.hits / self.n


@dataclass(frozen=True)
class TimeSplit:
    before: int
    after: int
    undated: int
    cutoff: date


class TermOverlapScorer:
    """Baseline: how many present terms sit on a disease's term list."""

    def __init__(self, catalogue: Mapping[str, Iterable[str]]) -> None:
        self._catalogue = {disease: set(terms) for disease, terms in catalogue.items()}

    def score(self, hpo_ids: Sequence[str]) -> list[DiseaseScore]:
        terms = set(hpo_ids)
        return [
            DiseaseScore(disease, float(len(terms & profile)))
            for disease, profile in self._catalogue.items()
        ]


def load_pins(path: Path = PIN_PATH) -> Pins:
    raw = tomllib.loads(path.read_text())
    store = raw["store"]
    mondo = raw["mondo"]
    hpo = raw["hpo"]
    metric = raw["metric"]
    tool = raw["tool"]
    return Pins(
        store_version=store["version"],
        store_bytes=int(store["bytes"]),
        store_sha256=store["sha256"],
        store_doi=store["doi"],
        store_url=store["url"],
        mondo_version=mondo["version"],
        mondo_url=mondo["url"],
        hpo_version=hpo["version"],
        hpo_url=hpo["url"],
        ks=tuple(int(k) for k in metric["k"]),
        tied_at_best=int(metric["tied_at_best"]),
        keep_fraction=float(metric["keep_fraction"]),
        knowledge_cutoff=date.fromisoformat(metric["knowledge_cutoff"]),
        tool_name=tool["name"],
        tool_version=tool["version"],
    )


def load_cases(path: Path) -> StoreLoad:
    pins = load_pins()
    cases: list[EvalCase] = []
    skipped = 0
    summary: str | None = None
    for name, payload in _members(path):
        if name.endswith("phenopacket_store.summary.tsv"):
            summary = payload.decode() if isinstance(payload, bytes) else payload
            continue
        if not str(name).endswith(".json"):
            continue
        try:
            packet = json.loads(payload)
            case = _case_from_packet(packet, pins.store_version)
        except Exception:
            skipped += 1
            continue
        if case is None:
            skipped += 1
            continue
        cases.append(case)
    if summary is None:
        disease_ids = _first(case.truth_disease_id for case in cases)
    else:
        disease_ids = _summary_diseases(summary)
    return StoreLoad(tuple(cases), tuple(disease_ids), skipped)


def present_hpo_ids(case: EvalCase) -> list[str]:
    return [term.hpo_id for term in case.pipeline.accepted_terms if term.presence == "present"]


def degrade(
    case: EvalCase,
    level: Literal["full", "fewer", "vaguer", "patient"],
    parents: Mapping[str, tuple[str, str]],
    keep_fraction: float,
) -> EvalCase:
    """Patient-style input. Fewer terms, then optional parents.

    ponytail: PhEval scramble is random and also inserts unrelated terms. This keeps a
    sorted prefix and one parent. Ceiling: not lay synonyms. Upgrade with an HPO synonym table.
    """
    features = list(case.source.get("phenotypicFeatures") or [])
    present = [feature for feature in features if not feature.get("excluded")]
    excluded = [feature for feature in features if feature.get("excluded")]
    if level == "full":
        changed = present
    elif level == "fewer":
        changed = _fewer(present, keep_fraction)
    elif level == "vaguer":
        changed = _vaguer(present, parents)
    elif level == "patient":
        changed = _vaguer(_fewer(present, keep_fraction), parents)
    else:
        _never(level)
    packet = deepcopy(case.source)
    packet["phenotypicFeatures"] = [*changed, *excluded]
    rebuilt = _case_from_packet(packet, case.pipeline.evidence[0].version)
    if rebuilt is None:
        raise ValueError(case.packet_id)
    return rebuilt


def load_orphanet_tsv(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            disease = row["disease_id"].strip()
            mapping.setdefault(disease, set())
            orpha = row["orphanet_id"].strip()
            if orpha:
                mapping[disease].add(_orpha(orpha))
    return mapping


def load_parents(path: Path) -> dict[str, tuple[str, str]]:
    parents: dict[str, tuple[str, str]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["hpo_id"].strip()] = (row["parent_id"].strip(), row["parent_label"].strip())
    return parents


def load_catalogue(path: Path) -> dict[str, set[str]]:
    raw = json.loads(path.read_text())
    return {disease: set(terms) for disease, terms in raw.items()}


def parents_from_obo(path: Path) -> dict[str, tuple[str, str]]:
    names: dict[str, str] = {}
    first_parent: dict[str, str] = {}
    obsolete: set[str] = set()
    current: str | None = None
    for line in path.read_text().splitlines():
        if line == "[Term]" or (line.startswith("[") and line.endswith("]")):
            current = None
            continue
        if line.startswith("id: HP:"):
            current = line.removeprefix("id: ").strip()
            continue
        if current is None:
            continue
        if line.startswith("name: "):
            names.setdefault(current, line.removeprefix("name: ").strip())
        elif line.startswith("is_obsolete: true"):
            obsolete.add(current)
        elif line.startswith("is_a: HP:") and current not in first_parent:
            parent = line.removeprefix("is_a: ").split("!", 1)[0].strip()
            first_parent[current] = parent
    return {
        hpo: (parent, names.get(parent, parent))
        for hpo, parent in first_parent.items()
        if hpo not in obsolete
    }


def orphanet_from_mondo_nodes(path: Path) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            xref = row.get("xref") or ""
            orphas = {_orpha(f"ORPHA:{digits}") for digits in _ORPHA.findall(xref)}
            if not orphas:
                continue
            for digits in _OMIM.findall(xref):
                found.setdefault(f"OMIM:{digits}", set()).update(orphas)
    return found


def unique_orphanet(
    disease_ids: Iterable[str],
    mapping: Mapping[str, set[str]],
) -> tuple[set[str], int]:
    unique: set[str] = set()
    excluded = 0
    for disease in disease_ids:
        if len(mapping.get(disease, ())) == 1:
            unique.add(disease)
        else:
            excluded += 1
    return unique, excluded


def rank_diseases(scores: Sequence[DiseaseScore]) -> dict[str, int]:
    """Ties take the worst rank in the tie. Rank 1 is the best score."""
    ordered = sorted(scores, key=lambda item: (-item.score, item.disease_id))
    ranks: dict[str, int] = {}
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end].score == ordered[index].score:
            end += 1
        for item in ordered[index:end]:
            ranks[item.disease_id] = end
        index = end
    return ranks


def is_no_confident(scores: Sequence[DiseaseScore], tied_at_best: int) -> bool:
    if not scores:
        return True
    best = max(item.score for item in scores)
    if best <= 0:
        return True
    tied = sum(1 for item in scores if item.score == best)
    return tied >= tied_at_best


def run_eval(
    cases: Sequence[EvalCase],
    scorer: PhenotypeScorer,
    disease_ids: Iterable[str],
    mapping: Mapping[str, set[str]],
    ks: Sequence[int],
    tied_at_best: int,
) -> RunResult:
    unique, excluded = unique_orphanet(disease_ids, mapping)
    rows = [rank_case(case, scorer, unique, tied_at_best) for case in cases]
    return summarize(rows, excluded, ks)


def rank_case(
    case: EvalCase,
    scorer: PhenotypeScorer,
    unique: set[str],
    tied_at_best: int,
) -> CaseRank:
    if case.truth_disease_id not in unique:
        return CaseRank(case.packet_id, None, False, None, False)
    scores = [item for item in scorer.score(present_hpo_ids(case)) if item.disease_id in unique]
    if is_no_confident(scores, tied_at_best):
        return CaseRank(case.packet_id, None, True, None, True)
    ranks = rank_diseases(scores)
    top = max(item.score for item in scores)
    return CaseRank(
        case.packet_id,
        ranks.get(case.truth_disease_id),
        False,
        float(top),
        True,
    )


def summarize(rows: Sequence[CaseRank], excluded: int, ks: Sequence[int]) -> RunResult:
    hits = {k: 0 for k in ks}
    confident: list[tuple[float, bool]] = []
    no_confident = 0
    scored = 0
    for row in rows:
        if not row.scored:
            continue
        scored += 1
        if row.no_confident:
            no_confident += 1
            continue
        for k in ks:
            if row.rank is not None and row.rank <= k:
                hits[k] += 1
        if row.top_score is not None:
            confident.append((row.top_score, row.rank is not None and row.rank <= 1))
    return RunResult(
        cases=tuple(rows),
        hits=hits,
        packets_scored=scored,
        packets_not_unique=sum(1 for row in rows if not row.scored),
        excluded_diseases=excluded,
        no_confident=no_confident,
        confident=tuple(confident),
    )


def loo_catalogue(
    cases: Sequence[EvalCase],
    query_id: str,
    allowed: set[str],
) -> dict[str, set[str]]:
    """Term lists from other public packets. The query packet's terms are left out."""
    profiles = {disease: set() for disease in allowed}
    for case in cases:
        if case.packet_id == query_id or case.truth_disease_id not in profiles:
            continue
        profiles[case.truth_disease_id].update(present_hpo_ids(case))
    return profiles


def count_terms(cases: Sequence[EvalCase], allowed: set[str]) -> dict[str, dict[str, int]]:
    counts = {disease: {} for disease in allowed}
    for case in cases:
        bucket = counts.get(case.truth_disease_id)
        if bucket is None:
            continue
        for term in set(present_hpo_ids(case)):
            bucket[term] = bucket.get(term, 0) + 1
    return counts


def holdout_from_counts(
    counts: Mapping[str, Mapping[str, int]],
    disease: str,
    terms: set[str],
) -> dict[str, set[str]]:
    profiles: dict[str, set[str]] = {}
    for name, bucket in counts.items():
        kept: set[str] = set()
        for term, count in bucket.items():
            drop = 1 if name == disease and term in terms else 0
            if count - drop > 0:
                kept.add(term)
        profiles[name] = kept
    return profiles


def calibration_curve(rows: Sequence[tuple[float, bool]]) -> list[CalibrationBin]:
    grouped: dict[float, list[bool]] = {}
    for score, hit in rows:
        grouped.setdefault(score, []).append(hit)
    return [CalibrationBin(score, len(hits), sum(hits)) for score, hits in sorted(grouped.items())]


def time_split(cases: Sequence[EvalCase], cutoff: date) -> TimeSplit:
    before = after = undated = 0
    for case in cases:
        if case.created is None:
            undated += 1
        elif case.created.date() <= cutoff:
            before += 1
        else:
            after += 1
    return TimeSplit(before, after, undated, cutoff)


def time_split_note(split: TimeSplit) -> str:
    return (
        f"Time-split leakage note. Cutoff {split.cutoff.isoformat()}. "
        f"before={split.before} after={split.after} undated={split.undated}. "
        "The packet created timestamp is not a publication date. "
        "This check is not a pass. "
        "A packet dated before the cutoff can still share a paper with the public table."
    )


def gene_topk(true_genes: Sequence[str], ranked_genes: Sequence[str], k: int) -> bool:
    """Evaluation only. The disease runner does not call this."""
    top = set(ranked_genes[:k])
    return any(gene in top for gene in true_genes)


def results_markdown(
    result: RunResult,
    pins: Pins,
    level: str,
    note: str,
    tool: str | None = None,
) -> str:
    return results_document([(level, result)], pins, note, tool)


def results_document(
    rows: Sequence[tuple[str, RunResult]],
    pins: Pins,
    note: str,
    tool: str | None = None,
) -> str:
    name = tool or pins.tool_name
    lines = [
        "# Public-case method results",
        "",
        "For research use only. Not for use in diagnostic procedures.",
        "",
        "These rows are method results on public cases. They are not a benefit to a real patient.",
        "",
        "| degradation | tool | tool_version | store | store_sha256 | mondo "
        "| top1 | top3 | top10 | excluded_diseases | packets_scored | no_confident |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for level, result in rows:
        scored = result.packets_scored
        lines.append(
            "| "
            + " | ".join(
                [
                    level,
                    name,
                    pins.tool_version,
                    pins.store_version,
                    pins.store_sha256,
                    pins.mondo_version,
                    _ratio(result.hits.get(1, 0), scored),
                    _ratio(result.hits.get(3, 0), scored),
                    _ratio(result.hits.get(10, 0), scored),
                    str(result.excluded_diseases),
                    str(scored),
                    _ratio(result.no_confident, scored),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Calibration", ""])
    for level, result in rows:
        lines.extend(
            [
                f"### {level}",
                "",
                "| top_score | n | top1_hits | hit_rate |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in calibration_curve(result.confident):
            lines.append(f"| {item.score} | {item.n} | {item.hits} | {item.hit_rate:.3f} |")
        lines.append("")
    lines.extend(["## Time-split leakage note", "", note, ""])
    return "\n".join(lines)


def check_store_file(path: Path, pins: Pins) -> None:
    size = path.stat().st_size
    if size != pins.store_bytes:
        raise SystemExit(f"store zip is {size} bytes, pin is {pins.store_bytes}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != pins.store_sha256:
        raise SystemExit(f"store sha256 {digest} does not match the pin")


def _never(value: Never) -> Never:
    raise ValueError(value)


def _ratio(hits: int, total: int) -> str:
    return f"{hits}/{total}"


def _orpha(value: str) -> str:
    match = _ORPHA.search(value)
    if match is None:
        return value
    return f"ORPHA:{match.group(1)}"


def _first(values: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def _members(path: Path) -> list[tuple[str, bytes | str]]:
    if path.is_dir():
        found = [(file.name, file.read_text()) for file in sorted(path.glob("*.json"))]
        summary = path / "phenopacket_store.summary.tsv"
        if summary.exists():
            found.append((summary.name, summary.read_text()))
        return found
    with zipfile.ZipFile(path) as handle:
        return [(name, handle.read(name)) for name in sorted(handle.namelist())]


def _summary_diseases(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for row in csv.DictReader(text.splitlines(), delimiter="\t"):
        disease = (row.get("disease_id") or "").strip()
        if disease and disease not in seen:
            seen.add(disease)
            found.append(disease)
    return found


def _fewer(features: list[dict], keep_fraction: float) -> list[dict]:
    ordered = sorted(features, key=lambda feature: (feature.get("type") or {}).get("id") or "")
    keep = math.ceil(len(ordered) * keep_fraction)
    return ordered[:keep]


def _vaguer(features: list[dict], parents: Mapping[str, tuple[str, str]]) -> list[dict]:
    changed: list[dict] = []
    seen: set[str] = set()
    for feature in features:
        term = dict(feature.get("type") or {})
        hpo = term.get("id") or ""
        parent = parents.get(hpo)
        if parent is not None:
            hpo, label = parent
            term = {"id": hpo, "label": label}
        if hpo in seen:
            continue
        seen.add(hpo)
        updated = dict(feature)
        updated["type"] = term
        updated.pop("excluded", None)
        changed.append(updated)
    return changed


def _case_from_packet(packet: dict, store_version: str) -> EvalCase | None:
    diseases = _disease_ids(packet)
    if len(diseases) != 1:
        return None
    packet_id = str(packet.get("id") or "")
    if not packet_id:
        return None
    created = _created(packet)
    report_date = created.date() if created is not None else date(2020, 1, 1)
    decided = created or datetime(2020, 1, 1, tzinfo=timezone.utc)
    case_uuid = _uuid(packet_id, "case")
    drafts = []
    accepted = []
    approvals = []
    for hpo_id, label, presence in _terms(packet):
        draft_id = _uuid(packet_id, hpo_id, presence, "draft")
        approval_id = _uuid(packet_id, hpo_id, presence, "approval")
        draft = {
            "id": str(draft_id),
            "case_id": str(case_uuid),
            "hpo_id": hpo_id,
            "label": label,
            "presence": presence,
        }
        drafts.append(draft)
        accepted.append(
            {
                "id": str(_uuid(packet_id, hpo_id, presence, "accepted")),
                "case_id": str(case_uuid),
                "draft_id": str(draft_id),
                "hpo_id": hpo_id,
                "label": label,
                "presence": presence,
                "approval_id": str(approval_id),
            }
        )
        approvals.append(
            {
                "id": str(approval_id),
                "draft_id": str(draft_id),
                "reviewer": "public-case-loader",
                "decision": "approve",
                "body_hash": body_hash({"hpo_id": hpo_id, "label": label, "presence": presence}),
                "decided_at": decided.isoformat(),
            }
        )
    pipeline = parse_pipeline(
        {
            "case": packet,
            "hpo_term_drafts": drafts,
            "accepted_terms": accepted,
            "lab_reported_variants": _variants(packet, case_uuid, report_date),
            "evidence": [
                {
                    "id": str(_uuid(packet_id, "evidence")),
                    "source": "phenopacket-store",
                    "version": store_version,
                }
            ],
            "change_events": [],
            "approvals": approvals,
        }
    )
    return EvalCase(
        pipeline=pipeline,
        truth_disease_id=diseases[0],
        truth_genes=_genes(packet),
        created=created,
        packet_id=packet_id,
        source=packet,
    )


def _disease_ids(packet: dict) -> list[str]:
    found: list[str] = []
    for interpretation in packet.get("interpretations") or []:
        disease = ((interpretation.get("diagnosis") or {}).get("disease") or {}).get("id")
        if disease:
            found.append(str(disease))
    if not found:
        for disease in packet.get("diseases") or []:
            term = (disease.get("term") or {}).get("id")
            if term:
                found.append(str(term))
    return _first(found)


def _descriptor(genomic: dict) -> dict:
    variant = genomic.get("variantInterpretation") or {}
    descriptor = variant.get("variationDescriptor") or {}
    return descriptor if isinstance(descriptor, dict) else {}


def _genes(packet: dict) -> tuple[str, ...]:
    found: list[str] = []
    for interpretation in packet.get("interpretations") or []:
        diagnosis = interpretation.get("diagnosis") or {}
        for genomic in diagnosis.get("genomicInterpretations") or []:
            descriptor = _descriptor(genomic)
            symbol = (descriptor.get("geneContext") or {}).get("symbol")
            if not symbol:
                symbol = (genomic.get("gene") or {}).get("symbol")
            if symbol and symbol not in found:
                found.append(str(symbol))
    return tuple(found)


def _variants(packet: dict, case_uuid: uuid.UUID, report_date: date) -> list[dict]:
    variants: list[dict] = []
    packet_id = str(packet.get("id") or "")
    for interpretation in packet.get("interpretations") or []:
        diagnosis = interpretation.get("diagnosis") or {}
        for genomic in diagnosis.get("genomicInterpretations") or []:
            descriptor = _descriptor(genomic)
            symbol = (descriptor.get("geneContext") or {}).get("symbol")
            if not symbol or not descriptor.get("id"):
                continue
            variants.append(
                {
                    "id": str(_uuid(packet_id, symbol, descriptor["id"], "variant")),
                    "case_id": str(case_uuid),
                    "gene_symbol": symbol,
                    "lab_words": "quoted from the public phenopacket",
                    "report_date": report_date.isoformat(),
                    "variation": descriptor,
                }
            )
    return variants


def _terms(packet: dict) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for feature in packet.get("phenotypicFeatures") or []:
        term = feature.get("type") or {}
        hpo_id = str(term.get("id") or "")
        if not re.fullmatch(r"HP:[0-9]{7}", hpo_id):
            continue
        presence = "excluded" if feature.get("excluded") else "present"
        rows.append((hpo_id, str(term.get("label") or hpo_id), presence))
    return rows


def _created(packet: dict) -> datetime | None:
    raw = (packet.get("metaData") or {}).get("created")
    if not raw:
        return None
    parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _uuid(*parts: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, "https://d1.local/eval/" + "/".join(parts))
