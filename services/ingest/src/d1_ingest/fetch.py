"""Download a public file. Matching never calls this."""

import re
from pathlib import Path
from urllib.request import urlretrieve

# ponytail: on 10 October 2026, 2025 and 2026 variant_summary files sat in
# archive/, and 2024 sat in archive/YYYY/. Recheck the listing if a month 404s.
_ARCHIVE = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive"


def clinvar_archive_url(month: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError(f"expected YYYY-MM, got {month}")
    name = f"variant_summary_{month}.txt.gz"
    year = int(month[:4])
    if year >= 2025:
        return f"{_ARCHIVE}/{name}"
    return f"{_ARCHIVE}/{year}/{name}"


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, dest)
    return dest
