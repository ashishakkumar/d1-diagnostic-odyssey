"""Stub ports for the scoring and safety work happening in parallel."""

from uuid import UUID

from d1_contracts import HpoTermDraft

# ponytail: a handful of pinned lay phrases. Upgrade: the scoring lay-term port.
_LAY = {
    "HP:0001250": (
        "seizures",
        "A burst of brain activity that changes movement, awareness, or sensation.",
    ),
    "HP:0001252": (
        "low muscle tone",
        "Muscles that feel floppy and do less of the work of holding a posture.",
    ),
}


def proposed_symptom_drafts(case_id: UUID) -> list[HpoTermDraft]:
    """TODO(scoring): return that agent's drafted terms for this case.

    This notebook does not score. An empty list means nothing was proposed.
    """
    del case_id
    return []


def lay_wording(hpo_id: str, official_name: str) -> tuple[str, str]:
    """TODO(scoring): replace this glossary with the lay-term port.

    Plain words and a short explanation. The official name stays the draft label.
    """
    pinned = _LAY.get(hpo_id)
    if pinned is not None:
        return pinned
    return official_name, "No short explanation is pinned for this term."


def scan_notebook_text(text: str) -> str:
    """TODO(safety): pass this fixed-template text through the never-say scanner.

    This function does not scan. It returns the template text unchanged.
    """
    return text
