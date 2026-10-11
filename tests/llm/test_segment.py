"""Open-band notes are synthetic. The gazetteer leaves them unscored until a span exists."""

import json
from pathlib import Path

from app.demo_cases import demo_frequency_rows
from d4_llm.fallback import ReplayCache
from d4_llm.segment import (
    CACHE_PATH,
    OPEN_BAND,
    gazetteer_spans,
    parse_spans,
    rerun,
    segment_open_band,
)

NOTE = "The fingers are long for the hand."


def test_the_gazetteer_leaves_all_nine_open_band_notes_unscored() -> None:
    assert len(OPEN_BAND) == 9
    ids = [packet["id"] for packet in OPEN_BAND]
    assert len(set(ids)) == 9
    for packet in OPEN_BAND:
        assert gazetteer_spans(packet["note"]) == []


def test_a_closed_phrase_does_not_need_a_model() -> None:
    spans = gazetteer_spans("A seizure was written in the synthetic note.")
    assert [span.hpo_id for span in spans] == ["HP:0001250"]
    assert spans[0].start == 2


def test_a_span_must_sit_inside_the_note_and_on_the_allow_list() -> None:
    raw = json.dumps(
        {
            "spans": [
                {"start": 0, "end": 4, "hpo_id": "HP:0001166", "label": "Arachnodactyly"},
                {"start": 0, "end": 4, "hpo_id": "HP:9999999", "label": "No such term"},
                {"start": 80, "end": 90, "hpo_id": "HP:0001166", "label": "Arachnodactyly"},
            ]
        }
    )
    spans = parse_spans(NOTE, raw)
    assert len(spans) == 1
    assert spans[0].hpo_id == "HP:0001166"
    assert NOTE[spans[0].start : spans[0].end] == "The "


def test_an_end_past_the_note_is_clipped_to_the_note() -> None:
    note = "The body shakes in a fit."
    raw = json.dumps(
        {"spans": [{"start": 4, "end": 26, "hpo_id": "HP:0001250", "label": "Seizure"}]}
    )
    spans = parse_spans(note, raw)
    assert len(spans) == 1
    assert spans[0].end == len(note)
    assert note[spans[0].start : spans[0].end] == "body shakes in a fit."


def test_rerun_scores_only_packets_that_received_a_span() -> None:
    raw = json.dumps(
        {
            "spans": [
                {"start": 0, "end": len(NOTE), "hpo_id": "HP:0001166", "label": "Arachnodactyly"}
            ]
        }
    )
    spans = parse_spans(NOTE, raw)
    by_id = {packet["id"]: [] for packet in OPEN_BAND}
    by_id["synthetic-open-01"] = spans
    rows = rerun(by_id, demo_frequency_rows())
    assert len(rows) == 9
    scored = [row for row in rows if row["scored"]]
    assert [row["id"] for row in scored] == ["synthetic-open-01"]
    assert scored[0]["leading"] == "ORPHA:9000001"


def test_a_cached_segmentation_is_not_requested_again(tmp_path: Path) -> None:
    calls = {"n": 0}

    def primary(prompt: str) -> str:
        calls["n"] += 1
        assert "SYNTHETIC-ONLY" in prompt
        return json.dumps(
            {"spans": [{"start": 0, "end": 10, "hpo_id": "HP:0001250", "label": "Seizure"}]}
        )

    cache = ReplayCache(tmp_path / "replay.json")
    first = segment_open_band(primary=primary, cache=cache, sleep=lambda _seconds: None)
    second = segment_open_band(primary=primary, cache=cache, sleep=lambda _seconds: None)
    assert calls["n"] == 9
    assert second.keys() == first.keys()
    assert all(second[key] == first[key] for key in first)


def test_recorded_cache_reruns_the_nine_without_calling_a_provider() -> None:
    assert CACHE_PATH.is_file()
    raw = CACHE_PATH.read_text()
    assert "AIza" not in raw
    assert "sk-or" not in raw
    calls = {"n": 0}

    def primary(_prompt: str) -> str:
        calls["n"] += 1
        raise AssertionError("provider")

    spans = segment_open_band(
        primary=primary,
        cache=ReplayCache(CACHE_PATH),
        sleep=lambda _seconds: None,
    )
    assert calls["n"] == 0
    rows = rerun(spans, demo_frequency_rows())
    assert len(rows) == 9
    assert [row["id"] for row in rows if not row["scored"]] == ["synthetic-open-09"]
    assert sum(1 for row in rows if row["scored"]) == 8
