"""Red-flag stop screen. Phrases come from the cited file, not from a model."""

from __future__ import annotations

import re
from pathlib import Path

from d1_safety.render import render, templates_dir
from d1_safety.scan import scan

_STOP = (
    "Stop. Your words match an example on the London Ambulance Service page: {phrase}. "
    "You should only call 999 if it's a life-threatening emergency. "
    "You can call an ambulance by using 999 or 112."
)


def stop_template() -> str:
    return _STOP


def load_phrases(path: Path | None = None) -> list[str]:
    source = path if path is not None else templates_dir() / "red_flags.txt"
    phrases = [line.strip() for line in source.read_text().splitlines() if line.strip()]
    if not phrases:
        raise ValueError("red-flag phrase list is empty")
    return phrases


def match_red_flags(text: str, phrases: list[str] | None = None) -> list[str]:
    found = []
    for phrase in phrases if phrases is not None else load_phrases():
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(phrase)
    return found


def footer_text() -> str:
    text, _ = render("emergency_footer", {})
    return text


def stop_screen(user_text: str) -> dict[str, str | list[str]] | None:
    hits = match_red_flags(user_text)
    if not hits:
        return None
    body = _STOP.replace("{phrase}", "; ".join(hits))
    rules = scan(body)
    if rules:
        raise RuntimeError("stop screen failed the never-say scan: " + ",".join(rules))
    return {"title": "Stop", "matched": hits, "body": body, "footer": footer_text()}
