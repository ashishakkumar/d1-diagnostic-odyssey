"""Five synthetic demo cases. Loading them still goes through apply_decision."""

from __future__ import annotations

from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb

from app.session import apply_decision, bind_reviewer
from d1_contracts import HpoTermDraft, LabReportedVariant

CaseId = str


def _row(n: int, orphanet: str, mondo: str, hpo_id: str, bin_name: str) -> dict:
    return {
        "id": f"00000000-0000-4000-8000-{n:012d}",
        "source": "orphanet-en_product4",
        "version": "2026-06-23-synthetic",
        "subject_key": f"{orphanet}|{hpo_id}",
        "orphanet_id": orphanet,
        "mondo_id": mondo,
        "hpo_id": hpo_id,
        "bin": bin_name,
    }


def demo_frequency_rows() -> list[dict]:
    """Ten scoreable diseases. Separated, stable, and abstain cases share this table."""
    rows = [
        _row(1, "ORPHA:9000001", "MONDO:8000001", "HP:0001166", "obligate"),
        _row(2, "ORPHA:9000001", "MONDO:8000001", "HP:0000272", "very_frequent"),
        _row(3, "ORPHA:9000001", "MONDO:8000001", "HP:0001250", "obligate"),
        _row(4, "ORPHA:9000002", "MONDO:8000002", "HP:0001166", "very_rare"),
        _row(5, "ORPHA:9000002", "MONDO:8000002", "HP:0000272", "excluded"),
        _row(6, "ORPHA:9000002", "MONDO:8000002", "HP:0001250", "obligate"),
        _row(7, "ORPHA:9000011", "MONDO:8000011", "HP:0001251", "obligate"),
        _row(8, "ORPHA:9000011", "MONDO:8000011", "HP:0001252", "obligate"),
        _row(9, "ORPHA:9000011", "MONDO:8000011", "HP:0000272", "excluded"),
        _row(10, "ORPHA:9000011", "MONDO:8000011", "HP:0001250", "obligate"),
        _row(11, "ORPHA:9000012", "MONDO:8000012", "HP:0001251", "frequent"),
        _row(12, "ORPHA:9000012", "MONDO:8000012", "HP:0001252", "frequent"),
        _row(13, "ORPHA:9000012", "MONDO:8000012", "HP:0000272", "excluded"),
        _row(14, "ORPHA:9000012", "MONDO:8000012", "HP:0001250", "obligate"),
    ]
    for index, orphanet in enumerate(range(9000021, 9000027)):
        orpha = f"ORPHA:{orphanet}"
        mondo = f"MONDO:{8000021 + index}"
        rows.append(_row(21 + index * 2, orpha, mondo, "HP:0000272", "excluded"))
        rows.append(_row(22 + index * 2, orpha, mondo, "HP:0001250", "obligate"))
    return rows


_SEPARATED = (
    {"hpo_id": "HP:0001166", "label": "Arachnodactyly", "presence": "present"},
    {"hpo_id": "HP:0000272", "label": "Malar flattening", "presence": "present"},
)
_ABSTAIN = ({"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"},)
_STABLE = (
    {"hpo_id": "HP:0001251", "label": "Ataxia", "presence": "present"},
    {"hpo_id": "HP:0001252", "label": "Hypotonia", "presence": "present"},
)
_VARIANT = {
    "gene_symbol": "FBN1",
    "variant": "NM_000138.5:c.1A>G",
    "lab_words": "the synthetic report's own words",
    "report_date": "2024-03-01",
}

DEMO_CASES: tuple[dict, ...] = (
    {
        "slug": "separated",
        "case_id": "00000000-0000-4000-8000-0000000000d1",
        "title": "Separated rows",
        "blurb": "Synthetic terms. One row is ahead, and the next row is zero.",
        "terms": _SEPARATED,
        "variant": None,
    },
    {
        "slug": "abstain",
        "case_id": "00000000-0000-4000-8000-0000000000d2",
        "title": "No separated row",
        "blurb": "Synthetic terms. Several rows sit too close, so the page abstains.",
        "terms": _ABSTAIN,
        "variant": None,
    },
    {
        "slug": "stable",
        "case_id": "00000000-0000-4000-8000-0000000000d3",
        "title": "Stable at both ends",
        "blurb": "Synthetic terms. The first row stays first at both ends of each bin.",
        "terms": _STABLE,
        "variant": None,
    },
    {
        "slug": "variant",
        "case_id": "00000000-0000-4000-8000-0000000000d4",
        "title": "Variant does not move the comparison",
        "blurb": "Same synthetic terms as Separated rows, plus a variant typed from a report.",
        "terms": _SEPARATED,
        "variant": _VARIANT,
    },
    {
        "slug": "limits",
        "case_id": "00000000-0000-4000-8000-0000000000d5",
        "title": "No dose on this page",
        "blurb": "Synthetic terms. This page does not choose a dose or a substitute.",
        "terms": _STABLE,
        "variant": None,
    },
)


def case_by_slug(slug: str) -> dict | None:
    for case in DEMO_CASES:
        if case["slug"] == slug:
            return case
    return None


def _variation(gene_symbol: str, variant: str) -> dict:
    return {
        "geneContext": {"symbol": gene_symbol},
        "expressions": [{"syntax": "hgvs", "value": variant}],
    }


def load_demo_case(connection: psycopg.Connection, slug: str, reviewer: str) -> str:
    """Approve the case through the gate. An existing observation is left as it is."""
    case = case_by_slug(slug)
    if case is None:
        raise KeyError(slug)
    case_id = str(case["case_id"])
    found = connection.execute(
        "SELECT 1 FROM app.observation WHERE case_id = %s::uuid LIMIT 1",
        (case_id,),
    ).fetchone()
    if found is not None:
        return case_id
    # Circular: ports.frequency_rows imports demo_frequency_rows from this module.
    from app.routes.ports import lay_wording

    bind_reviewer(connection, reviewer)
    for term in case["terms"]:
        _plain, explanation = lay_wording(str(term["hpo_id"]), str(term["label"]))
        draft_id = uuid4()
        draft = HpoTermDraft(
            id=draft_id,
            case_id=UUID(case_id),
            hpo_id=term["hpo_id"],
            label=term["label"],
            presence=term["presence"],
            explanation=explanation,
        )
        stored = draft.model_dump(mode="json", exclude_none=True)
        row = connection.execute(
            """
            INSERT INTO app.draft (id, case_id, kind, body)
            VALUES (%s, %s, 'hpo_term', %s)
            RETURNING body_hash
            """,
            (draft_id, case_id, Jsonb(stored)),
        ).fetchone()
        if row is None:
            raise RuntimeError("draft was not stored")
        apply_decision(connection, str(draft_id), "approve", row[0])
    variant = case["variant"]
    if variant is not None:
        draft_id = uuid4()
        draft = LabReportedVariant(
            id=draft_id,
            case_id=UUID(case_id),
            gene_symbol=variant["gene_symbol"],
            lab_words=variant["lab_words"],
            report_date=variant["report_date"],
            variation=_variation(variant["gene_symbol"], variant["variant"]),
        )
        stored = draft.model_dump(mode="json", exclude_none=True)
        row = connection.execute(
            """
            INSERT INTO app.draft (id, case_id, kind, body)
            VALUES (%s, %s, 'lab_reported_variant', %s)
            RETURNING body_hash
            """,
            (draft_id, case_id, Jsonb(stored)),
        ).fetchone()
        if row is None:
            raise RuntimeError("draft was not stored")
        apply_decision(connection, str(draft_id), "approve", row[0])
    return case_id
