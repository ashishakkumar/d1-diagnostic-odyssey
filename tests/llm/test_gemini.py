"""Gemini is primary. The model id comes from a models list, not from a guessed constant."""

import json
from pathlib import Path

from d4_llm.gemini import choose_model, gemini_text


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
    from d4_llm.fallback import is_rate_limited

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


def test_uploads_and_env_files_are_gitignored() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / ".gitignore").read_text()
    assert "uploads/" in text
    assert ".env" in text.splitlines()
