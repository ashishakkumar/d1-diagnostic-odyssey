"""Refuse to start unless the local gate is present, then bind loopback."""

import os
import sys
from pathlib import Path

import uvicorn

from d1_engine.gate import GateError, resolve_bind, start_allowed
from d1_engine.http import create_app


def main() -> int:
    ack = Path(os.environ.get("D1_ACK", "engine/ACKNOWLEDGEMENT"))
    if not start_allowed(os.environ, ack):
        print("experimental engine refused to start", file=sys.stderr)
        return 2
    try:
        host = resolve_bind(os.environ.get("D1_BIND"))
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    mode = os.environ.get("D1_BUILD", "hosted")
    app = create_app(dict(os.environ), ack, mode)
    uvicorn.run(app, host=host, port=8090)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
