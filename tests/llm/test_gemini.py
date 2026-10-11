"""Gemini is primary. The model id comes from a models list, not from a guessed constant."""

import json
from pathlib import Path

import pytest

from d4_llm.fallback import ReplayCache, SyntheticRejected, is_rate_limited
from d4_llm.gemini import choose_model, complete_with_gemini, gemini_text, load_models


class _Response:
    def __init__(self, status: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


def test_choose_model_returns_an_id_from_the_list_and_skips_speech_models() -> None:
    models = [
        {"name": "models/gemini-pro-latest", "supportedGenerationMethods": ["generateContent"]},
        {
            "name": "models/gemini-2.5-flash-lite",
            "supportedGenerationMethods": ["generateContent"],
        },
        {
            "name": "models/gemini-2.5-flash-preview-tts",
            "supportedGenerationMethods": ["generateContent"],
        },
        {"name": "models/embed-one", "supportedGenerationMethods": ["embedContent"]},
    ]
    chosen = choose_model(models)
    assert chosen == "gemini-2.5-flash-lite"


def test_a_newer_flash_lite_in_the_list_wins() -> None:
    models = [
        {
            "name": "models/gemini-2.5-flash-lite",
            "supportedGenerationMethods": ["generateContent"],
        },
        {
            "name": "models/gemini-3.5-flash-lite",
            "supportedGenerationMethods": ["generateContent"],
        },
    ]
    assert choose_model(models) == "gemini-3.5-flash-lite"


def test_an_empty_models_list_is_an_error() -> None:
    try:
        choose_model([])
    except RuntimeError as exc:
        assert "generateContent" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_gemini_text_posts_the_chosen_model_and_keeps_the_key_out_of_the_body() -> None:
    seen: dict = {}

    def post(url: str, headers: dict, payload: dict) -> _Response:
        seen["url"] = url
        seen["headers"] = headers
        seen["payload"] = payload
        return _Response(200, {"candidates": [{"content": {"parts": [{"text": "pong"}]}}]})

    text = gemini_text(
        "SYNTHETIC-ONLY reply with pong",
        key="secret-key",
        model="gemini-2.5-flash-lite",
        post=post,
    )
    assert text == "pong"
    assert "secret-key" not in seen["url"]
    assert seen["headers"]["x-goog-api-key"] == "secret-key"
    assert "secret-key" not in json.dumps(seen["payload"])
    assert "gemini-2.5-flash-lite:generateContent" in seen["url"]
    assert seen["payload"]["generationConfig"]["temperature"] == 0


def test_a_429_from_gemini_is_a_rate_limit() -> None:
    def post(_url: str, _headers: dict, _payload: dict) -> _Response:
        return _Response(429, text="RESOURCE_EXHAUSTED quota")

    try:
        gemini_text(
            "SYNTHETIC-ONLY",
            key="secret-key",
            model="gemini-2.5-flash-lite",
            post=post,
        )
    except RuntimeError as exc:
        assert is_rate_limited(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_non_synthetic_text_is_not_posted() -> None:
    def post(*_args: object) -> _Response:
        raise AssertionError("posted")

    try:
        gemini_text("a real chart", key="secret-key", model="gemini-2.5-flash-lite", post=post)
    except RuntimeError as exc:
        assert "synthetic" in str(exc).casefold()
    else:
        raise AssertionError("expected RuntimeError")


MODELS = "https://generativelanguage.googleapis.com/v1beta/models"
FLASH = {
    "name": "models/gemini-3.5-flash-lite",
    "supportedGenerationMethods": ["generateContent"],
}


def test_load_models_follows_the_next_page_token() -> None:
    pages = {
        MODELS: {
            "models": [
                {
                    "name": "models/gemini-2.5-flash-lite",
                    "supportedGenerationMethods": ["generateContent"],
                }
            ],
            "nextPageToken": "page-2",
        },
        f"{MODELS}?pageToken=page-2": {"models": [FLASH]},
    }

    def get(url: str, headers: dict) -> _Response:
        assert headers["x-goog-api-key"] == "secret-key"
        assert "secret-key" not in url
        return _Response(200, pages[url])

    rows = load_models("secret-key", get=get)
    assert choose_model(rows) == "gemini-3.5-flash-lite"


def _cache(tmp_path: Path) -> ReplayCache:
    return ReplayCache(tmp_path / "replay.json")


def test_complete_with_gemini_records_the_chosen_model(tmp_path: Path) -> None:
    calls = {"post": 0}

    def get(url: str, headers: dict) -> _Response:
        assert headers["x-goog-api-key"] == "secret-key"
        assert url == MODELS
        return _Response(200, {"models": [FLASH]})

    def post(url: str, headers: dict, payload: dict) -> _Response:
        calls["post"] += 1
        assert "openrouter" not in url
        assert "secret-key" not in url
        assert headers["x-goog-api-key"] == "secret-key"
        assert "secret-key" not in json.dumps(payload)
        return _Response(200, {"candidates": [{"content": {"parts": [{"text": "pong"}]}}]})

    result = complete_with_gemini(
        "SYNTHETIC-ONLY reply with pong",
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={"GEMINI_API_KEY": "secret-key", "OPENROUTER_API_KEY": "or-key"},
        root=tmp_path,
        get=get,
        post=post,
        sleep=lambda _seconds: None,
    )
    assert result.provider == "gemini"
    assert result.model == "gemini-3.5-flash-lite"
    assert result.text == "pong"
    assert calls["post"] == 1


def test_a_resource_exhausted_body_uses_openrouter(tmp_path: Path) -> None:
    def get(_url: str, _headers: dict) -> _Response:
        return _Response(200, {"models": [FLASH]})

    def post(url: str, _headers: dict, payload: dict) -> _Response:
        if "generativelanguage.googleapis.com" in url:
            return _Response(503, text="RESOURCE_EXHAUSTED")
        assert str(payload["model"]).endswith(":free")
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete_with_gemini(
        "SYNTHETIC-ONLY reply with pong",
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={"GEMINI_API_KEY": "secret-key", "OPENROUTER_API_KEY": "or-key"},
        root=tmp_path,
        get=get,
        post=post,
        sleep=lambda _seconds: None,
    )
    assert result.provider == "openrouter"
    assert result.model == "example/test:free"


def test_a_models_list_429_uses_openrouter(tmp_path: Path) -> None:
    def get(_url: str, _headers: dict) -> _Response:
        return _Response(429, text="RESOURCE_EXHAUSTED")

    def post(url: str, _headers: dict, payload: dict) -> _Response:
        assert "generativelanguage.googleapis.com" not in url
        assert str(payload["model"]).endswith(":free")
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete_with_gemini(
        "SYNTHETIC-ONLY reply with pong",
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={"GEMINI_API_KEY": "secret-key", "OPENROUTER_API_KEY": "or-key"},
        root=tmp_path,
        get=get,
        post=post,
        sleep=lambda _seconds: None,
    )
    assert result.provider == "openrouter"
    assert result.model == "example/test:free"
    assert result.text == "pong"


def test_a_non_quota_gemini_error_does_not_call_openrouter(tmp_path: Path) -> None:
    def get(_url: str, _headers: dict) -> _Response:
        return _Response(200, {"models": [FLASH]})

    def post(url: str, _headers: dict, _payload: dict) -> _Response:
        if "generativelanguage.googleapis.com" in url:
            return _Response(503, text="quota")
        raise AssertionError("openrouter")

    with pytest.raises(RuntimeError, match="Gemini returned 503"):
        complete_with_gemini(
            "SYNTHETIC-ONLY reply with pong",
            cache=_cache(tmp_path),
            models=["example/test:free"],
            environ={"GEMINI_API_KEY": "secret-key", "OPENROUTER_API_KEY": "or-key"},
            root=tmp_path,
            get=get,
            post=post,
            sleep=lambda _seconds: None,
        )


def test_complete_with_gemini_uses_openrouter_after_a_429(tmp_path: Path) -> None:
    def get(_url: str, _headers: dict) -> _Response:
        return _Response(200, {"models": [FLASH]})

    def post(url: str, _headers: dict, payload: dict) -> _Response:
        if "generativelanguage.googleapis.com" in url:
            return _Response(429, text="RESOURCE_EXHAUSTED")
        assert str(payload["model"]).endswith(":free")
        return _Response(200, {"choices": [{"message": {"content": "pong"}}]})

    result = complete_with_gemini(
        "SYNTHETIC-ONLY reply with pong",
        cache=_cache(tmp_path),
        models=["example/test:free"],
        environ={
            "GEMINI_API_KEY": "secret-key",
            "OPENROUTER_API_KEY": "or-key",
        },
        root=tmp_path,
        get=get,
        post=post,
        sleep=lambda _seconds: None,
    )
    assert result.provider == "openrouter"
    assert result.model == "example/test:free"
    assert result.text == "pong"


def test_complete_with_gemini_without_a_key_does_not_call_http(tmp_path: Path) -> None:
    def get(*_args: object) -> _Response:
        raise AssertionError("get")

    def post(*_args: object) -> _Response:
        raise AssertionError("post")

    result = complete_with_gemini(
        "SYNTHETIC-ONLY reply with pong",
        cache=_cache(tmp_path),
        environ={},
        root=tmp_path,
        get=get,
        post=post,
        sleep=lambda _seconds: None,
    )
    assert result.provider == "gazetteer"
    assert "pinned wording" in result.text
    assert not (tmp_path / "replay.json").exists()
    with pytest.raises(AssertionError, match="get"):
        complete_with_gemini(
            "SYNTHETIC-ONLY reply with pong",
            cache=_cache(tmp_path),
            environ={"GEMINI_API_KEY": "secret-key"},
            root=tmp_path,
            get=get,
            post=post,
            sleep=lambda _seconds: None,
        )


def test_complete_with_gemini_rejects_non_synthetic_text_before_listing_models(
    tmp_path: Path,
) -> None:
    def get(*_args: object) -> _Response:
        raise AssertionError("get")

    with pytest.raises(SyntheticRejected):
        complete_with_gemini(
            "a real chart",
            cache=_cache(tmp_path),
            environ={"GEMINI_API_KEY": "secret-key"},
            root=tmp_path,
            get=get,
        )


def test_uploads_and_env_files_are_gitignored() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / ".gitignore").read_text()
    assert "uploads/" in text
    assert ".env" in text.splitlines()
