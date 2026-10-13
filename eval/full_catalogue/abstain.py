"""Calibrate the weak-signal flag. Features per packet: top score, top-5 relative spread,
max IC among present terms. Thresholds are chosen on train; flagged vs unflagged top-1 reported on test."""
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/api"))
from app.catalog import catalog
c = catalog(); pos = {d: i for i, d in enumerate(c.diseases)}
rows = []
with zipfile.ZipFile(sys.argv[1]) as z:
    for n in z.namelist():
        if not n.endswith(".json"): continue
        pk = json.loads(z.read(n))
        tr = [d["term"]["id"] for d in pk.get("diseases", []) if d["term"]["id"].startswith("OMIM:")]
        f = pk.get("phenotypicFeatures", [])
        p = list(dict.fromkeys(c.idx[x["type"]["id"]] for x in f if not x.get("excluded") and x["type"]["id"] in c.idx))
        a = list(dict.fromkeys(c.idx[x["type"]["id"]] for x in f if x.get("excluded") and x["type"]["id"] in c.idx))
        if not tr or tr[0] not in pos or not p: continue
        _, _, s = c.scores(p, a)
        o = np.argsort(-s)[:5]; top = float(s[o[0]])
        rows.append((top, (top - float(s[o[4]])) / max(top, 1e-9), float(max(c.ic[p])), len(p),
                     int((s >= s[pos[tr[0]]]).sum()) == 1,
                     int(hashlib.sha256(pk["id"].encode()).hexdigest(), 16) % 5 == 0))
np.save("/tmp/abst.npy", np.array(rows, dtype=float))
