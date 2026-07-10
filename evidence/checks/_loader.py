"""Shared solution loader for the objective-gate checkers.

Each objective-gated Python node ships a `*_check.py` whose gate command is
`python evidence/checks/<node>_check.py`. Running a script puts its directory
(`evidence/checks/`) on `sys.path[0]`, so every checker can `from _loader import
load_solution` — the leading underscore keeps it out of `pytest` collection
(which is scoped to `tests/`) and marks it as checker infrastructure, not a node
checker itself.

`load_solution` imports the learner's solution from the fixed artifacts path the
node body and artifact spec both name. Resolution is relative to *this file*, not
the cwd, so the only cwd contract the gate command carries is "run from the repo
root" (to find the checker). A missing solution is a clean `SystemExit`, not a
traceback — the learner hasn't written it yet, which is a plain instruction, not
a crash.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def check(condition: object, message: str) -> None:
    """Fail the gate with a loud, non-zero exit when `condition` is falsy.

    Deliberately not `assert`: Python run with `-O` (or `PYTHONOPTIMIZE`) strips
    assert statements, which would let a checker run to the end and exit 0 for a
    *wrong* solution — silently accepting anything. `raise SystemExit` is never
    optimized away, so the gate's verdict holds under any interpreter flags.
    """
    if not condition:
        raise SystemExit(f"FAILED: {message}")

# Every objective-gated node points its learner solution under here; the dir is
# gitignored, so the shipped seed carries checkers but never solutions. Bands
# home their solutions in a subdirectory (`programming/`, `data/`, …) so a node's
# artifacts never collide with another band's.
_ARTIFACTS_ROOT = Path(__file__).resolve().parents[1] / "artifacts"


def solution_path(filename: str, subdir: str = "programming") -> Path:
    """The fixed artifacts path a learner writes `filename` to, for band `subdir`.

    Resolved relative to *this file*, not the cwd — the SQL harness and the CSV
    checkers reuse this so every band names its solution the same way.
    """
    return _ARTIFACTS_ROOT / subdir / filename


def load_solution(filename: str, subdir: str = "programming") -> ModuleType:
    """Import and return the learner's solution module `filename` from `subdir`."""
    path = solution_path(filename, subdir)
    if not path.exists():
        raise SystemExit(
            f"no solution found at {path} — write your solution there first "
            "(see the node's Learning target for the required names and behavior)."
        )
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
