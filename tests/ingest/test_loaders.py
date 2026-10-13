import gzip
from pathlib import Path
from uuid import UUID

import pytest
from d1_ingest.fetch import clinvar_archive_url, download
from d1_ingest.load import (
    load_clingen_gene_validity,
    load_clinvar,
    load_hpo,
    load_orphadata_genes,
    load_orphadata_phenotypes,
)

from d1_contracts import EvidenceRow

FIXTURES = Path(__file__).parent / "fixtures"
ROW_ID = UUID("00000000-0000-4000-8000-0000000000aa")


def _evidence(rows):
    assert rows, "a release with records yields rows"
    evidences = []
    for row in rows:
        evidence = row.evidence(ROW_ID)
        EvidenceRow.model_validate(evidence.model_dump(mode="json"))
        dumped = evidence.model_dump()
        assert set(dumped) <= {"id", "source", "version", "subject_key"}
        assert dumped["source"]
        assert dumped["version"]
        evidences.append(evidence)
    return evidences


def test_hpo_rows_carry_the_file_version_and_term_ids():
    rows = load_hpo(FIXTURES / "hp_mini.obo")
    evidences = _evidence(rows)
    assert {item.source for item in evidences} == {"HPO"}
    assert {item.version for item in evidences} == {"hp/releases/2026-09-01"}
    by_id = {row.subject_key: row.text for row in rows}
    assert by_id == {"HP:0000001": "All", "HP:0001250": "Seizure"}


def test_orphadata_phenotype_rows_quote_the_frequency_label():
    rows = load_orphadata_phenotypes(FIXTURES / "en_product4_mini.xml")
    evidences = _evidence(rows)
    assert {item.source for item in evidences} == {"Orphadata Science en_product4"}
    assert {item.version for item in evidences} == {"2026-06-23 07:57:18"}
    by_id = {row.subject_key: row.text for row in rows}
    assert by_id == {
        "ORPHA:999999|HP:0001250": "Very frequent (99-80%)",
        "ORPHA:999999|HP:0001251": "Occasional (29-5%)",
    }


def test_orphadata_gene_rows_quote_the_association_type():
    rows = load_orphadata_genes(FIXTURES / "en_product6_mini.xml")
    evidences = _evidence(rows)
    assert evidences[0].source == "Orphadata Science en_product6"
    assert evidences[0].version == "2026-06-23 07:57:31"
    assert rows[0].subject_key == "ORPHA:999999|FAKEGENE"
    assert rows[0].text == "Fixture association type"


def test_clinvar_rows_use_the_archive_month_and_one_row_per_variation():
    rows = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    evidences = _evidence(rows)
    assert {item.source for item in evidences} == {"ClinVar"}
    assert {item.version for item in evidences} == {"2024-01"}
    by_id = {row.subject_key: row.text for row in rows}
    assert by_id == {
        "42": "ClinicalSignificance: ALPHA; LastEvaluated: Jan 01, 2024",
        "7": "ClinicalSignificance: SAME; LastEvaluated: Jan 01, 2024",
    }
    fbn1 = next(row for row in rows if row.subject_key == "42")
    assert "hgvs:NM_000138.5:c.1A>G" in fbn1.match_keys
    assert "gene:FBN1" in fbn1.match_keys
    assert "variation:42" in fbn1.match_keys


def test_clinvar_keeps_the_grch38_words_when_assemblies_disagree(tmp_path: Path):
    path = tmp_path / "variant_summary_2024-05.txt"
    path.write_text(
        "#AlleleID\tClinicalSignificance\tLastEvaluated\tAssembly\tVariationID\t"
        "Name\tGeneSymbol\n"
        "1\tFROM37\tJan 01, 2024\tGRCh37\t5\tNM_1.1(G):c.1A>T\tG,H\n"
        "1\tFROM38\tFeb 02, 2024\tGRCh38\t5\tNM_1.1(G):c.1A>T\tG,H\n",
        encoding="utf-8",
    )
    rows = load_clinvar(path)
    assert len(rows) == 1
    assert rows[0].text == "ClinicalSignificance: FROM38; LastEvaluated: Feb 02, 2024"
    assert "gene:G" in rows[0].match_keys
    assert "gene:H" in rows[0].match_keys


def test_clinvar_reads_gzip_and_refuses_an_undated_name(tmp_path: Path):
    raw = (FIXTURES / "variant_summary_2024-01.txt").read_bytes()
    gz = tmp_path / "variant_summary_2024-01.txt.gz"
    gz.write_bytes(gzip.compress(raw))
    assert load_clinvar(gz)[0].version == "2024-01"
    undated = tmp_path / "variant_summary.txt"
    undated.write_text("AlleleID\tVariationID\n", encoding="utf-8")
    with pytest.raises(ValueError, match="YYYY-MM"):
        load_clinvar(undated)


def test_clingen_rows_quote_the_published_classification_and_date():
    rows = load_clingen_gene_validity(FIXTURES / "clingen_gene_validity_mini.csv")
    evidences = _evidence(rows)
    assert evidences[0].source == "ClinGen gene-disease validity"
    assert evidences[0].version == "2026-10-10"
    assert rows[0].subject_key == "FAKEGENE|MONDO:9999999|AD"
    assert rows[0].text == (
        "CLASSIFICATION: Fixture label; CLASSIFICATION DATE: 2024-03-14T16:00:00.000Z"
    )


def test_clinvar_archive_url_follows_the_ftp_layout():
    assert clinvar_archive_url("2026-10") == (
        "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/"
        "variant_summary_2026-10.txt.gz"
    )
    assert clinvar_archive_url("2024-01") == (
        "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/2024/"
        "variant_summary_2024-01.txt.gz"
    )


def test_download_copies_a_local_file_url(tmp_path: Path):
    src = tmp_path / "hp.obo"
    src.write_text("data-version: hp/releases/2026-09-01\n", encoding="utf-8")
    dest = tmp_path / "out" / "hp.obo"
    download(src.as_uri(), dest)
    assert dest.read_text(encoding="utf-8").startswith("data-version:")
