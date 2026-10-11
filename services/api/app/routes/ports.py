"""Notebook calls into the scorer, the scanner, and the change watcher."""

import json
import os
from pathlib import Path

from d1_ingest.load import load_clinvar
from d1_ingest.watch import watch
from d1_safety.redflag import footer_text, stop_screen
from d1_safety.render import SafetyError, render
from d1_safety.scan import scan

from d1_contracts import LabReportedVariant, parse_report
from scoring import catalogue_score, to_public

ROOT = Path(__file__).resolve().parents[4]

# ponytail: two pinned lay sentences. Upgrade: an HPO lay-synonym file.
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
    path = Path(raw) if raw else ROOT / "tests" / "scoring" / "fixtures" / "frequencies.json"
    if not path.is_file():
        return []
    return json.loads(path.read_text())


def report_for(accepted: list[tuple[str, str]]) -> dict:
    """`to_public` evidence and margin, in the shared report shape."""
    public = to_public(catalogue_score(accepted, frequency_rows()))
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
                "background": term["background"],
            }
            for term in public["evidence"]["terms"]
        ],
        "margin": public["margin"],
        "abstained": not public["evidence"]["confident"],
    }
    if public.get("margin_fact"):
        body["margin_fact"] = public["margin_fact"]
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


def country_footer() -> str:
    return footer_text()


def red_flag(text: str) -> dict | None:
    return stop_screen(text)
