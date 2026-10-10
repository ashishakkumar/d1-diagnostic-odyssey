from pathlib import Path


def test_license_note_marks_hpo_until_the_source_page_loads():
    text = (Path(__file__).resolve().parents[2] / "services" / "ingest" / "LICENSES.md").read_text(
        encoding="utf-8"
    )
    assert "HPO" in text
    assert "UNCLEAR" in text
    assert "CC-BY-4.0" in text or "CC BY 4.0" in text
    assert "CC0" in text
