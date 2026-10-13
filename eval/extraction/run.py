"""Text-to-HPO extraction eval on GSC+ (206-abstract test split, PhenoTagger repo) and ID-68 (PhenoBERT repo).

Usage: python eval/extraction/run.py <GSCplus_test_gold.tsv> <ID-68 dir> [--path ai|rules] [--limit N]
Document-level HPO id sets, micro-averaged precision/recall/F1.
- exact: same id.
- relaxed: a predicted id counts if it equals, is an ancestor of, or is a descendant of a gold id
  in the same document (and a gold id counts as found the same way).
- invalid: predicted ids not present in the loaded HPO release (the model never supplies ids,
  so this should be 0); gold ids missing from the release (obsolete/alt ids) are reported too.
- downstream proxy: these corpora carry no diagnosis labels, so we rank the full catalogue with
  gold ids and with extracted ids, and report how often the gold-ranked top-1 disease is
  top-1 / in the top-5 of the extracted ranking. This is agreement, not accuracy.
LLM outputs are cached in eval/extraction/cache_<path>.json so the run is resumable.
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api"))
from app import llm_extract
CONFIDENT = 0.8  # same as app.analyze.CONFIDENT
from app.catalog import catalog

args = sys.argv[1:]
path = args[args.index("--path") + 1] if "--path" in args else "ai"
cached_only = "--cached-only" in args
limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
cat = catalog()
here = Path(__file__).resolve().parent
cache_file = here / f"cache_{'ai' if path == 'hybrid' else path}.json"
cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}


def gsc(file):
    docs, block = [], []
    for line in open(file, encoding="utf-8").read().split("\n") + [""]:
        if line.strip() == "":
            if block:
                docs.append((block[0].strip(), block[1], {l.split("\t")[3].strip() for l in block[2:] if l.count("\t") >= 3}))
            block = []
        else:
            block.append(line)
    return docs


def id68(d):
    d = Path(d); out = []
    for f in sorted((d / "corpus").iterdir()):
        gold = set()
        for l in (d / "ann" / f.name).read_text(encoding="utf-8").splitlines():
            parts = l.split("\t")
            if len(parts) >= 4: gold.add(parts[3].strip().replace("_", ":"))
        out.append((f.name, f.read_text(encoding="utf-8"), gold))
    return out


def predict(key, text):
    if path == "rules":
        if "--same-docs" in args and key not in json.loads((here / "cache_ai.json").read_text()):
            return None
        return {f["candidates"][0]["hpo_id"] for f in cat.extract_rules(text)}
    if key not in cache and cached_only:
        return None
    if key not in cache:
        for attempt in range(6):
            try:
                cache[key] = llm_extract.extract(text)
                break
            except llm_extract.NoModel as exc:
                print("quota/err", key, exc, flush=True); time.sleep(20 * (attempt + 1))
        else:
            return None
        cache_file.write_text(json.dumps(cache))
        time.sleep(4)
    ids = set()
    for f in cache[key]["findings"]:
        c = cat.ground(f["phrase"], hint=f.get("label"))
        if c and c[0]["score"] >= CONFIDENT:
            ids.add(c[0]["hpo_id"])
    if path == "hybrid":
        ids |= {f["candidates"][0]["hpo_id"] for f in cat.extract_rules(text)}
    return ids


def related(a, b):
    ia, ib = cat.idx.get(a), cat.idx.get(b)
    if ia is None or ib is None: return a == b
    return ia in cat.ancestors[ib] or ib in cat.ancestors[ia]


def top(ids, k=5):
    p = [cat.idx[i] for i in ids if i in cat.idx]
    if not p: return []
    _s, _b, sc = cat.scores(p, [])
    return [int(x) for x in np.argsort(-sc, kind="stable")[:k]]


def run(name, docs):
    tp = fp = fn = rtp_p = rtp_g = npred = ngold = invalid = gold_missing = done = 0
    t1 = t5 = nrank = 0
    for key, text, gold in docs[:limit]:
        pred = predict(f"{name}:{key}", text)
        if pred is None: continue
        done += 1
        invalid += sum(1 for i in pred if i not in cat.idx)
        gold_missing += sum(1 for g in gold if g not in cat.idx)
        tp += len(pred & gold); fp += len(pred - gold); fn += len(gold - pred)
        rtp_p += sum(1 for p in pred if any(related(p, g) for g in gold))
        rtp_g += sum(1 for g in gold if any(related(p, g) for p in pred))
        npred += len(pred); ngold += len(gold)
        gt, et = top(gold), top(pred)
        if gt:
            nrank += 1; t1 += bool(et) and et[0] == gt[0]; t5 += gt[0] in et
    P = tp / max(tp + fp, 1); R = tp / max(tp + fn, 1)
    rP = rtp_p / max(npred, 1); rR = rtp_g / max(ngold, 1)
    f = lambda p, r: round(2 * p * r / (p + r), 4) if p + r else 0.0
    return {"docs_scored": done, "docs_total": len(docs[:limit]), "exact": {"P": round(P, 4), "R": round(R, 4), "F1": f(P, R)},
            "relaxed": {"P": round(rP, 4), "R": round(rR, 4), "F1": f(rP, rR)},
            "invalid_predicted_ids": invalid, "gold_ids_not_in_release": gold_missing,
            "downstream_agreement": {"docs": nrank, "gold_top1_is_extracted_top1": round(t1 / max(nrank, 1), 4),
                                     "gold_top1_in_extracted_top5": round(t5 / max(nrank, 1), 4)}}

out = {"path": path, "models": sorted({v.get("model") for v in cache.values()}) if path in ("ai", "hybrid") else None,
       "GSC+": run("gsc", gsc(args[0])), "ID-68": run("id68", id68(args[1]))}
print(json.dumps(out, indent=1))
(here / f"results_{path}{'_samedocs' if '--same-docs' in args else ''}{'_partial' if cached_only else ''}.json").write_text(json.dumps(out, indent=1))
