#!/usr/bin/env python3
"""Interactive prototype for SkillTrace reports design (Issue #31).

Mocks terminal outputs for the four reports:
1. Blocker report
2. Review report
3. Evidence report
4. Progress report

Information design variants:
- [A] Actionable / Diagnostic (status-forward, grouped by urgency, direct actions)
- [B] Mentor / Guided (conversational overview, context, guided next moves)
- [C] Structural Ledger (compact, table/card layout, audit-oriented)

Run:
  python archive/prototype_reports_design_issue_31.py
  python archive/prototype_reports_design_issue_31.py --report progress --variant A
"""

from __future__ import annotations

import argparse
import sys

# Sample realistic domain data from SkillTrace seed graph & learner state
SAMPLE_PROGRESS = {
    "total_nodes": 81,
    "mastered": 8,
    "passed": 12,
    "active": 3,
    "available": 18,
    "locked": 40,
    "total_sessions": 24,
    "total_minutes": 1340,
    "tracks": [
        {"name": "Math Foundations", "total": 20, "passed": 6, "mastered": 6, "active": 1, "available": 3, "locked": 4},
        {"name": "Programming & Tooling", "total": 18, "passed": 4, "mastered": 2, "active": 1, "available": 5, "locked": 6},
        {"name": "Data & Communication", "total": 24, "passed": 2, "mastered": 0, "active": 1, "available": 6, "locked": 15},
        {"name": "Cross-Cutting & Portfolio", "total": 19, "passed": 0, "mastered": 0, "active": 0, "available": 4, "locked": 15},
    ],
}

SAMPLE_BLOCKERS = {
    "open": [
        {
            "id": "blk.data.pandas.groupby_aggregation_01.001",
            "node_id": "data.pandas.groupby_aggregation_01",
            "node_title": "Pandas: GroupBy and Aggregation",
            "created_at": "2026-08-16",
            "days_open": 4,
            "description": "Multi-level index aggregation and custom transform functions failing on missing date ranges.",
            "actions": [
                {
                    "id": "rem.data.pandas.groupby_aggregation_01.001",
                    "status": "open",
                    "description": "Work through 5 custom aggregation exercises on Kaggle pandas tutorial.",
                }
            ],
            "remediation_node": "data.pandas.dataframe_basics_01",
            "remediation_edge_active": True,
        },
        {
            "id": "blk.math.calculus.derivative_intuition_01.001",
            "node_id": "math.calculus.derivative_intuition_01",
            "node_title": "Calculus: Derivative Intuition",
            "created_at": "2026-08-18",
            "days_open": 2,
            "description": "Geometric rate-of-change vs instantaneous slope intuition still hazy on polynomial curves.",
            "actions": [],
            "remediation_node": "math.functions.slope_01",
            "remediation_edge_active": True,
        },
    ],
    "resolved": [
        {
            "id": "blk.math.algebra.systems_equations_01.001",
            "node_id": "math.algebra.systems_equations_01",
            "node_title": "Algebra: Systems of Linear Equations",
            "created_at": "2026-07-12",
            "resolved_at": "2026-07-14",
            "days_stuck": 2,
            "description": "Matrix substitution method producing arithmetic sign errors.",
            "resolution": "Completed 10 Khan Academy practice problems on elimination method.",
            "actions": [
                {
                    "id": "rem.math.algebra.systems_equations_01.001",
                    "status": "completed",
                    "description": "Khan Academy elimination exercises",
                    "result": "10/10 correct on practice set",
                }
            ],
        }
    ],
}

SAMPLE_REVIEWS = {
    "scheduled": [
        {
            "id": "rev.math.algebra.linear_equations_01.001",
            "node_id": "math.algebra.linear_equations_01",
            "node_title": "Algebra: Linear Equations",
            "scheduled_for": "2026-08-15",
            "days_overdue": 5,
            "is_overdue": True,
            "pass_date": "2026-07-14",
            "node_state": "passed",
            "mastery_candidate": True,
        },
        {
            "id": "rev.prog.python.functions_01.001",
            "node_id": "prog.python.functions_01",
            "node_title": "Python: Functions & Scope",
            "scheduled_for": "2026-08-22",
            "days_overdue": 0,
            "is_overdue": False,
            "pass_date": "2026-08-08",
            "node_state": "passed",
            "mastery_candidate": False,
        },
    ],
    "completed": [
        {
            "id": "rev.math.arithmetic.fractions_01.001",
            "node_id": "math.arithmetic.fractions_01",
            "node_title": "Arithmetic: Fractions & Decimals",
            "scheduled_for": "2026-07-20",
            "completed_at": "2026-07-21",
            "outcome": "satisfactory",
            "summary": "15/15 mental fraction conversions without lookup table.",
            "node_state": "mastered",
        },
        {
            "id": "rev.data.csv.read_csv_01.001",
            "node_id": "data.csv.read_csv_01",
            "node_title": "Data: Reading CSV Files",
            "scheduled_for": "2026-08-01",
            "completed_at": "2026-08-02",
            "outcome": "unsatisfactory",
            "summary": "Stumbled on dialect parsing with custom delimiter and header skipping.",
            "node_state": "passed",
        },
    ],
    "cancelled": [
        {
            "id": "rev.math.algebra.variables_expressions_01.001",
            "node_id": "math.algebra.variables_expressions_01",
            "node_title": "Algebra: Variables & Expressions",
            "scheduled_for": "2026-07-18",
            "cancelled_at": "2026-07-17",
            "reason": "Rescheduled into comprehensive math foundations consolidation sitting.",
        }
    ],
}

SAMPLE_EVIDENCE = {
    "nodes": [
        {
            "node_id": "data.csv.read_csv_01",
            "node_title": "Data: Reading CSV Files",
            "node_state": "passed",
            "gate": {
                "authority": "objective_gate",
                "command": "python checks/data.csv.read_csv_check.py artifacts/data/csv_read_csv_solution.py",
            },
            "specs": [
                {
                    "id": "spec.data.csv.read_csv_01.code",
                    "name": "Working read_csv implementation with error handling",
                    "min_count": 1,
                    "required": True,
                    "records": [
                        {
                            "id": "ev.data.csv.read_csv_01.001",
                            "status": "superseded",
                            "submitted_at": "2026-07-10",
                            "location": "artifacts/data/csv_read_csv_v1.py",
                            "verdict": "rejected",
                            "note": "Failed check on trailing comma newline.",
                            "superseded_by": "ev.data.csv.read_csv_01.002",
                            "reason": "Fixed delimiter sniffing and newline stripping.",
                        },
                        {
                            "id": "ev.data.csv.read_csv_01.002",
                            "status": "accepted",
                            "submitted_at": "2026-07-11",
                            "location": "artifacts/data/csv_read_csv_solution.py",
                            "verdict": "accepted",
                            "note": "Passed objective check (10/10 test assertions passed).",
                        },
                    ],
                }
            ],
        },
        {
            "node_id": "communication.reports.results_summary_01",
            "node_title": "Communication: Technical Results Summary",
            "node_state": "active",
            "gate": {
                "authority": "learner_manual_review",
                "rubric": "rubrics/communication/results_summary_rubric.md",
            },
            "specs": [
                {
                    "id": "spec.comm.results_summary.pdf",
                    "name": "One-page executive findings brief",
                    "min_count": 1,
                    "required": True,
                    "records": [],
                },
                {
                    "id": "spec.comm.results_summary.notes",
                    "name": "Draft observations and raw tables",
                    "min_count": 0,
                    "required": False,
                    "records": [
                        {
                            "id": "ev.comm.results_summary.001",
                            "status": "accepted",
                            "submitted_at": "2026-08-19",
                            "location": "evidence/artifacts/notes_draft.md",
                            "verdict": "accepted",
                            "note": "Optional raw notes attached as reference slot.",
                        }
                    ],
                },
            ],
        },
    ]
}


# ==========================================
# RENDERERS: BLOCKER REPORT
# ==========================================

def render_blockers_A():
    b = SAMPLE_BLOCKERS
    lines = [
        "============================================================",
        "  SKILLTRACE BLOCKER REPORT — Actionable View",
        "============================================================",
        f"Status: {len(b['open'])} open blocker(s) | {len(b['resolved'])} resolved in history",
        "",
        "--- [OPEN BLOCKERS] (Sorted oldest first) --------------------",
    ]
    for blk in b["open"]:
        lines.extend([
            f"* {blk['id']} [{blk['days_open']}d open since {blk['created_at']}]",
            f"  Node:        {blk['node_id']} ({blk['node_title']})",
            f"  Obstacle:    {blk['description']}",
        ])
        if blk["actions"]:
            for act in blk["actions"]:
                lines.append(f"  Action:      [{act['status']}] {act['id']} — {act['description']}")
        else:
            lines.append("  Action:      [none logged] -> Run: `skilltrace remediation create`")
        if blk.get("remediation_node"):
            lines.append(f"  Rescue Node: {blk['remediation_node']} (Remediation edge ACTIVE)")
        lines.append("")

    lines.append("--- [RESOLVED HISTORY] -------------------------------------")
    for blk in b["resolved"]:
        lines.extend([
            f"[OK] {blk['id']} [resolved {blk['resolved_at']} | was stuck {blk['days_stuck']}d]",
            f"  Node:        {blk['node_id']} ({blk['node_title']})",
            f"  Obstacle:    {blk['description']}",
            f"  Resolution:  {blk['resolution']}",
            "",
        ])
    lines.append("Next move: Address blk.data.pandas.groupby_aggregation_01.001 or study rescue node.")
    return "\n".join(lines)


def render_blockers_B():
    b = SAMPLE_BLOCKERS
    lines = [
        "Where you are stuck",
        "-------------------",
        f"You have 2 open blockers holding back your progress. One has an active rescue node ready in your graph.",
        "",
        "Current Obstacles",
        "-----------------",
    ]
    for blk in b["open"]:
        lines.extend([
            f"1. {blk['node_title']} ({blk['days_open']} days open)",
            f"   Obstacle: {blk['description']}",
        ])
        if blk.get("remediation_node"):
            lines.append(f"   Where to turn: Rescue node '{blk['remediation_node']}' is now prioritized in `skilltrace next`.")
        if blk["actions"]:
            lines.append(f"   Intervention: {blk['actions'][0]['description']}")
        lines.extend([
            f"   How to proceed: Finish your remediation action or resolve once clear.",
            f"   Do this next: `skilltrace blocker resolve {blk['id']} --summary \"...\"`",
            "",
        ])

    lines.extend([
        "Resolved History",
        "----------------",
        f"1. {b['resolved'][0]['node_title']} -- stuck 2 days; resolved via {b['resolved'][0]['resolution']}",
        "",
        "Mentor Note: Don't let pandas groupby sit past a week -- switch to the rescue node if you're hitting a wall.",
    ])
    return "\n".join(lines)


def render_blockers_C():
    b = SAMPLE_BLOCKERS
    lines = [
        "+-----------------------------------------------------------------------------+",
        "| BLOCKER LEDGER                                                              |",
        "+-----------------------------------------------------------------------------+",
        f"| Open: {len(b['open']):<2} | Resolved: {len(b['resolved']):<2} | Remediation Edges Active: 2                          |",
        "+-----------------------------------------------------------------------------+",
        "| ID / NODE                                 | AGE | STATUS | ACTIONS | RESCUE |",
        "+-----------------------------------------------------------------------------+",
    ]
    for blk in b["open"]:
        lines.append(f"| {blk['node_id'][:40]:<41} | {blk['days_open']}d  | OPEN   | {len(blk['actions'])} act   | YES    |")
        lines.append(f"|   Desc: {blk['description'][:72]:<74} |")
    for blk in b["resolved"]:
        lines.append(f"| {blk['node_id'][:40]:<41} | {blk['days_stuck']}d  | CLOSED | {len(blk['actions'])} act   | -      |")
    lines.append("+-----------------------------------------------------------------------------+")
    return "\n".join(lines)


# ==========================================
# RENDERERS: REVIEW REPORT
# ==========================================

def render_reviews_A():
    r = SAMPLE_REVIEWS
    lines = [
        "============================================================",
        "  SKILLTRACE REVIEW & RETENTION REPORT",
        "============================================================",
        f"Scheduled: {len(r['scheduled'])} (1 overdue) | Completed: {len(r['completed'])} (50% satisfactory) | Cancelled: {len(r['cancelled'])}",
        "",
        "--- [DUE & OVERDUE RETENTION CHECKS] -----------------------",
    ]
    for rev in r["scheduled"]:
        tag = "[OVERDUE - 5d LATE]" if rev["is_overdue"] else "[DUE IN 2d]"
        mastery_tag = " -> [ELIGIBLE FOR MASTERY UPON SATISFACTORY REVIEW]" if rev.get("mastery_candidate") else ""
        lines.extend([
            f"* {rev['id']} {tag}{mastery_tag}",
            f"  Node:          {rev['node_id']} ({rev['node_title']})",
            f"  Scheduled:     {rev['scheduled_for']} (Passed on {rev['pass_date']})",
            f"  Command:       `skilltrace review complete {rev['id']} --outcome satisfactory --summary \"...\"`",
            "",
        ])

    lines.append("--- [COMPLETED REVIEWS] ------------------------------------")
    for rev in r["completed"]:
        mark = "[OK] PASS" if rev["outcome"] == "satisfactory" else "[!] RE-STUDY NEEDED"
        lines.extend([
            f"{mark} {rev['id']} [{rev['outcome'].upper()}] on {rev['completed_at']}",
            f"  Node:          {rev['node_id']} (State: {rev['node_state']})",
            f"  Summary:       {rev['summary']}",
            "",
        ])

    lines.append("--- [CANCELLED REVIEWS] ------------------------------------")
    for rev in r["cancelled"]:
        lines.append(f"[-] {rev['id']} cancelled {rev['cancelled_at']}: {rev['reason']}")

    lines.append("")
    lines.append("Retention Summary: 1 mastery promotion ready to unlock; 1 failed retention check needs review.")
    return "\n".join(lines)


def render_reviews_B():
    r = SAMPLE_REVIEWS
    lines = [
        "Retention & Mastery Health",
        "--------------------------",
        "Your retention checks keep passed skills from fading. You have 1 overdue review that can unlock mastery.",
        "",
        "Ready for Mastery Verification",
        "------------------------------",
        f"1. {r['scheduled'][0]['node_title']} (Due {r['scheduled'][0]['scheduled_for']} / 5 days overdue)",
        "   Why this matters: Passed 30+ days ago. A satisfactory review today promotes this node to permanent mastery.",
        "   Where to check: Review your algebraic equation solutions without scratch notes.",
        "   Do this next: `skilltrace review complete rev.math.algebra.linear_equations_01.001 --outcome satisfactory --summary \"...\"`",
        "",
        "Recent Review Outcomes",
        "----------------------",
        f"[OK] {r['completed'][0]['node_title']} -- Satisfactory! Promoted to mastered.",
        f"[!] {r['completed'][1]['node_title']} -- Unsatisfactory. Dialect parsing slipped; added to study suggestions.",
    ]
    return "\n".join(lines)


def render_reviews_C():
    r = SAMPLE_REVIEWS
    lines = [
        "+-----------------------------------------------------------------------------+",
        "| REVIEW AUDIT REGISTER                                                       |",
        "+-----------------------------------------------------------------------------+",
        f"| Overdue: 1 | Scheduled: 2 | Completed: 2 (1 pass, 1 fail) | Cancelled: 1     |",
        "+-----------------------------------------------------------------------------+",
        "| ID / NODE                             | DUE DATE   | STATUS       | OUTCOME |",
        "+-----------------------------------------------------------------------------+",
        f"| {r['scheduled'][0]['node_id'][:35]:<37} | 2026-08-15 | OVERDUE (5d) | PENDING |",
        f"| {r['scheduled'][1]['node_id'][:35]:<37} | 2026-08-22 | SCHEDULED    | PENDING |",
        f"| {r['completed'][0]['node_id'][:35]:<37} | 2026-07-20 | COMPLETED    | SATIS   |",
        f"| {r['completed'][1]['node_id'][:35]:<37} | 2026-08-01 | COMPLETED    | UNSATIS |",
        f"| {r['cancelled'][0]['node_id'][:35]:<37} | 2026-07-18 | CANCELLED    | -       |",
        "+-----------------------------------------------------------------------------+",
    ]
    return "\n".join(lines)


# ==========================================
# RENDERERS: EVIDENCE REPORT
# ==========================================

def render_evidence_A():
    e = SAMPLE_EVIDENCE
    lines = [
        "============================================================",
        "  SKILLTRACE EVIDENCE & PROOF TRAIL REPORT",
        "============================================================",
        "Proof records: 3 submitted (2 accepted, 0 rejected, 1 superseded) across 2 nodes",
        "",
    ]
    for node in e["nodes"]:
        gate_type = "Objective Gate" if node["gate"]["authority"] == "objective_gate" else "Learner Manual Review"
        lines.extend([
            f"NODE: {node['node_id']} [{node['node_state'].upper()}] -- {node['node_title']}",
            f"Gate Authority: {gate_type}",
        ])
        if node["gate"].get("command"):
            lines.append(f"Gate Command:   `{node['gate']['command']}`")
        if node["gate"].get("rubric"):
            lines.append(f"Gate Rubric:    `{node['gate']['rubric']}`")

        for spec in node["specs"]:
            req_str = f"REQUIRED (min {spec['min_count']})" if spec["required"] else "OPTIONAL SLOT"
            accepted_cnt = len([r for r in spec["records"] if r["status"] == "accepted"])
            status_tag = "[SATISFIED]" if accepted_cnt >= spec["min_count"] and spec["min_count"] > 0 else "[INCOMPLETE]" if spec["required"] else "[ATTACHED]"
            lines.append(f"  Spec: {spec['id']} -- {spec['name']} ({req_str}) {status_tag}")

            if not spec["records"]:
                lines.append("    (no evidence submitted yet)")
            for rec in spec["records"]:
                if rec["status"] == "superseded":
                    lines.extend([
                        f"    [SUPERSEDED] {rec['id']} submitted {rec['submitted_at']}",
                        f"      File:          {rec['location']}",
                        f"      Superseded by: {rec['superseded_by']} (Reason: {rec['reason']})",
                    ])
                else:
                    lines.extend([
                        f"    [ACCEPTED]   {rec['id']} submitted {rec['submitted_at']} ({rec['verdict']})",
                        f"      File:          {rec['location']}",
                        f"      Note:          {rec['note']}",
                    ])
        lines.append("")
    return "\n".join(lines)


def render_evidence_B():
    e = SAMPLE_EVIDENCE
    lines = [
        "Evidence & Proof Trail",
        "----------------------",
        "Every pass is backed by verified artifacts. Here is how your proof records stand:",
        "",
        "1. Reading CSV Files (`data.csv.read_csv_01`) / State: PASSED",
        "   Gate: Objective verification command (`python checks/data.csv.read_csv_check.py`)",
        "   Proof chain:",
        "   - ev.001 (superseded): initial solution failed trailing comma check",
        "   - ev.002 (accepted): fixed delimiter sniffing; 10/10 automated assertions passed",
        "   Status: Fully satisfied and verified.",
        "",
        "2. Technical Results Summary (`communication.reports.results_summary_01`) / State: ACTIVE",
        "   Gate: Learner manual review against rubric",
        "   Proof chain:",
        "   - Required one-page executive brief: NOT YET SUBMITTED",
        "   - Optional draft notes: attached as reference",
        "   Do this next: Submit your final one-page brief to become pass-eligible:",
        "   `skilltrace submit communication.reports.results_summary_01 --location artifacts/summary.pdf --accept`",
    ]
    return "\n".join(lines)


def render_evidence_C():
    lines = [
        "+-----------------------------------------------------------------------------+",
        "| EVIDENCE TRAIL REGISTER                                                     |",
        "+-----------------------------------------------------------------------------+",
        "| NODE / SPEC ID                        | GATE TYPE | RECORDS | STATUS        |",
        "+-----------------------------------------------------------------------------+",
        "| data.csv.read_csv_01                  | OBJECTIVE | 2 recs  | SATISFIED     |",
        "|   spec.data.csv.read_csv_01.code      | Required  | 1 head  | 1/1 accepted  |",
        "|     ev.001 (superseded) -> ev.002 (accepted on 2026-07-11)                  |",
        "| communication.reports.results_summary | MANUAL    | 1 rec   | INCOMPLETE    |",
        "|   spec.comm.results_summary.pdf       | Required  | 0 recs  | 0/1 missing   |",
        "|   spec.comm.results_summary.notes     | Optional  | 1 rec   | 1/0 attached  |",
        "+-----------------------------------------------------------------------------+",
    ]
    return "\n".join(lines)


# ==========================================
# RENDERERS: PROGRESS REPORT
# ==========================================

def render_progress_A():
    p = SAMPLE_PROGRESS
    pct_done = round((p["passed"] + p["mastered"]) / p["total_nodes"] * 100, 1)
    lines = [
        "============================================================",
        "  SKILLTRACE CURRICULUM PROGRESS REPORT",
        "============================================================",
        f"Overall: {p['passed'] + p['mastered']}/{p['total_nodes']} nodes completed ({pct_done}%) | {p['total_sessions']} sessions ({p['total_minutes'] // 60}h {p['total_minutes'] % 60}m studied)",
        "",
        "--- [NODE STATE ROLL-UP] -----------------------------------",
        f"  Mastered:   {p['mastered']:>2} ({round(p['mastered']/p['total_nodes']*100)}%)  [Permanent retention confirmed]",
        f"  Passed:     {p['passed']:>2} ({round(p['passed']/p['total_nodes']*100)}%)  [Evidence requirements met]",
        f"  Active:     {p['active']:>2} ({round(p['active']/p['total_nodes']*100)}%)  [Currently in progress in sessions]",
        f"  Available:  {p['available']:>2} ({round(p['available']/p['total_nodes']*100)}%)  [Prerequisites satisfied, ready to start]",
        f"  Locked:     {p['locked']:>2} ({round(p['locked']/p['total_nodes']*100)}%)  [Hard prerequisites pending]",
        "",
        "--- [TRACK & BAND PROGRESS] --------------------------------",
    ]
    for t in p["tracks"]:
        done = t["passed"] + t["mastered"]
        pct = round(done / t["total"] * 100)
        bar_len = 20
        filled = round(bar_len * (done / t["total"]))
        bar = "=" * filled + "-" * (bar_len - filled)
        lines.extend([
            f"{t['name']:<26} [{bar}] {pct:>3}% ({done}/{t['total']})",
            f"  Mastered: {t['mastered']} | Passed: {t['passed']} | Active: {t['active']} | Ready: {t['available']} | Locked: {t['locked']}",
            "",
        ])
    lines.append("Next milestone: 3 available nodes ready to unlock Pandas Data Exploration band.")
    return "\n".join(lines)


def render_progress_B():
    p = SAMPLE_PROGRESS
    lines = [
        "Your Learning Journey",
        "---------------------",
        f"You have completed 20 of 81 skills ({p['mastered']} mastered, {p['passed']} passed) across {p['total_sessions']} study sessions (22.3 hours).",
        "",
        "Track Breakdown",
        "---------------",
        "1. Math Foundations -- 60% complete (12/20 nodes)",
        "   You have solid coverage in algebra and arithmetic. Next up: calculus derivative intuition.",
        "",
        "2. Programming & Tooling -- 33% complete (6/18 nodes)",
        "   Core Python and virtual environments are solid. Next up: automated test writing.",
        "",
        "3. Data & Communication -- 8% complete (2/24 nodes)",
        "   CSV parsing complete; pandas dataframes available to start.",
        "",
        "4. Cross-Cutting & Portfolio -- 0% complete (0/19 nodes)",
        "   Capstones unlock as you complete data analysis and modeling tracks.",
        "",
        "Mentor Note: Great momentum on math and programming fundamentals. Starting the pandas track will unlock your first data analysis capstone.",
    ]
    return "\n".join(lines)


def render_progress_C():
    p = SAMPLE_PROGRESS
    lines = [
        "+-----------------------------------------------------------------------------+",
        "| CURRICULUM PROGRESS LEDGER                                                  |",
        "+-----------------------------------------------------------------------------+",
        f"| TOTAL NODES: 81 | COMPLETED: 20 (24.7%) | STUDY TIME: 22.3 hrs | SESSIONS: 24 |",
        "+-----------------------------------------------------------------------------+",
        "| TRACK                      | MAST | PASS | ACTV | AVAIL | LOCK | TOTAL | DONE |",
        "+-----------------------------------------------------------------------------+",
        "| Math Foundations           |    6 |    6 |    1 |     3 |    4 |    20 |  60% |",
        "| Programming & Tooling      |    2 |    4 |    1 |     5 |    6 |    18 |  44% |",
        "| Data & Communication       |    0 |    2 |    1 |     6 |   15 |    24 |   8% |",
        "| Cross-Cutting & Portfolio  |    0 |    0 |    0 |     4 |   15 |    19 |   0% |",
        "+-----------------------------------------------------------------------------+",
        "| TOTAL                      |    8 |   12 |    3 |    18 |   40 |    81 | 24.7%|",
        "+-----------------------------------------------------------------------------+",
    ]
    return "\n".join(lines)


# ==========================================
# MAIN DISPATCHER
# ==========================================

REPORTS = {
    "blockers": {"A": render_blockers_A, "B": render_blockers_B, "C": render_blockers_C},
    "reviews": {"A": render_reviews_A, "B": render_reviews_B, "C": render_reviews_C},
    "evidence": {"A": render_evidence_A, "B": render_evidence_B, "C": render_evidence_C},
    "progress": {"A": render_progress_A, "B": render_progress_B, "C": render_progress_C},
}

CLI_OPTIONS_DEMO = """
================================================================================
CLI INVOCATION OPTIONS EVALUATION
================================================================================

Option 1: Unified Subcommand Family (`skilltrace report <target>`) [RECOMMENDED]
--------------------------------------------------------------------------------
  skilltrace report blockers
  skilltrace report reviews
  skilltrace report evidence [--node-id <id>]
  skilltrace report progress
  skilltrace report resources (aliasing/subsuming resource-report)

  Why it works:
  - Clean discovery under `skilltrace report --help`.
  - Mirrors existing structured subcommand families: `validate <layer>`, `export <format>`, `suggest <topic>`.
  - Distinguishes fast daily listings (`skilltrace blockers`, `skilltrace reviews`) from deep analytical reports (`skilltrace report blockers`, `skilltrace report reviews`).
  - Top-level aliases like `skilltrace progress` -> `skilltrace report progress` can be added via #32 alias policy.

Option 2: Flags on Existing Commands & Top-Level Spread
--------------------------------------------------------------------------------
  skilltrace blockers --report (or --all)
  skilltrace reviews --report (or --all)
  skilltrace evidence report [--node-id <id>]
  skilltrace progress
  skilltrace resource-report

  Trade-offs:
  - Spreads reports across different syntax conventions (flags vs subcommands vs top-level).
  - Less cohesive mental model for generating audit/retrospective views.

Option 3: Top-Level `<name>-report` Family
--------------------------------------------------------------------------------
  skilltrace blocker-report
  skilltrace review-report
  skilltrace evidence-report
  skilltrace progress-report
  skilltrace resource-report

  Trade-offs:
  - Clutters the top-level `--help` with 5 separate report commands.
"""


def main():
    parser = argparse.ArgumentParser(description="SkillTrace Reports Design Prototype")
    parser.add_argument("--report", choices=["blockers", "reviews", "evidence", "progress", "all"], default="all")
    parser.add_argument("--variant", choices=["A", "B", "C", "all"], default="all")
    parser.add_argument("--cli-options", action="store_true", help="Print CLI invocation options comparison")
    args = parser.parse_args()

    if args.cli_options:
        print(CLI_OPTIONS_DEMO)
        return

    reports_to_show = [args.report] if args.report != "all" else ["progress", "blockers", "reviews", "evidence"]
    variants_to_show = [args.variant] if args.variant != "all" else ["A", "B", "C"]

    variant_names = {
        "A": "Variant A: Actionable Diagnostic (Urgency-First, Plain Text)",
        "B": "Variant B: Mentor Voice (Conversational, Guided Next Steps)",
        "C": "Variant C: Structural Ledger (Compact Register / Table)",
    }

    for r_name in reports_to_show:
        print("\n" + "#" * 70)
        print(f"  REPORT: skilltrace report {r_name}".upper())
        print("#" * 70)
        for v_name in variants_to_show:
            print(f"\n>>> {variant_names[v_name]}:\n")
            print(REPORTS[r_name][v_name]())
            print("\n" + "-" * 70)


if __name__ == "__main__":
    main()
