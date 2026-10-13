"""Vercel serverless entry for the D1 FastAPI backend (synthetic demo data only).

The repo is a set of source trees rather than installed packages, so put them on
sys.path the same way `make demo` does. Requests arrive as /api/<path> or <path>
depending on the caller, so a thin ASGI wrapper strips a leading /api.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in (
    "services/api",
    "contracts/src",
    "services/scoring",
    "services/safety",
    "services/ingest/src",
    "services/llm",
):
    sys.path.insert(0, str(ROOT / rel))

from app.routes.notebook import app as _fastapi_app  # noqa: E402


async def app(scope, receive, send):
    if scope["type"] in ("http", "websocket"):
        path = scope.get("path", "")
        for prefix in ("/api/index", "/api"):
            if path == prefix or path.startswith(prefix + "/"):
                path = path[len(prefix) :] or "/"
                break
        scope = dict(scope, path=path, raw_path=path.encode())
    await _fastapi_app(scope, receive, send)
