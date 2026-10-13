"""Commands for the public-case harness. Downloads stay behind `make eval-download`."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

from d1_eval.bars import measure_bars
from d1_eval.frequency import FrequencyBinScorer, frequency_table
from d1_eval.harness import (
    Pins,
    RunResult,
    StoreLoad,
    TermOverlapScorer,
    check_store_file,
    count_terms,
    degrade,
    holdout_from_counts,
    load_cases,
    load_catalogue,
    load_orphanet_tsv,
    load_parents,
    load_pins,
    orphanet_from_mondo_nodes,
    parents_from_obo,
    present_hpo_ids,
    rank_case,
    results_document,
    run_eval,
    summarize,
    time_split,
    time_split_note,
    unique_orphanet,
)
from d1_eval.heldout import main as heldout_main

LEVELS = ("full", "fewer", "vaguer", "patient")
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Public-case evaluation harness")
    commands = parser.add_subparsers(dest="command", required=True)

    fixtures = commands.add_parser("fixtures")
    fixtures.add_argument("--out", type=Path, required=True)

    download = commands.add_parser("download")
    download.add_argument("--dest", type=Path, required=True)

    store = commands.add_parser("store")
    store.add_argument("--data", type=Path, required=True)
    store.add_argument("--out", type=Path, required=True)

    bars = commands.add_parser("bars")
    bars.add_argument("--data", type=Path, required=True)
    bars.add_argument("--out", type=Path, required=True)

    heldout = commands.add_parser("heldout")
    heldout.add_argument("--data", type=Path, required=True)
    heldout.add_argument("--choice", type=Path, required=True)
    heldout.add_argument("--out", type=Path, required=True)
    heldout.add_argument("--record", type=Path, required=True)
    heldout.add_argument("--results", type=Path, required=False)

    check = commands.add_parser("check-download")
    check.add_argument("--data", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "fixtures":
        return _fixtures(args.out)
    if args.command == "download":
        return _download(args.dest)
    if args.command == "check-download":
        return _check(args.data)
    if args.command == "store":
        return _store(args.data, args.out)
    if args.command == "bars":
        return _bars(args.data, args.out)
    if args.command == "heldout":
        heldout_main(args.data, args.choice, args.out, args.results, args.record)
        return 0
    raise ValueError(args.command)


def _bars(data: Path, out: Path) -> int:
    text = measure_bars(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


def _fixtures(out: Path) -> int:
    pins = load_pins()
    loaded = load_cases(FIXTURES / "packets")
    parents = load_parents(FIXTURES / "parents.tsv")
    catalogue = load_catalogue(FIXTURES / "catalogue.json")
    mapping = load_orphanet_tsv(FIXTURES / "orphanet.tsv")
    rows = []
    for level in LEVELS:
        degraded = tuple(degrade(case, level, parents, pins.keep_fraction) for case in loaded.cases)
        result = run_eval(
            degraded,
            TermOverlapScorer(catalogue),
            catalogue,
            mapping,
            pins.ks,
            pins.tied_at_best,
        )
        rows.append((level, result))
    note = time_split_note(time_split(loaded.cases, pins.knowledge_cutoff))
    out.write_text(results_document(rows, pins, note))
    full = rows[0][1]
    print(f"excluded_diseases={full.excluded_diseases}")
    print(f"top1={full.hits[1]}/{full.packets_scored}")
    print(f"top3={full.hits[3]}/{full.packets_scored}")
    print(f"top10={full.hits[10]}/{full.packets_scored}")
    print(f"no_confident={full.no_confident}/{full.packets_scored}")
    return 0


def _download(dest: Path) -> int:
    pins = load_pins()
    dest.mkdir(parents=True, exist_ok=True)
    _fetch(pins.store_url, dest / "all_phenopackets.zip")
    check_store_file(dest / "all_phenopackets.zip", pins)
    _fetch(pins.mondo_url, dest / "mondo_nodes.tsv")
    _fetch(pins.hpo_url, dest / "hp.obo")
    _fetch_orphanet(dest, pins.orphanet_url, pins.orphanet_fallback_url)
    print(f"downloaded {dest}")
    return 0


def _check(dest: Path) -> int:
    check_store_file(dest / "all_phenopackets.zip", load_pins())
    print("store zip matches the pin")
    return 0


def _archive_previous(previous: str) -> str:
    """Keep an earlier frequency-bin 0.0.1 document when a new run is written."""
    marker = "| full | frequency-bin | 0.0.1 |"
    if marker not in previous:
        return ""
    heading = previous.rfind("# Public-case method results", 0, previous.find(marker))
    if heading == -1:
        body = previous
    else:
        body = previous[heading:].lstrip("\n")
    body = body.replace(
        "The background stays 0.05. The notebook ships this scorer.",
        "The background stays 0.05. This archived run is not the shipped scorer.",
    )
    banner = (
        "# Archived frequency-bin 0.0.1\n\n"
        "The notebook does not ship this block. It is the earlier flat-background run, "
        "kept so the 1292/4815 rows stay next to the 0.0.2 document above.\n\n"
    )
    return banner + body


def _store(data: Path, out: Path) -> int:
    previous = out.read_text() if out.is_file() else ""
    pins = load_pins()
    check_store_file(data / "all_phenopackets.zip", pins)
    loaded = load_cases(data / "all_phenopackets.zip")
    mapping = orphanet_from_mondo_nodes(data / "mondo_nodes.tsv")
    obo = data / "hp.obo"
    parents = parents_from_obo(obo) if obo.exists() else {}
    unique, excluded = unique_orphanet(loaded.disease_ids, mapping)
    note = time_split_note(time_split(loaded.cases, pins.knowledge_cutoff))
    note += (
        " The term-overlap-loo catalogue is other packets in this same store release, "
        "with the packet being scored left out. It is not an Orphanet frequency table."
    )
    counts = count_terms(loaded.cases, unique)
    rows = []
    for level in LEVELS:
        print(f"level={level}", flush=True)
        ranked = []
        for case in loaded.cases:
            degraded = degrade(case, level, parents, pins.keep_fraction)
            catalogue = holdout_from_counts(
                counts,
                case.truth_disease_id,
                set(present_hpo_ids(case)),
            )
            ranked.append(
                rank_case(
                    degraded,
                    TermOverlapScorer(catalogue),
                    unique,
                    pins.tied_at_best,
                )
            )
        rows.append((level, summarize(ranked, excluded, pins.ks)))
    standin = results_document(rows, pins, note, tool="term-overlap-loo")
    frequency_text, frequency_status, frequency_full = _frequency_rows(
        loaded,
        mapping,
        unique,
        excluded,
        parents,
        pins,
        data / "en_product4.xml",
        data / "orphanet-error.txt",
    )
    text = frequency_text + "\n" + standin
    text += "\n" + f"mondo_sha256: {_sha256(data / 'mondo_nodes.tsv')}\n"
    text += f"hpo_version: {pins.hpo_version}\n"
    if parents:
        text += f"hpo_sha256: {_sha256(obo)}\n"
    else:
        text += "hpo parent map was not loaded, so vaguer left the terms as they were.\n"
    text += f"packets_skipped: {loaded.skipped}\n"
    text += f"orphanet: {frequency_status}\n"
    archived = _archive_previous(previous)
    if archived:
        text = text.rstrip() + "\n\n" + archived
        if not text.endswith("\n"):
            text += "\n"
    out.write_text(text)
    print(
        command_summary(
            frequency_full,
            rows[0][1],
            skipped=loaded.skipped,
            orphanet=frequency_status,
        ),
        end="",
    )
    return 0


def command_summary(
    frequency: RunResult | None,
    standin: RunResult,
    *,
    skipped: int,
    orphanet: str,
) -> str:
    """Print the shipped frequency-bin totals. Label the term-overlap stand-in."""
    headline = frequency if frequency is not None else standin
    lines = [
        f"excluded_diseases={headline.excluded_diseases}",
        f"packets_scored={headline.packets_scored}",
        f"packets_not_unique={headline.packets_not_unique}",
        f"packets_skipped={skipped}",
    ]
    if frequency is None:
        lines.append("frequency-bin did not run")
    else:
        scored = frequency.packets_scored
        lines.append(f"frequency-bin top1={frequency.hits[1]}/{scored}")
        lines.append(f"frequency-bin top3={frequency.hits[3]}/{scored}")
        lines.append(f"frequency-bin top10={frequency.hits[10]}/{scored}")
        lines.append(f"frequency-bin no_confident={frequency.no_confident}/{scored}")
    standin_scored = standin.packets_scored
    lines.append(f"term-overlap-loo top1={standin.hits[1]}/{standin_scored}")
    lines.append(f"orphanet={orphanet}")
    return "\n".join(lines) + "\n"


def _frequency_rows(
    loaded: StoreLoad,
    mapping: dict[str, set[str]],
    unique: set[str],
    excluded: int,
    parents: dict[str, tuple[str, str]],
    pins: Pins,
    xml_path: Path,
    error_path: Path,
) -> tuple[str, str, RunResult | None]:
    note = (
        "Frequency-bin 0.0.2 uses P(feature | not this disease) = (k + 1) / (n + 2) "
        "on every disorder in en_product4, including disorders that are not ranked. "
        "A missing row contributes a ratio of 1. Abstentions are misses. "
        "CLOSE_DISEASE_COUNT stays 10 and CLOSE_FACTOR stays 2.0. They were not refit. "
        "An ancestor climb on the older flat 0.05 background lowered full-set top-1 "
        "from 1292/4815 to 841/4815. A train-only climb on this background is in "
        "eval/bars-resnik.md and is not used by this command. This run does not pass a parent map. "
        "Degree baseline and precision@k at k = 1 and k = 5 for frequency-bin are in "
        "eval/bars-0.0.2.md. Frequency-bin does not beat that baseline. "
        "The public-case ranker is Resnik best-match average in eval/bars-resnik.md. "
        "The synthetic notebook card uses frequency-bin. "
        "Term-overlap-loo copies terms from other packets in this release, "
        "so it uses the labels the score is judged against. It is not shipped."
    )
    if not xml_path.is_file():
        reason = (
            error_path.read_text().strip() if error_path.is_file() else "en_product4.xml is missing"
        )
        return f"Frequency-bin scorer did not run: {reason}\n", reason, None
    try:
        kept = {disease: mapping[disease] for disease in unique}
        freq_rows, orpha_to_disease = frequency_table(xml_path, kept)
        scorer = FrequencyBinScorer(freq_rows, orpha_to_disease)
        ranked_rows = []
        for level in LEVELS:
            print(f"frequency level={level}", flush=True)
            ranked = [
                rank_case(
                    degrade(case, level, parents, pins.keep_fraction),
                    scorer,
                    unique,
                    pins.tied_at_best,
                )
                for case in loaded.cases
            ]
            ranked_rows.append((level, summarize(ranked, excluded, pins.ks)))
        status = f"{pins.orphanet_version} sha256 {_sha256(xml_path)} rows {len(freq_rows)}"
        return (
            results_document(
                ranked_rows,
                pins,
                note,
                tool="frequency-bin",
                tool_version="0.0.2",
            ),
            status,
            ranked_rows[0][1],
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        return f"Frequency-bin scorer did not run: {reason}\n", reason, None


def _fetch_orphanet(dest: Path, url: str, fallback: str) -> None:
    target = dest / "en_product4.xml"
    error_path = dest / "orphanet-error.txt"
    if target.is_file() and target.stat().st_size > 0:
        return
    errors: list[str] = []
    for candidate in (url, fallback):
        if not candidate:
            continue
        try:
            _fetch(candidate, target)
        except Exception as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
            continue
        if error_path.exists():
            error_path.unlink()
        return
    error_path.write_text("\n".join(errors) + "\n")


def _fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception:
        if dest.exists():
            dest.unlink()
        raise


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
