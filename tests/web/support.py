"""Shared database cleanup for notebook tests."""

import os

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://d1:d1@127.0.0.1:5432/d1")


def wipe(case_id: str) -> None:
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("DELETE FROM app.snapshot WHERE case_id = %s::uuid", (case_id,))
        connection.execute("DELETE FROM app.observation WHERE case_id = %s::uuid", (case_id,))
        connection.execute(
            """
            DELETE FROM app.decision
            WHERE draft_id IN (SELECT id FROM app.draft WHERE case_id = %s::uuid)
            """,
            (case_id,),
        )
        connection.execute("DELETE FROM app.draft WHERE case_id = %s::uuid", (case_id,))
