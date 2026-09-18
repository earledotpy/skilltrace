"""Follow-up probes: replace-resource positional form (fixes B13's flag error),
plus full `report evidence` chain readout and stale-session warning detail.

Outputs: prototype/study-fortnight/out/probes2.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_lib import Recorder, build_fixture, clock_at, run_step  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"

rec = Recorder()


def main() -> None:
    root = build_fixture("b13b_replace")
    run_step(root, clock_at("2026-09-22", 9, 0), ["sync"])
    rec.day("B13b — replace-resource, positional form (corrected invocation)", "probe")
    c = clock_at("2026-09-22", 9, 0)
    rec.step("mark the math resource broken", ["verify-resource", "khan-arithmetic", "--broken", "--reason", "Course reorganized; deep link dead."], root, c)
    rec.step("retire it onto a verified candidate from another strand", ["replace-resource", "khan-arithmetic", "python-tutorial"], root, c)
    rec.step("resources for the math node afterwards", ["resources", "--node-id", "math.arithmetic.order_operations_01"], root, c)

    base = Path(__file__).resolve().parent / "fixture" / "baseline"
    rec.day("Detail reads on the finished baseline", "probe")
    c = clock_at("2026-10-05", 9, 0)
    rec.step("evidence report: supersession chain", ["report", "evidence"], base, c)
    rec.step("b14-style stale readback on the real baseline session store", ["today", "--minutes", "105"], base, c)

    rec.write(OUT / "probes2.json")
    print("probes2 written")


if __name__ == "__main__":
    main()
