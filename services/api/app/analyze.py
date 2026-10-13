"""One-box flow: note -> findings -> HPO ids -> ranked catalogue. Nothing is stored."""

from __future__ import annotations

import time

from app import llm_extract
from app.catalog import catalog
from app.routes.ports import red_flag

CONFIDENT = 0.8
ATTRIBUTION = (
    "Uses the Human Phenotype Ontology (HPO release v2026-09-01) and its disease annotations "
    "(phenotype.hpoa 2026-09-02), hpo.jax.org. Disease names come from OMIM, Orphanet and "
    "DECIPHER as listed in those annotations; follow the links for the source records."
)
DISCLAIMER = "Research prototype on public data. This is not a diagnosis. Discuss results with a clinician."


def _locate(note: str, phrase: str) -> tuple[int | None, int | None]:
    i = note.lower().find(phrase.lower())
    return (i, i + len(phrase)) if i >= 0 else (None, None)


def analyze(note: str, use_ai: bool = True) -> dict:
    note = (note or "").strip()
    if not note:
        raise ValueError("the note is empty")
    if len(note) > 8000:
        raise ValueError("the note is longer than 8000 characters")
    stop = red_flag(note)
    if stop is not None:
        return {"stop": stop}
    cat = catalog()
    t0 = time.perf_counter()
    path, model, why, context = "rules", None, None, None
    findings: list[dict] = []
    if use_ai and llm_extract.available():
        try:
            got = llm_extract.extract(note)
            path, model, context = got["provider"], got["model"], got["context"]
            for f in got["findings"]:
                start, end = _locate(note, f["phrase"])
                cands = cat.ground(f["phrase"], hint=f["label"])
                findings.append({**f, "start": start, "end": end, "candidates": cands})
        except llm_extract.NoModel as exc:
            why = f"AI extraction unavailable ({exc}); rules ran instead."
    elif use_ai:
        why = "No model key is configured on this server, so the rules matcher ran."
    else:
        why = "AI extraction was switched off for this request."
    rule_hits = cat.extract_rules(note)
    if path == "rules":
        for f in rule_hits:
            findings.append({**f, "onset": None, "label": None, "source": "rules"})
    else:
        for f in findings:
            f["source"] = "model"
    t1 = time.perf_counter()
    for f in findings:
        top = f["candidates"][0] if f["candidates"] else None
        f["chosen"] = top["hpo_id"] if top and top["score"] >= CONFIDENT else None
        f["needs_review"] = f["chosen"] is None and bool(top)
    if path != "rules":
        # Hybrid: exact HPO label/synonym hits the model missed are added (raised GSC+ recall,
        # see eval/extraction/RESULTS.md). They are labelled as rules in the UI.
        have = {f["chosen"] for f in findings if f["chosen"]}
        for f in rule_hits:
            hid = f["candidates"][0]["hpo_id"]
            if hid not in have:
                findings.append({**f, "onset": None, "label": None, "source": "rules",
                                 "chosen": hid, "needs_review": False})
                have.add(hid)
    present = [f["chosen"] for f in findings if f["chosen"] and f["present"]]
    absent = [f["chosen"] for f in findings if f["chosen"] and not f["present"]]
    ranked = cat.rank(present, absent)
    t2 = time.perf_counter()
    extract_actor = "Rules (HPO label and synonym matcher)" if path == "rules" else f"Language model ({model})"
    stages = [
        {"id": "extract", "label": "Extract", "actor": extract_actor, "ms": round((t1 - t0) * 1000),
         "did": f"Found {len(findings)} findings ({sum(f.get('source') == 'rules' for f in findings)} from the rules matcher), {sum(not f['present'] for f in findings)} marked absent."},
        {"id": "map", "label": "Map", "actor": "Exact, fuzzy and embedding search over HPO",
         "did": f"Grounded {sum(1 for f in findings if f['chosen'])} to HPO ids; "
                f"{sum(f['needs_review'] for f in findings)} need your check. The model never supplies ids."},
        {"id": "rank", "label": "Rank", "actor": "Resnik best-match average",
         "ms": round((t2 - t1) * 1000),
         "did": f"Scored {cat.n_dis:,} diseases from the HPO annotations; absent findings lower a score."},
    ]
    return {"stop": None, "path": path, "model": model, "path_note": why, "context": context,
            "findings": findings, "stages": stages, **ranked,
            "catalogue": {"diseases": cat.n_dis, "terms": len(cat.terms), "hpo_version": cat.version},
            "attribution": ATTRIBUTION, "disclaimer": DISCLAIMER}


def rerank(present: list[str], absent: list[str]) -> dict:
    cat = catalog()
    return {**cat.rank(present, absent), "attribution": ATTRIBUTION, "disclaimer": DISCLAIMER}
