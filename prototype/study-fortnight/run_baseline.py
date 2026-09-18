"""Run the locked fortnight baseline (G-StudyContract §2) on fixture v0.

Eight 105-minute sessions on days 1/3/5/7/8/10/12/14; Day 1 = 2026-09-22 UTC.
Every step is a real read-only derivation or a fixture-local learner command.
pass_node/master_node/delete_record are never invoked. All timestamps are
fixture-clock values, labeled in the reports.

Outputs: prototype/study-fortnight/out/baseline.json
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_lib import Recorder, build_fixture, clock_at, run_step  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"

MATH = "math.arithmetic.order_operations_01"
PY = "programming.python.variables_01"
SQL = "data.sql.select_basics_01"


def seed_artifacts(root: Path) -> None:
    """Fabricated learner artifacts (scenario history, labeled)."""
    art = root / "evidence" / "artifacts" / "fortnight"
    art.mkdir(parents=True, exist_ok=True)
    (art / "order_operations_set_001.md").write_text(
        "# Order of operations set 001 (fabricated fixture artifact)\n\n"
        "1. 3 + 4 x 2 = 11 (multiply before add).\n"
        "2. (8 - 3) / 5 + 1**2 = 2 (group, exponent, divide).\n"
        "3. 6 / 2(1+2) resolved left-to-right after parens.\n",
        encoding="utf-8",
    )
    (art / "variables_set_001.md").write_text(
        "# Variables set 001 (fabricated fixture artifact)\n\n"
        "First script: variables, print, input; reassignment confusion on day 10.\n",
        encoding="utf-8",
    )


def main() -> None:
    root = build_fixture("baseline")
    rec = Recorder()
    seed_artifacts(root)

    def D(day: str, day_id: str):
        rec.day(f"Day {day_id}", day)
        return clock_at(day)

    # ---- Day 1 (2026-09-22) — discovery, select entry, open, first work
    c = D("2026-09-22", "1")
    rec.step("bootstrap: refresh readiness on the fabricated fixture", ["sync"], root, c)
    rec.step("today opens the day", ["today", "--minutes", "105"], root, c)
    rec.step("recommendations sized to the session", ["next", "--minutes", "105", "--limit", "5"], root, c)
    rec.step("discovery probe: locked skills visible?", ["next", "--show-locked", "--limit", "3"], root, c)
    rec.step("discovery probe: math entry detail", ["node", MATH], root, c)
    rec.step("discovery probe: python entry detail", ["node", PY], root, c)
    rec.step("discovery probe: sql entry detail", ["node", SQL], root, c)
    rec.step("resources for the chosen math entry", ["resources", "--node-id", MATH], root, c)
    rec.step("open the session on the math entry", ["start", MATH], root, c)
    rec.step("first artifact work", ["work", MATH, "--minutes", "70", "--notes", "Read Khan arithmetic intro; worked 12 problems."], root, c)
    rec.step("close the session honestly", ["close"], root, c)

    # ---- Day 3 (2026-09-24) — return to unfinished work, evidence inspection
    c = D("2026-09-24", "3")
    rec.step("today: what is unfinished?", ["today", "--minutes", "105"], root, c)
    rec.step("re-read the entry's evidence bar", ["node", MATH], root, c)
    rec.step("continue the artifact", ["work", MATH, "--minutes", "80", "--notes", "Sets 2-3; error pattern in nested parens."], root, c)
    # ---- Day 5 (2026-09-26) — discovery round 2, second strand, artifact work
    c = D("2026-09-26", "5")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("discovery round 2", ["next", "--minutes", "105", "--limit", "8"], root, c)
    rec.step("probe the Python entry", ["node", PY], root, c)
    rec.step("resources for the Python entry", ["resources", "--node-id", PY], root, c)
    rec.step("open the Python-strand session", ["start", PY], root, c)
    rec.step("Python artifact work", ["work", PY, "--minutes", "90", "--notes", "First script: variables, print, input."], root, c)
    rec.step("close", ["close"], root, c)

    # ---- Day 7 (2026-09-28) — submission + gate judgment readout
    c = D("2026-09-28", "7")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("submit without a manual verdict (observe the refusal path)", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "Set 001, three worked problems."], root, c)
    txt = rec.step("scripted learner's manual gate verdict (fabricated learner command)", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "Set 001, three worked problems.", "--accept"], root, c)
    m = re.search(r"ev\.[\w.\-]+", txt)
    rec.step("gate readback: is the node eligible?", ["eligibility", MATH], root, c)
    rec.step("today after the verdict", ["today", "--minutes", "105"], root, c)
    rec.step("close", ["close"], root, c)

    # ---- Day 8 (2026-09-29) — third strand, artifact work (no pass)
    c = D("2026-09-29", "8")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("probe the SQL entry", ["node", SQL], root, c)
    rec.step("open the SQL-strand session", ["start", SQL], root, c)
    rec.step("SQL artifact work (session ends without a pass)", ["work", SQL, "--minutes", "105", "--notes", "SELECT basics; WHERE filters partial."], root, c)
    rec.step("close", ["close"], root, c)

    # ---- Day 10 (2026-10-01) — blocker/failure handling
    c = D("2026-10-01", "10")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("open a Python return session", ["start", PY], root, c)
    rec.step("hit the wall honestly", ["work", PY, "--blocked", "--minutes", "45", "--notes", "Immutable reassignment confusion; needs a different source."], root, c)
    rec.step("record the failed attempt (immutable fact)", ["attempt", "record", PY, "--outcome", "failed", "--note", "Practice check failed on reassignment item."], root, c)
    rec.step("name the persistent stuckness", ["blocker", "create", PY, "--description", "Reassignment vs copy semantics not landing from current resource."], root, c)
    rec.step("open blockers", ["blockers"], root, c)
    rec.step("remediation pressure", ["suggest", "remediation"], root, c)
    rec.step("close", ["close"], root, c)

    # ---- Day 12 (2026-10-03) — return, correction/supersession
    c = D("2026-10-03", "12")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("resolve the blocker with how", ["blocker", "resolve", "blk." + PY + ".001", "--summary", "Found a tutorial with explicit rebinding diagrams; confusion cleared."], root, c)
    rec.step("log the corrective intervention", ["remediation", "create", PY, "--description", "Re-did variables practice from alternate source.", "--blocker", "blk." + PY + ".001"], root, c)
    if m:
        rid = m.group(0)
        txt2 = rec.step("supersede the day-7 record (real id " + rid + ")", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--supersedes", rid, "--reason", "Item 3 conclusion was wrong; corrected work attached.", "--accept"], root, c)
        m2 = re.search(r"ev\.[\w.\-]+", txt2)
        if m2:
            rec.step("supersede the superseding record (correction chain depth 2)", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--supersedes", m2.group(0), "--reason", "Typo in item 2 steps; tightened.", "--accept"], root, c)
        else:
            rec.note("uncertainty", "supersede of the day-7 record produced no new record id; output kept verbatim below")
            rec.days[-1]["steps"][-1]["output"] += "\n[chain-depth-2 raw output]\n" + txt2
    rec.step("evidence inspection after correction", ["eligibility", MATH], root, c)
    rec.step("close", ["close"], root, c)

    # ---- Day 14 (2026-10-05) — close honestly, final inspection, day report
    c = D("2026-10-05", "14")
    rec.step("today", ["today", "--minutes", "105"], root, c)
    rec.step("SQL evidence inspection (stays unfinished)", ["eligibility", SQL], root, c)
    rec.step("close the final session", ["close"], root, c)
    rec.step("progress report", ["report", "progress"], root, c)
    rec.step("evidence report", ["report", "evidence"], root, c)
    rec.step("blocker report", ["report", "blockers"], root, c)
    rec.step("review listing", ["reviews"], root, c)
    rec.step("retention status", ["retention", "status"], root, c)
    rec.step("analytics: velocity", ["analytics", "velocity"], root, c)
    rec.step("analytics: blockers", ["analytics", "blockers"], root, c)
    rec.step("health roll-up", ["health"], root, c)

    rec.write(OUT / "baseline.json")
    print("baseline written")


if __name__ == "__main__":
    main()
