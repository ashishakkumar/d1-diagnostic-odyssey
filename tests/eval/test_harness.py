"""Public-truth harness. Fixtures are synthetic. No store packet is committed."""

import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

import pytest

from d1_eval.__main__ import main
from d1_eval.harness import (
    DiseaseScore,
    TermOverlapScorer,
    calibration_curve,
    check_store_file,
    count_terms,
    degrade,
    gene_topk,
    holdout_from_counts,
    is_no_confident,
    load_cases,
    load_catalogue,
    load_orphanet_tsv,
    load_parents,
    load_pins,
    loo_catalogue,
    orphanet_from_mondo_nodes,
    parents_from_obo,
    present_hpo_ids,
    rank_diseases,
    results_document,
    results_markdown,
    run_eval,
    time_split,
    time_split_note,
    unique_orphanet,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "eval" / "fixtures"
PACKETS = FIXTURES / "packets"


def _run(cases, scorer, tied_at_best=10):
    pins = load_pins()
    return run_eval(
        cases,
        scorer,
        disease_ids=list(load_catalogue(FIXTURES / "catalogue.json")),
        mapping=load_orphanet_tsv(FIXTURES / "orphanet.tsv"),
        ks=pins.ks,
        tied_at_best=tied_at_best,
    )


def test_loader_builds_a_contract_case_from_a_frozen_packet() -> None:
    loaded = load_cases(PACKETS)
    by_id = {case.packet_id: case for case in loaded.cases}
    alpha = by_id["synthetic-alpha"]
    assert alpha.truth_disease_id == "SYN:ALPHA"
    assert alpha.truth_genes == ("SYN1",)
    assert present_hpo_ids(alpha) == ["HP:0001250", "HP:0001263", "HP:0001270"]
    assert "HP:0000118" not in present_hpo_ids(alpha)
    assert alpha.pipeline.evidence[0].source == "phenopacket-store"
    assert alpha.pipeline.evidence[0].version == "0.1.27"
    assert alpha.pipeline.lab_reported_variants[0].gene_symbol == "SYN1"
    assert loaded.skipped == 0


def test_loader_skips_a_file_that_is_not_a_phenopacket(tmp_path: Path) -> None:
    shutil.copy(PACKETS / "synthetic-alpha.json", tmp_path / "synthetic-alpha.json")
    (tmp_path / "bad.json").write_text('{"id": "not-a-phenopacket"}\n')
    loaded = load_cases(tmp_path)
    assert loaded.skipped == 1
    assert [case.packet_id for case in loaded.cases] == ["synthetic-alpha"]


def test_summary_gene_is_not_kept_as_truth(tmp_path: Path) -> None:
    archive = tmp_path / "store.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for path in sorted(PACKETS.glob("*.json")):
            handle.write(path, f"0.1.27/SYN/{path.name}")
        handle.write(FIXTURES / "summary.tsv", "0.1.27/phenopacket_store.summary.tsv")
    loaded = load_cases(archive)
    genes = {gene for case in loaded.cases for gene in case.truth_genes}
    assert "LEAKGENE" not in genes
    assert loaded.disease_ids == (
        "SYN:ALPHA",
        "SYN:BETA",
        "SYN:GAMMA",
        "SYN:DELTA",
    )


def test_degradation_makes_fewer_and_vaguer_terms() -> None:
    alpha = {case.packet_id: case for case in load_cases(PACKETS).cases}["synthetic-alpha"]
    parents = load_parents(FIXTURES / "parents.tsv")
    assert present_hpo_ids(degrade(alpha, "full", parents, 0.5)) == [
        "HP:0001250",
        "HP:0001263",
        "HP:0001270",
    ]
    assert present_hpo_ids(degrade(alpha, "fewer", parents, 0.5)) == [
        "HP:0001250",
        "HP:0001263",
    ]
    assert present_hpo_ids(degrade(alpha, "vaguer", parents, 0.5)) == [
        "HP:0001250",
        "HP:0000707",
    ]
    assert present_hpo_ids(degrade(alpha, "patient", parents, 0.5)) == [
        "HP:0001250",
        "HP:0000707",
    ]
    excluded = [
        term.hpo_id
        for term in degrade(alpha, "patient", parents, 0.5).pipeline.accepted_terms
        if term.presence == "excluded"
    ]
    assert excluded == ["HP:0000118"]


def test_unique_orphanet_count_is_the_printed_exclusion() -> None:
    mapping = load_orphanet_tsv(FIXTURES / "orphanet.tsv")
    unique, excluded = unique_orphanet(load_catalogue(FIXTURES / "catalogue.json"), mapping)
    assert unique == {"SYN:ALPHA", "SYN:BETA"}
    assert excluded == 2


def test_ties_take_the_worst_rank() -> None:
    ranks = rank_diseases(
        [
            DiseaseScore("A", 5),
            DiseaseScore("B", 5),
            DiseaseScore("C", 1),
        ]
    )
    assert ranks == {"A": 2, "B": 2, "C": 3}


def test_overlap_reports_top1_top3_and_top10() -> None:
    loaded = load_cases(PACKETS)
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    assert result.excluded_diseases == 2
    assert result.packets_scored == 3
    assert result.packets_not_unique == 1
    assert result.hits == {1: 2, 3: 2, 10: 2}
    assert result.no_confident == 1
    by_id = {row.packet_id: row for row in result.cases}
    assert by_id["synthetic-gamma"].rank is None
    assert by_id["synthetic-alpha"].rank == 1
    assert by_id["synthetic-none"].no_confident is True


def test_scorer_is_not_given_a_gene_or_an_excluded_disease() -> None:
    loaded = load_cases(PACKETS)
    seen: list[tuple[str, ...]] = []

    class Recording:
        def score(self, hpo_ids: list[str]) -> list[DiseaseScore]:
            seen.append(tuple(hpo_ids))
            return [
                DiseaseScore("SYN:GAMMA", 100),
                DiseaseScore("SYN:DELTA", 50),
                DiseaseScore("SYN:ALPHA", 1),
                DiseaseScore("SYN:BETA", 0),
            ]

    result = _run(loaded.cases, Recording())
    blob = " ".join(" ".join(call) for call in seen)
    assert "SYN1" not in blob
    assert "LEAKGENE" not in blob
    assert "HP:0000118" not in blob
    assert all(term.startswith("HP:") for call in seen for term in call)
    alpha = {row.packet_id: row for row in result.cases}["synthetic-alpha"]
    assert alpha.rank == 1


def test_score_rejects_a_gene_argument() -> None:
    scorer = TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json"))
    with pytest.raises(TypeError):
        scorer.score(["HP:0001250"], gene="SYN1")  # type: ignore[call-arg]


def test_decoy_gene_does_not_change_the_disease_rank(tmp_path: Path) -> None:
    raw = json.loads((PACKETS / "synthetic-alpha.json").read_text())
    decoy = json.loads(json.dumps(raw))
    decoy["id"] = "synthetic-alpha-decoy"
    genomic = decoy["interpretations"][0]["diagnosis"]["genomicInterpretations"][0]
    extra = json.loads(json.dumps(genomic))
    extra["variantInterpretation"]["variationDescriptor"]["id"] = "decoy-var"
    extra["variantInterpretation"]["variationDescriptor"]["geneContext"]["symbol"] = "DECOY9"
    decoy["interpretations"][0]["diagnosis"]["genomicInterpretations"].append(extra)
    (tmp_path / "synthetic-alpha.json").write_text(json.dumps(raw))
    (tmp_path / "synthetic-alpha-decoy.json").write_text(json.dumps(decoy))
    loaded = load_cases(tmp_path)
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    by_id = {row.packet_id: row for row in result.cases}
    assert by_id["synthetic-alpha"].rank == by_id["synthetic-alpha-decoy"].rank == 1
    genes = {case.packet_id: case.truth_genes for case in loaded.cases}
    assert genes["synthetic-alpha-decoy"] == ("SYN1", "DECOY9")


def test_gene_metric_is_evaluation_only(monkeypatch: pytest.MonkeyPatch) -> None:
    assert gene_topk(("SYN1",), ("OTHER", "SYN1"), 3) is True
    assert gene_topk(("SYN1",), ("OTHER",), 1) is False

    def boom(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("the disease runner called the gene metric")

    monkeypatch.setattr("d1_eval.harness.gene_topk", boom)
    loaded = load_cases(PACKETS)
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    assert all("gene" not in name for name in result.__dataclass_fields__)
    note = time_split_note(time_split(loaded.cases, date(2026, 6, 23)))
    text = results_markdown(result, load_pins(), "full", note)
    assert "gene_top" not in text
    assert "SYN1" not in text


def test_calibration_and_no_confident_rate() -> None:
    assert is_no_confident([DiseaseScore("A", 0), DiseaseScore("B", 0)], tied_at_best=10)
    assert is_no_confident(
        [DiseaseScore("A", 2), DiseaseScore("B", 2)],
        tied_at_best=2,
    )
    assert not is_no_confident(
        [DiseaseScore("A", 2), DiseaseScore("B", 2)],
        tied_at_best=10,
    )
    bins = calibration_curve([(3.0, True), (3.0, False), (1.0, True)])
    by_score = {item.score: item for item in bins}
    assert by_score[3.0].n == 2 and by_score[3.0].hits == 1
    assert by_score[1.0].n == 1 and by_score[1.0].hit_rate == 1.0
    loaded = load_cases(PACKETS)
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    assert result.no_confident_rate == pytest.approx(1 / 3)
    assert {row[0] for row in result.confident} == {2.0, 3.0}


def test_loo_catalogue_drops_the_query_case_terms() -> None:
    cases = load_cases(PACKETS).cases
    catalogue = loo_catalogue(cases, "synthetic-alpha", {"SYN:ALPHA", "SYN:BETA"})
    assert "HP:0001250" not in catalogue["SYN:ALPHA"]
    assert "HP:0009998" in catalogue["SYN:ALPHA"]
    assert catalogue["SYN:BETA"] == {"HP:0001250", "HP:0004322"}
    assert all(term.startswith("HP:") for terms in catalogue.values() for term in terms)
    shared = holdout_from_counts({"SYN:ALPHA": {"HP:0001250": 2}}, "SYN:ALPHA", {"HP:0001250"})
    assert shared["SYN:ALPHA"] == {"HP:0001250"}
    allowed = {"SYN:ALPHA", "SYN:BETA"}
    counts = count_terms(cases, allowed)
    for case in cases:
        held = holdout_from_counts(counts, case.truth_disease_id, set(present_hpo_ids(case)))
        assert held == loo_catalogue(cases, case.packet_id, allowed)


def test_time_split_counts_packet_dates_only() -> None:
    cases = load_cases(PACKETS).cases
    split = time_split(cases, date(2026, 6, 23))
    assert (split.before, split.after, split.undated) == (2, 1, 1)
    note = time_split_note(split)
    assert "not a publication date" in note
    assert "2026-06-23" in note
    assert "not a pass" in note


def test_held_out_split_uses_the_packet_id_and_prints_both_cohorts() -> None:
    from d1_eval.harness import cohort_split, held_out_lines

    assert cohort_split("synthetic-alpha") == cohort_split("synthetic-alpha")
    assert cohort_split("synthetic-alpha") in {"train", "test"}
    labels = {cohort_split(f"packet-{i}") for i in range(40)}
    assert labels == {"train", "test"}
    loaded = load_cases(PACKETS)
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    text = "\n".join(held_out_lines([("full", result)]))
    assert "Held-out split" in text
    assert "| train |" in text or "| full | train |" in text
    assert "test" in text
    assert "threshold" in text


def test_results_table_records_tool_and_data_versions() -> None:
    loaded = load_cases(PACKETS)
    pins = load_pins()
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    note = time_split_note(time_split(loaded.cases, pins.knowledge_cutoff))
    text = results_markdown(result, pins, "full", note)
    assert "0.1.27" in text
    assert pins.store_sha256 in text
    assert "v2026-10-06" in text
    assert "term-overlap" in text
    assert "2/3" in text
    assert "excluded_diseases" in text
    assert "| 2 |" in text or text.count("2") > 0


def test_results_document_can_name_the_frequency_scorer_version() -> None:
    loaded = load_cases(PACKETS)
    pins = load_pins()
    result = _run(loaded.cases, TermOverlapScorer(load_catalogue(FIXTURES / "catalogue.json")))
    note = time_split_note(time_split(loaded.cases, pins.knowledge_cutoff))
    text = results_document(
        [("full", result)],
        pins,
        note,
        tool="frequency-bin",
        tool_version="0.0.1",
    )
    assert "frequency-bin" in text
    assert "0.0.1" in text
    assert "0.0.0" not in text


def test_fixtures_command_prints_how_many_diseases_are_excluded(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "results.md"
    assert main(["fixtures", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "excluded_diseases=2" in printed
    assert "top1=" in printed
    text = out.read_text()
    assert "full" in text and "fewer" in text and "vaguer" in text and "patient" in text


def test_claims_file_limits_results_to_public_cases() -> None:
    text = (ROOT / "eval" / "CLAIMS.md").read_text()
    assert "Can claim" in text
    assert "Cannot claim" in text
    assert "real patient" in text
    assert "public" in text.lower()
    lowered = text.lower()
    assert "benefit" in lowered
    assert "not for use in diagnostic procedures" in lowered


def test_pin_matches_the_phenopacket_store_release() -> None:
    pins = load_pins()
    assert pins.store_version == "0.1.27"
    assert pins.store_bytes == 19431098
    assert pins.store_sha256 == "d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a"
    assert pins.store_doi == "10.5281/zenodo.20614899"
    assert pins.store_url.endswith("/0.1.27/all_phenopackets.zip")
    assert pins.mondo_version == "v2026-10-06"
    assert pins.ks == (1, 3, 10)
    assert pins.tied_at_best == 10
    assert pins.knowledge_cutoff == date(2026, 6, 23)


def test_mondo_nodes_keep_a_single_orphanet_id(tmp_path: Path) -> None:
    path = tmp_path / "nodes.tsv"
    path.write_text(
        "id\tcategory\tname\tdescription\txref\n"
        "MONDO:1\tbiolink:OntologyClass\tA\td\tOMIM:111111|Orphanet:1\n"
        "MONDO:2\tbiolink:OntologyClass\tB\td\tOMIM:222222|Orphanet:2|Orphanet:3\n"
        "MONDO:3\tbiolink:OntologyClass\tC\td\tOMIMPS:333333|Orphanet:4\n"
    )
    mapping = orphanet_from_mondo_nodes(path)
    unique, excluded = unique_orphanet(
        ["OMIM:111111", "OMIM:222222", "OMIM:333333", "OMIM:444444"],
        mapping,
    )
    assert mapping["OMIM:111111"] == {"ORPHA:1"}
    assert unique == {"OMIM:111111", "OMIM:333333"}
    assert excluded == 2


def test_obo_parent_is_the_first_is_a(tmp_path: Path) -> None:
    path = tmp_path / "hp.obo"
    path.write_text(
        "[Term]\n"
        "id: HP:0000707\n"
        "name: Abnormality of the nervous system\n"
        "\n"
        "[Term]\n"
        "id: HP:0001263\n"
        "name: Global developmental delay\n"
        "is_a: HP:0000707 ! Abnormality of the nervous system\n"
        "is_a: HP:0012759 ! Neurodevelopmental abnormality\n"
    )
    parents = parents_from_obo(path)
    assert parents["HP:0001263"] == ("HP:0000707", "Abnormality of the nervous system")


def test_store_check_rejects_the_wrong_file(tmp_path: Path) -> None:
    bad = tmp_path / "all_phenopackets.zip"
    bad.write_bytes(b"not the store")
    with pytest.raises(SystemExit):
        check_store_file(bad, load_pins())
