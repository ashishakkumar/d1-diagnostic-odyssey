"""Gemini stays primary. OpenRouter ':free' models run only after quota exhaustion.

Only text that carries the synthetic marker may be sent to either provider.
A missing fallback key raises RateLimitedNoFallback so the caller can degrade.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx

SYNTHETIC_MARK = "SYNTHETIC-ONLY"
COOLDOWN_SECONDS = 60.0
_MAX_TRIES = 3

Provider = Literal["gemini", "openrouter", "gazetteer"]


class RateLimitedNoFallback(RuntimeError):
    """Gemini was rate-limited and no OpenRouter free model could answer."""


class SyntheticRejected(RuntimeError):
    """The prompt is not marked as synthetic, so no provider is called."""


@dataclass(frozen=True)
class Completion:
    text: str
    provider: Provider
    model: str | None
    cached: bool = False


class ReplayCache:
    """JSON object keyed by SHA-256 of the prompt and schema. A hit is not re-requested."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def get(self, key: str) -> Completion | None:
        data = self._read()
        raw = data.get(key)
        if not isinstance(raw, dict):
            return None
        provider = raw.get("provider")
        if provider not in ("gemini", "openrouter", "gazetteer"):
            return None
        return Completion(
            text=str(raw.get("text") or ""),
            provider=provider,
            model=raw.get("model") if isinstance(raw.get("model"), str) else None,
            cached=True,
        )

    def put(self, key: str, item: Completion) -> None:
        data = self._read()
        data[key] = {
            "text": item.text,
            "provider": item.provider,
            "model": item.model,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, sort_keys=True))

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        loaded = json.loads(self.path.read_text() or "{}")
        if isinstance(loaded, dict):
            return loaded
        return {}


@dataclass
class FallbackState:
    cooldown_until: float = 0.0


def cache_key(prompt: str, schema: str) -> str:
    return hashlib.sha256(f"{schema}\n{prompt}".encode()).hexdigest()


def assert_synthetic(prompt: str) -> None:
    if SYNTHETIC_MARK not in prompt:
        raise SyntheticRejected("only synthetic text may be sent to a hosted model")


def is_rate_limited(exc: BaseException) -> bool:
    text = f"{type(exc).__name__} {exc}".lower().replace("-", "_")
    return "429" in text or "resource_exhausted" in text


def free_model_ids(raw: str) -> list[str]:
    models = [part.strip() for part in raw.split(",") if part.strip()]
    rejected = [model for model in models if not model.endswith(":free")]
    if rejected:
        raise ValueError("only :free models allowed")
    return models


def read_openrouter_key(
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
) -> str | None:
    env = os.environ if environ is None else environ
    value = str(env.get("OPENROUTER_API_KEY") or "").strip()
    if value:
        return value
    base = root if root is not None else Path.cwd()
    for name in ("uploads/openrouter.key", "uploads/openrouter-key.txt"):
        path = base / name
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    return None


def _log(path: Path | None, provider: str, model: str | None, reason: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "provider": provider,
        "model": model,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _retry(
    primary: Callable[[str], str],
    prompt: str,
    *,
    sleep: Callable[[float], None],
) -> str:
    last: BaseException | None = None
    for attempt in range(_MAX_TRIES):
        try:
            return primary(prompt)
        except Exception as exc:
            if not is_rate_limited(exc):
                raise
            last = exc
            if attempt + 1 == _MAX_TRIES:
                break
            sleep((2**attempt) + random.random())
    if last is None:
        raise RateLimitedNoFallback("Gemini was rate-limited")
    raise last


def _openrouter(
    prompt: str,
    models: list[str],
    *,
    key: str,
    base_url: str,
    post: Callable[[str, dict[str, str], dict], Any],
    sleep: Callable[[float], None],
) -> tuple[str, str]:
    if not models:
        raise RateLimitedNoFallback("Gemini exhausted and no OpenRouter free model is configured")
    free_model_ids(",".join(models))
    last = "no response"
    for model in models:
        try:
            response = post(
                f"{base_url.rstrip('/')}/chat/completions",
                {"Authorization": f"Bearer {key}"},
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
            )
        except httpx.HTTPError as exc:
            last = type(exc).__name__
            sleep(1 + random.random())
            continue
        status = int(getattr(response, "status_code", 0))
        if status in (429, 500, 502, 503):
            last = str(status)
            sleep(1 + random.random())
            continue
        if status >= 400:
            raise RuntimeError(f"OpenRouter returned {status}")
        payload = response.json()
        text = str(payload["choices"][0]["message"]["content"])
        return text, model
    raise RateLimitedNoFallback(f"all OpenRouter free models exhausted: {last}")


def complete(
    prompt: str,
    *,
    primary: Callable[[str], str],
    cache: ReplayCache,
    schema: str = "text",
    state: FallbackState | None = None,
    models: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
    now: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
    post: Callable[[str, dict[str, str], dict], Any] | None = None,
    log_path: Path | None = None,
    primary_model: str | None = None,
) -> Completion:
    """Call Gemini first. Fall back only on a rate limit, and only to ':free' models."""
    assert_synthetic(prompt)
    key_id = cache_key(prompt, schema)
    cached = cache.get(key_id)
    if cached is not None:
        return cached
    clock = time.monotonic if now is None else now
    pause = time.sleep if sleep is None else sleep
    held = state if state is not None else FallbackState()
    env = os.environ if environ is None else environ
    chosen = models
    if chosen is None:
        chosen = free_model_ids(str(env.get("OPENROUTER_FREE_MODELS") or ""))
    else:
        free_model_ids(",".join(chosen))

    def finish(text: str, provider: Provider, model: str | None, reason: str) -> Completion:
        item = Completion(text=text, provider=provider, model=model)
        cache.put(key_id, item)
        _log(log_path, provider, model, reason)
        return item

    if clock() < held.cooldown_until:
        return _fallback_completion(
            prompt,
            chosen,
            environ=env,
            root=root,
            post=post,
            sleep=pause,
            finish=finish,
        )
    try:
        text = _retry(primary, prompt, sleep=pause)
    except Exception as exc:
        if not is_rate_limited(exc):
            raise
        held.cooldown_until = clock() + COOLDOWN_SECONDS
        return _fallback_completion(
            prompt,
            chosen,
            environ=env,
            root=root,
            post=post,
            sleep=pause,
            finish=finish,
        )
    return finish(text, "gemini", primary_model, "ok")


def _fallback_completion(
    prompt: str,
    models: list[str],
    *,
    environ: Mapping[str, str],
    root: Path | None,
    post: Callable[[str, dict[str, str], dict], Any] | None,
    sleep: Callable[[float], None],
    finish: Callable[[str, Provider, str | None, str], Completion],
) -> Completion:
    key = read_openrouter_key(environ, root)
    if not key:
        raise RateLimitedNoFallback("Gemini exhausted and OPENROUTER_API_KEY is not set")
    base = str(environ.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1")
    sender = post if post is not None else _http_post
    text, model = _openrouter(prompt, models, key=key, base_url=base, post=sender, sleep=sleep)
    return finish(text, "openrouter", model, "rate_limited")


def _http_post(url: str, headers: dict[str, str], payload: dict) -> httpx.Response:
    return httpx.post(url, headers=headers, json=payload, timeout=120)


def complete_or_degrade(
    prompt: str,
    *,
    primary: Callable[[str], str],
    cache: ReplayCache,
    **kwargs: Any,
) -> Completion:
    """On a missing fallback, return the pinned gazetteer sentence instead of raising."""
    try:
        return complete(prompt, primary=primary, cache=cache, **kwargs)
    except RateLimitedNoFallback:
        return gazetteer("no_fallback", log_path=kwargs.get("log_path"))


def gazetteer(reason: str, *, log_path: Path | None = None) -> Completion:
    """Pinned wording. Logged, and not written into the replay cache."""
    _log(log_path, "gazetteer", None, reason)
    return Completion(
        text="No model is available. The pinned wording stays.",
        provider="gazetteer",
        model=None,
    )
