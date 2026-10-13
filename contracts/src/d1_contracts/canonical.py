"""Canonical JSON for a draft body. The database trigger matches this for text it stores."""

import hashlib
import json
import unicodedata
from typing import Any


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): _nfc(item) for key, item in value.items()}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _nfc(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def body_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
