"""Bind the session reviewer, then call the gate.

The connection has to be the API role. apply_decision takes no reviewer argument.
"""


def bind_reviewer(connection, reviewer: str) -> None:
    if reviewer is None or str(reviewer).strip() == "":
        raise ValueError("reviewer missing")
    connection.execute(
        "SELECT pg_catalog.set_config('app.reviewer', %s, true)",
        (reviewer,),
    )
    connection.execute(
        "SELECT pg_catalog.set_config('app.reviewer_txid', pg_catalog.txid_current()::text, true)"
    )


def apply_decision(connection, draft_id: str, decision: str, seen_hash: str) -> str:
    row = connection.execute(
        "SELECT app.apply_decision(%s::uuid, %s, %s)",
        (str(draft_id), decision, seen_hash),
    ).fetchone()
    if row is None or row[0] is None:
        raise RuntimeError("apply_decision returned no decision")
    return str(row[0])
