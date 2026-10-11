import os
import subprocess
import sys
from pathlib import Path

from d1_ingest.load import load_clinvar
from d1_ingest.replay import main, monthly_change_sizes
from d1_ingest.watch import diff_releases, fact_line

FIXTURES = Path(__file__).parent / "fixtures"
ARCHIVES = [
    FIXTURES / "variant_summary_2024-01.txt",
    FIXTURES / "variant_summary_2024-02.txt",
    FIXTURES / "variant_summary_2024-03.txt",
]


def test_replay_counts_match_the_watcher_diff(tmp_path: Path):
    sizes = monthly_change_sizes(ARCHIVES)
    assert [(row.earlier, row.later, row.changed_variants) for row in sizes] == [
        ("2024-01", "2024-02", 1),
        ("2024-02", "2024-03", 2),
    ]
    assert sizes[0].changed_genes == 1
    assert sizes[1].changed_genes == 2
    january = load_clinvar(ARCHIVES[0])
    february = load_clinvar(ARCHIVES[1])
    pairs = diff_releases(january, february)
    assert len(pairs) == sizes[0].changed_variants
    expected_bytes = 0
    for earlier, later in pairs:
        text_earlier = None if earlier is None else earlier.text
        text_later = None if later is None else later.text
        version_earlier = "2024-01" if earlier is None else earlier.version
        version_later = "2024-02" if later is None else later.version
        expected_bytes += len(fact_line("ClinVar", version_earlier, text_earlier).encode())
        expected_bytes += len(fact_line("ClinVar", version_later, text_later).encode())
    assert sizes[0].fact_bytes == expected_bytes

    out = tmp_path / "change-list-size.tsv"
    code = main([str(path) for path in ARCHIVES] + ["--out", str(out)])
    assert code == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "earlier\tlater\tchanged_variants\tchanged_genes\tfact_bytes"
    assert lines[1].startswith("2024-01\t2024-02\t1\t1\t")
    assert lines[2].startswith("2024-02\t2024-03\t2\t2\t")


def test_replay_module_writes_the_size_file(tmp_path: Path):
    out = tmp_path / "change-list-size.tsv"
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "d1_ingest.replay",
            "--out",
            str(out),
            *[str(path) for path in ARCHIVES],
        ],
        cwd=root,
        env={
            **os.environ,
            "PYTHONPATH": f"{root / 'services' / 'ingest' / 'src'}:{root / 'contracts' / 'src'}",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert out.read_text(encoding="utf-8").splitlines()[1].startswith("2024-01\t2024-02\t1\t1\t")
