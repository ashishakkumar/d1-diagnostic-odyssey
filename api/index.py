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


async def _diag(send):
    import json
    import traceback

    import psycopg

    out = {}
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10) as c:
            c.execute("SET ROLE d1_api")
            out["ok"] = c.execute("select current_user, session_user").fetchone()
    except Exception:
        out["err"] = traceback.format_exc()[-1500:].replace(os.environ.get("DATABASE_URL", "x"), "***")
    body = json.dumps(out, default=str).encode()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": body})


async def app(scope, receive, send):
    if scope["type"] == "http" and scope.get("path", "").endswith("/_diag"):
        return await _diag(send)
    if scope["type"] in ("http", "websocket"):
        path = scope.get("path", "")
        for prefix in ("/api/index", "/api"):
            if path == prefix or path.startswith(prefix + "/"):
                path = path[len(prefix) :] or "/"
                break
        scope = dict(scope, path=path, raw_path=path.encode())
    await _fastapi_app(scope, receive, send)
