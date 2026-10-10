"""Count how large each monthly ClinVar change list is."""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .load import clinvar_index, gene_tokens
from .watch import fact_line

Index = dict[str, tuple[str, str, bool]]


@dataclass(frozen=True)
class ChangeSize:
    earlier: str
    later: str
    changed_variants: int
    changed_genes: int
    fact_bytes: int


def _one_month(
    earlier_version: str,
    earlier_index: Index,
    later_version: str,
    later_index: Index,
) -> ChangeSize:
    changed = 0
    genes: set[str] = set()
    fact_bytes = 0

    def add(left: tuple[str, str, bool] | None, right: tuple[str, str, bool] | None) -> None:
        nonlocal changed, fact_bytes
        left_text = None if left is None else left[0]
        right_text = None if right is None else right[0]
        if left_text == right_text:
            return
        changed += 1
        if left is not None:
            genes.update(gene_tokens(left[1]))
        if right is not None:
            genes.update(gene_tokens(right[1]))
        fact_bytes += len(fact_line("ClinVar", earlier_version, left_text).encode())
        fact_bytes += len(fact_line("ClinVar", later_version, right_text).encode())

    for key, left in earlier_index.items():
        add(left, later_index.get(key))
    for key, right in later_index.items():
        if key not in earlier_index:
            add(None, right)
    return ChangeSize(earlier_version, later_version, changed, len(genes), fact_bytes)


def monthly_change_sizes(paths: Sequence[Path]) -> list[ChangeSize]:
    sizes: list[ChangeSize] = []
    previous: tuple[str, Index] | None = None
    for path in paths:
        current = clinvar_index(Path(path))
        print(f"indexed {current[0]} {len(current[1])}", file=sys.stderr, flush=True)
        if previous is not None:
            sizes.append(_one_month(previous[0], previous[1], current[0], current[1]))
        previous = current
    return sizes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write the size of each monthly ClinVar change list."
    )
    parser.add_argument("archives", nargs="+", help="Dated variant_summary files, oldest first")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    sizes = monthly_change_sizes([Path(path) for path in args.archives])
    lines = ["earlier\tlater\tchanged_variants\tchanged_genes\tfact_bytes"]
    lines.extend(
        f"{row.earlier}\t{row.later}\t{row.changed_variants}\t{row.changed_genes}\t{row.fact_bytes}"
        for row in sizes
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
