"""Build compact HPO artifacts for the full-catalogue ranker.

Inputs (public, HPO release v2026-09-01): hp.json and phenotype.hpoa.
Outputs in services/api/app/data/hpo/: terms.json, catalog.npz.
Run: python scripts/build_hpo_index.py <dir-with-hp.json-and-phenotype.hpoa>
"""
import json, math, sys, collections
from pathlib import Path
import numpy as np

src = Path(sys.argv[1]); out = Path(__file__).resolve().parents[1] / "services/api/app/data/hpo"
out.mkdir(parents=True, exist_ok=True)
ROOT = "HP:0000118"  # Phenotypic abnormality
g = json.load(open(src / "hp.json"))["graphs"][0]
def cid(u): return u.rsplit("/", 1)[-1].replace("_", ":")
nodes = {}
for n in g["nodes"]:
    i = cid(n["id"])
    if not i.startswith("HP:") or n.get("type") != "CLASS" or n.get("meta", {}).get("deprecated"): continue
    if "lbl" not in n: continue
    syn = []
    for s in n.get("meta", {}).get("synonyms", []):
        if s["pred"] in ("hasExactSynonym", "hasRelatedSynonym") : syn.append(s["val"])
    nodes[i] = (n["lbl"], syn)
parents = collections.defaultdict(set)
for e in g["edges"]:
    if e["pred"] == "is_a":
        a, b = cid(e["sub"]), cid(e["obj"])
        if a in nodes and b in nodes: parents[a].add(b)
anc_cache = {}
def anc(t):
    if t in anc_cache: return anc_cache[t]
    s = {t}
    for p in parents[t]: s |= anc(p)
    anc_cache[t] = s; return s
sys.setrecursionlimit(10000)
terms = sorted(t for t in nodes if ROOT in anc(t))
idx = {t: i for i, t in enumerate(terms)}
# annotations
dis = {}; names = {}; frequent = set()
for line in open(src / "phenotype.hpoa"):
    if line.startswith("#") or line.startswith("database_id"): continue
    f = line.rstrip("\n").split("\t")
    if f[10] != "P" or f[3] not in idx: continue
    d = f[0]; names[d] = f[1]
    pos, neg = dis.setdefault(d, (set(), set()))
    (neg if f[2] == "NOT" else pos).add(f[3])
    fq = f[7].strip()
    hi = fq in ("HP:0040280", "HP:0040281")
    if "/" in fq:
        a_, b_ = fq.split("/"); hi = int(b_) > 0 and int(a_) / int(b_) >= 0.8
    elif fq.endswith("%"):
        hi = float(fq[:-1]) >= 80
    if hi and f[2] != "NOT":
        frequent.add((d, f[3]))
dids = sorted(d for d in dis if dis[d][0])
N = len(dids)
cnt = collections.Counter()
for d in dids:
    s = set()
    for t in dis[d][0]: s |= anc(t)
    cnt.update(s)
ic = np.array([math.log(N / cnt[t]) if cnt[t] else math.log(N) for t in terms], dtype=np.float32)
pa, pb = [], []
for t in terms:
    for a in anc(t):
        if a in idx: pa.append(idx[t]); pb.append(idx[a])
dd, dt, nd, nt, df = [], [], [], [], []
for k, d in enumerate(dids):
    for t in dis[d][0]: dd.append(k); dt.append(idx[t]); df.append((d, t) in frequent)
    for t in dis[d][1]: nd.append(k); nt.append(idx[t])
np.savez_compressed(out / "catalog.npz", ic=ic, anc_term=np.array(pa, np.int32), anc_of=np.array(pb, np.int32),
    dis_idx=np.array(dd, np.int32), dis_term=np.array(dt, np.int32), dis_freq=np.array(df, np.bool_), not_idx=np.array(nd, np.int32), not_term=np.array(nt, np.int32))
json.dump({"hpo_version": "2026-09-01", "hpoa_version": "2026-09-02", "terms": terms,
           "labels": [nodes[t][0] for t in terms], "synonyms": [nodes[t][1] for t in terms],
           "diseases": dids, "disease_names": [names[d] for d in dids]}, open(out / "terms.json", "w"), separators=(",", ":"))
print(len(terms), "terms", N, "diseases", len(dd), "annotations", len(pa), "anc pairs")
