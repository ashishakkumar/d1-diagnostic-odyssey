"""Synthetic open-band notes. The gazetteer leaves these nine unscored until a span exists.

The notes are fictional. A hosted model sees only the SYNTHETIC-ONLY prompt.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from d4_llm.fallback import ReplayCache, cache_key, complete, read_openrouter_key
from d4_llm.gemini import choose_model, load_models, make_gemini_primary
from scoring import catalogue_score

SCHEMA = "segment-v1"
CACHE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "open_band_replay.json"
ALLOW: tuple[tuple[str, str], ...] = (
    ("HP:0001166", "Arachnodactyly"),
    ("HP:0000272", "Malar flattening"),
    ("HP:0001250", "Seizure"),
    ("HP:0001251", "Ataxia"),
    ("HP:0001252", "Hypotonia"),
)
_ALLOW_IDS = {hpo_id for hpo_id, _label in ALLOW}
GAZETTEER: dict[str, tuple[str, str]] = {
    "seizure": ("HP:0001250", "Seizure"),
    "ataxia": ("HP:0001251", "Ataxia"),
    "hypotonia": ("HP:0001252", "Hypotonia"),
    "arachnodactyly": ("HP:0001166", "Arachnodactyly"),
    "malar flattening": ("HP:0000272", "Malar flattening"),
}
OPEN_BAND: tuple[dict[str, str], ...] = (
    {"id": "synthetic-open-01", "note": "The fingers are long for the hand."},
    {"id": "synthetic-open-02", "note": "The cheeks look flat."},
    {"id": "synthetic-open-03", "note": "The fingers are long for the hand. The cheeks look flat."},
    {"id": "synthetic-open-04", "note": "The body shakes in a fit."},
    {"id": "synthetic-open-05", "note": "Walking is unsteady."},
    {"id": "synthetic-open-06", "note": "The muscles feel floppy."},
    {"id": "synthetic-open-07", "note": "Walking is unsteady. The muscles feel floppy."},
    {"id": "synthetic-open-08", "note": "Long fingers and a flat cheek are both written here."},
    {"id": "synthetic-open-09", "note": "A fit of shaking happened once."},
)


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    hpo_id: str
    label: str


def gazetteer_spans(note: str) -> list[Span]:
    folded = note.casefold()
    found: list[Span] = []
    for phrase, (hpo_id, label) in GAZETTEER.items():
        start = folded.find(phrase)
        if start < 0:
            continue
        found.append(Span(start, start + len(phrase), hpo_id, label))
    return found


def prompt_for(note: str) -> str:
    lines = "\n".join(f"- {hpo_id} {label}" for hpo_id, label in ALLOW)
    return (
        "SYNTHETIC-ONLY\n"
        "This note is fictional. Reply with JSON only.\n"
        "Allow-list:\n"
        f"{lines}\n"
        "Note:\n"
        f"{note}\n"
        'Return {"spans":[{"start":0,"end":0,"hpo_id":"HP:0000000","label":"Name"}]}.\n'
        "Offsets are into the note above. hpo_id must be on the allow-list. "
        'If nothing fits, return {"spans":[]}.'
    )


def parse_spans(note: str, raw: str) -> list[Span]:
    payload = _json_object(raw)
    rows = payload.get("spans") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    spans: list[Span] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            start = int(row.get("start"))
            end = int(row.get("end"))
        except (TypeError, ValueError):
            continue
        hpo_id = str(row.get("hpo_id") or "")
        if hpo_id not in _ALLOW_IDS or start < 0 or start >= len(note):
            continue
        end = min(end, len(note))
        if end <= start or not note[start:end].strip():
            continue
        spans.append(Span(start, end, hpo_id, dict(ALLOW)[hpo_id]))
    return spans


def segment_open_band(
    *,
    primary: Callable[[str], str],
    cache: ReplayCache,
    sleep: Callable[[float], None] | None = None,
    environ: Mapping[str, str] | None = None,
    post: Callable[[str, dict[str, str], dict], Any] | None = None,
    models: list[str] | None = None,
) -> dict[str, list[Span]]:
    """Segment the nine open-band notes. A cache hit does not call the provider."""
    found: dict[str, list[Span]] = {}
    for packet in OPEN_BAND:
        result = complete(
            prompt_for(packet["note"]),
            primary=primary,
            cache=cache,
            schema=SCHEMA,
            models=models if models is not None else ["unused:free"],
            environ=environ if environ is not None else {},
            sleep=sleep,
            post=post,
            root=CACHE_PATH.parent,
        )
        found[packet["id"]] = parse_spans(packet["note"], result.text)
    return found


def rerun(spans_by_id: Mapping[str, Sequence[Span]], rows: Sequence[Mapping]) -> list[dict]:
    """Score a packet only after a span exists. An empty span list stays unscored."""
    out: list[dict] = []
    for packet in OPEN_BAND:
        spans = list(spans_by_id.get(packet["id"]) or [])
        if not spans:
            out.append({"id": packet["id"], "scored": False, "leading": None, "confident": False})
            continue
        report = catalogue_score([(span.hpo_id, "present") for span in spans], rows)
        out.append(
            {
                "id": packet["id"],
                "scored": True,
                "leading": report.leading_orphanet_id,
                "confident": report.confident,
                "abstain_reason": report.abstain_reason,
            }
        )
    return out


def read_gemini_key(
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
) -> str | None:
    env = os.environ if environ is None else environ
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = str(env.get(name) or "").strip()
        if value:
            return value
    base = root if root is not None else Path.cwd()
    for name in ("uploads/gemini.key", "uploads/gemini-key.txt"):
        path = base / name
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    return None


def record_cache(path: Path = CACHE_PATH, *, pause: float = 2.0) -> dict[str, list[Span]]:
    """One live pass. Cached notes are not sent again. Gemini stays primary."""
    key = read_gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    model = choose_model(load_models(key))
    cache = ReplayCache(path)
    primary = make_gemini_primary(key=key, model=model)
    fallback = _free_models()

    def sleep(seconds: float) -> None:
        time.sleep(seconds)

    found: dict[str, list[Span]] = {}
    for packet in OPEN_BAND:
        prompt = prompt_for(packet["note"])
        if cache.get(cache_key(prompt, SCHEMA)) is None:
            time.sleep(pause)
        result = complete(
            prompt,
            primary=primary,
            cache=cache,
            schema=SCHEMA,
            models=fallback,
            sleep=sleep,
            log_path=None,
        )
        found[packet["id"]] = parse_spans(packet["note"], result.text)
    stamp = path.with_name("open_band_model.json")
    stamp.write_text(
        json.dumps({"provider": "gemini", "model": model, "packets": len(OPEN_BAND)}) + "\n"
    )
    return found


def _free_models() -> list[str]:
    raw = os.environ.get("OPENROUTER_FREE_MODELS", "")
    models = [part.strip() for part in raw.split(",") if part.strip()]
    if models:
        return models
    key = read_openrouter_key()
    if not key:
        return ["unused:free"]
    found = _discover_free(key)
    return found or ["unused:free"]


def _discover_free(key: str) -> list[str]:
    base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    try:
        response = httpx.get(
            f"{base}/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
    except httpx.HTTPError:
        return []
    if response.status_code >= 400:
        return []
    chosen: list[str] = []
    for row in response.json().get("data") or []:
        model_id = str(row.get("id") or "")
        pricing = row.get("pricing") or {}
        if not model_id.endswith(":free"):
            continue
        if str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0":
            chosen.append(model_id)
        if len(chosen) == 3:
            break
    return chosen


def _json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.casefold().startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        loaded = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}
