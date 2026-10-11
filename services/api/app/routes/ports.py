"""Notebook calls into the scorer, the scanner, and the change watcher."""

import json
import os
from pathlib import Path

from d1_ingest.load import load_clinvar
from d1_ingest.watch import watch
from d1_safety.redflag import footer_text, stop_screen
from d1_safety.render import SafetyError, render
from d1_safety.scan import scan

from app.demo_cases import demo_frequency_rows
from d1_contracts import LabReportedVariant, parse_report
from scoring import catalogue_score, to_public
from scoring.allele import population_prior

ROOT = Path(__file__).resolve().parents[4]

# ponytail: two pinned lay sentences. Upgrade: an HPO lay-synonym file.
_LAY = {
    "HP:0001166": (
        "long fingers",
        "Fingers that are long for the hand.",
    ),
    "HP:0000272": (
        "flat cheeks",
        "Cheeks that look flatter than usual.",
    ),
    "HP:0001250": (
        "seizures",
        "A burst of brain activity that changes movement, awareness, or sensation.",
    ),
    "HP:0001251": (
        "unsteady movement",
        "Movement that is hard to keep steady.",
    ),
    "HP:0001252": (
        "low muscle tone",
        "Muscles that feel floppy and do less of the work of holding a posture.",
    ),
}


def lay_wording(hpo_id: str, official_name: str) -> tuple[str, str]:
    """Plain words and the explanation stored on the term draft."""
    pinned = _LAY.get(hpo_id)
    if pinned is not None:
        return pinned
    return official_name, "No short explanation is pinned for this term."


def scan_notebook_text(
    text: str,
    quotes: list[tuple[int, int, str]] | None = None,
) -> str:
    """Return the text only when the never-say scan finds nothing."""
    rules = scan(text, quotes)
    if rules:
        raise SafetyError(rules)
    return text


def frequency_rows() -> list[dict]:
    raw = os.environ.get("D1_FREQUENCY_ROWS", "")
    if raw:
        path = Path(raw)
        if not path.is_file():
            return []
        return json.loads(path.read_text())
    return demo_frequency_rows()


def allele_rows() -> list[dict]:
    raw = os.environ.get("D1_ALLELE_ROWS", "")
    default = Path(__file__).resolve().parents[1] / "data" / "allele_frequencies.json"
    path = Path(raw) if raw else default
    if not path.is_file():
        return []
    return json.loads(path.read_text())


def report_for(accepted: list[tuple[str, str]]) -> dict:
    """`to_public` evidence and margin, in the shared report shape."""
    # Decision ids tie when one transaction approves several rows. Sort so the
    # comparison does not shuffle between two cases with the same terms.
    ordered = sorted(accepted, key=lambda item: (item[0], item[1]))
    public = to_public(catalogue_score(ordered, frequency_rows()))
    body: dict = {
        "evidence": [
            {
                "hpo_id": term["hpo_id"],
                "relation": term["relation"],
                "source": term["source"],
                "version": term["version"],
                "orphanet_id": term["orphanet_id"],
                "lower_ratio": term["lower_ratio"],
                "upper_ratio": term["upper_ratio"],
            }
            for term in public["evidence"]["terms"]
        ],
        "margin": public["margin"],
        "abstained": not public["evidence"]["confident"],
    }
    if public["evidence"].get("abstain_reason"):
        body["abstain_reason"] = public["evidence"]["abstain_reason"]
    if public["evidence"].get("leading_orphanet_id"):
        body["leading_orphanet_id"] = public["evidence"]["leading_orphanet_id"]
    if public.get("margin_reason"):
        body["margin_reason"] = public["margin_reason"]
    if "probability" in public:
        body["probability"] = public["probability"]
        body["reliability_curve"] = public["reliability_curve"]
    dumped = parse_report(body).model_dump(mode="json", exclude_none=True)
    dumped.setdefault("margin", None)
    return dumped


def _snapshots() -> tuple[list, list]:
    earlier = Path(
        os.environ.get(
            "D1_CLINVAR_EARLIER",
            ROOT / "tests" / "ingest" / "fixtures" / "variant_summary_2024-01.txt",
        )
    )
    later = Path(
        os.environ.get(
            "D1_CLINVAR_LATER",
            ROOT / "tests" / "ingest" / "fixtures" / "variant_summary_2024-02.txt",
        )
    )
    if not earlier.is_file() or not later.is_file():
        return [], []
    return load_clinvar(earlier), load_clinvar(later)


def change_events(variants: list[LabReportedVariant]) -> list:
    earlier, later = _snapshots()
    if not earlier or not later:
        return []
    found = []
    for variant in variants:
        found.extend(watch(earlier=earlier, later=later, variant=variant))
    return found


def render_sentence(template_id: str, row: dict) -> tuple[str, list[tuple[int, int, str]]]:
    return render(template_id, row)


def prior_for(variant: str, *, opted_in: bool) -> dict:
    body = population_prior(variant, allele_rows(), opted_in=opted_in)
    text = " ".join(str(body[key]) for key in ("label", "limits") if body.get(key))
    rules = scan(text)
    if rules:
        raise SafetyError(rules)
    return body


def country_footer() -> str:
    return footer_text()


def red_flag(text: str) -> dict | None:
    return stop_screen(text)
