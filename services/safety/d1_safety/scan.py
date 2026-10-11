"""Never-say scan over a template or a rendered sentence.

`quotes` are half-open spans `(start, end, speaker)`. `pathogenic` and `benign`
are allowed only inside a span whose speaker is `lab` or `public_file`.
Every other rule still applies inside those spans.
"""

from __future__ import annotations

import re

_QUOTE_OK = frozenset({"lab", "public_file"})

_DIAGNOSIS = re.compile(
    r"\bdiagnos(?:is|es|ed)\b|\byou have\b|\byou(?:'re| are) diagnosed\b",
    re.IGNORECASE,
)
_NEGATION = re.compile(r"\b(?:not|no|never|without|cannot)\b|n't\b", re.IGNORECASE)
_PERCENT = re.compile(
    r"\d+(?:\.\d+)?\s*%|\bpercent(?:age)?s?\b|\bprobabilit(?:y|ies)\b|\blikelihoods?\b|\bodds\b",
    re.IGNORECASE,
)
_CALIBRATION = re.compile(r"calibration curve", re.IGNORECASE)
_VERDICT = re.compile(r"\b(?:pathogenic|benign)\b", re.IGNORECASE)
_DOSE_WORD = re.compile(
    r"\bprescri(?:be|bes|bed|bing|ption)s?\b"
    r"|\bdos(?:e|es|age|ing)\b"
    r"|\bmedications?\b"
    r"|\bmedicines?\b"
    r"|\btreatments?\b"
    r"|\b\d+(?:\.\d+)?\s*mg\b",
    re.IGNORECASE,
)
_ADVICE = re.compile(
    r"\bstop taking\b|\btake (?:this |the |your )?(?:medicine|medication|drug|pill)s?\b",
    re.IGNORECASE,
)
_ELIGIBLE = re.compile(r"\beligib(?:le|ility)\b|\byou qualify\b|\bqualifies you\b", re.IGNORECASE)
_ENROLL = re.compile(r"\benroll(?:ed|ment|ing)?\b", re.IGNORECASE)
_TRIAL = re.compile(r"\btrials?\b", re.IGNORECASE)


_INVISIBLE = re.compile("[\u200b\u200c\u200d\ufeff\u2060\u202a-\u202e\u2066-\u2069]")


def clean_text(text: str) -> str:
    """Drop characters that hide a word without showing a gap."""
    return _INVISIBLE.sub("", text)


def _negated(text: str, start: int) -> bool:
    # Count negation words in the same sentence only. "This is not a diagnosis."
    # is one negation. "This is not not a diagnosis" is two, so it is still a claim.
    # The previous sentence's "not" must not leak across the period.
    sentence = max(text.rfind(mark, 0, start) for mark in ".?!")
    window = text[sentence + 1 : start]
    return len(_NEGATION.findall(window)) % 2 == 1


def _strip_invisible(
    text: str, quotes: list[tuple[int, int, str]]
) -> tuple[str, list[tuple[int, int, str]]]:
    if _INVISIBLE.search(text) is None:
        return text, quotes
    old_to_new: dict[int, int] = {}
    kept: list[str] = []
    for index, char in enumerate(text):
        if _INVISIBLE.fullmatch(char):
            continue
        old_to_new[index] = len(kept)
        kept.append(char)

    def map_index(index: int, *, end: bool) -> int:
        if index in old_to_new:
            return old_to_new[index]
        probe = index - 1
        while probe >= 0 and probe not in old_to_new:
            probe -= 1
        if probe < 0:
            return 0
        return old_to_new[probe] + 1 if end else old_to_new[probe]

    remapped: list[tuple[int, int, str]] = []
    for start, end, speaker in quotes:
        new_start = map_index(start, end=False)
        new_end = map_index(end, end=True)
        if new_start < new_end:
            remapped.append((new_start, new_end, speaker))
    return "".join(kept), remapped


def _covered(quotes: list[tuple[int, int, str]]) -> list[tuple[int, int]]:
    spans = sorted((s, e) for s, e, speaker in quotes if speaker in _QUOTE_OK and 0 <= s < e)
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def _in_quote(start: int, end: int, covered: list[tuple[int, int]]) -> bool:
    return any(start >= qstart and end <= qend for qstart, qend in covered)


def scan(text: str, quotes: list[tuple[int, int, str]] | None = None) -> list[str]:
    """Return rule ids. An empty list means the text may be shown."""
    text, quotes = _strip_invisible(text, list(quotes or []))
    covered = _covered(quotes)
    found: list[str] = []

    def add(rule: str) -> None:
        if rule not in found:
            found.append(rule)

    cursor = 0
    for start, end in [*covered, (len(text), len(text))]:
        for match in _DIAGNOSIS.finditer(text[cursor:start]):
            if not _negated(text, cursor + match.start()):
                add("diagnosis_in_product_voice")
                break
        cursor = end

    if _PERCENT.search(text) and not _CALIBRATION.search(text):
        add("percent_or_probability_without_calibration")

    for match in _VERDICT.finditer(text):
        if not _in_quote(match.start(), match.end(), covered):
            add("pathogenic_or_benign_as_own_verdict")
            break

    for match in _DOSE_WORD.finditer(text):
        if not _negated(text, match.start()):
            add("treatment_or_medication_advice")
            break
    if _ADVICE.search(text):
        add("treatment_or_medication_advice")

    if _ELIGIBLE.search(text):
        add("trial_eligibility")
    else:
        for match in _ENROLL.finditer(text):
            window = text[max(0, match.start() - 40) : match.end() + 40]
            if _TRIAL.search(window):
                add("trial_eligibility")
                break

    return found
