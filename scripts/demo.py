"""Start the API and the notebook. `make demo` resets the database, then runs this."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
API = "http://127.0.0.1:8000/footer"
WEB = "http://127.0.0.1:3000"


def _ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return response.status < 500
    except Exception:
        return False


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = ":".join(
        [
            str(ROOT / "services" / "api"),
            str(ROOT / "contracts" / "src"),
            str(ROOT / "services" / "scoring"),
            str(ROOT / "services" / "safety"),
            str(ROOT / "services" / "ingest" / "src"),
            str(ROOT / "services" / "llm"),
            env.get("PYTHONPATH", ""),
        ]
    )
    env["API_URL"] = "http://127.0.0.1:8000"
    api = subprocess.Popen(
        [
            str(PYTHON),
            "-m",
            "uvicorn",
            "app.routes.notebook:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=ROOT,
        env=env,
    )
    web = subprocess.Popen(
        ["npm", "--prefix", "apps/web", "run", "dev", "--", "--port", "3000"],
        cwd=ROOT,
        env=env,
    )
    children = (api, web)

    def stop(*_args: object) -> None:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if api.poll() is not None or web.poll() is not None:
            stop()
        if _ready(API) and _ready(WEB):
            print("Notebook is at http://127.0.0.1:3000")
            print("For research use only. Not for use in diagnostic procedures.")
            break
        time.sleep(0.4)
    else:
        stop()
    while api.poll() is None and web.poll() is None:
        time.sleep(0.5)
    stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
