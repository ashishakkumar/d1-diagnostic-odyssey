"""The notebook component suite runs with the rest of make test."""

import subprocess
from pathlib import Path


def test_notebook_components() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(["npm", "--prefix", "apps/web", "test"], cwd=root, check=False)
    assert completed.returncode == 0
