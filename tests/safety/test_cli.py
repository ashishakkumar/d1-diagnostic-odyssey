"""The make target calls this module. A forbidden template fails the process."""

from d1_safety.__main__ import main


def test_safety_scan_exits_clean_on_the_shipped_templates() -> None:
    assert main() == 0
