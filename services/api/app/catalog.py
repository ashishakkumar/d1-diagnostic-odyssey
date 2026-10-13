"""Full-catalogue reading: extract findings, ground them to real HPO ids, rank diseases.

Data: HPO release v2026-09-01 (hp.json) and phenotype.hpoa 2026-09-02, precomputed by
scripts/build_hpo_index.py. Ranking is Resnik best-match average with information content
from the annotations, minus a penalty for findings the note says are absent.
Nothing here stores the note. Research prototype, not a diagnosis.
"""

from __future__ import annotations

import difflib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

ABSENT_WEIGHT = 0.05  # set on the train split only, see eval/full_catalogue
DATA = Path(__file__).resolve().parent / "data" / "hpo"
_NEG_CUES = re.compile(
    r"\b(no|not|denies|denied|without|negative for|absence of|absent|free of|never had|rules? out)\b",
    re.I,
)
_SCOPE_END = re.compile(r"[.;:,\n]|\b(but|however|although|except|and has|with)\b", re.I)
_STOP = {"of", "the", "a", "an", "and", "in", "with", "to", "on", "at", "for", "is", "was", "has"}


def norm(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for w in words:
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss") and not w.endswith("us"):
            w = w[:-1]
        out.append(w)
    return " ".join(out)


class Catalog:
    def __init__(self) -> None:
        meta = json.loads((DATA / "terms.json").read_text())
        arr = np.load(DATA / "catalog.npz")
        self.version = meta["hpo_version"]
        self.terms: list[str] = meta["terms"]
        self.labels: list[str] = meta["labels"]
        self.synonyms: list[list[str]] = meta["synonyms"]
        self.diseases: list[str] = meta["diseases"]
        self.names: list[str] = meta["disease_names"]
        self.idx = {t: i for i, t in enumerate(self.terms)}
        self.ic = arr["ic"]
        self.anc_term, self.anc_of = arr["anc_term"], arr["anc_of"]
        self.dis_idx, self.dis_term = arr["dis_idx"], arr["dis_term"]
        self.dis_freq = arr["dis_freq"]
        self.not_idx, self.not_term = arr["not_idx"], arr["not_term"]
        self.n_dis = len(self.diseases)
        self.dis_len = np.bincount(self.dis_idx, minlength=self.n_dis).astype(np.float32)
        order = np.argsort(self.anc_term, kind="stable")
        self.anc_term, self.anc_of = self.anc_term[order], self.anc_of[order]
        bounds = np.searchsorted(self.anc_term, np.arange(len(self.terms) + 1))
        self.ancestors = [set(self.anc_of[bounds[i]:bounds[i + 1]].tolist()) for i in range(len(self.terms))]
        self.lex: dict[str, int] = {}
        for i, (label, syns) in enumerate(zip(self.labels, self.synonyms)):
            for s in [label, *syns]:
                key = norm(s)
                if key and (key not in self.lex or self.ic[i] > self.ic[self.lex[key]] and s == label):
                    self.lex.setdefault(key, i)
        self.max_len = 8
        self.single_keys = [k for k in self.lex if " " not in k and len(k) >= 6]
        dis_terms: list[list[int]] = [[] for _ in range(self.n_dis)]
        for d, t in zip(self.dis_idx.tolist(), self.dis_term.tolist()):
            dis_terms[d].append(t)
        self.dis_terms = dis_terms
        self._embed = None

    # ---------- grounding ----------
    def embedder(self):
        """potion-base-8M static embeddings (MIT): mean of token vectors, then L2 norm."""
        if self._embed is None:
            try:
                from tokenizers import Tokenizer

                tok = Tokenizer.from_file(str(DATA / "potion_tokenizer.json"))
                table = np.load(DATA / "potion_vectors.npy").astype(np.float32)
                e = np.load(DATA / "embed.npz")

                def encode(texts: list[str]) -> np.ndarray:
                    rows = []
                    for enc in tok.encode_batch(texts, add_special_tokens=False):
                        ids = enc.ids or [0]
                        rows.append(table[ids].mean(axis=0))
                    return np.stack(rows)

                self._embed = (encode, e["q"].astype(np.float32) / 127.0, e["owner"])
            except Exception:  # noqa: BLE001
                self._embed = False
        return self._embed

    def ground(self, phrase: str, hint: str | None = None, k: int = 3) -> list[dict]:
        """Candidate HPO terms for a phrase. Only ids from the loaded ontology come back."""
        found: dict[int, tuple[float, str]] = {}
        for text in [t for t in (hint, phrase) if t]:
            key = norm(text)
            if key in self.lex:
                found[self.lex[key]] = (1.0, "exact")
        emb = self.embedder()
        if emb:
            model, vecs, owner = emb
            q = model([t for t in (hint, phrase) if t]).astype(np.float32)
            q /= np.linalg.norm(q, axis=1, keepdims=True) + 1e-9
            sims = (vecs @ q.T).max(axis=1)
            for j in np.argsort(-sims)[: 3 * k]:
                t = int(owner[j]); s = float(sims[j])
                if t not in found or found[t][0] < min(s, 0.99):
                    found[t] = (min(s, 0.99), "semantic")
        key = norm(phrase)
        if " " not in key and len(key) >= 6:
            for m in difflib.get_close_matches(key, self.single_keys, n=2, cutoff=0.85):
                t = self.lex[m]
                score = 0.9 * difflib.SequenceMatcher(None, key, m).ratio()
                if t not in found or found[t][0] < score:
                    found[t] = (score, "fuzzy")
        best = sorted(found.items(), key=lambda kv: -kv[1][0])[:k]
        return [
            {"hpo_id": self.terms[t], "label": self.labels[t], "score": round(s, 3), "how": how}
            for t, (s, how) in best
        ]

    # ---------- deterministic extraction ----------
    def extract_rules(self, note: str) -> list[dict]:
        """Longest exact match of HPO labels and synonyms, with simple negation scope."""
        tokens = [(m.group(), m.start(), m.end()) for m in re.finditer(r"[A-Za-z0-9]+", note)]
        normed = [norm(t[0]) for t in tokens]
        out, i, seen = [], 0, set()
        while i < len(tokens):
            hit = None
            for n in range(min(self.max_len, len(tokens) - i), 0, -1):
                key = " ".join(w for w in normed[i:i + n])
                if n == 1 and (key in _STOP or len(key) < 4):
                    continue
                if key in self.lex:
                    hit = (n, self.lex[key]); break
            if hit is None:
                i += 1; continue
            n, t = hit
            start, end = tokens[i][1], tokens[i + n - 1][2]
            if self.terms[t] not in seen:
                seen.add(self.terms[t])
                out.append({
                    "phrase": note[start:end], "start": start, "end": end,
                    "present": not _negated(note, start),
                    "candidates": [{"hpo_id": self.terms[t], "label": self.labels[t], "score": 1.0, "how": "exact"}],
                })
            i += n
        return out

    # ---------- ranking ----------
    def _sim_to_all(self, t: int) -> np.ndarray:
        v = np.zeros(len(self.terms), np.float32)
        anc = np.fromiter(self.ancestors[t], np.int32)
        v[anc] = self.ic[anc]
        out = np.zeros(len(self.terms), np.float32)
        np.maximum.at(out, self.anc_term, v[self.anc_of])
        return out

    def scores(self, p: list[int], a: list[int]):
        """Resnik BMA per disease, minus ABSENT_WEIGHT x mean IC of absent findings it lists as frequent (>=80%)."""
        sims = np.stack([self._sim_to_all(t) for t in p])  # Q x T
        pair = sims[:, self.dis_term]  # Q x A
        best_q = np.zeros((len(p), self.n_dis), np.float32)
        for qi in range(len(p)):
            np.maximum.at(best_q[qi], self.dis_idx, pair[qi])
        left = best_q.mean(axis=0)
        right = np.zeros(self.n_dis, np.float32)
        np.add.at(right, self.dis_idx, pair.max(axis=0))
        right /= np.maximum(self.dis_len, 1)
        score = 0.5 * (left + right)
        penalty = np.zeros(self.n_dis, np.float32)
        for t in a:
            s = self._sim_to_all(t)[self.dis_term]
            has = np.zeros(self.n_dis, np.float32)
            listed = (s >= self.ic[t] - 1e-6) & self.dis_freq
            np.maximum.at(has, self.dis_idx, listed.astype(np.float32))
            penalty += has * self.ic[t]
        if a:
            score = score - ABSENT_WEIGHT * penalty / len(a)
        return sims, best_q, score

    def rank(self, present: list[str], absent: list[str], top: int = 10) -> dict:
        p = [self.idx[x] for x in dict.fromkeys(present) if x in self.idx]
        a = [self.idx[x] for x in dict.fromkeys(absent) if x in self.idx]
        if not p:
            return {"ranks": [], "abstained": True, "reason": "No present finding was grounded to an HPO term."}
        sims, best_q, score = self.scores(p, a)
        order = np.argsort(-score, kind="stable")[: max(top, 10)]
        best = float(score[order[0]])
        second = float(score[order[1]])
        weak = len(p) < 2 or best < 1.5 or (best - second) < 1e-6
        ranks = []
        for d in order[:top]:
            d = int(d)
            ev = []
            for qi, t in enumerate(p):
                val = float(best_q[qi, d])
                if val <= 0.5:
                    continue
                dt = self.dis_terms[d]
                m = max(dt, key=lambda x: sims[qi, x])
                ev.append({"query": self.labels[t], "query_id": self.terms[t], "disease_term": self.labels[m],
                           "disease_term_id": self.terms[m], "ic": round(val, 2),
                           "exact": m == t})
            against = [self.labels[t] for t in a if any(t in self.ancestors[x] for x in self.dis_terms[d])]
            ranks.append({"disease_id": self.diseases[d], "name": self.names[d], "score": round(float(score[d]), 3),
                          "bar": round(max(float(score[d]), 0) / best, 3) if best > 0 else 0.0,
                          "evidence": ev, "against": against, "link": disease_link(self.diseases[d])})
        return {"ranks": ranks, "abstained": bool(weak),
                "reason": ("Weak signal: fewer than two findings, a low top score, or a tie. "
                           "Treat this list as unordered.") if weak else None,
                "discriminators": self.discriminators([int(d) for d in order[:5]], set(p) | set(a))}

    def discriminators(self, top: list[int], asked: set[int], k: int = 5) -> list[dict]:
        """Findings listed by some but not all top candidates, weighted by rarity."""
        counts: dict[int, list[int]] = {}
        known = set()
        for t in asked:
            known |= self.ancestors[t]
        for d in top:
            for t in set(self.dis_terms[d]):
                if t in known:
                    continue
                counts.setdefault(t, []).append(d)
        n = len(top)
        scored = []
        for t, ds in counts.items():
            if 0 < len(ds) < n:
                balance = 1 - abs(len(ds) / n - 0.5) * 2
                scored.append((self.ic[t] * (0.5 + balance), t, ds))
        scored.sort(key=lambda x: -x[0])
        out, used = [], set()
        for _s, t, ds in scored:
            if any(t in self.ancestors[u] or u in self.ancestors[t] for u in used):
                continue
            used.add(t)
            out.append({"hpo_id": self.terms[t], "label": self.labels[t],
                        "seen_in": [self.names[d] for d in ds]})
            if len(out) == k:
                break
        return out


def disease_link(disease_id: str) -> str:
    db, _, num = disease_id.partition(":")
    if db == "OMIM":
        return f"https://omim.org/entry/{num}"
    if db == "ORPHA":
        return f"https://www.orpha.net/en/disease/detail/{num}"
    if db == "DECIPHER":
        return f"https://www.deciphergenomics.org/syndrome/{num}"
    return f"https://hpo.jax.org/browse/disease/{disease_id}"


def _negated(note: str, start: int) -> bool:
    window = note[max(0, start - 60):start]
    cut = list(_SCOPE_END.finditer(window))
    if cut:
        window = window[cut[-1].end():]
    return bool(_NEG_CUES.search(window))


@lru_cache(maxsize=1)
def catalog() -> Catalog:
    return Catalog()
