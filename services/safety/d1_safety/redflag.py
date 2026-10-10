"""Red-flag stop screen. Phrases and numbers come from one country file."""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from d1_safety.render import render, templates_dir
from d1_safety.scan import scan


def _root() -> Path:
    return templates_dir() / "red_flags"


def countries() -> list[str]:
    return sorted(path.name for path in _root().iterdir() if (path / "source.toml").is_file())


def country() -> str:
    raw = os.environ.get("D1_COUNTRY", "").strip().lower()
    code = raw or (_root() / "default.txt").read_text().strip().lower()
    if not (_root() / code / "source.toml").is_file():
        raise ValueError(f"unknown country {code}")
    return code


def _source(code: str | None = None) -> dict:
    chosen = country() if code is None else code
    path = _root() / chosen / "source.toml"
    if not path.is_file():
        raise ValueError(f"unknown country {chosen}")
    return tomllib.loads(path.read_text())


def load_phrases(path: Path | None = None) -> list[str]:
    source = path if path is not None else _root() / country() / "phrases.txt"
    phrases = [line.strip() for line in source.read_text().splitlines() if line.strip()]
    if not phrases:
        raise ValueError("red-flag phrase list is empty")
    return phrases


def cited_sentences() -> tuple[str, ...]:
    found: list[str] = []
    for code in countries():
        data = _source(code)
        for key in ("call_sentence", "number_sentence"):
            sentence = str(data.get(key) or "")
            if sentence and sentence not in found:
                found.append(sentence)
    return tuple(found)


def stop_template() -> str:
    return str(_source()["stop"])


def match_red_flags(text: str, phrases: list[str] | None = None) -> list[str]:
    found = []
    for phrase in phrases if phrases is not None else load_phrases():
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(phrase)
    return found


def footer_text() -> str:
    shell, _quotes = render("emergency_footer", {})
    data = _source()
    lines = [str(data[key]) for key in ("call_sentence", "number_sentence") if data.get(key)]
    text = shell
    if lines:
        head, sep, tail = shell.partition(". ")
        inserted = " ".join(lines)
        text = f"{shell} {inserted}" if not sep else f"{head}{sep}{inserted} {tail}"
    rules = scan(text)
    if rules:
        raise RuntimeError("footer failed the never-say scan: " + ",".join(rules))
    return text


def stop_screen(user_text: str) -> dict[str, str | list[str]] | None:
    hits = match_red_flags(user_text)
    if not hits:
        return None
    body = stop_template().replace("{phrase}", "; ".join(hits))
    rules = scan(body)
    if rules:
        raise RuntimeError("stop screen failed the never-say scan: " + ",".join(rules))
    return {"title": "Stop", "matched": hits, "body": body, "footer": footer_text()}
