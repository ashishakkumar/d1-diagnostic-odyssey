"""Approval gate. These are the failures a graph pause produced, expressed as database tests."""

import json
from collections.abc import Callable

import psycopg
import pytest

from canonical_oracle import body_hash, canonical_json

CASE_ID = "00000000-0000-4000-8000-000000000010"
GATE_FUNCTIONS = ("app.apply_decision", "app.gate_renamed")


def insert_draft(connection: psycopg.Connection, body: dict, client_hash: str | None = None):
    connection.execute("SET ROLE d1_api")
    if client_hash is None:
        row = connection.execute(
            """
            INSERT INTO app.draft (case_id, kind, body)
            VALUES (%s, 'hpo_term', %s::jsonb)
            RETURNING id::text, body_hash, body_text
            """,
            (CASE_ID, json.dumps(body)),
        ).fetchone()
    else:
        row = connection.execute(
            """
            INSERT INTO app.draft (case_id, kind, body, body_hash)
            VALUES (%s, 'hpo_term', %s::jsonb, %s)
            RETURNING id::text, body_hash, body_text
            """,
            (CASE_ID, json.dumps(body), client_hash),
        ).fetchone()
    assert row is not None
    return row[0], row[1], row[2]


def bind_reviewer(connection: psycopg.Connection, reviewer: str) -> None:
    connection.execute("SELECT set_config('app.reviewer', %s, true)", (reviewer,))
    connection.execute("SELECT set_config('app.reviewer_txid', txid_current()::text, true)")


def apply_decision(
    connection: psycopg.Connection,
    draft_id: str,
    decision: str,
    seen_hash: str,
    reviewer: str = "ashish",
    function: str = "app.apply_decision",
) -> str:
    if function not in GATE_FUNCTIONS:
        raise AssertionError(function)
    connection.execute("SET ROLE d1_api")
    bind_reviewer(connection, reviewer)
    row = connection.execute(
        f"SELECT {function}(%s::uuid, %s, %s)",
        (draft_id, decision, seen_hash),
    ).fetchone()
    assert row is not None
    return str(row[0])


def expect(
    connection: psycopg.Connection, error: type[BaseException], fn: Callable[[], object]
) -> None:
    connection.execute("SAVEPOINT gate")
    try:
        fn()
    except error:
        connection.execute("ROLLBACK TO SAVEPOINT gate")
    else:
        raise AssertionError(f"expected {error.__name__}")


def count(connection: psycopg.Connection, table: str) -> int:
    if table not in {"app.draft", "app.decision", "app.observation", "app.snapshot"}:
        raise AssertionError(table)
    row = connection.execute(f"SELECT count(*) FROM {table}").fetchone()
    assert row is not None
    return int(row[0])


def status_of(connection: psycopg.Connection, draft_id: str) -> str:
    row = connection.execute(
        "SELECT status FROM app.draft WHERE id = %s::uuid",
        (draft_id,),
    ).fetchone()
    assert row is not None
    return str(row[0])


def test_double_resume_writes_once(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "seizure", "presence": "present"})
    apply_decision(db, draft_id, "approve", digest)
    expect(
        db,
        psycopg.errors.ObjectNotInPrerequisiteState,
        lambda: apply_decision(db, draft_id, "approve", digest),
    )
    assert count(db, "app.decision") == 1
    assert count(db, "app.observation") == 1
    assert count(db, "app.snapshot") == 1


def test_edited_after_approval_is_rejected(db: psycopg.Connection) -> None:
    original = {"hpo_id": "HP:0001250", "label": "Seizure", "presence": "present"}
    edited = {"hpo_id": "HP:0001250", "label": "Seizure", "presence": "excluded"}
    old_id, old_hash, _old_text = insert_draft(db, original)
    new_id, new_hash, _new_text = insert_draft(db, edited)
    assert old_hash != new_hash
    db.execute("SET ROLE d1_api")
    db.execute("UPDATE app.draft SET status = 'superseded' WHERE id = %s::uuid", (old_id,))

    expect(
        db,
        psycopg.errors.CheckViolation,
        lambda: apply_decision(db, new_id, "approve", old_hash),
    )
    expect(
        db,
        psycopg.errors.ObjectNotInPrerequisiteState,
        lambda: apply_decision(db, old_id, "approve", old_hash),
    )
    assert count(db, "app.observation") == 0
    assert count(db, "app.decision") == 0
    assert status_of(db, new_id) == "pending"

    apply_decision(db, new_id, "approve", new_hash)
    stored = db.execute("SELECT body_hash FROM app.observation").fetchone()
    assert stored is not None
    assert stored[0] == new_hash

    db.execute("SET ROLE d1_api")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "UPDATE app.observation SET body = %s::jsonb",
            (json.dumps({"edited": True}),),
        ),
    )
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "UPDATE app.draft SET body = %s::jsonb WHERE id = %s::uuid",
            (json.dumps({"edited": True}), new_id),
        ),
    )


def test_side_effect_before_the_pause_runs_once(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "before the decision"})
    assert count(db, "app.draft") == 1
    assert count(db, "app.snapshot") == 0
    assert count(db, "app.observation") == 0

    apply_decision(db, draft_id, "approve", digest)
    expect(
        db,
        psycopg.errors.ObjectNotInPrerequisiteState,
        lambda: apply_decision(db, draft_id, "approve", digest),
    )
    assert count(db, "app.draft") == 1
    assert count(db, "app.snapshot") == 1
    assert count(db, "app.observation") == 1


def test_renaming_the_function_does_not_drop_a_pending_approval(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "still pending"})
    db.execute("RESET ROLE")
    db.execute("ALTER FUNCTION app.apply_decision(uuid, text, text) RENAME TO gate_renamed")

    assert status_of(db, draft_id) == "pending"
    assert count(db, "app.observation") == 0
    columns = {
        row[0]
        for row in db.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'app' AND table_name = 'draft'
            """
        ).fetchall()
    }
    assert columns.isdisjoint({"node", "node_name", "graph_node", "checkpoint"})

    apply_decision(db, draft_id, "approve", digest, function="app.gate_renamed")
    assert status_of(db, draft_id) == "approved"
    assert count(db, "app.observation") == 1


def test_public_execute_is_denied(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "not for public"})
    db.execute("RESET ROLE")
    granted = db.execute(
        """
        SELECT has_function_privilege(
            'public',
            'app.apply_decision(uuid, text, text)',
            'execute'
        )
        """
    ).fetchone()
    assert granted is not None
    assert granted[0] is False

    db.execute("CREATE ROLE d1_stranger NOLOGIN")
    db.execute("GRANT d1_stranger TO CURRENT_USER")
    db.execute("GRANT USAGE ON SCHEMA app TO d1_stranger")
    db.execute("SET ROLE d1_stranger")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "SELECT app.apply_decision(%s::uuid, 'approve', %s)",
            (draft_id, digest),
        ),
    )
    db.execute("RESET ROLE")
    assert status_of(db, draft_id) == "pending"
    assert count(db, "app.observation") == 0


def test_pending_stays_when_the_function_is_not_called(db: psycopg.Connection) -> None:
    draft_id, _digest, _text = insert_draft(db, {"label": "waiting"})
    db.execute("SET ROLE d1_api")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute("DELETE FROM app.draft WHERE id = %s::uuid", (draft_id,)),
    )
    assert status_of(db, draft_id) == "pending"
    assert count(db, "app.decision") == 0


def test_reviewer_comes_from_the_session(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "session"})
    db.execute("RESET ROLE")
    arguments = db.execute(
        """
        SELECT pg_get_function_identity_arguments(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'app' AND p.proname = 'apply_decision'
        """
    ).fetchone()
    assert arguments is not None
    assert arguments[0] == "draft_id uuid, decision text, seen_hash text"

    apply_decision(db, draft_id, "approve", digest, reviewer="ashish")
    stored = db.execute("SELECT reviewer FROM app.decision").fetchone()
    assert stored is not None
    assert stored[0] == "ashish"

    other_id, other_hash, _other_text = insert_draft(db, {"label": "other session"})
    apply_decision(db, other_id, "reject", other_hash, reviewer="caregiver")
    reviewers = {
        row[0]
        for row in db.execute(
            "SELECT reviewer FROM app.decision WHERE draft_id = %s::uuid",
            (other_id,),
        ).fetchall()
    }
    assert reviewers == {"caregiver"}
    assert count(db, "app.observation") == 1


def test_session_level_setting_does_not_authorize_the_next_transaction(
    db: psycopg.Connection,
) -> None:
    db.execute("SELECT set_config('app.reviewer', 'leaked', false)")
    db.execute("SELECT set_config('app.reviewer_txid', '999', false)")
    draft_id, digest, _text = insert_draft(db, {"label": "pooled"})
    db.execute("SET ROLE d1_api")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "SELECT app.apply_decision(%s::uuid, 'approve', %s)",
            (draft_id, digest),
        ),
    )
    assert count(db, "app.decision") == 0
    apply_decision(db, draft_id, "approve", digest, reviewer="ashish")
    stored = db.execute("SELECT reviewer FROM app.decision").fetchone()
    assert stored is not None
    assert stored[0] == "ashish"


def test_trigger_stores_the_hash_the_reviewer_saw(db: psycopg.Connection) -> None:
    body = {"z": True, "a": {"b": None, "a": ["x y", 'say "hi"']}, "n": "é"}
    draft_id, digest, text = insert_draft(db, body, client_hash="ab" * 32)
    assert text == canonical_json(body)
    assert digest == body_hash(body)
    assert digest != "ab" * 32
    apply_decision(db, draft_id, "approve", digest)
    stored = db.execute("SELECT body_hash FROM app.decision").fetchone()
    assert stored is not None
    assert stored[0] == digest


def test_gate_owner_and_privileges(db: psycopg.Connection) -> None:
    db.execute("RESET ROLE")
    owner = db.execute(
        """
        SELECT r.rolname
        FROM pg_class c
        JOIN pg_roles r ON r.oid = c.relowner
        WHERE c.relname = 'draft' AND c.relnamespace = 'app'::regnamespace
        """
    ).fetchone()
    assert owner is not None, "app.draft is missing"
    assert owner[0] == "d1_owner"

    function_owner = db.execute(
        """
        SELECT r.rolname, p.prosecdef, p.proconfig
        FROM pg_proc p
        JOIN pg_roles r ON r.oid = p.proowner
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'app' AND p.proname = 'apply_decision'
        """
    ).fetchone()
    assert function_owner is not None, "app.apply_decision is missing"
    assert function_owner[0] == "d1_owner"
    assert function_owner[1] is True
    assert function_owner[2] is not None
    assert "search_path=pg_catalog, app" in function_owner[2]

    login = db.execute(
        "SELECT rolcanlogin, rolinherit FROM pg_roles WHERE rolname = 'd1_owner'"
    ).fetchone()
    assert login == (False, True)
    api = db.execute(
        "SELECT rolcanlogin, rolinherit FROM pg_roles WHERE rolname = 'd1_api'"
    ).fetchone()
    assert api == (False, False)
    member = db.execute("SELECT pg_has_role('d1_api', 'd1_owner', 'member')").fetchone()
    assert member == (False,)

    for schema in ("app", "public"):
        privilege = db.execute(
            "SELECT has_schema_privilege('d1_api', %s, 'CREATE')",
            (schema,),
        ).fetchone()
        assert privilege == (False,)

    for table in ("app.decision", "app.observation", "app.snapshot"):
        for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            allowed = db.execute(
                "SELECT has_table_privilege('d1_api', %s, %s)",
                (table, privilege),
            ).fetchone()
            assert allowed == (False,), f"{table} {privilege}"

    body_update = db.execute(
        "SELECT has_column_privilege('d1_api', 'app.draft', 'body', 'UPDATE')"
    ).fetchone()
    status_update = db.execute(
        "SELECT has_column_privilege('d1_api', 'app.draft', 'status', 'UPDATE')"
    ).fetchone()
    assert body_update == (False,)
    assert status_update == (True,)

    draft_id, _digest, _text = insert_draft(db, {"label": "direct update"})
    db.execute("SET ROLE d1_api")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "UPDATE app.draft SET status = 'approved' WHERE id = %s::uuid",
            (draft_id,),
        ),
    )
    assert status_of(db, draft_id) == "pending"
    assert count(db, "app.observation") == 0


def test_missing_reviewer_is_rejected(db: psycopg.Connection) -> None:
    draft_id, digest, _text = insert_draft(db, {"label": "no reviewer"})
    db.execute("SET ROLE d1_api")
    expect(
        db,
        psycopg.errors.InsufficientPrivilege,
        lambda: db.execute(
            "SELECT app.apply_decision(%s::uuid, 'approve', %s)",
            (draft_id, digest),
        ),
    )
    assert status_of(db, draft_id) == "pending"


@pytest.mark.parametrize(
    ("body",),
    [
        ({"b": 1, "a": "é"},),
        ({"z": True, "a": {"b": None, "a": ["x y", 'say "hi"']}, "n": "é"},),
    ],
)
def test_database_canonical_json_matches_the_oracle(db: psycopg.Connection, body: dict) -> None:
    _draft_id, digest, text = insert_draft(db, body)
    assert text == canonical_json(body)
    assert digest == body_hash(body)
