"""Discovery and Health probes on identical inputs (contract §4.1 + §d).

Discovery probes run on a fresh fixture; Health probes run read-only against
the finished baseline fixture (day-14 clock). Every probe is a real
read-only engine observation; proposed-UI renderings live only in the HTML,
labeled PROPOSED.

Outputs: prototype/study-fortnight/out/probes.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_lib import Recorder, build_fixture, clock_at, run_step  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"

rec = Recorder()


def S(root, clock, name, argv):
    return rec.step(name, argv, root, clock)


def main() -> None:
    root = build_fixture("discovery")
    run_step(root, clock_at("2026-09-22", 9, 0), ["sync"])
    rec.day("Discovery probes (identical inputs, current engine)", "probe")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "the only discovery surface's flags (no query parameter)", ["next", "--help"])
    S(root, c, "intent probe: 'python for beginners' has no search input anywhere", ["next", "--minutes", "105", "--limit", "5"])
    S(root, c, "synonym probe: guess the id 'variables_01' without the full path", ["node", "variables_01"])
    S(root, c, "synonym probe: guess 'python.vars_01'", ["node", "programming.python.vars_01"])
    S(root, c, "ambiguity probe: two plausible chart skills, no way to search", ["node", "data.visualization.choosing_charts_01"])
    S(root, c, "ambiguity probe: the sibling chart skill", ["node", "data.visualization.plotting_basics_01"])
    S(root, c, "no-results probe: nonsense id", ["node", "nonexistent.foo_01"])
    S(root, c, "locked-skill probe: a locked calculus entry", ["node", "math.calculus.integral_intuition_01"])
    S(root, c, "locked skills in next (does --show-locked render them?)", ["next", "--minutes", "105", "--limit", "3", "--show-locked"])
    S(root, c, "math strand breadth probe (learner browsing math)", ["next", "--minutes", "105", "--limit", "12"])
    S(root, c, "negative probe: empty summaries in graph (0/100 exist — case not present)", ["node", MATH] if False else ["node", "math.arithmetic.order_operations_01"])

    # Health probes against the finished baseline fixture (identical inputs)
    base = Path(__file__).resolve().parent / "fixture" / "baseline"
    rec.day("Health probes (current engine, baseline day-14 state)", "probe")
    c = clock_at("2026-10-05", 9, 0)
    S(base, c, "health roll-up", ["health"])
    S(base, c, "evidence warnings detail", ["validate", "evidence"])
    S(base, c, "review health", ["report", "reviews"])
    S(base, c, "blocker health", ["report", "blockers"])
    S(base, c, "progress health", ["report", "progress"])
    S(base, c, "resource health", ["resource-report"])
    S(base, c, "review suggestions", ["suggest", "reviews"])
    S(base, c, "remediation suggestions", ["suggest", "remediation"])

    rec.write(OUT / "probes.json")
    print("probes written")


if __name__ == "__main__":
    main()
