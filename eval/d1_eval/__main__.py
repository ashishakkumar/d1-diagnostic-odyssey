"""Commands for the public-case harness. Downloads stay behind `make eval-download`."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

from d1_eval.harness import (
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
    raise ValueError(args.command)


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
    print(f"downloaded {dest}")
    return 0


def _check(dest: Path) -> int:
    check_store_file(dest / "all_phenopackets.zip", load_pins())
    print("store zip matches the pin")
    return 0


def _store(data: Path, out: Path) -> int:
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
    text = results_document(rows, pins, note, tool="term-overlap-loo")
    text += "\n" + f"mondo_sha256: {_sha256(data / 'mondo_nodes.tsv')}\n"
    text += f"hpo_version: {pins.hpo_version}\n"
    if parents:
        text += f"hpo_sha256: {_sha256(obo)}\n"
    else:
        text += "hpo parent map was not loaded, so vaguer left the terms as they were.\n"
    text += f"packets_skipped: {loaded.skipped}\n"
    out.write_text(text)
    full = rows[0][1]
    print(f"excluded_diseases={excluded}")
    print(f"packets_scored={full.packets_scored}")
    print(f"packets_not_unique={full.packets_not_unique}")
    print(f"packets_skipped={loaded.skipped}")
    print(f"top1={full.hits[1]}/{full.packets_scored}")
    print(f"top3={full.hits[3]}/{full.packets_scored}")
    print(f"top10={full.hits[10]}/{full.packets_scored}")
    print(f"no_confident={full.no_confident}/{full.packets_scored}")
    return 0


def _fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    urllib.request.urlretrieve(url, dest)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
