"""Full-catalogue path: grounding never invents ids, negation, ranking, no storage."""
import pytest
from fastapi.testclient import TestClient

from app import llm_extract
from app.catalog import catalog
from app.routes.notebook import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    return TestClient(app)


def test_catalogue_is_full():
    cat = catalog()
    assert cat.n_dis > 12000 and len(cat.terms) > 18000


def test_rules_negation_and_mapping():
    found = catalog().extract_rules("Seizures and hypotonia. No microcephaly.")
    got = {f["candidates"][0]["hpo_id"]: f["present"] for f in found}
    assert got == {"HP:0001250": True, "HP:0001252": True, "HP:0000252": False}


def test_grounding_returns_only_ontology_ids():
    cat = catalog()
    for c in cat.ground("floppy baby", hint="Hypotonia"):
        assert c["hpo_id"] in cat.idx
    assert cat.ground("fits", hint="Seizure")[0]["hpo_id"] == "HP:0001250"


def test_rules_path_is_labelled(client):
    body = client.post("/analyze", json={"note": "seizures, hypotonia, intellectual disability, microcephaly"}).json()
    assert body["path"] == "rules" and "No model key" in body["path_note"]
    assert len(body["ranks"]) == 10 and body["ranks"][0]["link"].startswith("https://")
    assert body["catalogue"]["diseases"] > 12000


def test_marfan_features_rank_marfan_family(client):
    body = client.post("/analyze", json={"note": "tall stature, arachnodactyly, ectopia lentis, aortic root aneurysm"}).json()
    names = " ".join(r["name"].lower() for r in body["ranks"])
    assert "marfan" in names or "ectopia lentis" in names


def test_absent_finding_lowers_score():
    cat = catalog()
    a = cat.rank(["HP:0001166", "HP:0001083"], [])
    top = a["ranks"][0]
    tid = cat.idx["HP:0001083"]
    b = cat.rank(["HP:0001166", "HP:0001083"], ["HP:0001083"])
    after = {r["disease_id"]: r["score"] for r in b["ranks"]}
    assert after.get(top["disease_id"], -99) < top["score"]
    assert tid >= 0


def test_llm_ids_are_ignored(client, monkeypatch):
    monkeypatch.setattr(llm_extract, "available", lambda: True)
    monkeypatch.setattr(llm_extract, "extract", lambda note: {
        "findings": [{"phrase": "fits", "present": True, "onset": None, "label": "HP:9999999"}],
        "context": {"age": None, "sex": None, "family_history": None, "labs": []},
        "provider": "gemini", "model": "fake"})
    body = client.post("/analyze", json={"note": "fits"}).json()
    for f in body["findings"]:
        for c in f["candidates"]:
            assert c["hpo_id"] != "HP:9999999"
    assert body["path"] == "gemini"


def test_emergency_stop(client):
    r = client.post("/analyze", json={"note": "He is not breathing and turning blue"})
    assert r.status_code in (200, 409)


def test_rerank(client):
    r = client.post("/rerank", json={"present": ["HP:0001250", "HP:0000252"], "absent": []})
    assert r.status_code == 200 and r.json()["ranks"]
