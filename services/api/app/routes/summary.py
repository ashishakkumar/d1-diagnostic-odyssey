"""Fill the fixed summary template from accepted rows and wrap it in a short PDF."""

import os
from pathlib import Path
from uuid import UUID

import psycopg
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.routes.ports import scan_notebook_text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://d1:d1@127.0.0.1:5432/d1")
_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=False,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)
# ponytail: Helvetica is cp1252, about 80 characters a line, 46 lines a page.
# Upgrade: embed a font when a saved row needs characters outside cp1252.
_LINE_CHARS = 80
_PAGE_LINES = 46


def accepted_rows(case_id: UUID) -> list[tuple[object, str, dict]]:
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("SET ROLE d1_api")
        rows = connection.execute(
            """
            SELECT d.decided_at, o.kind, o.body
            FROM app.snapshot s
            JOIN app.decision d ON d.id = s.decision_id
            JOIN app.observation o ON o.draft_id = d.draft_id
            WHERE s.case_id = %s
            ORDER BY d.decided_at DESC, d.id DESC
            """,
            (case_id,),
        ).fetchall()
    return [(row[0], str(row[1]), row[2] if isinstance(row[2], dict) else {}) for row in rows]


def summary_text(case_id: UUID) -> str:
    terms: list[dict] = []
    variants: list[dict] = []
    for _decided_at, kind, body in accepted_rows(case_id):
        if kind == "hpo_term":
            terms.append(body)
        elif kind == "lab_reported_variant":
            expressions = (body.get("variation") or {}).get("expressions") or []
            variant = expressions[0].get("value", "") if expressions else ""
            variants.append({**body, "variant": variant})
    rendered = _ENV.get_template("summary.txt.j2").render(
        case_id=str(case_id),
        terms=terms,
        variants=variants,
    )
    return scan_notebook_text(rendered)


def text_to_pdf(text: str) -> bytes:
    lines = _wrap(text)
    return _pdf(_paginate(lines))


def _wrap(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        words = raw.split(" ")
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            if len(current) + 1 + len(word) <= _LINE_CHARS:
                current = f"{current} {word}"
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _paginate(lines: list[str]) -> list[list[str]]:
    size = _PAGE_LINES
    if len(lines) <= size:
        return [lines or [""]]
    if len(lines) <= size * 2:
        return [lines[:size], lines[size:]]
    note = "The rest of this notebook is on the timeline."
    return [lines[:size], [*lines[size : size * 2 - 1], note]]


def _escape(text: str) -> str:
    encoded = text.encode("cp1252", errors="replace").decode("cp1252")
    return encoded.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "54 740 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({_escape(line)}) Tj")
    commands.append("ET")
    return ("\n".join(commands) + "\n").encode("cp1252", errors="replace")


def _pdf(pages: list[list[str]]) -> bytes:
    font_id = 3 + 2 * len(pages)
    objects: list[bytes] = []
    kids: list[str] = []
    next_id = 3
    page_blobs: list[tuple[int, int, list[str]]] = []
    for lines in pages:
        page_id = next_id
        content_id = next_id + 1
        kids.append(f"{page_id} 0 R")
        page_blobs.append((page_id, content_id, lines))
        next_id += 2
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode())
    for _page_id, content_id, lines in page_blobs:
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_id} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ).encode()
        )
        stream = _stream(lines)
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    header = b"%PDF-1.4\n"
    chunks = [header]
    offsets = [0]
    cursor = len(header)
    for number, obj in enumerate(objects, start=1):
        offsets.append(cursor)
        piece = f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
        chunks.append(piece)
        cursor += len(piece)
    xref_at = cursor
    size = len(objects) + 1
    xref = [f"xref\n0 {size}\n".encode(), b"0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    trailer = f"trailer << /Size {size} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return b"".join(chunks + xref + [trailer])
