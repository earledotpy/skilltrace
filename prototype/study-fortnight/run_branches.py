"""Branch matrix driver (G-StudyContract §5) on isolated fixtures.

Every branch is a separate throwaway fixture; stress branches never touch the
baseline. Hand-authored pass/review history below is fabricated scenario
history — written directly as labeled fixture data, never produced by
pass_node/master_node/delete_record, never in the real repo.

Outputs: prototype/study-fortnight/out/branches.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_lib import Recorder, build_fixture, clock_at, run_step  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
MATH = "math.arithmetic.order_operations_01"
PY = "programming.python.variables_01"
SQL = "data.sql.select_basics_01"
DF = "data.pandas.dataframe_basics_01"
CPF = "consolidation.python_fundamentals_01"
CDR = "consolidation.data_roundtrip_01"
STATE = "graph/state.yaml"
EV_REC = "evidence/evidence_records.yaml"
REVIEWS = "execution/reviews.yaml"
EDGES = "graph/edges.yaml"

rec = Recorder()


def append_text(root: Path, rel: str, extra: str) -> None:
    p = root / rel
    p.write_text(p.read_text(encoding="utf-8") + extra, encoding="utf-8")


def spec_of(root: Path, node: str) -> str | None:
    doc = yaml.safe_load((root / "evidence" / "artifact_specs.yaml").read_text(encoding="utf-8"))
    for s in doc["artifact_specs"]:
        if s["node_id"] == node:
            return s["id"]
    return None


def seed_history(root: Path, node: str, day: str, hh: int = 8, n_records: int = 1) -> None:
    """Fabricated starting fact: the node is passed (asserted by the scenario,
    hand-authored — never by pass_node) with accepted manual-gate evidence.
    Written by load-modify-dump so no duplicate keys are created."""
    art = root / "evidence" / "artifacts" / "fortnight"
    art.mkdir(parents=True, exist_ok=True)
    (art / "fabricated_history.md").write_text(
        f"# fabricated history for {node} (scenario data, not real learner evidence)\n",
        encoding="utf-8",
    )
    sp = root / STATE
    state = yaml.safe_load(sp.read_text(encoding="utf-8"))
    state["progress"][node] = {
        "state": "passed",
        "changed_at": f"{day}T{hh:02d}:00:00+00:00",
        "transitions": {"passed": f"{day}T{hh:02d}:00:00+00:00"},
    }
    sp.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8")
    spec = spec_of(root, node)
    ep = root / EV_REC
    ev = yaml.safe_load(ep.read_text(encoding="utf-8"))
    ev.setdefault("evidence_records", [])
    for i in range(1, n_records + 1):
        ev["evidence_records"].append({
            "id": f"ev.{node}.00{i}",
            "artifact_spec_id": spec,
            "location": "evidence/artifacts/fortnight/fabricated_history.md",
            "accepted": True,
            "accepted_by": "learner_manual",
            "created_at": f"{day}T{hh:02d}:30:00+00:00",
        })
    ep.write_text(yaml.safe_dump(ev, sort_keys=False, allow_unicode=True), encoding="utf-8")


def seed_review(root: Path, node: str, scheduled_for: str, created: str = "2026-09-20T08:00:00+00:00") -> None:
    """Fabricated starting fact: one scheduled review (hand-authored)."""
    rp = root / REVIEWS
    doc = yaml.safe_load(rp.read_text(encoding="utf-8"))
    doc.setdefault("reviews", [])
    doc["reviews"].append({
        "id": f"rev.{node}.001",
        "node_id": node,
        "status": "scheduled",
        "scheduled_for": scheduled_for,
        "created_at": created,
    })
    rp.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def prep(name: str, seed_fn=None) -> Path:
    root = build_fixture(name)
    run_step(root, clock_at("2026-09-21", 8, 0), ["sync"])
    if seed_fn:
        seed_fn(root)
    return root


def S(root: Path, clock, name: str, argv: list[str]) -> str:
    return rec.step(name, argv, root, clock)


def main() -> None:  # noqa: C901
    # B01 cold start — no history at all
    root = prep("b01_cold")
    rec.day("B01 — Cold start (no history)", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "today on day zero", ["today", "--minutes", "105"])
    S(root, c, "next on day zero", ["next", "--minutes", "105", "--limit", "3"])
    S(root, c, "today with 30 minutes", ["today", "--minutes", "30"])

    # B02 prior learning — pass direct from available (fabricated history)
    root = prep("b02_prior", lambda r: seed_history(r, DF, "2026-08-15"))
    rec.day("B02 — Prior learning (pass direct from available)", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "node view of the already-passed skill", ["node", DF])
    S(root, c, "next: does a passed node resurface?", ["next", "--minutes", "105", "--limit", "3"])
    S(root, c, "today with a passed skill in history", ["today", "--minutes", "105"])
    S(root, c, "starting a passed node (expected refusal)", ["start", DF])

    # B03 multiple active nodes
    def b03(r: Path) -> None:
        run_step(r, clock_at("2026-09-22", 9, 0), ["start", DF])
        run_step(r, clock_at("2026-09-22", 9, 5), ["close"])
        run_step(r, clock_at("2026-09-22", 9, 6), ["start", PY])
        run_step(r, clock_at("2026-09-22", 9, 7), ["close"])
    root = prep("b03_active", b03)
    rec.day("B03 — Multiple active nodes", "branch")
    c = clock_at("2026-09-24", 9, 0)
    S(root, c, "start a third strand (past the warn threshold of 2)", ["start", SQL])
    S(root, c, "today with three active strands", ["today", "--minutes", "105"])
    S(root, c, "next with three active strands", ["next", "--minutes", "105", "--limit", "5"])

    # B04 hard vs soft prerequisites
    root = prep("b04_prereq")
    edges = yaml.safe_load((root / EDGES).read_text(encoding="utf-8"))["edges"]
    hard = [e for e in edges if str(e["edge_type"]).startswith("hard") and e["source"] in (MATH, PY, SQL, DF)]
    soft = [e for e in edges if str(e["edge_type"]).startswith("soft") and e["source"] in (MATH, PY, SQL, DF)]
    he, se = hard[0], soft[0]
    rec.day("B04 — Hard vs soft prerequisites", "branch")
    rec.note("uncertainty", f"observing hard edge {he['id']} and soft edge {se['id']}")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "soft target before its helper is passed", ["node", se["target"]])
    S(root, c, "hard target before its prerequisite is passed", ["node", he["target"]])
    seed_history(root, he["source"], "2026-09-20")
    seed_history(root, se["source"], "2026-09-20")
    run_step(root, clock_at("2026-09-22", 9, 10), ["sync"])
    S(root, c, "soft target after its helper is passed", ["node", se["target"]])
    S(root, c, "hard target after its prerequisite is passed", ["node", he["target"]])
    rec.write(OUT / "branches.json")
    print("B01-B04 written")

    # B05 insufficient evidence — rejected artifact stays rejected
    root = prep("b05_insufficient")
    rec.day("B05 — Insufficient evidence (rejected artifact)", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "open the math entry", ["start", MATH])
    S(root, c, "learner rejects their own draft (manual gate)", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--reject"])
    S(root, c, "eligibility after the rejection", ["eligibility", MATH])
    S(root, c, "node view mid-struggle", ["node", MATH])
    S(root, c, "next while below the evidence bar", ["next", "--minutes", "105", "--limit", "3"])

    # B06 failed attempts below the remediation threshold (2 < 3)
    def attempts(r: Path, node: str, n: int) -> None:
        for i in range(1, n + 1):
            run_step(r, clock_at("2026-09-22", 9, i), ["attempt", "record", node, "--outcome", "failed", "--note", f"Failed practice {i}."])
    root = prep("b06_below", lambda r: attempts(r, PY, 2))
    rec.day("B06 — Failed attempts below threshold (2/3)", "branch")
    c = clock_at("2026-09-24", 9, 0)
    S(root, c, "remediation pressure at 2 failed attempts", ["suggest", "remediation"])
    S(root, c, "node view with 2 failed attempts", ["node", PY])
    S(root, c, "next with 2 failed attempts", ["next", "--minutes", "105", "--limit", "3"])

    # B07 failed attempts at the threshold (3/3) — edge activation signal
    root = prep("b07_at", lambda r: attempts(r, PY, 3))
    rec.day("B07 — Failed attempts at threshold (3/3)", "branch")
    c = clock_at("2026-09-24", 9, 0)
    S(root, c, "remediation pressure at the threshold", ["suggest", "remediation"])
    S(root, c, "node view at the threshold", ["node", PY])
    S(root, c, "next at the threshold", ["next", "--minutes", "105", "--limit", "3"])

    # B08 failed attempts above the threshold (4/3)
    root = prep("b08_above", lambda r: attempts(r, PY, 4))
    rec.day("B08 — Failed attempts above threshold (4/3)", "branch")
    c = clock_at("2026-09-24", 9, 0)
    S(root, c, "remediation pressure above the threshold", ["suggest", "remediation"])
    S(root, c, "today above the threshold", ["today", "--minutes", "105"])
    S(root, c, "eligibility is untouched by failures (node state unchanged)", ["eligibility", PY])

    # B09 blocker lifecycle
    root = prep("b09_blocker")
    rec.day("B09 — Blocker creation, remediation, resolution", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "open a session", ["start", PY])
    S(root, c, "stuck work", ["work", PY, "--blocked", "--minutes", "40", "--notes", "Stuck on loop scoping."])
    S(root, c, "create the blocker", ["blocker", "create", PY, "--description", "Loop variable scope confusion."])
    S(root, c, "open blockers", ["blockers"])
    S(root, c, "suggestions while blocked", ["suggest", "remediation"])
    S(root, c, "log a corrective action bound to the blocker", ["remediation", "create", PY, "--description", "Worked two scope exercises.", "--blocker", "blk." + PY + ".001"])
    S(root, c, "complete the corrective action", ["remediation", "complete", "rem." + PY + ".001", "--summary", "Exercises done; confusion resolved."])
    S(root, c, "resolve the blocker", ["blocker", "resolve", "blk." + PY + ".001", "--summary", "Scope model rebuilt with exercises."])
    S(root, c, "open blockers after resolution", ["blockers"])
    S(root, c, "suggestions after resolution", ["suggest", "remediation"])
    # B10 review grace boundary — due 2026-09-24, grace 2 days
    def b10(r: Path) -> None:
        seed_history(r, SQL, "2026-09-20")
        seed_review(r, SQL, "2026-09-24")
    root = prep("b10_grace", b10)
    rec.day("B10 — Due/overdue reviews around the 2-day grace boundary", "branch")
    S(root, clock_at("2026-09-24", 9, 0), "reviews on the due date", ["reviews"])
    S(root, clock_at("2026-09-24", 9, 0), "review suggestions on the due date", ["suggest", "reviews"])
    S(root, clock_at("2026-09-24", 9, 0), "today on the due date", ["today", "--minutes", "105"])
    S(root, clock_at("2026-09-25", 9, 0), "reviews one day late (inside grace)", ["reviews"])
    S(root, clock_at("2026-09-26", 9, 0), "reviews two days late (grace boundary)", ["reviews"])
    S(root, clock_at("2026-09-27", 9, 0), "reviews three days late (overdue)", ["reviews"])
    S(root, clock_at("2026-09-27", 9, 0), "today once overdue", ["today", "--minutes", "105"])
    S(root, clock_at("2026-09-27", 9, 0), "retention view", ["retention", "status"])

    # B11 failed review without demotion
    def b11(r: Path) -> None:
        seed_history(r, SQL, "2026-09-18")
        seed_review(r, SQL, "2026-09-25", created="2026-09-18T09:00:00+00:00")
    root = prep("b11_failed_review", b11)
    rec.day("B11 — Failed review without demotion", "branch")
    c = clock_at("2026-09-26", 9, 0)
    S(root, c, "node before the review", ["node", SQL])
    S(root, c, "complete the review unsatisfactorily", ["review", "complete", "rev." + SQL + ".001", "--outcome", "unsatisfactory", "--summary", "Forgot WHERE semantics; needs rework."])
    S(root, c, "node after the failed review (state must hold)", ["node", SQL])
    S(root, c, "reviews after completion", ["reviews"])
    S(root, c, "remediation pressure after the failed review", ["suggest", "remediation"])

    # B12 superseding correction chain (depth 3, observed via report)
    root = prep("b12_chain")
    rec.day("B12 — Superseding correction chain", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "open the math entry", ["start", MATH])
    t1 = S(root, c, "submit v1", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "v1", "--accept"])
    t2 = S(root, c, "submit v2 superseding v1", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--supersedes", "ev." + MATH + ".001", "--reason", "v1 wrong on item 3", "--accept"])
    S(root, c, "submit v3 superseding v2", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--supersedes", "ev." + MATH + ".002", "--reason", "v2 tightened steps", "--accept"])
    S(root, c, "evidence report shows the chain", ["report", "evidence"])
    S(root, c, "eligibility counts only live records", ["eligibility", MATH])

    # B13 broken / mismatched resource
    root = prep("b13_resource")
    rec.day("B13 — Broken resource and replacement refusal", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "mark the math resource broken", ["verify-resource", "khan-arithmetic", "--broken", "--reason", "Course reorganized; deep link dead."])
    S(root, c, "resources for the node afterwards", ["resources", "--node-id", MATH])
    S(root, c, "resource report", ["resource-report"])
    S(root, c, "node view with a broken resource", ["node", MATH])
    S(root, c, "today with a broken resource", ["today", "--minutes", "105"])
    S(root, c, "replace-resource with no verified candidate (expected refusal)", ["replace-resource", "khan-arithmetic", "--candidate", "none-exists"])

    # B14 interrupted / stale session
    root = prep("b14_stale")
    rec.day("B14 — Interrupted and stale session, honest close", "branch")
    S(root, clock_at("2026-10-01", 20, 0), "start a late-evening session", ["start", MATH])
    c = clock_at("2026-10-02", 9, 0)
    S(root, c, "today the next morning (13h open, stale > 12h)", ["today", "--minutes", "105"])
    S(root, c, "honest backdated close", ["close", "--end", "2026-10-01T21:45:00+00:00"])
    S(root, c, "today after the honest close", ["today", "--minutes", "105"])

    # B15 duplicate submission — new record; rejected stays rejected
    root = prep("b15_duplicate")
    rec.day("B15 — Duplicate submission and rejected-stays-rejected", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "open the math entry", ["start", MATH])
    S(root, c, "submit the same artifact twice (both kept)", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "first", "--accept"])
    S(root, c, "second identical submission", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "second", "--accept"])
    S(root, c, "a rejected record", ["submit", MATH, "--location", "evidence/artifacts/fortnight/order_operations_set_001.md", "--note", "rejected draft", "--reject"])
    S(root, c, "evidence report shows all records", ["report", "evidence"])
    S(root, c, "eligibility counts accepted records only", ["eligibility", MATH])
    # B16 sparse vs established history (two fixtures, one comparison)
    root = prep("b16_sparse")
    rec.day("B16a — Sparse history (1 session)", "branch")
    c = clock_at("2026-09-22", 9, 0)
    S(root, c, "one session", ["start", MATH])
    S(root, c, "one work item", ["work", MATH, "--minutes", "60", "--notes", "First ever stint."])
    S(root, c, "close", ["close"])
    S(root, c, "velocity on sparse history", ["analytics", "velocity"])
    S(root, c, "health on sparse history", ["health"])
    S(root, c, "today on sparse history", ["today", "--minutes", "105"])

    def b16b(r: Path) -> None:
        for i, day in enumerate(["2026-09-08", "2026-09-10", "2026-09-12"]):
            cc = clock_at(day, 9, 0)
            run_step(r, cc, ["start", MATH if i == 0 else PY])
            run_step(r, clock_at(day, 10, 30), ["work", MATH if i == 0 else PY, "--minutes", "60", "--notes", f"Session {i+1}."])
            run_step(r, clock_at(day, 11, 0), ["close"])
    root = prep("b16_established", b16b)
    rec.day("B16b — Established history (3-session full-data line)", "branch")
    c = clock_at("2026-09-14", 9, 0)
    S(root, c, "velocity on established history", ["analytics", "velocity"])
    S(root, c, "health on established history", ["health"])
    S(root, c, "today on established history", ["today", "--minutes", "105"])
    S(root, c, "retention on established history", ["retention", "status"])

    # B17 curriculum edit flips available<->locked while asserted progress holds
    root = prep("b17_flip")
    rec.day("B17 — Curriculum edit flips readiness; asserted progress holds", "branch")
    c = clock_at("2026-09-22", 9, 0)
    FRA = "math.arithmetic.fractions_01"
    S(root, c, "start the consolidation node (asserted progress)", ["start", CPF])
    S(root, c, "close its session (state stays active)", ["close"])
    orig = (root / EDGES).read_text(encoding="utf-8")
    doc = yaml.safe_load(orig)
    doc["edges"].append({
        "id": "edge.fixture.cdr_to_fra",
        "source": CDR,
        "target": FRA,
        "edge_type": "hard_prerequisite",
        "reason": "Fixture-only edit (reverted after observation).",
        "active": True,
        "created_at": "2026-09-22",
        "updated_at": "2026-09-22",
    })
    (root / EDGES).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    S(root, c, "graph impact on a non-git fixture (observed behavior)", ["graph", "impact"])
    S(root, c, "sync after the edit", ["sync"])
    S(root, c, "available node whose readiness flipped", ["node", FRA])
    S(root, c, "active node: asserted progress must hold", ["node", CPF])
    S(root, c, "today: the active node is still the thread", ["today", "--minutes", "105"])
    S(root, c, "next: does the flipped node disappear?", ["next", "--minutes", "105", "--limit", "3", "--show-locked"])
    (root / EDGES).write_text(orig, encoding="utf-8")
    run_step(root, clock_at("2026-09-22", 9, 20), ["sync"])
    S(root, c, "node after the edit is reverted", ["node", FRA])

    rec.write(OUT / "branches.json")
    print("all branches written")


if __name__ == "__main__":
    main()
