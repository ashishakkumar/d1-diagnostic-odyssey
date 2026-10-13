"""Opt-in population allele-frequency prior. It is not a catalogue input."""

from collections.abc import Mapping, Sequence

LABEL_OFF = "Population prior is off. This is not a diagnosis."
LABEL_ON = "Population prior. Not a classification. This is not a diagnosis."
LIMITS = (
    "Checked-in fixture standing in for a public allele-frequency file. "
    "This build did not call gnomAD or ClinVar. "
    "A frequency is not applied as a rarity rule, and it does not change the catalogue comparison."
)


def population_prior(
    variant: str,
    rows: Sequence[Mapping],
    *,
    opted_in: bool,
) -> dict:
    """A labeled frequency, or an explicit absence. Off unless opted_in."""
    body: dict = {
        "experimental": True,
        "track": "experimental",
        "opted_in": opted_in,
        "found": False,
        "label": LABEL_ON if opted_in else LABEL_OFF,
        "limits": LIMITS,
        "source": None,
        "version": None,
        "population": None,
        "variant": variant or None,
        "allele_frequency": None,
    }
    if not opted_in:
        return body
    for row in rows:
        if str(row.get("variant") or "") != variant:
            continue
        body["found"] = True
        body["source"] = str(row["source"])
        body["version"] = str(row["version"])
        body["population"] = str(row["population"])
        body["allele_frequency"] = float(row["allele_frequency"])
        note = str(row.get("limits") or "")
        if note:
            body["limits"] = note
        return body
    body["limits"] = f"{LIMITS} No row matched this variant, so the prior is absent."
    return body
