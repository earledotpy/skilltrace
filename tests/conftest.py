"""Top-level pytest conftest.

Makes the `tests/` directory importable so layer `conftest.py` files can
`from _builders import write_node` and reach the shared node-writing helper
(issue #117, Slice B). Adds `tests/` to `sys.path` exactly once per pytest
run.

Adding this conftest is not a `tests/` reorg: the directory layout, the
per-layer `conftest.py` files, the test discovery path, and the existing
fixtures are all unchanged. Only the import seam that lets the seven
write_node copies collapse to one shared helper is added.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
