"""Fill a fixed template from one structured row. No model text is added."""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from d1_safety.scan import clean_text, scan

_HPO = re.compile(r"^HP:[0-9]{7}$")
_QUOTE_SLOT = {
    "lab_words": "lab",
    "previous_text": "public_file",
    "current_text": "public_file",
}
_PRESENCE = {"questions_for_doctor": None, "reason_marked_excluded": "excluded"}


class SafetyError(Exception):
    """Rendered text failed the never-say scan, so it is not returned."""

    def __init__(self, rules: list[str]) -> None:
        self.rules = rules
        super().__init__(",".join(rules))


def templates_dir() -> Path:
    override = os.environ.get("D1_TEMPLATES")
    if override:
        path = Path(override)
        if (path / "sentences.toml").is_file():
            return path
        raise FileNotFoundError("templates/sentences.toml")
    here = Path(__file__).resolve()
    candidates = [Path.cwd(), *here.parents]
    for parent in candidates:
        candidate = parent / "templates" / "sentences.toml"
        if candidate.is_file():
            return candidate.parent
    raise FileNotFoundError("templates/sentences.toml")


def _load() -> dict:
    path = templates_dir() / "sentences.toml"
    raw = tomllib.loads(path.read_text())
    loaded: dict = {}
    for key, value in raw.items():
        if not isinstance(value, dict) or "text" not in value:
            continue
        quotes = value.get("quotes", {})
        for slot, speaker in quotes.items():
            if _QUOTE_SLOT.get(slot) != speaker:
                raise ValueError(f"quote slot {slot} cannot be marked {speaker}")
        loaded[key] = {"text": value["text"].strip(), "quotes": dict(quotes)}
    return loaded


def templates() -> dict:
    return _load()


def template_text(template_id: str) -> str:
    book = _load()
    if template_id not in book:
        raise ValueError(f"unknown template {template_id}")
    return book[template_id]["text"]


def _slots(text: str) -> list[str]:
    found: list[str] = []
    cursor = 0
    while True:
        start = text.find("{", cursor)
        if start < 0:
            return found
        end = text.find("}", start)
        if end < 0:
            raise ValueError("unclosed slot")
        found.append(text[start + 1 : end])
        cursor = end + 1


def _check_row(template_id: str, slots: list[str], row: dict) -> None:
    allowed = set(slots)
    extra = sorted(set(row) - allowed)
    missing = sorted(allowed - set(row))
    if extra:
        raise ValueError(f"unknown field {extra[0]}")
    if missing:
        raise ValueError(f"missing slot {missing[0]}")
    if "presence" in row and row["presence"] not in ("present", "excluded"):
        raise ValueError("presence must be present or excluded")
    required = _PRESENCE.get(template_id)
    if required is not None and row.get("presence") != required:
        raise ValueError(f"presence must be {required}")
    for key, value in row.items():
        if key == "confirmed_count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("confirmed_count must be an integer")
            continue
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{key} must be text")
        if key == "hpo_id" and not _HPO.fullmatch(value):
            raise ValueError("hpo_id is not an HPO id")


def _fill(text: str, row: dict, quotes: dict[str, str]) -> tuple[str, list[tuple[int, int, str]]]:
    parts: list[str] = []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    while cursor < len(text):
        start = text.find("{", cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        end = text.find("}", start)
        name = text[start + 1 : end]
        value = row[name]
        shown = str(value) if name == "confirmed_count" else value
        parts.append(text[cursor:start])
        offset = sum(len(part) for part in parts)
        parts.append(shown)
        if name in quotes:
            spans.append((offset, offset + len(shown), quotes[name]))
        cursor = end + 1
    return "".join(parts), spans


def render(template_id: str, row: dict) -> tuple[str, list[tuple[int, int, str]]]:
    book = _load()
    if template_id not in book:
        raise ValueError(f"unknown template {template_id}")
    item = book[template_id]
    slots = _slots(item["text"])
    row = {
        key: clean_text(value) if isinstance(value, str) else value for key, value in row.items()
    }
    _check_row(template_id, slots, row)
    text, spans = _fill(item["text"], row, item["quotes"])
    rules = scan(text, spans)
    if rules:
        raise SafetyError(rules)
    return text, spans
