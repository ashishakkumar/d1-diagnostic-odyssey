"""Gemini first. OpenRouter free models only after a 429. No live network."""

import json
from pathlib import Path

import pytest

from d4_llm import (
    Completion,
    RateLimitedNoFallback,
    ReplayCache,
    SyntheticRejected,
    complete,
    complete_or_degrade,
    is_rate_limited,
)
from d4_llm.fallback import DEFAULT_OPENROUTER_FREE_MODELS, configured_free_models

ROOT = Path(__file__).resolve().parents[2]
PROMPT = "SYNTHETIC-ONLY reply with pong"


class Quota(RuntimeError):
    def __str__(self) -> str:
        return "429 RESOURCE_EXHAUSTED quota"


class _Response:
    def __init__(self, status: int, payload: dict | None = None) -> None:
        self.status_code = status
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def _cache(tmp_path: Path) -> ReplayCache:
    return ReplayCache(tmp_path / "replay.json")


def test_gemini_success_does_not_call_openrouter(tmp_path: Path) -> None:
    calls = {"primary": 0, "post": 0}

    def primary(_prompt: str) -> str:
        calls["primary"] += 1
        return "pong"

    def post(*_args: object) -> _Response:
        calls["post"] += 1
        raise AssertionError("openrouter")

    result = complete(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
    )
    assert result == Completion(text="pong", provider="gemini", model=None)
    assert calls == {"primary": 1, "post": 0}


def test_a_429_uses_openrouter_and_records_the_provider(tmp_path: Path) -> None:
    calls = {"primary": 0, "post": 0}

    def primary(_prompt: str) -> str:
        calls["primary"] += 1
        raise Quota()

    def post(_url: str, _headers: dict, payload: dict) -> _Response:
        calls["post"] += 1
        assert str(payload["model"]).endswith(":free")
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={"OPENROUTER_API_KEY": "test-key"},
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
    )
    assert result.provider == "openrouter"
    assert result.model == "example/test:free"
    assert result.text == "pong"
    assert calls["primary"] == 3
    assert calls["post"] == 1


def test_a_non_rate_limit_error_is_raised_and_openrouter_is_not_called(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        raise RuntimeError("schema mismatch")

    def post(*_args: object) -> _Response:
        raise AssertionError("openrouter")

    with pytest.raises(RuntimeError, match="schema mismatch"):
        complete(
            PROMPT,
            primary=primary,
            cache=_cache(tmp_path),
            models=["example/test:free"],
            environ={"OPENROUTER_API_KEY": "test-key"},
            root=tmp_path,
            sleep=lambda _seconds: None,
            post=post,
        )


def test_a_429_without_a_key_degrades_to_the_gazetteer(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        raise Quota()

    def post(*_args: object) -> _Response:
        raise AssertionError("openrouter")

    with pytest.raises(RateLimitedNoFallback):
        complete(
            PROMPT,
            primary=primary,
            cache=_cache(tmp_path),
            models=["example/test:free"],
            environ={},
            root=tmp_path,
            sleep=lambda _seconds: None,
            post=post,
        )
    degraded = complete_or_degrade(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
    )
    assert degraded.provider == "gazetteer"
    assert "pinned wording" in degraded.text


def test_the_default_free_model_list_is_non_empty() -> None:
    assert DEFAULT_OPENROUTER_FREE_MODELS
    assert all(model.endswith(":free") for model in DEFAULT_OPENROUTER_FREE_MODELS)
    assert configured_free_models({}) == list(DEFAULT_OPENROUTER_FREE_MODELS)
    assert configured_free_models({"OPENROUTER_FREE_MODELS": ""}) == list(
        DEFAULT_OPENROUTER_FREE_MODELS
    )
    assert configured_free_models({"OPENROUTER_FREE_MODELS": "   "}) == list(
        DEFAULT_OPENROUTER_FREE_MODELS
    )
    with pytest.raises(ValueError, match=":free"):
        configured_free_models({"OPENROUTER_FREE_MODELS": "example/paid"})


def test_an_unset_free_model_list_calls_the_default(tmp_path: Path) -> None:
    seen: list[str] = []

    def primary(_prompt: str) -> str:
        raise Quota()

    def post(_url: str, _headers: dict, payload: dict) -> _Response:
        seen.append(str(payload["model"]))
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        environ={"OPENROUTER_API_KEY": "test-key"},
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
    )
    assert result.provider == "openrouter"
    assert result.model == DEFAULT_OPENROUTER_FREE_MODELS[0]
    assert seen == [DEFAULT_OPENROUTER_FREE_MODELS[0]]


def test_a_set_free_model_list_replaces_the_default(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        raise Quota()

    def post(_url: str, _headers: dict, payload: dict) -> _Response:
        assert payload["model"] == "example/other:free"
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        environ={
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_FREE_MODELS": "example/other:free",
        },
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
    )
    assert result.provider == "openrouter"
    assert result.model == "example/other:free"


def test_a_model_id_without_the_free_suffix_is_rejected(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        raise AssertionError("primary")

    def post(*_args: object) -> _Response:
        raise AssertionError("openrouter")

    with pytest.raises(ValueError, match=":free"):
        complete(
            PROMPT,
            primary=primary,
            cache=_cache(tmp_path),
            models=["example/paid"],
            environ={"OPENROUTER_API_KEY": "test-key"},
            root=tmp_path,
            sleep=lambda _seconds: None,
            post=post,
        )


def test_non_synthetic_text_is_blocked_before_either_provider(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        raise AssertionError("primary")

    def post(*_args: object) -> _Response:
        raise AssertionError("openrouter")

    with pytest.raises(SyntheticRejected):
        complete(
            "a real chart",
            primary=primary,
            cache=_cache(tmp_path),
            models=["example/test:free"],
            environ={"OPENROUTER_API_KEY": "test-key"},
            root=tmp_path,
            sleep=lambda _seconds: None,
            post=post,
        )


def test_a_cached_answer_is_not_requested_again(tmp_path: Path) -> None:
    calls = {"primary": 0}

    def primary(_prompt: str) -> str:
        calls["primary"] += 1
        return "pong"

    cache = _cache(tmp_path)
    first = complete(
        PROMPT,
        primary=primary,
        cache=cache,
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
    )
    second = complete(
        PROMPT,
        primary=primary,
        cache=cache,
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
    )
    assert first.text == second.text == "pong"
    assert second.cached is True
    assert calls["primary"] == 1


def test_quota_without_a_429_is_not_a_rate_limit() -> None:
    assert is_rate_limited(RuntimeError("quota")) is False
    assert is_rate_limited(RuntimeError("rate limit")) is False
    assert is_rate_limited(RuntimeError("429 RESOURCE_EXHAUSTED")) is True
    assert is_rate_limited(RuntimeError("RESOURCE_EXHAUSTED")) is True


def test_a_missing_fallback_logs_the_gazetteer_and_does_not_cache_it(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "llm.jsonl"

    def primary(_prompt: str) -> str:
        raise Quota()

    def post(*_args: object) -> _Response:
        raise AssertionError("openrouter")

    cache = _cache(tmp_path)
    degraded = complete_or_degrade(
        PROMPT,
        primary=primary,
        cache=cache,
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
        post=post,
        log_path=log_path,
    )
    assert degraded.provider == "gazetteer"
    row = json.loads(log_path.read_text().splitlines()[-1])
    assert row["provider"] == "gazetteer"
    assert row["model"] is None
    with pytest.raises(RateLimitedNoFallback):
        complete(
            PROMPT,
            primary=primary,
            cache=cache,
            models=["example/test:free"],
            environ={},
            root=tmp_path,
            sleep=lambda _seconds: None,
            post=post,
        )


def test_a_gemini_success_records_the_primary_model_id(tmp_path: Path) -> None:
    def primary(_prompt: str) -> str:
        return "pong"

    result = complete(
        PROMPT,
        primary=primary,
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={},
        root=tmp_path,
        sleep=lambda _seconds: None,
        primary_model="gemini-3.5-flash-lite",
    )
    assert result.provider == "gemini"
    assert result.model == "gemini-3.5-flash-lite"


def test_the_notebook_routes_do_not_call_a_model() -> None:
    text = (ROOT / "services" / "api" / "app" / "routes" / "notebook.py").read_text().casefold()
    assert "d4_llm" not in text
    assert "openrouter" not in text
    assert "gemini" not in text
