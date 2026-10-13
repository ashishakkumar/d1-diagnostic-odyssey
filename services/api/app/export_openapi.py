"""Write the OpenAPI document and the TypeScript client types it generates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.routes.notebook import create_app

ROOT = Path(__file__).resolve().parents[3]


def openapi_document() -> dict[str, Any]:
    return create_app().openapi()


def _type_name(schema: dict, names: dict[str, str]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema and schema.get("type") == "string":
        return " | ".join(json.dumps(item) for item in schema["enum"])
    if "const" in schema and isinstance(schema["const"], str):
        return json.dumps(schema["const"])
    kind = schema.get("type")
    if "anyOf" in schema:
        return " | ".join(_type_name(item, names) for item in schema["anyOf"])
    if kind == "string":
        return "string"
    if kind == "integer" or kind == "number":
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "array":
        return f"{_type_name(schema.get('items') or {}, names)}[]"
    if kind == "object":
        return "Record<string, unknown>"
    if kind == "null":
        return "null"
    return "unknown"


def typescript_client(spec: dict) -> str:
    schemas: dict[str, dict] = spec.get("components", {}).get("schemas", {})
    lines = [
        "/* Generated from contracts/openapi.json. Do not edit by hand. */",
        "",
    ]
    for name in sorted(schemas):
        schema = schemas[name]
        if schema.get("type") != "object":
            continue
        required = set(schema.get("required") or [])
        properties = schema.get("properties") or {}
        lines.append(f"export interface {name} {{")
        for prop in sorted(properties):
            rendered = _type_name(properties[prop], schemas)
            optional = "" if prop in required else "?"
            lines.append(f"  {prop}{optional}: {rendered};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def write_documents() -> None:
    spec = openapi_document()
    spec_path = ROOT / "contracts" / "openapi.json"
    spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    client = typescript_client(json.loads(spec_path.read_text()))
    (ROOT / "contracts" / "ts" / "src" / "api.ts").write_text(client)


if __name__ == "__main__":
    write_documents()
