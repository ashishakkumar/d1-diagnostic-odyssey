import inspect
import json
from pathlib import Path

import phenopackets.schema.v2 as pps2
import pytest
from google.protobuf.json_format import MessageToDict
from scoring.catalogue import BACKGROUND_PRIOR, CLOSE_DISEASE_COUNT, CLOSE_FACTOR

from app.routes.ports import report_for
from d1_contracts import EvidenceRow
from scoring import (
    GeneFit,
    catalogue_score,
    gene_fit,
    hpo_from_phenopacket,
    suggest_questions,
    to_public,
)

FIXTURES = Path(__file__).parent / "fixtures"
# Leave-one-out rate is (k + 1) / (n + 2) on the two fixture disorders.
# HP:0001166 is listed on both, so p = 2/3 and an obligate ratio is 1.5.
# HP:0000272 is excluded on ORPHA:9000002, so for ORPHA:9000001 p = 1/3.
# Very frequent 0.80 and 0.99 become 2.4 and 2.97. Products: 3.6 and 4.455.
# ORPHA:9000002's excluded bin still makes the product 0.


def frequency_rows() -> list[dict]:
    return json.loads((FIXTURES / "frequencies.json").read_text())


def frequency_row(n: int, orphanet: str, mondo: str, hpo_id: str, bin_name: str) -> dict:
    return {
        "id": f"00000000-0000-4000-8000-{n:012d}",
        "source": "orphanet-en_product4",
        "version": "2026-06-23-synthetic",
        "subject_key": f"{orphanet}|{hpo_id}",
        "orphanet_id": orphanet,
        "mondo_id": mondo,
        "hpo_id": hpo_id,
        "bin": bin_name,
    }


def test_frequency_bounds_score_each_disease_and_keep_term_evidence() -> None:
    rows = frequency_rows()
    for row in rows:
        EvidenceRow.model_validate(
            {key: row[key] for key in ("id", "source", "version", "subject_key")}
        )

    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        rows,
    )

    by_id = {disease.orphanet_id: disease for disease in report.diseases}
    assert set(by_id) == {"ORPHA:9000001", "ORPHA:9000002"}
    leader = by_id["ORPHA:9000001"]
    other = by_id["ORPHA:9000002"]
    assert leader.mondo_id == "MONDO:8000001"
    assert leader.lower_ratio == pytest.approx(3.6)
    assert leader.upper_ratio == pytest.approx(4.455)
    assert other.lower_ratio == pytest.approx(0)
    assert other.upper_ratio == pytest.approx(0)
    assert report.diseases[0].orphanet_id == "ORPHA:9000001"

    leader_terms = {term.hpo_id: term for term in leader.terms}
    arachnodactyly = leader_terms["HP:0001166"]
    assert arachnodactyly.relation == "supports"
    assert arachnodactyly.source == "orphanet-en_product4"
    assert arachnodactyly.version == "2026-06-23-synthetic"
    assert arachnodactyly.lower_ratio == pytest.approx(1.5)
    assert arachnodactyly.upper_ratio == pytest.approx(1.5)
    assert arachnodactyly.background == pytest.approx(2 / 3)
    malar = leader_terms["HP:0000272"]
    assert malar.relation == "supports"
    assert malar.source == "orphanet-en_product4"
    assert malar.version == "2026-06-23-synthetic"
    assert malar.lower_ratio == pytest.approx(2.4)
    assert malar.upper_ratio == pytest.approx(2.97)
    assert malar.background == pytest.approx(1 / 3)

    other_terms = {term.hpo_id: term for term in other.terms}
    assert other_terms["HP:0001166"].relation == "supports"
    assert other_terms["HP:0000272"].relation == "does_not_support"
    assert other_terms["HP:0000272"].source == "orphanet-en_product4"
    assert other_terms["HP:0000272"].version == "2026-06-23-synthetic"


def test_a_term_missing_from_the_disease_does_not_support_it() -> None:
    # HP:0001251 is on neither disorder, so p = 1/3 and the ratio is 1.
    report = catalogue_score(
        [
            ("HP:0001166", "present"),
            ("HP:0000272", "present"),
            ("HP:0001251", "present"),
        ],
        frequency_rows(),
    )
    leader = report.diseases[0]
    assert leader.orphanet_id == "ORPHA:9000001"
    assert leader.lower_ratio == pytest.approx(3.6)
    assert leader.upper_ratio == pytest.approx(4.455)
    missing = {term.hpo_id: term for term in leader.terms}["HP:0001251"]
    assert missing.relation == "does_not_support"
    assert missing.source == "orphanet-en_product4"
    assert missing.version == "2026-06-23-synthetic"
    assert missing.lower_ratio == pytest.approx(1)
    assert missing.upper_ratio == pytest.approx(1)
    assert missing.background == pytest.approx(1 / 3)


def test_an_excluded_term_supports_only_an_excluded_bin() -> None:
    # Patient excludes HP:0000272. Ratio is (1 - bound) / (1 - p).
    # ORPHA:9000001 very frequent, p = 1/3: (1-0.80)/(2/3) and (1-0.99)/(2/3).
    # Present obligate uses p = 2/3, ratio 1.5.
    # ORPHA:9000002 excluded bin, p = 2/3: (1-0)/(1/3) = 3.
    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "excluded")],
        frequency_rows(),
    )
    by_id = {disease.orphanet_id: disease for disease in report.diseases}
    listed = {term.hpo_id: term for term in by_id["ORPHA:9000001"].terms}["HP:0000272"]
    excluded_bin = {term.hpo_id: term for term in by_id["ORPHA:9000002"].terms}["HP:0000272"]
    assert listed.relation == "does_not_support"
    assert listed.lower_ratio == pytest.approx(0.3)
    assert listed.upper_ratio == pytest.approx(0.015)
    assert by_id["ORPHA:9000001"].lower_ratio == pytest.approx(0.45)
    assert excluded_bin.relation == "supports"
    assert excluded_bin.lower_ratio == pytest.approx(3)
    assert by_id["ORPHA:9000002"].lower_ratio == pytest.approx(0.045)


def test_abstain_thresholds_stay_at_the_plan_values() -> None:
    assert CLOSE_DISEASE_COUNT == 10
    assert CLOSE_FACTOR == 2
    assert BACKGROUND_PRIOR == 1


def test_ten_diseases_within_a_factor_of_two_are_not_confident() -> None:
    rows = [
        frequency_row(
            300 + i,
            f"ORPHA:9000{101 + i}",
            f"MONDO:8000{101 + i}",
            "HP:0001166",
            "obligate",
        )
        for i in range(10)
    ]
    report = catalogue_score([("HP:0001166", "present")], rows)
    assert report.confident is False
    assert report.abstain_reason == "many_within_factor"
    assert report.leading_orphanet_id is None


def test_top_disease_flips_between_bin_bounds() -> None:
    # Both disorders list both terms, so p = 2/3.
    # Lower products: 1.5 * 0.015 = 0.0225, and 0.075 ** 2 = 0.005625.
    # Upper products: 1.5 * 0.06 = 0.09, and 0.435 ** 2 = 0.189225.
    rows = [
        frequency_row(401, "ORPHA:9000021", "MONDO:8000021", "HP:0001166", "obligate"),
        frequency_row(402, "ORPHA:9000021", "MONDO:8000021", "HP:0000272", "very_rare"),
        frequency_row(403, "ORPHA:9000022", "MONDO:8000022", "HP:0001166", "occasional"),
        frequency_row(404, "ORPHA:9000022", "MONDO:8000022", "HP:0000272", "occasional"),
    ]
    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        rows,
    )
    by_id = {disease.orphanet_id: disease for disease in report.diseases}
    assert by_id["ORPHA:9000021"].lower_ratio == pytest.approx(0.0225)
    assert by_id["ORPHA:9000022"].lower_ratio == pytest.approx(0.005625)
    assert by_id["ORPHA:9000021"].upper_ratio == pytest.approx(0.09)
    assert by_id["ORPHA:9000022"].upper_ratio == pytest.approx(0.189225)
    assert report.confident is False
    assert report.abstain_reason == "top_flips_between_bounds"
    assert report.leading_orphanet_id is None


def test_a_tie_for_first_is_not_confident() -> None:
    rows = [
        frequency_row(501, "ORPHA:9000031", "MONDO:8000031", "HP:0001166", "obligate"),
        frequency_row(502, "ORPHA:9000032", "MONDO:8000032", "HP:0001166", "obligate"),
    ]
    report = catalogue_score([("HP:0001166", "present")], rows)
    assert report.confident is False
    assert report.abstain_reason == "tied_for_first"
    assert report.margin == pytest.approx(1)


def test_a_zero_runner_up_states_the_excluded_term() -> None:
    """A lower ratio of 0 is not a blank margin. The report names the excluded term."""
    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        frequency_rows(),
    )
    public = to_public(report)
    runner_up = report.diseases[1]
    assert runner_up.orphanet_id == "ORPHA:9000002"
    assert runner_up.lower_ratio == pytest.approx(0)
    assert public["margin"] is None
    fact = public["margin_fact"]
    assert "runner-up" in fact
    assert "excluded term" in fact
    assert "ORPHA:9000002" in fact
    assert "HP:0000272" in fact
    assert public["margin"] is not None or public["margin_fact"]


def test_a_zero_from_an_obligate_bin_is_not_called_an_excluded_term() -> None:
    rows = [
        frequency_row(901, "ORPHA:9000091", "MONDO:8000091", "HP:0001166", "obligate"),
        frequency_row(902, "ORPHA:9000092", "MONDO:8000092", "HP:0001166", "very_rare"),
    ]
    report = catalogue_score([("HP:0001166", "excluded")], rows)
    public = to_public(report)
    assert report.diseases[1].orphanet_id == "ORPHA:9000091"
    assert report.diseases[1].lower_ratio == pytest.approx(0)
    fact = public["margin_fact"]
    assert "obligate" in fact
    assert "HP:0001166" in fact
    assert "excluded term" not in fact


def test_the_notebook_report_names_the_excluded_term() -> None:
    body = report_for([("HP:0001166", "present"), ("HP:0000272", "present")])
    assert body["margin"] is None
    assert "excluded term" in body["margin_fact"]
    assert "HP:0000272" in body["margin_fact"]


def test_background_is_the_leave_one_out_corpus_frequency() -> None:
    """P(feature | not this disease) is (k + 1) / (n + 2), not a fixed 0.05 or 0.01."""
    report = catalogue_score([("HP:0001166", "present")], frequency_rows())
    leader = next(disease for disease in report.diseases if disease.orphanet_id == "ORPHA:9000001")
    term = next(item for item in leader.terms if item.hpo_id == "HP:0001166")
    # The other disease lists HP:0001166 outside the excluded bin. n = 1, k = 1.
    assert term.background == pytest.approx(2 / 3)
    assert term.lower_ratio == pytest.approx(1.0 / (2 / 3))
    assert term.upper_ratio == pytest.approx(1.0 / (2 / 3))
    assert "(k + 1) / (n + 2)" in to_public(report)["evidence"]["background_rule"]


def test_a_missing_row_uses_the_corpus_frequency_not_a_fixed_stand_in() -> None:
    """No row means the disease rate is the corpus rate, so the ratio is 1."""
    report = catalogue_score([("HP:0001251", "present")], frequency_rows())
    term = report.diseases[0].terms[0]
    # Neither disease lists HP:0001251. n = 1, k = 0, so the rate is 1/3.
    assert term.background == pytest.approx(1 / 3)
    assert term.lower_ratio == pytest.approx(1)
    assert term.upper_ratio == pytest.approx(1)
    assert term.relation == "does_not_support"


def test_a_separated_leader_keeps_a_margin() -> None:
    # Leader 20 * 20 = 400. Nine others 0.2 * 0.2 = 0.04, which is not within a factor of 2.
    rows = [
        frequency_row(601, "ORPHA:9000040", "MONDO:8000040", "HP:0001166", "obligate"),
        frequency_row(602, "ORPHA:9000040", "MONDO:8000040", "HP:0000272", "obligate"),
    ]
    for i in range(9):
        rows.append(
            frequency_row(
                610 + i,
                f"ORPHA:900004{i + 1}",
                f"MONDO:800004{i + 1}",
                "HP:0001166",
                "very_rare",
            )
        )
        rows.append(
            frequency_row(
                620 + i,
                f"ORPHA:900004{i + 1}",
                f"MONDO:800004{i + 1}",
                "HP:0000272",
                "very_rare",
            )
        )
    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        rows,
    )
    assert report.confident is True
    assert report.abstain_reason is None
    assert report.leading_orphanet_id == "ORPHA:9000040"
    assert report.margin == pytest.approx(400 / 0.04)


def test_a_disease_with_two_mondo_ids_is_left_out() -> None:
    rows = frequency_rows()
    rows.append(frequency_row(701, "ORPHA:9000051", "MONDO:8000051", "HP:0001166", "obligate"))
    rows.append(frequency_row(702, "ORPHA:9000051", "MONDO:8000052", "HP:0000272", "obligate"))
    report = catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        rows,
    )
    assert {disease.orphanet_id for disease in report.diseases} == {
        "ORPHA:9000001",
        "ORPHA:9000002",
    }
    assert report.excluded_disease_count == 1


def test_two_orphanets_on_one_mondo_are_left_out() -> None:
    rows = [
        frequency_row(801, "ORPHA:9000061", "MONDO:8000061", "HP:0001166", "obligate"),
        frequency_row(802, "ORPHA:9000062", "MONDO:8000061", "HP:0001166", "very_rare"),
        frequency_row(803, "ORPHA:9000063", "MONDO:8000063", "HP:0001166", "obligate"),
    ]
    report = catalogue_score([("HP:0001166", "present")], rows)
    assert {disease.orphanet_id for disease in report.diseases} == {"ORPHA:9000063"}
    assert report.excluded_disease_count == 2


def test_questions_stay_off_unless_asked() -> None:
    assert suggest_questions(["HP:0001166"], frequency_rows()) == []


def test_nonspecific_terms_are_never_suggested() -> None:
    rows = frequency_rows()
    for n, hpo_id in enumerate(
        ("HP:0001249", "HP:0001250", "HP:0001256", "HP:0002197"),
        start=901,
    ):
        rows.append(frequency_row(n, "ORPHA:9000001", "MONDO:8000001", hpo_id, "occasional"))
    suggested = suggest_questions(
        ["HP:0001166"],
        rows,
        enabled=True,
        ontology_path=FIXTURES / "nonspecific.obo",
    )
    assert suggested == ["HP:0000272"]


def gene_rows() -> list[dict]:
    return json.loads((FIXTURES / "gene_hpo.json").read_text())


def test_gene_fit_states_which_accepted_terms_the_gene_explains() -> None:
    associations = gene_rows()
    for row in associations:
        EvidenceRow.model_validate(
            {key: row[key] for key in ("id", "source", "version", "subject_key")}
        )
    accepted = [("HP:0001166", "present"), ("HP:0000272", "present")]
    before = catalogue_score(accepted, frequency_rows())
    fit = gene_fit(["HP:0001166", "HP:0000272"], "SYN1", associations)
    after = catalogue_score(accepted, frequency_rows())
    assert fit.explained_hpo_ids == ["HP:0001166"]
    assert fit.unexplained_hpo_ids == ["HP:0000272"]
    assert [item.model_dump() for item in fit.sources] == [
        {"source": "synthetic-gene-hpo", "version": "fixture-1"}
    ]
    assert "lower_ratio" not in GeneFit.model_fields
    assert before.model_dump() == after.model_dump()


def _scored():
    return catalogue_score(
        [("HP:0001166", "present"), ("HP:0000272", "present")],
        frequency_rows(),
    )


def test_without_a_reliability_curve_the_output_is_evidence_and_margin() -> None:
    public = to_public(_scored(), probability=0.4)
    assert set(public) == {"evidence", "margin", "margin_fact"}
    assert "excluded term" in public["margin_fact"]
    assert "probability" not in json.dumps(public)
    term = public["evidence"]["terms"][0]
    assert term["source"] == "orphanet-en_product4"
    assert term["version"] == "2026-06-23-synthetic"
    assert "relation" in term


def test_a_probability_appears_only_beside_its_reliability_curve() -> None:
    curve = [
        {"predicted": 0.2, "observed": 0.1},
        {"predicted": 0.8, "observed": 0.75},
    ]
    public = to_public(_scored(), probability=0.4, reliability_curve=curve)
    assert public["probability"] == 0.4
    assert public["reliability_curve"] == curve
    assert set(public) == {"evidence", "margin", "margin_fact", "probability", "reliability_curve"}


def test_a_short_or_out_of_range_curve_does_not_unlock_a_probability() -> None:
    report = _scored()
    one_point = to_public(
        report,
        probability=0.4,
        reliability_curve=[{"predicted": 0.5, "observed": 0.5}],
    )
    out_of_range = to_public(
        report,
        probability=0.4,
        reliability_curve=[
            {"predicted": 1.2, "observed": 0.4},
            {"predicted": 0.2, "observed": 0.1},
        ],
    )
    assert set(one_point) == {"evidence", "margin", "margin_fact"}
    assert set(out_of_range) == {"evidence", "margin", "margin_fact"}


def test_public_questions_drop_nonspecific_terms() -> None:
    public = to_public(
        _scored(),
        questions=["HP:0000272", "HP:0001250", "HP:0001256"],
        ontology_path=FIXTURES / "nonspecific.obo",
    )
    assert public["evidence"]["questions"] == ["HP:0000272"]


def test_public_output_does_not_use_forbidden_words() -> None:
    public = to_public(_scored(), questions=["HP:0000272"])
    assert public["evidence"]["terms"]
    blob = json.dumps(public).casefold()
    for word in ("diagnosis", "pathogenic", "benign"):
        assert word not in blob


def test_clinvar_rows_make_a_zero_score_diff() -> None:
    accepted = [("HP:0001166", "present"), ("HP:0000272", "present")]
    base = catalogue_score(accepted, frequency_rows())
    poisoned = [
        *frequency_rows(),
        {
            "id": "00000000-0000-4000-8000-000000000961",
            "source": "ClinVar",
            "version": "2026-10-01",
            "subject_key": "VCV000000001",
        },
        {
            "id": "00000000-0000-4000-8000-000000000962",
            "source": "ClinVar",
            "version": "2026-10-01",
            "subject_key": "VCV000000002",
            "orphanet_id": "ORPHA:9000001",
            "mondo_id": "MONDO:8000001",
            "hpo_id": "HP:0001166",
            "bin": "excluded",
            "note": "pathogenic",
        },
    ]
    other = catalogue_score(accepted, poisoned)
    diff = 0.0
    for left, right in zip(base.diseases, other.diseases, strict=True):
        diff += abs(left.lower_ratio - right.lower_ratio)
        diff += abs(left.upper_ratio - right.upper_ratio)
    assert diff == 0
    blob = json.dumps(to_public(other)).casefold()
    for word in ("diagnosis", "pathogenic", "benign"):
        assert word not in blob


def _packet(*, with_gene: bool) -> dict:
    packet = pps2.Phenopacket(
        id="synthetic-score-1",
        subject=pps2.Individual(id="synthetic-subject"),
        phenotypic_features=[
            pps2.PhenotypicFeature(
                type=pps2.OntologyClass(id="HP:0001166", label="Arachnodactyly")
            ),
            pps2.PhenotypicFeature(
                type=pps2.OntologyClass(id="HP:0000272", label="Malar flattening")
            ),
        ],
        meta_data=pps2.MetaData(
            created_by="synthetic-fixture",
            phenopacket_schema_version="2.0.2",
        ),
    )
    if with_gene:
        packet.interpretations.append(
            pps2.Interpretation(
                id="synthetic-interp",
                diagnosis=pps2.Diagnosis(
                    genomic_interpretations=[
                        pps2.GenomicInterpretation(
                            subject_or_biosample_id="synthetic-subject",
                            gene=pps2.GeneDescriptor(value_id="HGNC:1", symbol="SYN1"),
                        )
                    ]
                ),
            )
        )
    return MessageToDict(packet)


def test_a_gene_on_the_phenopacket_does_not_change_the_score() -> None:
    plain = hpo_from_phenopacket(_packet(with_gene=False))
    with_gene = hpo_from_phenopacket(_packet(with_gene=True))
    assert plain == with_gene == [("HP:0001166", "present"), ("HP:0000272", "present")]
    assert (
        catalogue_score(plain, frequency_rows()).model_dump()
        == catalogue_score(with_gene, frequency_rows()).model_dump()
    )


def test_a_clinvar_association_does_not_explain_a_term() -> None:
    associations = [
        *gene_rows(),
        {
            "id": "00000000-0000-4000-8000-000000000952",
            "source": "ClinVar",
            "version": "2026-10-01",
            "subject_key": "SYN1|HP:0000272",
            "gene_symbol": "SYN1",
            "hpo_id": "HP:0000272",
        },
    ]
    fit = gene_fit(["HP:0001166", "HP:0000272"], "SYN1", associations)
    assert fit.explained_hpo_ids == ["HP:0001166"]
    assert fit.unexplained_hpo_ids == ["HP:0000272"]
    assert [item.source for item in fit.sources] == ["synthetic-gene-hpo"]


def test_an_excluded_phenotypic_feature_stays_excluded() -> None:
    packet = pps2.Phenopacket(
        id="synthetic-score-2",
        phenotypic_features=[
            pps2.PhenotypicFeature(
                type=pps2.OntologyClass(id="HP:0000272", label="Malar flattening"),
                excluded=True,
            )
        ],
        meta_data=pps2.MetaData(
            created_by="synthetic-fixture",
            phenopacket_schema_version="2.0.2",
        ),
    )
    assert hpo_from_phenopacket(MessageToDict(packet)) == [("HP:0000272", "excluded")]


def test_likelihood_signature_has_no_text_and_no_gene_symbol() -> None:
    assert set(inspect.signature(catalogue_score).parameters) == {"accepted_hpo", "rows"}
