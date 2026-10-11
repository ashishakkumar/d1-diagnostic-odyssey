"""Start only with the local track variable and a typed acknowledgement file."""

from pathlib import Path
from typing import Mapping


class GateError(RuntimeError):
    """The engine refuses to start or to bind."""


ACK_TEXT = (
    "experimental-local: I understand this engine is research only "
    "and must not be used on a real person's data.\n"
)
BANNER = "EXPERIMENTAL, RESEARCH ONLY. For research use only. Not for use in diagnostic procedures."
GRADE = "research-grade, unverified, confirm in a clinical lab"
LOOPBACK = "127.0.0.1"


def acknowledgement_ok(path: Path) -> bool:
    try:
        return path.read_text(encoding="utf-8") == ACK_TEXT
    except OSError:
        return False


def resolve_bind(host: str | None) -> str:
    if host is None or host == "":
        return LOOPBACK
    if host != LOOPBACK:
        raise GateError("the engine binds to loopback only")
    return host


def start_allowed(environ: Mapping[str, str], ack_path: Path) -> bool:
    if environ.get("D1_TRACK") != "experimental-local":
        return False
    if environ.get("D1_BIND") not in (None, "", LOOPBACK):
        return False
    return acknowledgement_ok(ack_path)
