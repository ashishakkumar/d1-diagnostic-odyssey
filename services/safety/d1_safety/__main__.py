"""Scan every shipped sentence.

Exit 1 when a never-say rule, an empty phrase list, or a grade fails.

Web and scoring code can call `d1_safety.scan`. This module is `make safety-scan`.
"""

import os

from d1_safety.readability import CEILING, grade, prose_for_grade, template_grades
from d1_safety.redflag import countries, footer_text, load_phrases, stop_template
from d1_safety.render import SafetyError, render, templates
from d1_safety.scan import scan

_FIXTURES: dict[str, dict] = {
    "questions_for_doctor": {
        "label": "Fever",
        "hpo_id": "HP:0001945",
        "presence": "present",
    },
    "reason_marked_excluded": {
        "label": "Fever",
        "hpo_id": "HP:0001945",
        "presence": "excluded",
    },
    "reason_no_public_row": {
        "source": "ClinVar",
        "version": "2026-10",
        "subject_key": "NM_000138.5",
    },
    "public_database_change": {
        "source": "ClinVar",
        "version": "2026-10",
        "subject_key": "NM_000138.5",
        "previous_text": "older wording",
        "current_text": "newer wording",
    },
    "not_confident_yet": {"confirmed_count": 2},
    "lab_report_words": {
        "report_date": "2020-01-02",
        "gene_symbol": "FBN1",
        "lab_words": "seen in the report",
    },
    "emergency_footer": {},
    "catalogue_row": {
        "source": "orphanet-en_product4",
        "version": "2026-06-23-synthetic",
        "orphanet_id": "ORPHA:9000001",
    },
    "catalogue_margin": {"margin": "11.111"},
    "catalogue_margin_unbounded": {},
    "catalogue_abstained": {"abstain_reason": "several rows sit close together"},
    "no_dose": {},
}


def _grade(code: str, name: str, text: str, problems: list[str]) -> None:
    found = scan(text)
    if found:
        problems.append(f"{code} {name}: {', '.join(found)}")
    score = grade(prose_for_grade(text))
    if score > CEILING:
        problems.append(f"{code} {name} grade {score:.2f} is above {CEILING}")


def _check_country(code: str, problems: list[str]) -> None:
    os.environ["D1_COUNTRY"] = code
    try:
        load_phrases()
    except ValueError as exc:
        problems.append(f"{code}: {exc}")
    _grade(code, "stop_screen", stop_template(), problems)
    try:
        footer = footer_text()
    except RuntimeError as exc:
        problems.append(f"{code} emergency_footer: {exc}")
    else:
        _grade(code, "emergency_footer", footer, problems)


def main() -> int:
    problems: list[str] = []
    for template_id, item in templates().items():
        found = scan(item["text"])
        if found:
            problems.append(f"{template_id}: {', '.join(found)}")
    for template_id, row in _FIXTURES.items():
        try:
            render(template_id, row)
        except SafetyError as exc:
            problems.append(f"render {template_id}: {', '.join(exc.rules)}")
        except ValueError as exc:
            problems.append(f"render {template_id}: {exc}")
    saved = os.environ.get("D1_COUNTRY")
    try:
        for code in countries():
            _check_country(code, problems)
    finally:
        if saved is None:
            os.environ.pop("D1_COUNTRY", None)
        else:
            os.environ["D1_COUNTRY"] = saved
    for name, score in template_grades().items():
        if name in {"stop_screen", "emergency_footer"}:
            continue
        if score > CEILING:
            problems.append(f"{name} grade {score:.2f} is above {CEILING}")
    if problems:
        print("\n".join(problems))
        return 1
    print("safety-scan: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
