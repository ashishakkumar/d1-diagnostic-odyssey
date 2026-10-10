"""Flesch-Kincaid grade for the fixed sentences.

SOURCE: Centers for Disease Control and Prevention, Consent for CDC Research:
A Reference for Developing Consent Forms and Oral Scripts (November 1998),
https://stacks.cdc.gov/view/cdc/12420 , opened 10 October 2026. That guide names
the Flesch-Kincaid test and says reading skills tend to be at or below the 8th
grade. Cited emergency sentences are copied from the London Ambulance Service
page and are removed before scoring so they are not rewritten to chase a grade.
"""

from __future__ import annotations

import re

import textstat

from d1_safety.redflag import stop_template
from d1_safety.render import templates

CEILING = 8
SOURCE = (
    "Flesch-Kincaid grade, CDC Consent for CDC Research (November 1998), "
    "https://stacks.cdc.gov/view/cdc/12420 , at or below the 8th grade. "
    "Opened 10 October 2026."
)
_CITED = (
    "You should only call 999 if it's a life-threatening emergency.",
    "You can call an ambulance by using 999 or 112.",
)


def grade(text: str) -> float:
    return float(textstat.flesch_kincaid_grade(text))


def prose_for_grade(text: str) -> str:
    cleaned = text
    for sentence in _CITED:
        cleaned = cleaned.replace(sentence, " ")
    cleaned = re.sub(r"\{[A-Za-z0-9_]+\}", "cat", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def template_grades() -> dict[str, float]:
    texts = {key: item["text"] for key, item in templates().items()}
    texts["stop_screen"] = stop_template()
    return {key: grade(prose_for_grade(value)) for key, value in texts.items()}
