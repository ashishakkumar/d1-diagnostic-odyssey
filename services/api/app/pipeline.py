"""One-screen reading of a synthetic note. No language model.

Phrases come from a fixed lexicon. Ranks are Resnik best-match average on the
ten-row synthetic table, the same symmetric formula as the measured public-case
ranker. This is not the 249-disease held-out run. phenotype.hpoa is not read.
"""

from __future__ import annotations

import math
import re
from uuid import uuid4

from d1_safety.render import render
from d1_safety.scan import scan

from app.demo_cases import case_by_slug, demo_frequency_rows
from app.routes.ports import lay_wording, red_flag

METHOD = (
    "Lexicon match, then Resnik best-match average on the synthetic table. "
    "No language model ran. The free-tier quota is closed until 2026-10-12 00:00 UTC."
)
REVIEWER = "synthetic-reader"

# Longer phrases are listed first so "seizures" wins over "seizure".
_LEXICON: tuple[tuple[str, str, str], ...] = (
    ("arachnodactyly", "HP:0001166", "Arachnodactyly"),
    ("long fingers", "HP:0001166", "Arachnodactyly"),
    ("malar flattening", "HP:0000272", "Malar flattening"),
    ("flat cheeks", "HP:0000272", "Malar flattening"),
    ("low muscle tone", "HP:0001252", "Hypotonia"),
    ("hypotonia", "HP:0001252", "Hypotonia"),
    ("seizures", "HP:0001250", "Seizure"),
    ("seizure", "HP:0001250", "Seizure"),
    ("unsteady", "HP:0001251", "Ataxia"),
    ("ataxia", "HP:0001251", "Ataxia"),
)

_NOTES = {
    "separated": (
        "Synthetic note, not a real patient. The hands show long fingers. "
        "The face shows flat cheeks."
    ),
    "abstain": "Synthetic note, not a real patient. There was one seizure.",
    "stable": (
        "Synthetic note, not a real patient. Walking is unsteady. Resting tone is low muscle tone."
    ),
    "variant": (
        "Synthetic note, not a real patient. The hands show long fingers. "
        "The face shows flat cheeks. The lab sheet names FBN1 and NM_000138.5:c.1A>G."
    ),
    "limits": (
        "Synthetic note, not a real patient. Walking is unsteady. Resting tone is low muscle tone."
    ),
}


def synthetic_profiles() -> dict[str, set[str]]:
    """Non-excluded HPO ids on each synthetic Orphanet row."""
    profiles: dict[str, set[str]] = {}
    for row in demo_frequency_rows():
        terms = profiles.setdefault(str(row["orphanet_id"]), set())
        if str(row["bin"]) != "excluded":
            terms.add(str(row["hpo_id"]))
    return profiles


def _information(profiles: dict[str, set[str]]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for terms in profiles.values():
        for term in terms:
            counts[term] = counts.get(term, 0) + 1
    n_diseases = len(profiles)
    found: dict[str, float] = {}
    for term, count in counts.items():
        if n_diseases and 0 < count < n_diseases:
            found[term] = -math.log(count / n_diseases)
    return found


def resnik_scores(
    query: list[str],
    profiles: dict[str, set[str]],
) -> list[tuple[str, float]]:
    """Symmetric Resnik best-match average. Ancestors are the term itself on this table."""
    information = _information(profiles)
    query_set = set(query)
    found: list[tuple[str, float]] = []
    for disease, terms in profiles.items():
        if not query:
            found.append((disease, 0.0))
            continue
        left = sum(information.get(term, 0.0) if term in terms else 0.0 for term in query)
        left /= len(query)
        if terms:
            right = sum(information.get(term, 0.0) if term in query_set else 0.0 for term in terms)
            right /= len(terms)
        else:
            right = 0.0
        found.append((disease, 0.5 * (left + right)))
    found.sort(key=lambda item: (-item[1], item[0]))
    return found


def extract_terms(note: str) -> list[dict[str, object]]:
    """Pinned phrases only. Overlaps keep the longer phrase."""
    occupied = [False] * len(note)
    found: list[dict[str, object]] = []
    seen: set[str] = set()
    ordered = sorted(_LEXICON, key=lambda item: len(item[0]), reverse=True)
    for phrase, hpo_id, label in ordered:
        pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(note):
            start, end = match.span()
            if any(occupied[start:end]):
                continue
            if hpo_id in seen:
                for index in range(start, end):
                    occupied[index] = True
                continue
            for index in range(start, end):
                occupied[index] = True
            seen.add(hpo_id)
            plain, explanation = lay_wording(hpo_id, label)
            found.append(
                {
                    "hpo_id": hpo_id,
                    "label": label,
                    "plain_words": plain,
                    "explanation": explanation,
                    "quote": note[start:end],
                    "start": start,
                    "end": end,
                }
            )
    found.sort(key=lambda item: int(item["start"]))
    return found


def _reason(listed: list[str], score: float, best: float, tied: bool) -> str:
    if score <= 0 or not listed:
        return "This row does not list a rare term from the note."
    words = ", ".join(listed)
    if score == best and tied:
        return f"Lists {words}. The best score is shared, so no first row is separated."
    if score == best:
        return f"Lists {words}. This is the highest score on the synthetic table."
    return f"Lists {words}."


def _checked(text: str) -> str:
    rules = scan(text)
    if rules:
        raise RuntimeError("pipeline text failed the never-say scan")
    return text


def questions_for(terms: list[dict[str, object]]) -> list[str]:
    questions: list[str] = []
    for term in terms:
        sentence, _quotes = render(
            "questions_for_doctor",
            {
                "label": str(term["plain_words"]),
                "hpo_id": str(term["hpo_id"]),
                "presence": "present",
            },
        )
        questions.append(sentence)
    return questions


def build_pipeline(slug: str | None, note: str | None) -> dict[str, object]:
    """Read a synthetic note. This does not write the database."""
    if slug and note:
        raise ValueError("send a case or a note, not both")
    if not slug and not note:
        raise ValueError("a case or a note is required")
    chosen = case_by_slug(slug) if slug else None
    if slug and chosen is None:
        raise KeyError(slug)
    text = _NOTES[str(slug)] if slug else str(note or "").strip()
    if not text:
        raise ValueError("the note is empty")
    screen = red_flag(text)
    if screen is not None:
        return {"stop": screen}
    terms = extract_terms(text)
    profiles = synthetic_profiles()
    query = [str(term["hpo_id"]) for term in terms]
    labels = {str(term["hpo_id"]): str(term["plain_words"]) for term in terms}
    scored = resnik_scores(query, profiles)
    best = scored[0][1] if scored else 0.0
    tied = sum(1 for _disease, score in scored if score == best and best > 0) > 1
    abstained = best <= 0 or tied
    if best <= 0:
        abstain_text = (
            "Not enough signal to separate a first row. "
            "This does not mean you are well. This is not a diagnosis."
        )
    elif tied:
        abstain_text = (
            "Not enough signal to separate a first row. "
            "More than one synthetic row shares the best score. "
            "This does not mean you are well. This is not a diagnosis."
        )
    else:
        abstain_text = None
    ranks = []
    for disease, score in scored:
        listed = [labels[term] for term in query if term in profiles[disease]]
        bar = 0.0 if best <= 0 else score / best
        ranks.append(
            {
                "orphanet_id": disease,
                "score": score,
                "bar": bar,
                "reason": _checked(_reason(listed, score, best, tied)),
            }
        )
    cells = [
        {
            "orphanet_id": disease,
            "hpo_id": hpo_id,
            "listed": hpo_id in profiles[disease],
        }
        for disease, _score in scored
        for hpo_id in query
    ]
    limit_line = None
    if slug == "limits":
        limit_line, _quotes = render("no_dose", {})
    gene_line = None
    if "FBN1" in text:
        gene_line = _checked(
            "A gene symbol is written in the note. Resnik did not use it. This is not a diagnosis."
        )
    stages = [
        {
            "id": "read",
            "label": "Read",
            "actor": "software",
            "did": _checked(
                "The software scanned the note for pinned phrases. No language model ran."
            ),
        },
        {
            "id": "map",
            "label": "Map",
            "actor": "software",
            "did": _checked(
                "Each highlighted phrase was looked up in a fixed lexicon "
                "and paired with an HPO id."
            ),
        },
        {
            "id": "match",
            "label": "Match",
            "actor": "software",
            "did": _checked(
                "Each HPO id was checked against the synthetic reference table. "
                "A cell lights when that row lists the term outside the excluded bin."
            ),
        },
        {
            "id": "rank",
            "label": "Rank",
            "actor": "software",
            "did": _checked(
                "Rows were ordered with Resnik best-match average on this synthetic table. "
                "It is not the 249-disease held-out run. "
                "This is not a diagnosis."
            ),
        },
    ]
    case_id = str(chosen["case_id"]) if chosen else str(uuid4())
    return {
        "stop": None,
        "note": text,
        "case_id": case_id,
        "slug": slug,
        "method": _checked(METHOD),
        "stages": stages,
        "terms": terms,
        "cells": cells,
        "ranks": ranks,
        "abstained": abstained,
        "abstain_text": _checked(abstain_text) if abstain_text else None,
        "questions": questions_for(terms),
        "limit_line": limit_line,
        "gene_line": gene_line,
    }
