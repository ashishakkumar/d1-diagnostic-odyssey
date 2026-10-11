"""One opt-in live call. Set D4_LLM_LIVE=1. Unit tests never import this path."""

import os
from pathlib import Path

import httpx
import pytest

from d4_llm import ReplayCache, complete
from d4_llm.fallback import free_model_ids

pytestmark = pytest.mark.skipif(os.environ.get("D4_LLM_LIVE") != "1", reason="opt-in live smoke")


def test_one_openrouter_free_completion(tmp_path: Path) -> None:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        pytest.skip("OPENROUTER_API_KEY is not set")
    base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    listing = httpx.get(f"{base}/models", timeout=60)
    listing.raise_for_status()
    chosen = ""
    for row in listing.json().get("data") or []:
        model_id = str(row.get("id") or "")
        pricing = row.get("pricing") or {}
        if not model_id.endswith(":free"):
            continue
        if str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0":
            chosen = model_id
            break
    if not chosen:
        pytest.skip("no priced-zero :free model in the catalogue")
    free_model_ids(chosen)

    def primary(_prompt: str) -> str:
        raise RuntimeError("429 RESOURCE_EXHAUSTED quota")

    result = complete(
        "SYNTHETIC-ONLY reply with the single word pong",
        primary=primary,
        cache=ReplayCache(tmp_path / "live.json"),
        models=[chosen],
        sleep=lambda _seconds: None,
        log_path=None,
    )
    assert result.provider == "openrouter"
    assert result.model == chosen
    assert result.model is not None and result.model.endswith(":free")
    assert result.text.strip()
