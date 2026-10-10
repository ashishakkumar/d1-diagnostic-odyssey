"""Read HPO, Orphadata Science, ClinVar, and ClinGen into cited rows."""

import csv
import gzip
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from xml.etree import ElementTree

from .records import CitedRow

_MONTH = re.compile(r"variant_summary_(\d{4}-\d{2})")
_HGVS = re.compile(r"^([A-Za-z]{2}_\d+\.\d+)\([^)]+\):([A-Za-z]\.[^\s(]+)")


def load_hpo(path: Path) -> list[CitedRow]:
    version = None
    terms: list[tuple[str, str]] = []
    current: dict[str, str] | None = None

    def flush() -> None:
        nonlocal current
        if current and current.get("id") and current.get("name"):
            terms.append((current["id"], current["name"]))
        current = None

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("[") and line.endswith("]"):
            flush()
            current = {} if line == "[Term]" else None
            continue
        if current is None:
            if line.startswith("data-version:"):
                version = line.split(":", 1)[1].strip()
            continue
        if line.startswith("id:"):
            current["id"] = line.split(":", 1)[1].strip()
        elif line.startswith("name:"):
            current["name"] = line.split(":", 1)[1].strip()
    flush()
    if not version:
        raise ValueError(f"HPO file has no data-version: {path}")
    return [
        CitedRow(
            source="HPO",
            version=version,
            subject_key=term_id,
            text=name,
            match_keys=(term_id,),
        )
        for term_id, name in terms
    ]


def load_orphadata_phenotypes(path: Path) -> list[CitedRow]:
    root = ElementTree.parse(path).getroot()
    version = root.attrib.get("date", "").strip()
    if not version:
        raise ValueError(f"Orphadata file has no date: {path}")
    rows: list[CitedRow] = []
    for disorder in root.iter("Disorder"):
        code = (disorder.findtext("OrphaCode") or "").strip()
        if not code:
            continue
        associations = disorder.findall("HPODisorderAssociationList/HPODisorderAssociation")
        for assoc in associations:
            hpo_id = (assoc.findtext("HPO/HPOId") or "").strip()
            frequency = (assoc.findtext("HPOFrequency/Name") or "").strip()
            if not hpo_id or not frequency:
                continue
            key = f"ORPHA:{code}|{hpo_id}"
            rows.append(
                CitedRow(
                    source="Orphadata Science en_product4",
                    version=version,
                    subject_key=key,
                    text=frequency,
                    match_keys=(key,),
                )
            )
    return rows


def load_orphadata_genes(path: Path) -> list[CitedRow]:
    root = ElementTree.parse(path).getroot()
    version = root.attrib.get("date", "").strip()
    if not version:
        raise ValueError(f"Orphadata file has no date: {path}")
    rows: list[CitedRow] = []
    for disorder in root.iter("Disorder"):
        code = (disorder.findtext("OrphaCode") or "").strip()
        if not code:
            continue
        associations = disorder.findall("DisorderGeneAssociationList/DisorderGeneAssociation")
        for assoc in associations:
            symbol = (assoc.findtext("Gene/Symbol") or "").strip()
            kind = (assoc.findtext("DisorderGeneAssociationType/Name") or "").strip()
            if not symbol or not kind:
                continue
            key = f"ORPHA:{code}|{symbol}"
            rows.append(
                CitedRow(
                    source="Orphadata Science en_product6",
                    version=version,
                    subject_key=key,
                    text=kind,
                    match_keys=(key, f"gene:{symbol}"),
                )
            )
    return rows


def clinvar_version(path: Path) -> str:
    match = _MONTH.search(path.name)
    if not match:
        raise ValueError(f"ClinVar archive name has no YYYY-MM: {path.name}")
    return match.group(1)


def published_clinvar_text(significance: str, last_evaluated: str) -> str:
    return f"ClinicalSignificance: {significance}; LastEvaluated: {last_evaluated}"


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open(encoding="utf-8", newline="")


def _iter_records(path: Path) -> Iterator[dict[str, str | None]]:
    with _open_text(path) as handle:
        header_line = handle.readline()
        if not header_line:
            raise ValueError(f"empty ClinVar file: {path}")
        fieldnames = header_line.lstrip("\ufeff").lstrip("#").rstrip("\r\n").split("\t")
        reader = csv.DictReader(handle, fieldnames=fieldnames, delimiter="\t")
        for record in reader:
            yield record


def _cell(record: dict[str, str | None], name: str) -> str:
    return (record.get(name) or "").strip()


def gene_tokens(raw: str) -> frozenset[str]:
    return frozenset(
        part.strip() for part in re.split(r"[,;]", raw) if part.strip() and part.strip() != "-"
    )


def _genes(record: dict[str, str | None]) -> frozenset[str]:
    return gene_tokens(_cell(record, "GeneSymbol"))


def _match_keys(variation_id: str, record: dict[str, str | None]) -> tuple[str, ...]:
    keys = [f"variation:{variation_id}"]
    allele = _cell(record, "AlleleID")
    name = _cell(record, "Name")
    if allele:
        keys.append(f"allele:{allele}")
    if name:
        keys.append(f"name:{name}")
        found = _HGVS.match(name)
        if found:
            keys.append(f"hgvs:{found.group(1)}:{found.group(2)}")
    keys.extend(f"gene:{gene}" for gene in sorted(_genes(record)))
    return tuple(keys)


def _keep(variation_id: str, assembly: str, seen: dict | set, grch38: set[str]) -> bool:
    if not variation_id or variation_id in grch38:
        return False
    if variation_id in seen and assembly != "GRCh38":
        return False
    return True


def load_clinvar(path: Path) -> list[CitedRow]:
    version = clinvar_version(path)
    rows: dict[str, CitedRow] = {}
    grch38: set[str] = set()
    for record in _iter_records(path):
        variation_id = _cell(record, "VariationID")
        assembly = _cell(record, "Assembly")
        if not _keep(variation_id, assembly, rows, grch38):
            continue
        rows[variation_id] = CitedRow(
            source="ClinVar",
            version=version,
            subject_key=variation_id,
            text=published_clinvar_text(
                _cell(record, "ClinicalSignificance"),
                _cell(record, "LastEvaluated"),
            ),
            match_keys=_match_keys(variation_id, record),
        )
        if assembly == "GRCh38":
            grch38.add(variation_id)
    return [rows[key] for key in sorted(rows, key=lambda item: (len(item), item))]


def clinvar_index(path: Path) -> tuple[str, dict[str, tuple[str, str, bool]]]:
    """Variation id to (published text, gene-symbol cell, GRCh38 already kept)."""
    version = clinvar_version(path)
    index: dict[str, tuple[str, str, bool]] = {}
    for record in _iter_records(path):
        variation_id = _cell(record, "VariationID")
        if not variation_id:
            continue
        assembly = _cell(record, "Assembly")
        current = index.get(variation_id)
        if current is not None and (current[2] or assembly != "GRCh38"):
            continue
        index[variation_id] = (
            sys.intern(
                published_clinvar_text(
                    _cell(record, "ClinicalSignificance"),
                    _cell(record, "LastEvaluated"),
                )
            ),
            sys.intern(_cell(record, "GeneSymbol")),
            assembly == "GRCh38",
        )
    return version, index


def load_clingen_gene_validity(path: Path) -> list[CitedRow]:
    version = None
    header: list[str] | None = None
    rows: list[CitedRow] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for record in csv.reader(handle):
            if not record or not record[0].strip():
                continue
            cell = record[0].strip()
            if cell.startswith("FILE CREATED:"):
                version = cell.split(":", 1)[1].strip()
                continue
            if header is None:
                if cell == "GENE SYMBOL":
                    header = [part.strip() for part in record]
                continue
            if set(cell) <= {"+"}:
                continue
            data = {
                header[i]: (record[i].strip() if i < len(record) else "")
                for i in range(len(header))
            }
            symbol = data.get("GENE SYMBOL", "")
            if not symbol:
                continue
            mondo = data.get("DISEASE ID (MONDO)", "")
            moi = data.get("MOI", "")
            key = f"{symbol}|{mondo}|{moi}"
            text = (
                f"CLASSIFICATION: {data.get('CLASSIFICATION', '')}; "
                f"CLASSIFICATION DATE: {data.get('CLASSIFICATION DATE', '')}"
            )
            rows.append(
                CitedRow(
                    source="ClinGen gene-disease validity",
                    version=version or "",
                    subject_key=key,
                    text=text,
                    match_keys=(key, f"gene:{symbol}"),
                )
            )
    if not version:
        raise ValueError(f"ClinGen file has no FILE CREATED date: {path}")
    return rows
