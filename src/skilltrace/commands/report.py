"""`skilltrace report <target>` — unified learning and diagnostic reports (issue #42).

Per the #31 resolution:
- `skilltrace report progress`: whole-graph completion roll-up across all nodes,
  state counts (`mastered`, `passed`, `active`, `available`, `locked`), per-track
  progress breakdown, study session count & hours.
- `skilltrace report blockers`: persistent stuckness diagnostic, open blockers
  (oldest first, age in days, obstacle, open remediation actions, active rescue
  nodes in graph) + resolved history.
- `skilltrace report reviews`: retention & spaced-repetition health, overdue
  retention checks (`[OVERDUE]`), mastery promotion candidates, completed
  review outcomes (`[OK]` / `[!]`), cancelled history.
- `skilltrace report evidence [--node-id <id>]`: proof trail audit per node or
  curriculum-wide, gate authorities (objective vs manual), artifact specs status,
  submission records, supersession lineage (`ev.001 -> ev.002`).
- `skilltrace report resources`: aligned alias/canonical form of
  `resource-report` for consistency under `report --help`.

Mentor voice per #30/#31: conversational brief + guided Where to learn / How to
proceed + Do this next. Pure stdlib rendering via `src/skilltrace/render.py`,
ASCII safe across Windows console codepages. Read-only (always exits 0 on valid
data, no audit events logged, never reads event log for state).
"""

from __future__ import annotations

from pathlib import Path

from ..context import load_context_lenient
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import (
    days_overdue,
    is_overdue,
    overdue_reviews,
    parse_date,
    utc_today,
)
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.state import ProgressStoreError
from .resource_report import resource_report


# ==========================================
# 1. REPORT: PROGRESS
# ==========================================


def report_progress(ctx: Context) -> CommandResult:
    """Whole-curriculum completion, states roll-up, tracks, session hours."""
    root = ctx.root
    joined = ctx.joined
    if joined is None:
        try:
            joined = load_context_lenient(root)
        except (NodeLoadError, ProgressStoreError) as exc:
            print(f"report progress: FAILED -- {exc}")
            return CommandResult(exit_code=1)
    nodes = joined.nodes
    store = joined.store
    sessions = joined.sessions
    session_work = joined.work

    total_nodes = len(nodes)
    states = {"mastered": 0, "passed": 0, "active": 0, "available": 0, "locked": 0}
    for n in nodes:
        st = store.state_of(n.id)
        states[st] = states.get(st, 0) + 1

    mastered = states.get("mastered", 0)
    passed = states.get("passed", 0)
    completed = mastered + passed

    total_sessions = len(sessions)
    total_minutes = sum(w.minutes for w in session_work if w.minutes is not None)
    total_hours = total_minutes / 60.0

    lines: list[str] = [
        "Your Learning Journey",
        "---------------------",
        f"You have completed {completed} of {total_nodes} skills ({mastered} mastered, {passed} passed) across {total_sessions} study sessions ({total_hours:.1f} hours).",
        "",
        "Track Breakdown",
        "---------------",
    ]

    track_defs = [
        (
            "Math Foundations",
            lambda n: n.domain == "mathematics" and n.track == "foundational",
        ),
        (
            "Programming & Tooling",
            lambda n: n.domain in ("programming", "tooling") and n.track == "foundational",
        ),
        (
            "Data & Communication",
            lambda n: n.domain in ("data", "communication") and n.track == "foundational",
        ),
        (
            "Cross-Cutting & Portfolio",
            lambda n: n.track in ("consolidation", "portfolio", "remediation"),
        ),
    ]

    assigned_node_ids: set[str] = set()
    track_index = 1
    for track_name, predicate in track_defs:
        t_nodes = [n for n in nodes if predicate(n)]
        if not t_nodes:
            continue
        assigned_node_ids.update(n.id for n in t_nodes)
        t_total = len(t_nodes)
        t_mast = sum(1 for n in t_nodes if store.state_of(n.id) == "mastered")
        t_pass = sum(1 for n in t_nodes if store.state_of(n.id) == "passed")
        t_done = t_mast + t_pass
        t_pct = round(t_done / t_total * 100) if t_total > 0 else 0

        next_active = [n for n in t_nodes if store.state_of(n.id) == "active"]
        next_avail = [n for n in t_nodes if store.state_of(n.id) == "available"]

        lines.append(f"{track_index}. {track_name} -- {t_pct}% complete ({t_done}/{t_total} nodes)")
        if t_done == t_total:
            lines.append("   Complete! All skills in this track have been passed or mastered.")
        elif next_active:
            lines.append(f"   Currently working on {next_active[0].title}. Next up: finish active evidence submissions.")
        elif next_avail:
            lines.append(f"   {len(next_avail)} skill(s) ready to start. Next up: {next_avail[0].title}.")
        elif t_done > 0:
            lines.append("   Solid progress so far. Clear prerequisites to unlock remaining skills.")
        else:
            lines.append("   Prerequisites pending. Unlocks as you progress through foundational tracks.")
        lines.append("")
        track_index += 1

    remaining_nodes = [n for n in nodes if n.id not in assigned_node_ids]
    if remaining_nodes:
        r_total = len(remaining_nodes)
        r_done = sum(1 for n in remaining_nodes if store.state_of(n.id) in ("passed", "mastered"))
        r_pct = round(r_done / r_total * 100) if r_total > 0 else 0
        lines.append(f"{track_index}. Other Curriculum -- {r_pct}% complete ({r_done}/{r_total} nodes)")
        lines.append("")

    if completed == 0:
        mentor_text = "Start by picking a ready skill in Math Foundations or Programming & Tooling with `skilltrace next`."
    elif completed >= total_nodes:
        mentor_text = "Outstanding achievement! You have completed the entire curriculum."
    else:
        mentor_text = "Great momentum. Keep building core competence and demonstrating evidence across active tracks."
    lines.append(f"Mentor Note: {mentor_text}")

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


# ==========================================
# 2. REPORT: BLOCKERS
# ==========================================


def report_blockers(ctx: Context) -> CommandResult:
    """Persistent stuckness diagnostic, open blockers, and rescue nodes."""
    root = ctx.root
    try:
        joined = ctx.joined or load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"report blockers: FAILED -- {exc}")
        return CommandResult(exit_code=1)
    nodes = joined.nodes
    edges = joined.edges
    store = joined.store
    blockers = joined.blockers
    actions = joined.remediations
    titles = joined.titles
    today = utc_today()

    open_blockers = [b for b in blockers if b.status == "open"]
    open_blockers.sort(key=lambda b: str(b.created_at))
    resolved_blockers = [b for b in blockers if b.status in ("resolved", "closed")]

    lines: list[str] = [
        "Where you are stuck",
        "-------------------",
    ]

    if not open_blockers:
        lines.append("You have no open blockers -- smooth sailing!")
    else:
        rescue_count = 0
        for b in open_blockers:
            rescues = [e for e in edges if e.active and e.edge_type == "remediation" and e.target == b.node_id]
            if rescues:
                rescue_count += 1
        rescue_phrase = ""
        if rescue_count > 0:
            rescue_phrase = f" {'One has' if rescue_count == 1 else f'{rescue_count} have'} an active rescue node ready in your graph."
        lines.append(f"You have {len(open_blockers)} open blocker(s) holding back your progress.{rescue_phrase}")

    lines.append("")
    lines.append("Current Obstacles")
    lines.append("-----------------")

    if not open_blockers:
        lines.append("No open obstacles logged. When you encounter persistent friction, run `skilltrace blocker create`.")
    else:
        for idx, b in enumerate(open_blockers, 1):
            created_d = parse_date(b.created_at)
            days_open = (today - created_d).days if created_d else 0
            node_title = titles.get(b.node_id, b.node_id)
            lines.append(f"{idx}. {node_title} ({days_open} days open)")
            lines.append(f"   Obstacle: {b.description}")

            rescues = [e.source for e in edges if e.active and e.edge_type == "remediation" and e.target == b.node_id]
            if rescues:
                rescue_id = rescues[0]
                lines.append(f"   Where to turn: Rescue node '{rescue_id}' is now prioritized in `skilltrace next`.")

            blk_actions = [a for a in actions if a.blocker_id == b.id and a.status == "open"]
            if blk_actions:
                lines.append(f"   Intervention: {blk_actions[0].description}")
            else:
                lines.append("   How to proceed: Finish your remediation action or resolve once clear.")

            lines.append(f"   Do this next: `skilltrace blocker resolve {b.id} --summary \"...\"`")
            lines.append("")

    lines.append("Resolved History")
    lines.append("----------------")
    if not resolved_blockers:
        lines.append("No resolved blockers in history.")
    else:
        for idx, b in enumerate(resolved_blockers, 1):
            created_d = parse_date(b.created_at)
            resolved_d = parse_date(getattr(b, "resolved_at", None) or getattr(b, "updated_at", None))
            days_stuck = (resolved_d - created_d).days if (created_d and resolved_d) else 0
            node_title = titles.get(b.node_id, b.node_id)
            summary = getattr(b, "summary", "") or getattr(b, "resolution_summary", "") or getattr(b, "description", "")
            lines.append(f"{idx}. {node_title} -- stuck {days_stuck} days; resolved via {summary}")

    lines.append("")
    if open_blockers:
        oldest = open_blockers[0]
        lines.append(f"Mentor Note: Don't let {oldest.node_id} sit indefinitely -- switch to its rescue node or log a remediation action if you hit a wall.")
    else:
        lines.append("Mentor Note: Keeping blockers clear maintains steady learning momentum.")

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


# ==========================================
# 3. REPORT: REVIEWS
# ==========================================


def report_reviews(ctx: Context) -> CommandResult:
    """Retention & spaced-repetition health, overdue checks, and mastery candidates."""
    root = ctx.root
    try:
        joined = ctx.joined or load_context_lenient(root)
    except (NodeLoadError, ProgressStoreError) as exc:
        print(f"report reviews: FAILED -- {exc}")
        return CommandResult(exit_code=1)
    nodes = joined.nodes
    store = joined.store
    reviews = joined.reviews
    titles = joined.titles
    today = utc_today()

    scheduled = [r for r in reviews if r.status == "scheduled"]
    completed = [r for r in reviews if r.status == "completed"]
    cancelled = [r for r in reviews if r.status == "cancelled"]

    overdue_count = sum(1 for r in scheduled if is_overdue(r, today=today))

    lines: list[str] = [
        "Scheduled Reviews",
        "------------------",
    ]
    if overdue_count > 0:
        lines.append(f"Your retention checks keep passed skills from fading. You have {overdue_count} overdue review(s) that can unlock mastery.")
    elif scheduled:
        lines.append(f"Your retention checks keep passed skills from fading. You have {len(scheduled)} review(s) scheduled.")
    else:
        lines.append("Your retention checks keep passed skills from fading. No reviews currently scheduled.")

    lines.append("")
    lines.append("Ready for Mastery Verification")
    lines.append("------------------------------")
    if not scheduled:
        lines.append("No reviews currently scheduled. Pass a skill to schedule spaced retention checks.")
    else:
        for idx, r in enumerate(scheduled, 1):
            overdue_flag = is_overdue(r, today=today)
            days_over = days_overdue(r, today=today)
            node_title = titles.get(r.node_id, r.node_id)
            node_state = store.state_of(r.node_id)

            due_phrase = f"Due {r.scheduled_for}"
            if overdue_flag:
                due_phrase += f" / {days_over} days overdue"
            lines.append(f"{idx}. {node_title} ({due_phrase})")
            if node_state == "passed":
                lines.append("   Why this matters: Passed node awaiting retention verification. A satisfactory review today promotes this node toward permanent mastery.")
            else:
                lines.append("   Why this matters: Spaced retention verification for continuous fluency.")
            lines.append(f"   Where to check: Review and verify your practical recall for {node_title}.")
            lines.append(f"   Do this next: `skilltrace review complete {r.id} --outcome satisfactory --summary \"...\"`")
            lines.append("")

    lines.append("Recent Review Outcomes")
    lines.append("----------------------")
    if not completed:
        lines.append("No completed reviews in history.")
    else:
        for r in completed:
            node_title = titles.get(r.node_id, r.node_id)
            mark = "[OK]" if r.outcome == "satisfactory" else "[!]"
            summary = r.result_summary or ("Satisfactory! Promoted to mastered." if r.outcome == "satisfactory" else "Unsatisfactory. Needs further study.")
            lines.append(f"{mark} {node_title} -- {summary}")

    if cancelled:
        lines.append("")
        lines.append("Cancelled Reviews")
        lines.append("-----------------")
        for r in cancelled:
            lines.append(f"[-] {r.id} cancelled {r.cancelled_at or 'recently'}: {r.cancel_reason or 'no reason given'}")

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


# ==========================================
# 4. REPORT: EVIDENCE
# ==========================================


def report_evidence(ctx: Context) -> CommandResult:
    """Proof trail audit, gates, specs, submission records, supersession chains."""
    root = ctx.root
    node_id_filter = getattr(ctx.args, "node_id", None)

    try:
        joined = ctx.joined or load_context_lenient(root)
    except (NodeLoadError, ProgressStoreError) as exc:
        print(f"report evidence: FAILED -- {exc}")
        return CommandResult(exit_code=1)
    nodes = joined.nodes
    store = joined.store
    specs = joined.specs
    records = joined.records

    node_map = joined.node_map
    if node_id_filter:
        if node_id_filter not in node_map:
            print(f"report evidence: FAILED -- unknown node {node_id_filter}.")
            return CommandResult(exit_code=1)
        target_nodes = [node_map[node_id_filter]]
    else:
        target_nodes = nodes

    lines: list[str] = [
        "Evidence & Proof Trail",
        "----------------------",
        "Every pass is backed by verified artifacts. Here is how your proof records stand:",
        "",
    ]

    superseded_ids = {r.supersedes: r for r in records if r.supersedes is not None}

    item_idx = 1
    for node in target_nodes:
        n_specs = joined.specs_by_node.get(node.id, [])
        n_gate = joined.gates_by_node.get(node.id)
        n_records = [r for r in records if any(s.id == r.artifact_spec_id for s in n_specs)]
        state = store.state_of(node.id)

        if n_gate:
            if n_gate.authority == "objective":
                gate_desc = f"Objective verification command (`{n_gate.command}`)"
            else:
                gate_desc = "Learner manual review against rubric"
        else:
            gate_desc = "Learner judgment (no gate configured)"

        lines.append(f"{item_idx}. {node.title} (`{node.id}`) / State: {state.upper()}")
        lines.append(f"   Gate: {gate_desc}")
        lines.append("   Proof chain:")

        all_satisfied = True
        for spec in n_specs:
            spec_recs = [r for r in records if r.artifact_spec_id == spec.id]
            if not spec_recs:
                if spec.required:
                    lines.append(f"   - Required {spec.title}: NOT YET SUBMITTED")
                    all_satisfied = False
                else:
                    lines.append(f"   - Optional {spec.title}: (no submissions)")
            else:
                for rec in spec_recs:
                    if rec.id in superseded_ids:
                        successor = superseded_ids[rec.id]
                        lines.append(f"   - {rec.id} (superseded): {rec.note or 'initial solution'} (superseded by {successor.id})")
                    elif rec.accepted:
                        lines.append(f"   - {rec.id} (accepted): {rec.note or 'accepted solution'} ({rec.location})")
                    else:
                        lines.append(f"   - {rec.id} (rejected): {rec.note or 'rejected submission'} ({rec.location})")

        if not n_specs:
            lines.append("   - (no artifact specs required)")

        if state in ("passed", "mastered"):
            lines.append("   Status: Fully satisfied and verified.")
        elif all_satisfied and n_records:
            lines.append(f"   Status: Pass-eligible! Ready to mark passed: `skilltrace pass {node.id}`")
        else:
            req_unmet = [
                s for s in n_specs
                if s.required and not any(
                    r.artifact_spec_id == s.id and r.accepted and r.id not in superseded_ids
                    for r in n_records
                )
            ]
            if req_unmet:
                missing_name = req_unmet[0].title
                lines.append(f"   Do this next: Submit your {missing_name} to become pass-eligible:")
                if n_gate and n_gate.authority == "objective":
                    lines.append(f"   `skilltrace submit {node.id} --location <path>`")
                else:
                    lines.append(f"   `skilltrace submit {node.id} --location <path> --accept`")
            else:
                lines.append(f"   Do this next: Start studying with `skilltrace start {node.id}`")

        lines.append("")
        item_idx += 1

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


# ==========================================
# 5. REPORT: RESOURCES
# ==========================================


def report_resources(ctx: Context) -> CommandResult:
    """Aliased/canonical form of resource-report."""
    return resource_report(ctx)


# ==========================================
# REGISTRATION
# ==========================================


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="report progress",
            kind=Kind.READ_ONLY,
            handler=report_progress,
            help="Curriculum progress and track completion roll-up.",
        )
    )
    registry.register(
        Command(
            name="report blockers",
            kind=Kind.READ_ONLY,
            handler=report_blockers,
            help="Obstacles, open remediation, and rescue nodes.",
        )
    )
    registry.register(
        Command(
            name="report reviews",
            kind=Kind.READ_ONLY,
            handler=report_reviews,
            help="Retention checks, overdue reviews, and mastery candidates.",
        )
    )
    registry.register(
        Command(
            name="report evidence",
            kind=Kind.READ_ONLY,
            handler=report_evidence,
            help="Proof trail audit, gates, specs, and supersession chains.",
        )
    )
    registry.register(
        Command(
            name="report resources",
            kind=Kind.READ_ONLY,
            handler=report_resources,
            help="Resource verification status snapshot.",
        )
    )
