"""Never-say scanner. These tests describe the rules; the function comes after."""

from d1_safety import scan


def test_disclaimer_is_not_a_diagnosis_claim() -> None:
    assert scan("This is not a diagnosis.") == []


def test_research_label_is_not_a_diagnosis_claim() -> None:
    assert scan("For research use only. Not for use in diagnostic procedures.") == []


def test_diagnosis_in_product_voice_fails() -> None:
    found = scan("The diagnosis is Marfan syndrome.")
    assert "diagnosis_in_product_voice" in found


def test_you_have_in_product_voice_fails() -> None:
    found = scan("You have Marfan syndrome.")
    assert "diagnosis_in_product_voice" in found


def test_percent_without_calibration_curve_fails() -> None:
    found = scan("The model puts this at 80%.")
    assert "percent_or_probability_without_calibration" in found


def test_probability_word_without_calibration_curve_fails() -> None:
    found = scan("The probability is high.")
    assert "percent_or_probability_without_calibration" in found


def test_percent_with_calibration_curve_reference_passes() -> None:
    text = "80% is the hit rate on the pinned calibration curve."
    assert "percent_or_probability_without_calibration" not in scan(text)


def test_pathogenic_in_product_voice_fails() -> None:
    found = scan("This variant is pathogenic.")
    assert "pathogenic_or_benign_as_own_verdict" in found


def test_benign_in_product_voice_fails() -> None:
    found = scan("This variant is benign.")
    assert "pathogenic_or_benign_as_own_verdict" in found


def test_lab_marked_pathogenic_is_allowed() -> None:
    text = 'The lab report used this word: "Pathogenic".'
    start = text.index("Pathogenic")
    quotes = [(start, start + len("Pathogenic"), "lab")]
    assert scan(text, quotes) == []


def test_public_file_marked_pathogenic_is_allowed() -> None:
    text = 'The public file now says "Benign".'
    start = text.index("Benign")
    quotes = [(start, start + len("Benign"), "public_file")]
    assert "pathogenic_or_benign_as_own_verdict" not in scan(text, quotes)


def test_unmarked_quote_does_not_hide_pathogenic() -> None:
    text = 'The lab report used this word: "Pathogenic".'
    assert "pathogenic_or_benign_as_own_verdict" in scan(text)


def test_other_speaker_does_not_hide_pathogenic() -> None:
    text = "Pathogenic"
    assert "pathogenic_or_benign_as_own_verdict" in scan(text, [(0, len(text), "user")])


def test_dose_advice_fails() -> None:
    found = scan("Take 10 mg each morning.")
    assert "treatment_or_medication_advice" in found


def test_dose_disclaimer_is_not_advice() -> None:
    assert "treatment_or_medication_advice" not in scan("This page does not set a dose.")


def test_negative_instruction_is_still_advice() -> None:
    found = scan("Do not take this drug.")
    assert "treatment_or_medication_advice" in found


def test_eligibility_claim_fails_even_when_negated() -> None:
    found = scan("You are not eligible for this trial.")
    assert "trial_eligibility" in found


def test_calibration_curve_does_not_allow_eligibility() -> None:
    text = "You are eligible for the trial. See the calibration curve."
    found = scan(text)
    assert "trial_eligibility" in found
    assert "percent_or_probability_without_calibration" not in found
