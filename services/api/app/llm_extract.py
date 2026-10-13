"""AI extraction of findings from free text. Gemini first, then an OpenRouter ':free' model.

The model returns phrases and a suggested plain HPO-style label. It never supplies ids:
ids come only from grounding against the loaded ontology (app.catalog). The note is sent
to the provider for this one call and is not stored by this app.
"""

from __future__ import annotations

import json
import os
import re

import httpx

GEMINI_MODELS = [m.strip() for m in os.environ.get(
    "GEMINI_MODELS", "gemini-3.5-flash-lite,gemini-2.5-flash").split(",") if m.strip()]
GEMINI_MODEL = GEMINI_MODELS[0]
OPENROUTER_MODELS = [
    m.strip() for m in os.environ.get(
        "OPENROUTER_FREE_MODELS",
        "google/gemma-4-31b-it:free,nvidia/nemotron-3-super-120b-a12b:free",
    ).split(",") if m.strip().endswith(":free")
]

PROMPT = """You extract clinical findings from a note for a rare-disease research tool.
Return JSON only, with this shape:
{"findings":[{"phrase":"exact words from the note","present":true,"onset":"age or null",
"label":"short standard phenotype name, e.g. Seizure, Hypotonia, Microcephaly"}],
"context":{"age":null,"sex":null,"family_history":null,"labs":[]}}
Rules: one finding per distinct sign or symptom; present=false when the note says it is absent
(no, denies, without, negative for); phrase must be copied from the note; do not give codes or ids;
do not guess a diagnosis; ignore diagnoses and medications as findings; put lab or genetic
results in context.labs as short strings.
Note:
<<<
{note}
>>>"""


class NoModel(RuntimeError):
    pass


def available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model output")
    data = json.loads(m.group())
    out = []
    for f in data.get("findings") or []:
        phrase = str(f.get("phrase") or "").strip()
        if not phrase:
            continue
        out.append({"phrase": phrase[:200], "present": f.get("present") is not False,
                    "onset": (str(f["onset"])[:60] if f.get("onset") else None),
                    "label": str(f.get("label") or "")[:120] or None})
    ctx = data.get("context") or {}
    labs = [str(x)[:160] for x in (ctx.get("labs") or [])][:10]
    return {"findings": out[:40], "context": {
        "age": ctx.get("age"), "sex": ctx.get("sex"),
        "family_history": ctx.get("family_history"), "labs": labs}}


def extract(note: str, post=httpx.post) -> dict:
    """Return {'findings', 'context', 'provider', 'model'} or raise NoModel."""
    prompt = PROMPT.replace("{note}", note[:8000])
    errors = []
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        for gmodel in GEMINI_MODELS:
            try:
                r = post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{gmodel}:generateContent",
                    headers={"x-goog-api-key": key},
                    json={"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                          "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}},
                    timeout=25,
                )
                if r.status_code == 200:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                    return {**_parse(text), "provider": "gemini", "model": gmodel}
                errors.append(f"{gmodel} {r.status_code}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{gmodel} {type(exc).__name__}")
    okey = os.environ.get("OPENROUTER_API_KEY")
    if okey:
        for model in OPENROUTER_MODELS:
            try:
                r = post("https://openrouter.ai/api/v1/chat/completions",
                         headers={"Authorization": f"Bearer {okey}"},
                         json={"model": model, "temperature": 0,
                               "messages": [{"role": "user", "content": prompt}]}, timeout=25)
                if r.status_code == 200:
                    result = _parse(r.json()["choices"][0]["message"]["content"])
                    return {**result, "provider": "openrouter", "model": model}
                errors.append(f"{model} {r.status_code}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{model} {type(exc).__name__}")
    raise NoModel("; ".join(errors) or "no model key configured")
