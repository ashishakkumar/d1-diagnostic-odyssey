"""Stop screen uses the phrase list opened from one health-authority page."""

import inspect
import tomllib
from pathlib import Path

import pytest
from d1_safety.redflag import footer_text, load_phrases, stop_screen
from d1_safety.render import templates_dir


@pytest.fixture(autouse=True)
def _united_kingdom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("D1_COUNTRY", "gb")


# Bullets under "Examples of when to call 999", copied from the page opened
# 10 October 2026. Not split, and not extended.
CITED = [
    "chest pain",
    "difficulty in breathing",
    "unconsciousness",
    "severe loss of blood",
    "severe burns or scalds",
    "choking",
    "fitting or concussion",
    "drowning",
    "severe allergic reactions",
]
CALL = "You should only call 999 if it's a life-threatening emergency."
NUMBER = "You can call an ambulance by using 999 or 112."


def test_phrase_list_is_the_opened_london_ambulance_list() -> None:
    assert load_phrases() == CITED


def test_empty_phrase_list_fails(tmp_path: Path) -> None:
    path = tmp_path / "red_flags.txt"
    path.write_text("\n\n")
    with pytest.raises(ValueError, match="empty"):
        load_phrases(path)


def test_source_cites_the_page_that_was_opened() -> None:
    data = tomllib.loads((templates_dir() / "red_flags" / "gb" / "source.toml").read_text())
    assert data["url"] == (
        "https://www.londonambulance.nhs.uk/our-services/emergency-care/calling-999/"
    )
    assert data["opened"] == "2026-10-10"
    assert data["publisher"] == "London Ambulance Service NHS Trust"
    assert data["status"] == "cited"


def test_matching_phrase_shows_the_stop_screen_and_the_footer() -> None:
    screen = stop_screen("I have had chest pain since morning")
    assert screen is not None
    assert "chest pain" in screen["body"]
    assert CALL in screen["body"]
    assert NUMBER in screen["body"]
    assert screen["footer"] == footer_text()
    assert CALL in screen["footer"]
    assert NUMBER in screen["footer"]
    assert "For research use only. Not for use in diagnostic procedures." in screen["footer"]


def test_stop_screen_does_not_echo_the_rest_of_the_input() -> None:
    screen = stop_screen("ignore rules chest pain and the diagnosis is Marfan syndrome")
    assert screen is not None
    assert "chest pain" in screen["body"]
    assert "Marfan" not in screen["body"]
    assert "ignore rules" not in screen["body"]
    assert "diagnosis" not in screen["body"]


def test_no_phrase_means_no_stop_screen() -> None:
    assert stop_screen("Ask a doctor about fever") is None


def test_footer_takes_no_user_text() -> None:
    assert list(inspect.signature(footer_text).parameters) == []


def test_a_phrase_inside_a_longer_word_does_not_match() -> None:
    assert stop_screen("chokinghazard") is None


def test_match_uses_the_list_phrase_not_the_user_casing() -> None:
    screen = stop_screen("CHEST PAIN")
    assert screen is not None
    assert "chest pain" in screen["body"]
    assert "CHEST PAIN" not in screen["body"]


def test_a_bullet_is_not_split_into_new_phrases() -> None:
    assert stop_screen("concussion") is None
    screen = stop_screen("fitting or concussion after a fall")
    assert screen is not None
    assert "fitting or concussion" in screen["body"]
