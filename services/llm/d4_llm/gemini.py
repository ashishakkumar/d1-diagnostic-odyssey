"""Gemini primary client. The model id is chosen from a models list the caller fetched."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import httpx

from d4_llm.fallback import assert_synthetic

MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_SKIP = (
    "tts",
    "image",
    "preview",
    "robotics",
    "lyria",
    "computer-use",
    "deep-research",
    "antigravity",
    "omni",
    "transcribe",
    "customtools",
    "nano-banana",
    "gemma",
)


def choose_model(models: list[dict]) -> str:
    """Pick a text generateContent id from `models`. Flash-lite, then other flash, then the rest."""
    ids: list[str] = []
    for row in models:
        methods = row.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        model_id = str(row.get("name") or "").split("/")[-1].strip()
        if not model_id or any(token in model_id.casefold() for token in _SKIP):
            continue
        ids.append(model_id)
    if not ids:
        raise RuntimeError("models list has no text generateContent model")

    def rank(model_id: str) -> tuple:
        folded = model_id.casefold()
        major, minor = _version(model_id)
        return (
            0 if "flash" in folded else 1,
            0 if "lite" in folded else 1,
            1 if "latest" in folded else 0,
            -major,
            -minor,
            model_id,
        )

    return sorted(ids, key=rank)[0]


def _version(model_id: str) -> tuple[int, int]:
    match = re.search(r"(\d+)(?:\.(\d+))?", model_id)
    if match is None:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2) or 0))


def load_models(
    key: str,
    get: Callable[..., Any] | None = None,
) -> list[dict]:
    sender = get if get is not None else _http_get
    response = sender(MODELS_URL, {"x-goog-api-key": key})
    status = int(getattr(response, "status_code", 0))
    if status == 429:
        raise RuntimeError("429 RESOURCE_EXHAUSTED")
    if status >= 400:
        raise RuntimeError(f"Gemini models list returned {status}")
    payload = response.json()
    rows = payload.get("models") or []
    if not isinstance(rows, list):
        raise RuntimeError("Gemini models list has no models")
    return [row for row in rows if isinstance(row, dict)]


def gemini_text(
    prompt: str,
    *,
    key: str,
    model: str,
    post: Callable[[str, dict[str, str], dict], Any],
) -> str:
    assert_synthetic(prompt)
    if not model or "/" in model or ":" in model:
        raise ValueError("model id must be a single path segment from the models list")
    url = f"{MODELS_URL}/{model}:generateContent"
    response = post(
        url,
        {"x-goog-api-key": key},
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
    )
    status = int(getattr(response, "status_code", 0))
    if status == 429:
        raise RuntimeError(f"429 {getattr(response, 'text', '')}")
    if status >= 400:
        raise RuntimeError(f"Gemini returned {status}")
    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(str(part.get("text") or "") for part in parts)


def make_gemini_primary(
    *,
    key: str,
    model: str,
    post: Callable[[str, dict[str, str], dict], Any] | None = None,
) -> Callable[[str], str]:
    sender = post if post is not None else _http_post

    def primary(prompt: str) -> str:
        return gemini_text(prompt, key=key, model=model, post=sender)

    return primary


def _http_get(url: str, headers: dict[str, str]) -> httpx.Response:
    return httpx.get(url, headers=headers, timeout=60)


def _http_post(url: str, headers: dict[str, str], payload: dict) -> httpx.Response:
    return httpx.post(url, headers=headers, json=payload, timeout=120)
