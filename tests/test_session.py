import inspect

import psycopg

from app.session import apply_decision, bind_reviewer

CASE_ID = "00000000-0000-4000-8000-000000000010"


def test_apply_decision_takes_no_reviewer() -> None:
    parameters = list(inspect.signature(apply_decision).parameters)
    assert parameters == ["connection", "draft_id", "decision", "seen_hash"]


def test_helper_stores_the_session_reviewer(db: psycopg.Connection) -> None:
    db.execute("SET ROLE d1_api")
    row = db.execute(
        """
        INSERT INTO app.draft (case_id, kind, body)
        VALUES (%s, 'hpo_term', %s::jsonb)
        RETURNING id::text, body_hash
        """,
        (CASE_ID, '{"label":"helper"}'),
    ).fetchone()
    assert row is not None
    draft_id, digest = row
    bind_reviewer(db, "ashish")
    decision_id = apply_decision(db, draft_id, "approve", digest)
    assert decision_id
    stored = db.execute("SELECT reviewer, body_hash FROM app.decision").fetchone()
    assert stored == ("ashish", digest)
