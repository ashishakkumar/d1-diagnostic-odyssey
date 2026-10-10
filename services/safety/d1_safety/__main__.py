"""Scan every shipped sentence.

Exit 1 when a never-say rule, an empty phrase list, or a grade fails.

Web and scoring code can call `d1_safety.scan`. This module is `make safety-scan`.
"""

from d1_safety.readability import CEILING, template_grades
from d1_safety.redflag import load_phrases, stop_template
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
}


def main() -> int:
    problems: list[str] = []
    for template_id, item in templates().items():
        found = scan(item["text"])
        if found:
            problems.append(f"{template_id}: {', '.join(found)}")
    found = scan(stop_template())
    if found:
        problems.append(f"stop_screen: {', '.join(found)}")
    for template_id, row in _FIXTURES.items():
        try:
            render(template_id, row)
        except SafetyError as exc:
            problems.append(f"render {template_id}: {', '.join(exc.rules)}")
        except ValueError as exc:
            problems.append(f"render {template_id}: {exc}")
    try:
        load_phrases()
    except ValueError as exc:
        problems.append(str(exc))
    for name, score in template_grades().items():
        if score > CEILING:
            problems.append(f"{name} grade {score:.2f} is above {CEILING}")
    if problems:
        print("\n".join(problems))
        return 1
    print("safety-scan: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
