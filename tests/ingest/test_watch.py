import socket
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from d1_ingest.load import load_clinvar
from d1_ingest.watch import fact_line, watch

from d1_contracts import ChangeEvent, LabReportedVariant

FIXTURES = Path(__file__).parent / "fixtures"
CASE_ID = UUID("00000000-0000-4000-8000-000000000010")
BANNED = (
    "reclassified",
    "upgrade",
    "downgrade",
    "discordant",
    "diagnosis",
    "recommend",
    "pathogenic",
)


def _variant(variation_id: str, hgvs: str, gene: str = "FBN1") -> LabReportedVariant:
    return LabReportedVariant.model_validate(
        {
            "id": "00000000-0000-4000-8000-000000000003",
            "case_id": str(CASE_ID),
            "gene_symbol": gene,
            "lab_words": "ALPHA",
            "report_date": "2020-01-02",
            "variation": {
                "id": variation_id,
                "expressions": [{"syntax": "hgvs.c", "value": hgvs}],
            },
        }
    )


def _events(variant, earlier, later, gene=None):
    return watch(
        earlier=earlier,
        later=later,
        variant=variant,
        gene_symbol=gene,
        new_id=lambda: UUID("00000000-0000-4000-8000-000000000005"),
    )


def test_watch_quotes_lab_words_against_the_two_clinvar_texts():
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    events = _events(_variant("42", "NM_000138.5:c.1A>G"), earlier, later)
    assert len(events) == 1
    event = events[0]
    ChangeEvent.model_validate(event.model_dump(mode="json"))
    assert event.case_id == CASE_ID
    assert event.source == "ClinVar"
    assert event.version == "2024-02"
    assert event.subject_key == "42"
    assert event.observed_at == datetime(2024, 2, 1, tzinfo=timezone.utc)
    assert event.previous_text == fact_line(
        "ClinVar",
        "2024-01",
        "ClinicalSignificance: ALPHA; LastEvaluated: Jan 01, 2024",
        lab_words="ALPHA",
        lab_report_date=date(2020, 1, 2),
    )
    assert event.current_text == fact_line(
        "ClinVar",
        "2024-02",
        "ClinicalSignificance: BETA; LastEvaluated: Feb 02, 2024",
        lab_words="ALPHA",
        lab_report_date=date(2020, 1, 2),
    )
    blob = f"{event.previous_text} {event.current_text}".lower()
    for word in BANNED:
        assert word not in blob


def test_watch_matches_hgvs_when_the_stored_id_is_not_a_variation_id():
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    events = _events(_variant("synthetic-var-1", "NM_000138.5:c.1A>G"), earlier, later)
    assert [event.subject_key for event in events] == ["42"]


def test_watch_emits_nothing_when_the_quoted_text_is_unchanged():
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    events = _events(_variant("7", "NM_000001.1:c.2T>C", gene="OTHER"), earlier, later)
    assert events == []


def test_watch_does_not_substitute_another_variant_in_the_same_gene():
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    events = _events(_variant("missing", "NM_missing.1:c.1A>T", gene="FBN1"), earlier, later)
    assert events == []


def test_watch_for_a_gene_lists_only_that_genes_changed_variations():
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-03.txt")
    events = watch(earlier=earlier, later=later, gene_symbol="FBN1", case_id=CASE_ID)
    assert [event.subject_key for event in events] == ["9"]
    assert "GAMMA" in (events[0].current_text or "")
    assert "lab_words" not in (events[0].current_text or "")
    gone = watch(earlier=earlier, later=later, gene_symbol="OTHER", case_id=CASE_ID)
    assert [event.subject_key for event in gone] == ["7"]
    assert gone[0].current_text == fact_line("ClinVar", "2024-03", None)


def test_watch_does_not_open_a_socket(monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "socket", boom)
    earlier = load_clinvar(FIXTURES / "variant_summary_2024-01.txt")
    later = load_clinvar(FIXTURES / "variant_summary_2024-02.txt")
    events = _events(_variant("42", "NM_000138.5:c.1A>G"), earlier, later)
    assert len(events) == 1
