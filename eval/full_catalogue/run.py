"""Full-catalogue ranker on Phenopacket Store 0.1.27 (public cases, known diagnoses).

Usage: python eval/full_catalogue/run.py path/to/all_phenopackets.zip
Truth is the packet's OMIM disease id. Ranking runs over every disease in phenotype.hpoa
(OMIM, Orphanet, DECIPHER). Ties take the worst rank. Abstentions are not removed.
Split: SHA-256 of packet id mod 5 == 0 is test (same rule as eval/RESULTS.md).
Known leak: phenotype.hpoa is partly curated from the same publications as the packets.
"""
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api"))
from app.catalog import catalog

cat = catalog()
pos = {d: i for i, d in enumerate(cat.diseases)}
rows = {"all": [], "test": []}
skipped = 0
with zipfile.ZipFile(sys.argv[1]) as z:
    for name in z.namelist():
        if not name.endswith(".json"): continue
        pk = json.loads(z.read(name))
        truth = [d["term"]["id"] for d in pk.get("diseases", []) if d.get("term", {}).get("id", "").startswith("OMIM:")]
        feats = pk.get("phenotypicFeatures", [])
        p = [cat.idx[f["type"]["id"]] for f in feats if not f.get("excluded") and f["type"]["id"] in cat.idx]
        a = [cat.idx[f["type"]["id"]] for f in feats if f.get("excluded") and f["type"]["id"] in cat.idx]
        if not truth or truth[0] not in pos or not p:
            skipped += 1; continue
        _s, _b, sc = cat.scores(list(dict.fromkeys(p)), list(dict.fromkeys(a)))
        t = sc[pos[truth[0]]]
        rank = int((sc >= t).sum())  # worst rank among ties
        rows["all"].append(rank)
        if int(hashlib.sha256(pk["id"].encode()).hexdigest(), 16) % 5 == 0:
            rows["test"].append(rank)
out = {"skipped": skipped, "catalogue_diseases": cat.n_dis}
for k, r in rows.items():
    r = np.array(r)
    out[k] = {"n": int(len(r)), **{f"top{n}": round(float((r <= n).mean()), 4) for n in (1, 5, 10)},
              "median_rank": int(np.median(r))}
print(json.dumps(out, indent=1))
