"""The committed OpenAPI document is generated from the app."""

import json
from pathlib import Path

from app.export_openapi import openapi_document, typescript_client

ROOT = Path(__file__).resolve().parents[1]


def test_committed_openapi_matches_the_app() -> None:
    spec = openapi_document()
    committed = json.loads((ROOT / "contracts" / "openapi.json").read_text())
    assert spec == committed
    assert "/demo/cases" in spec["paths"]
    assert "/cases/{case_id}/report" in spec["paths"]
    assert "/cases/{case_id}/population-prior" in spec["paths"]


def test_generated_client_types_match_the_spec() -> None:
    text = typescript_client(json.loads((ROOT / "contracts" / "openapi.json").read_text()))
    assert text == (ROOT / "contracts" / "ts" / "src" / "api.ts").read_text()
    assert "export interface DemoCaseOut" in text
    assert "export interface Report" in text
