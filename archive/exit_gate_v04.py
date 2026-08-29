#!/usr/bin/env python3
"""v0.4.0-rc1 exit-gate runner (issue #16).

Runs the roadmap's documented v0.4 exit-gate sequence and exits non-zero if any
step fails, so an RC sign-off is a single repeatable command:

    python scripts/exit_gate_v04.py

Steps (roadmap v0.4 "Exit gate"):

    1. pytest tests/evidence
    2. skilltrace validate evidence
    3. skilltrace eligibility math.arithmetic.order_operations_01

The CLI is invoked as `python -m skilltrace` (not the bare `skilltrace` shim) so
the gate runs on a fresh clone without the console script on PATH, and offline —
nothing here touches the network. Mirrors `scripts/exit_gate_v03.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_NODE = "math.arithmetic.order_operations_01"

STEPS: list[tuple[str, list[str]]] = [
    ("pytest tests/evidence", [sys.executable, "-m", "pytest", "tests/evidence", "-q"]),
    ("validate evidence", [sys.executable, "-m", "skilltrace", "validate", "evidence"]),
    (f"eligibility {_NODE}", [sys.executable, "-m", "skilltrace", "eligibility", _NODE]),
]


def main() -> int:
    failures: list[str] = []
    for label, argv in STEPS:
        print(f"\n=== v0.4 exit gate: {label} ===", flush=True)
        result = subprocess.run(argv, cwd=REPO_ROOT)
        if result.returncode != 0:
            failures.append(label)

    print("\n" + "=" * 60)
    if failures:
        print(f"v0.4 exit gate FAILED: {', '.join(failures)}")
        return 1
    print("v0.4 exit gate PASSED: all steps green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
