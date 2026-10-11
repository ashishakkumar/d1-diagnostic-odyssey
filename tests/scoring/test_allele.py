"""The population prior is opt-in and does not move the catalogue comparison."""

import json
from pathlib import Path

from scoring.allele import population_prior
from scoring.catalogue import catalogue_score

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads(
    (ROOT / "services" / "api" / "app" / "data" / "allele_frequencies.json").read_text()
)
FREQUENCIES = json.loads((ROOT / "tests" / "scoring" / "fixtures" / "frequencies.json").read_text())
ACCEPTED = [("HP:0001166", "present"), ("HP:0000272", "present")]


def test_the_prior_stays_off_until_asked() -> None:
    off = population_prior("NM_000138.5:c.1A>G", ROWS, opted_in=False)
    assert off["opted_in"] is False
    assert off["found"] is False
    assert off["experimental"] is True
    assert off["allele_frequency"] is None
    assert "not a diagnosis" in off["label"].casefold()


def test_an_opt_in_match_cites_the_fixture_and_its_limits() -> None:
    prior = population_prior("NM_000138.5:c.1A>G", ROWS, opted_in=True)
    assert prior["found"] is True
    assert prior["allele_frequency"] == 0.00012
    assert prior["source"] == "fixture-allele-frequency"
    assert "did not call gnomAD" in prior["limits"]
    assert prior["track"] == "experimental"


def test_a_missing_variant_says_the_prior_is_absent() -> None:
    prior = population_prior("NM_000000.0:c.2T>A", ROWS, opted_in=True)
    assert prior["found"] is False
    assert "absent" in prior["limits"]


def test_the_catalogue_json_does_not_change_when_the_prior_is_read() -> None:
    before = catalogue_score(ACCEPTED, FREQUENCIES).model_dump()
    population_prior("NM_000138.5:c.1A>G", ROWS, opted_in=True)
    after = catalogue_score(ACCEPTED, FREQUENCIES).model_dump()
    assert before == after
