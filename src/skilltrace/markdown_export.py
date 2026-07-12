"""`skilltrace export markdown` — the compact, human-readable snapshot.

Per the #33 resolution: a single-file reading artifact, not an interchange
format (that is `export sqlite`'s job) and not a report bundle (that is the
terminal's job). Overwritten each run at `data/export.md` — the export is a
snapshot of *now*; history belongs to git (source YAML) and `backup`.

Snapshot depth is complete-but-compact: every node appears exactly once, one
line each, grouped by state, with its accepted-evidence count; sessions are
summarized (totals + a recent handful), never enumerated in full.
"""

from __future__ import annotations

from pathlib import Path

from .evidence.eligibility import live_accepted_count
from .export_data import ExportData

MARKDOWN_EXPORT_RELPATH = Path("data") / "export.md"

# Most-progressed first — a snapshot for the learner to see where things stand,
# not a worklist (contrast `resource_report`'s worst-first ordering).
_STATE_GROUPS: tuple[str, ...] = ("mastered", "passed", "active", "available", "locked")

_RECENT_SESSION_COUNT = 5


def _accepted_counts(data: ExportData) -> dict[str, int]:
    """node_id -> live accepted evidence records, summed across its specs."""
    specs_by_node: dict[str, list[str]] = {}
    for spec in data.artifact_specs:
        specs_by_node.setdefault(spec.node_id, []).append(spec.id)

    counts: dict[str, int] = {}
    for node_id, spec_ids in specs_by_node.items():
        counts[node_id] = sum(
            live_accepted_count(data.evidence_records, spec_id) for spec_id in spec_ids
        )
    return counts


def _render_nodes(data: ExportData) -> list[str]:
    lines = [f"## Nodes ({len(data.nodes)} total)"]
    if not data.nodes:
        lines.append("")
        lines.append("no nodes.")
        return lines

    accepted = _accepted_counts(data)
    grouped: dict[str, list] = {state: [] for state in _STATE_GROUPS}
    for node in data.nodes:
        grouped.setdefault(data.state.state_of(node.id), []).append(node)

    for state in _STATE_GROUPS:
        members = grouped.get(state, [])
        if not members:
            continue
        lines.append("")
        lines.append(f"### {state} ({len(members)})")
        for node in members:
            count = accepted.get(node.id, 0)
            lines.append(f"- {node.id} — {node.title} (accepted evidence: {count})")
    return lines


def _render_evidence(data: ExportData) -> list[str]:
    required_specs = sum(1 for spec in data.artifact_specs if spec.required)
    accepted_records = sum(1 for record in data.evidence_records if record.accepted)
    superseded = {r.supersedes for r in data.evidence_records if r.supersedes is not None}
    live_accepted = sum(
        1
        for record in data.evidence_records
        if record.accepted and record.id not in superseded
    )
    passed_attempts = sum(1 for attempt in data.attempts if attempt.outcome == "passed")
    failed_attempts = len(data.attempts) - passed_attempts

    return [
        "",
        "## Evidence",
        f"artifact specs: {len(data.artifact_specs)} ({required_specs} required)",
        f"validation gates: {len(data.validation_gates)}",
        f"evidence records: {len(data.evidence_records)} "
        f"({accepted_records} accepted, {live_accepted} live-accepted)",
        f"assessment attempts: {len(data.attempts)} "
        f"({passed_attempts} passed, {failed_attempts} failed)",
    ]


def _render_sessions(data: ExportData) -> list[str]:
    lines = ["", "## Sessions"]
    if not data.sessions:
        lines.append("no sessions.")
        return lines

    open_count = sum(1 for s in data.sessions if s.status == "open")
    completed_count = len(data.sessions) - open_count
    total_minutes = sum(w.minutes for w in data.session_work if w.minutes is not None)
    lines.append(
        f"total: {len(data.sessions)} ({open_count} open, {completed_count} completed); "
        f"{total_minutes} minute(s) logged across {len(data.session_work)} work item(s)"
    )

    recent = sorted(data.sessions, key=lambda s: s.started_at, reverse=True)
    recent = recent[:_RECENT_SESSION_COUNT]
    lines.append("")
    lines.append(f"recent (most recent {len(recent)}):")
    for session in recent:
        end = f" — ended {session.ended_at}" if session.ended_at else " — open"
        lines.append(f"- {session.id} started {session.started_at}{end}")
    return lines


def render_markdown(data: ExportData, *, now: str) -> str:
    """Render the complete-but-compact snapshot. Pure — takes already-loaded data
    and an already-stamped `now` (the command handler owns the clock, matching
    `commands/_common.now_iso`)."""
    lines = ["# SkillTrace export", f"generated: {now}"]
    lines += ["", *_render_nodes(data)]
    lines += _render_evidence(data)
    lines += _render_sessions(data)
    return "\n".join(lines) + "\n"
