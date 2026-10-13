"""Hosted-model client. Gemini first. OpenRouter free models only after a rate limit."""

from d4_llm.fallback import (
    Completion,
    RateLimitedNoFallback,
    ReplayCache,
    SyntheticRejected,
    complete,
    complete_or_degrade,
    is_rate_limited,
)

__all__ = [
    "Completion",
    "RateLimitedNoFallback",
    "ReplayCache",
    "SyntheticRejected",
    "complete",
    "complete_or_degrade",
    "is_rate_limited",
]
