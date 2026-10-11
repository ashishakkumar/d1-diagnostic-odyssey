"""Import the safety package from this repo without an editable install."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SAFETY = _ROOT / "services" / "safety"
if str(_SAFETY) not in sys.path:
    sys.path.insert(0, str(_SAFETY))
