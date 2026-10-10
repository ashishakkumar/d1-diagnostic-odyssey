"""Flesch-Kincaid grade on the templates. The ceiling is the CDC 8th-grade line."""

from d1_safety.readability import CEILING, SOURCE, grade, template_grades
from d1_safety.render import template_text

CALL = "You should only call 999 if it's a life-threatening emergency."
NUMBER = "You can call an ambulance by using 999 or 112."


def test_ceiling_is_the_cdc_eighth_grade_line() -> None:
    assert CEILING == 8
    assert "https://stacks.cdc.gov/view/cdc/12420" in SOURCE
    assert "Flesch-Kincaid" in SOURCE


def test_templates_score_at_or_below_the_ceiling() -> None:
    scores = template_grades()
    assert set(scores) >= {
        "questions_for_doctor",
        "reason_marked_excluded",
        "reason_no_public_row",
        "public_database_change",
        "not_confident_yet",
        "lab_report_words",
        "emergency_footer",
        "stop_screen",
    }
    over = {name: score for name, score in scores.items() if score > CEILING}
    assert over == {}


def test_a_dense_paragraph_scores_above_the_ceiling() -> None:
    hard = (
        "The phenomenological heterogeneity of multisystem pathophysiological "
        "presentations necessitates individualized interpretation by appropriately "
        "credentialed subspecialists prior to any determination."
    )
    assert grade(hard) > CEILING


def test_cited_emergency_sentences_stay_verbatim() -> None:
    footer = template_text("emergency_footer")
    assert CALL in footer
    assert NUMBER in footer
