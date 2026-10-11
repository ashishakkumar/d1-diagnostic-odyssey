"""Commands for the public-case harness. Downloads stay behind `make eval-download`."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

from d1_eval.frequency import FrequencyBinScorer, frequency_table
from d1_eval.harness import (
    Pins,
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
    _fetch_orphanet(dest, pins.orphanet_url, pins.orphanet_fallback_url)
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
    standin = results_document(rows, pins, note, tool="term-overlap-loo")
    frequency_text, frequency_status = _frequency_rows(
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
    print(f"orphanet={frequency_status}")
    return 0


def _frequency_rows(
    loaded: StoreLoad,
    mapping: dict[str, set[str]],
    unique: set[str],
    excluded: int,
    parents: dict[str, tuple[str, str]],
    pins: Pins,
    xml_path: Path,
    error_path: Path,
) -> tuple[str, str]:
    note = (
        "Frequency-bin rows use the catalogue scorer on Orphanet phenotype frequencies. "
        "Abstentions are misses. The scorer thresholds were not changed for this run. "
        "A present term with no exact row uses the nearest annotated ancestor below "
        "HP:0000001 and HP:0000118. The background stays 0.05. "
        "The notebook ships this scorer. Term-overlap-loo copies terms from other packets "
        "in this release, so it uses the labels the score is judged against. It is not shipped."
    )
    if not xml_path.is_file():
        reason = (
            error_path.read_text().strip() if error_path.is_file() else "en_product4.xml is missing"
        )
        return f"Frequency-bin scorer did not run: {reason}\n", reason
    try:
        kept = {disease: mapping[disease] for disease in unique}
        freq_rows, orpha_to_disease = frequency_table(xml_path, kept)
        parent_ids = {hpo_id: pair[0] for hpo_id, pair in parents.items()}
        scorer = FrequencyBinScorer(freq_rows, orpha_to_disease, parent_ids)
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
                tool_version="0.0.1",
            ),
            status,
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        return f"Frequency-bin scorer did not run: {reason}\n", reason


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
