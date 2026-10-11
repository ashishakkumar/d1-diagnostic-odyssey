"""Fill the fixed summary template from accepted rows and wrap it in a short PDF."""

import os
from pathlib import Path
from typing import Literal, Never
from uuid import UUID

import psycopg
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.routes.ports import (
    change_events,
    country_footer,
    red_flag,
    render_sentence,
    report_for,
    scan_notebook_text,
)
from d1_contracts import LabReportedVariant

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


def _parts(case_id: UUID) -> tuple[list[dict], list[dict]]:
    terms: list[dict] = []
    variants: list[dict] = []
    for _decided_at, kind, body in accepted_rows(case_id):
        if kind == "hpo_term":
            terms.append({**body, "explanation": str(body.get("explanation") or "")})
        elif kind == "lab_reported_variant":
            expressions = (body.get("variation") or {}).get("expressions") or []
            variant = expressions[0].get("value", "") if expressions else ""
            variants.append({**body, "variant": variant})
    return terms, variants


def _append(
    pieces: list[str],
    spans: list[tuple[int, int, str]],
    sentence: str,
    quotes: list[tuple[int, int, str]],
) -> None:
    offset = sum(len(part) + 1 for part in pieces)
    pieces.append(sentence)
    for start, end, speaker in quotes:
        spans.append((offset + start, offset + end, speaker))


def _abstain_phrase(
    reason: Literal[
        "many_within_factor",
        "top_flips_between_bounds",
        "tied_for_first",
        "no_scoreable_disease",
    ],
) -> str:
    if reason == "many_within_factor":
        return "Several rows sit close together."
    if reason == "top_flips_between_bounds":
        return "The first row changes between the two ends of a bin."
    if reason == "tied_for_first":
        return "Two rows share the first place."
    if reason == "no_scoreable_disease":
        return "No row in the table could be compared."
    unknown: Never = reason
    raise ValueError(unknown)


PUBLIC_RANKER_SENTENCE = (
    "The rows in this summary are the synthetic frequency-bin card. "
    "The public-case ranker is Resnik best-match average. "
    "It abstains when the best score is at or below zero. "
    "On the held-out split that ranker beats the degree baseline at k=1 and k=5."
)


def _append_comparison(
    pieces: list[str],
    spans: list[tuple[int, int, str]],
    report: dict,
) -> None:
    evidence = report.get("evidence") or []
    if not evidence:
        return
    _append(pieces, spans, PUBLIC_RANKER_SENTENCE, [])
    first = evidence[0]
    if report.get("abstained"):
        reason = report.get("abstain_reason") or "no_scoreable_disease"
        sentence, quotes = render_sentence(
            "catalogue_abstained",
            {"abstain_reason": _abstain_phrase(reason)},
        )
        _append(pieces, spans, sentence, quotes)
        return
    sentence, quotes = render_sentence(
        "catalogue_row",
        {
            "source": str(first.get("source") or "frequency table"),
            "version": str(first.get("version") or "unversioned"),
            "orphanet_id": str(report.get("leading_orphanet_id") or first.get("orphanet_id")),
        },
    )
    _append(pieces, spans, sentence, quotes)
    if report.get("margin_reason") == "runner_up_ratio_is_zero":
        sentence, quotes = render_sentence("catalogue_margin_unbounded", {})
        _append(pieces, spans, sentence, quotes)
        return
    margin = report.get("margin")
    if isinstance(margin, (int, float)) and not isinstance(margin, bool):
        sentence, quotes = render_sentence("catalogue_margin", {"margin": f"{float(margin):.3f}"})
        _append(pieces, spans, sentence, quotes)


def summary_text(case_id: UUID) -> str:
    terms, variants = _parts(case_id)
    typed = "\n".join(
        str(item)
        for item in [
            *(term.get("label") or "" for term in terms),
            *(term.get("explanation") or "" for term in terms),
            *(variant.get("lab_words") or "" for variant in variants),
        ]
        if item
    )
    screen = red_flag(typed)
    if screen is not None:
        return scan_notebook_text(f"{screen['body']}\n{screen['footer']}")

    pieces: list[str] = []
    spans: list[tuple[int, int, str]] = []
    rendered = _ENV.get_template("summary.txt.j2").render(
        case_id=str(case_id),
        terms=terms,
        variants=variants,
    )
    _append(pieces, spans, rendered.rstrip("\n"), [])
    for term in terms:
        presence = str(term.get("presence") or "")
        if presence not in ("present", "excluded"):
            continue
        template_id = "questions_for_doctor" if presence == "present" else "reason_marked_excluded"
        sentence, quotes = render_sentence(
            template_id,
            {
                "label": str(term.get("label") or term.get("hpo_id")),
                "hpo_id": str(term["hpo_id"]),
                "presence": presence,
            },
        )
        _append(pieces, spans, sentence, quotes)
    for variant in variants:
        sentence, quotes = render_sentence(
            "lab_report_words",
            {
                "report_date": str(variant.get("report_date") or ""),
                "gene_symbol": str(variant.get("gene_symbol") or ""),
                "lab_words": str(variant.get("lab_words") or ""),
            },
        )
        _append(pieces, spans, sentence, quotes)
    stored = []
    for variant in variants:
        payload = {key: value for key, value in variant.items() if key != "variant"}
        stored.append(LabReportedVariant.model_validate(payload))
    for event in change_events(stored):
        sentence, quotes = render_sentence(
            "public_database_change",
            {
                "source": event.source,
                "version": event.version,
                "subject_key": event.subject_key,
                "previous_text": event.previous_text or "",
                "current_text": event.current_text or "",
            },
        )
        _append(pieces, spans, sentence, quotes)
    accepted = [
        (str(term["hpo_id"]), str(term["presence"]))
        for term in terms
        if term.get("presence") in ("present", "excluded")
    ]
    report = report_for(accepted)
    _append_comparison(pieces, spans, report)
    if report["abstained"]:
        present = sum(1 for term in terms if term.get("presence") == "present")
        sentence, quotes = render_sentence("not_confident_yet", {"confirmed_count": present})
        _append(pieces, spans, sentence, quotes)
    sentence, quotes = render_sentence("no_dose", {})
    _append(pieces, spans, sentence, quotes)
    _append(pieces, spans, country_footer(), [])
    return scan_notebook_text("\n".join(pieces), spans)


def pdf_text(data: bytes) -> str:
    chunks: list[str] = []
    for piece in data.split(b"Tj"):
        start = piece.rfind(b"(")
        end = piece.rfind(b")")
        if start < 0 or end < start:
            continue
        raw = piece[start + 1 : end]
        raw = raw.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
        chunks.append(raw.decode("cp1252", errors="replace"))
    return "\n".join(chunks)


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
