"""Match a stored variant or gene to two local release snapshots."""

import re
from collections.abc import Callable, Sequence
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from d1_contracts import ChangeEvent, LabReportedVariant

from .records import CitedRow

# ponytail: variant_summary has no release day. observed_at is the first of the
# YYYY-MM in the archive name. The FTP Released column is not that day
# (variant_summary_2026-08.txt.gz was released 2026-08-06). A caller that has
# the listing date can replace this.
_MONTH = re.compile(r"(\d{4})-(\d{2})")


def fact_line(
    source: str,
    version: str,
    text: str | None,
    lab_words: str | None = None,
    lab_report_date: date | None = None,
) -> str:
    body = f"{source} {version}: {text if text is not None else 'not in this release'}"
    if lab_words is None and lab_report_date is None:
        return body
    report = lab_report_date.isoformat() if lab_report_date else ""
    return f"lab_words: {lab_words}; lab_report_date: {report}; {body}"


def release_instant(version: str) -> datetime | None:
    found = _MONTH.search(version)
    if not found:
        return None
    return datetime(int(found.group(1)), int(found.group(2)), 1, tzinfo=timezone.utc)


def diff_releases(
    earlier: Sequence[CitedRow],
    later: Sequence[CitedRow],
) -> list[tuple[CitedRow | None, CitedRow | None]]:
    by_earlier = {row.subject_key: row for row in earlier}
    by_later = {row.subject_key: row for row in later}
    pairs: list[tuple[CitedRow | None, CitedRow | None]] = []
    for key in sorted(set(by_earlier) | set(by_later), key=lambda item: (len(item), item)):
        left = by_earlier.get(key)
        right = by_later.get(key)
        left_text = None if left is None else left.text
        right_text = None if right is None else right.text
        if left_text != right_text:
            pairs.append((left, right))
    return pairs


def _index(rows: Sequence[CitedRow]) -> dict[str, CitedRow]:
    index: dict[str, CitedRow] = {}
    for row in rows:
        for key in row.match_keys:
            index.setdefault(key, row)
    return index


def _variant_keys(variant: LabReportedVariant) -> list[str]:
    raw = variant.variation.model_dump(mode="python")
    keys: list[str] = []
    ident = raw.get("id")
    if ident:
        keys.append(f"variation:{ident}")
        keys.append(f"allele:{ident}")
    for expr in raw.get("expressions") or []:
        value = expr.get("value") if isinstance(expr, dict) else getattr(expr, "value", None)
        if value:
            keys.append(f"hgvs:{value}")
            keys.append(f"name:{value}")
    return keys


def _snapshot_version(rows: Sequence[CitedRow]) -> str:
    if not rows:
        raise ValueError("snapshot is empty")
    return rows[0].version


def _event(
    earlier: CitedRow | None,
    later: CitedRow | None,
    earlier_version: str,
    later_version: str,
    case_id: UUID,
    variant: LabReportedVariant | None,
    new_id: Callable[[], UUID],
) -> ChangeEvent:
    sample = later or earlier
    if sample is None:
        raise ValueError("a change needs a row on at least one side")
    lab_words = None if variant is None else variant.lab_words
    lab_date = None if variant is None else variant.report_date
    source = sample.source
    return ChangeEvent(
        id=new_id(),
        case_id=case_id,
        source=source,
        version=later_version,
        subject_key=sample.subject_key,
        previous_text=fact_line(
            source,
            earlier.version if earlier is not None else earlier_version,
            None if earlier is None else earlier.text,
            lab_words=lab_words,
            lab_report_date=lab_date,
        ),
        current_text=fact_line(
            source,
            later.version if later is not None else later_version,
            None if later is None else later.text,
            lab_words=lab_words,
            lab_report_date=lab_date,
        ),
        observed_at=release_instant(later_version),
    )


def watch(
    *,
    earlier: Sequence[CitedRow],
    later: Sequence[CitedRow],
    variant: LabReportedVariant | None = None,
    gene_symbol: str | None = None,
    case_id: UUID | None = None,
    new_id: Callable[[], UUID] = uuid4,
) -> list[ChangeEvent]:
    if variant is None and not gene_symbol:
        raise ValueError("pass a lab-reported variant or a gene symbol")
    resolved_case = variant.case_id if variant is not None else case_id
    if resolved_case is None:
        raise ValueError("case_id is required when matching a gene")
    earlier_version = _snapshot_version(earlier)
    later_version = _snapshot_version(later)
    if variant is not None:
        index_earlier = _index(earlier)
        index_later = _index(later)
        chosen = next(
            (key for key in _variant_keys(variant) if key in index_earlier or key in index_later),
            None,
        )
        if chosen is None:
            return []
        left = index_earlier.get(chosen)
        right = index_later.get(chosen)
        if (None if left is None else left.text) == (None if right is None else right.text):
            return []
        return [_event(left, right, earlier_version, later_version, resolved_case, variant, new_id)]
    subjects: set[str] = set()
    gene_key = f"gene:{gene_symbol}"
    for row in (*earlier, *later):
        if gene_key in row.match_keys:
            subjects.add(row.subject_key)
    by_earlier = {row.subject_key: row for row in earlier}
    by_later = {row.subject_key: row for row in later}
    events: list[ChangeEvent] = []
    for subject in sorted(subjects, key=lambda item: (len(item), item)):
        left = by_earlier.get(subject)
        right = by_later.get(subject)
        if (None if left is None else left.text) == (None if right is None else right.text):
            continue
        events.append(
            _event(left, right, earlier_version, later_version, resolved_case, None, new_id)
        )
    return events
