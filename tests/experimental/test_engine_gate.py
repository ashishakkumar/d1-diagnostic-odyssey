"""The experimental engine stays off unless the local gate is present.

These tests are the gate. The patient notebook is not a caller.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from d1_engine.gate import (
    ACK_TEXT,
    BANNER,
    GateError,
    acknowledgement_ok,
    resolve_bind,
    start_allowed,
)
from d1_engine.http import create_app

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ("apps/web", "services/api", "services/scoring", "services/safety", "services/ingest")
FORBIDDEN = ("d1_engine", "compose.experimental", "8090", "exomiser", "lirical")


def _env() -> dict[str, str]:
    return {"D1_TRACK": "experimental-local", "D1_BIND": "127.0.0.1"}


def _ack(tmp_path: Path, text: str | None = None) -> Path:
    path = tmp_path / "ACKNOWLEDGEMENT"
    path.write_text(ACK_TEXT if text is None else text, encoding="utf-8")
    return path


def test_start_requires_the_env_var_and_the_typed_acknowledgement(tmp_path: Path) -> None:
    ack = _ack(tmp_path)
    assert start_allowed(_env(), ack)
    assert acknowledgement_ok(ack)
    assert start_allowed({"D1_TRACK": "experimental-local"}, ack)
    assert not start_allowed({}, ack)
    assert not start_allowed({"D1_TRACK": "safe", "D1_BIND": "127.0.0.1"}, ack)
    assert not start_allowed({"D1_TRACK": "experimental-local", "D1_BIND": "0.0.0.0"}, ack)
    assert not start_allowed(_env(), tmp_path / "missing")
    empty = tmp_path / "empty"
    empty.write_text("", encoding="utf-8")
    assert not start_allowed(_env(), empty)
    wrong = _ack(tmp_path, "yes\n")
    assert not start_allowed(_env(), wrong)
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "engine/ACKNOWLEDGEMENT" in gitignore
    assert ".env" in gitignore.splitlines()


def test_banner_is_on_every_screen_and_export_and_cannot_be_dismissed(tmp_path: Path) -> None:
    app = create_app(_env(), _ack(tmp_path), mode="hosted")
    client = TestClient(app)
    paths = ("/", "/?dismiss=1", "/samples/public-synthetic", "/samples/public-synthetic/export")
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200
        assert BANNER in response.text
        assert "EXPERIMENTAL, RESEARCH ONLY" in response.text
    page = client.get("/?dismiss=1")
    assert "<button" not in page.text
    assert "dismiss" not in page.text.lower()
    export = client.get("/samples/public-synthetic/export?dismiss=1")
    assert export.text.startswith(BANNER)


def test_the_engine_container_has_no_network() -> None:
    compose = (ROOT / "compose.experimental.yaml").read_text(encoding="utf-8")
    assert 'network_mode: "none"' in compose
    assert "0.0.0.0" not in compose
    assert "\n    ports:" not in compose
    dockerfile = (ROOT / "engine" / "Dockerfile").read_text(encoding="utf-8")
    for line in dockerfile.splitlines():
        stripped = line.strip()
        if not stripped.startswith("COPY"):
            continue
        banned = (".zip", "mv.db", "phenotype", "hg38", "hg19")
        assert not any(token in stripped for token in banned)


def test_the_engine_binds_to_loopback_only() -> None:
    assert resolve_bind(None) == "127.0.0.1"
    assert resolve_bind("") == "127.0.0.1"
    assert resolve_bind("127.0.0.1") == "127.0.0.1"
    with pytest.raises(GateError):
        resolve_bind("0.0.0.0")
    with pytest.raises(GateError):
        resolve_bind("localhost")
    compose = (ROOT / "compose.experimental.yaml").read_text(encoding="utf-8")
    assert "D1_BIND: 127.0.0.1" in compose
    with pytest.raises(GateError):
        create_app(
            {"D1_TRACK": "experimental-local", "D1_BIND": "0.0.0.0"},
            Path("missing"),
            "hosted",
        )


def test_hosted_build_has_no_upload_and_serves_only_the_allowlist(tmp_path: Path) -> None:
    app = create_app(_env(), _ack(tmp_path), mode="hosted")
    client = TestClient(app)
    assert client.post("/upload").status_code == 404
    assert client.post("/run").status_code == 404
    assert client.get("/samples/not-a-public-sample").status_code == 404
    assert client.get("/samples/public-synthetic").status_code == 200
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not any("upload" in path for path in paths)
    assert "/run" not in paths


def test_the_notebook_has_no_route_to_the_engine() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    for word in ("d1_engine", "exomiser", "lirical", "8090"):
        assert word not in compose
    next_config = (ROOT / "apps" / "web" / "next.config.ts").read_text(encoding="utf-8")
    assert "8090" not in next_config
    assert "experimental" not in next_config
    for relative in NOTEBOOK:
        for path in (ROOT / relative).rglob("*"):
            if path.suffix not in {".py", ".ts", ".tsx"} or "node_modules" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for word in FORBIDDEN:
                assert word not in text, f"{path} contains {word}"
