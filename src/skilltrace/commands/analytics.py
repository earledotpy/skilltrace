"""`skilltrace analytics` — event-log analytics command family (issue #128).

Per the G4 resolution (#122):
- `skilltrace analytics`                — umbrella, all four themes stacked.
- `skilltrace analytics velocity`       — per-theme table + Mentor frame.
- `skilltrace analytics blockers`       — per-theme table + Mentor frame.
- `skilltrace analytics reviews`        — per-theme table + Mentor frame.
- `skilltrace analytics evidence`       — per-theme table + Mentor frame.

Shared flags: `--days <N>`, `--group-by <prefix|track>`,
`--state <X>` (repeatable; OR semantics).

Defaults from `policy/analytics.yaml`: `default_window_days=30`,
`default_group_by=prefix`. When the rolling window covers fewer sessions
than `min_sessions_for_full_data`, output is preceded by an
`[advisory] Limited data — ...` line (render.advisory()).

Read-only: no audit events emitted by this command family (Kind.READ_ONLY).
"""

from __future__ import annotations

import datetime
from pathlib import Path

from .. import render
from ..analytics.derive import derive_analytics
from ..analytics.models import (
    AnalyticsView,
    BlockersResult,
    EvidenceResult,
    ReviewsResult,
    VelocityResult,
)
from ..context import load_context_lenient
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError
from ..graph.state import ProgressStoreError
from ..policy.advisory import analytics_warnings

# ---------------------------------------------------------------------------
# Policy helpers
# ---------------------------------------------------------------------------

_DEFAULT_WINDOW_DAYS = 30
_DEFAULT_GROUP_BY = "prefix"
_DEFAULT_MIN_SESSIONS = 3


def _policy_int(doc: dict, key: str, default: int) -> int:
    val = doc.get(key)
    if isinstance(val, int) and not isinstance(val, bool) and val > 0:
        return val
    return default


def _resolve_params(ctx: Context) -> tuple[int, str, list[str], int]:
    """Resolve window_days, group_by, state_filter, min_sessions from args + policy."""
    args = ctx.args
    joined = ctx.joined

    # Read policy defaults when available; fall back to module constants.
    if joined is not None:
        policy_doc = joined.policy.analytics
    else:
        policy_doc = {}

    window_days_default = _policy_int(policy_doc, "default_window_days", _DEFAULT_WINDOW_DAYS)
    group_by_default = policy_doc.get("default_group_by", _DEFAULT_GROUP_BY)
    if group_by_default not in ("prefix", "track"):
        group_by_default = _DEFAULT_GROUP_BY
    min_sessions = _policy_int(policy_doc, "min_sessions_for_full_data", _DEFAULT_MIN_SESSIONS)

    days = getattr(args, "days", None) or window_days_default
    group_by = getattr(args, "group_by", None) or group_by_default
    state_raw = getattr(args, "state", None) or []
    state_filter = list(state_raw) if state_raw else []

    return int(days), str(group_by), state_filter, min_sessions


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

_COL_W = 28   # group column width
_NUM_W = 7    # numeric column width


def _limited_advisory(view: AnalyticsView) -> str:
    return (
        f"Limited data — fewer than {view.min_sessions_for_full_data} sessions "
        f"in the last {view.window_days} days "
        f"({view.sessions_in_window} found). Results may be sparse."
    )


def _header_line(label: str) -> list[str]:
    return ["", render.section_kicker(label), "-" * len(label)]


def _render_velocity(v: VelocityResult, group_by: str) -> list[str]:
    lines: list[str] = []
    lines += _header_line("Velocity")
    lines.append(
        f"  Sessions in window : {v.sessions_in_window}"
    )
    lines.append(f"  Nodes touched      : {v.nodes_touched}")
    hours = v.total_minutes / 60.0
    lines.append(f"  Study time         : {v.total_minutes} min ({hours:.1f} h)")
    if not v.group_rows:
        lines.append("")
        lines.append("  (no work items in window)")
        return lines
    lines.append("")
    col_label = "Prefix" if group_by == "prefix" else "Track"
    lines.append(
        f"  {'Group (' + col_label + ')':<{_COL_W}}  {'Sessions':>{_NUM_W}}  {'Nodes':>{_NUM_W}}"
    )
    lines.append("  " + "-" * (_COL_W + _NUM_W * 2 + 4))
    for grp, ses, nds in v.group_rows:
        lines.append(f"  {grp:<{_COL_W}}  {ses:>{_NUM_W}}  {nds:>{_NUM_W}}")
    return lines


def _render_blockers(b: BlockersResult, group_by: str) -> list[str]:
    lines: list[str] = []
    lines += _header_line("Blockers")
    lines.append(f"  Open blockers      : {b.open_count}")
    lines.append(f"  Resolved in window : {b.resolved_in_window}")
    if not b.rows:
        lines.append("")
        lines.append("  (no open blockers)")
        return lines
    lines.append("")
    col_label = "Prefix" if group_by == "prefix" else "Track"
    lines.append(
        f"  {'Group (' + col_label + ')':<{_COL_W}}  {'Days open':>{_NUM_W}}  Description"
    )
    lines.append("  " + "-" * (_COL_W + _NUM_W + 4 + 30))
    for row in b.rows:
        desc = row.description[:40] + "..." if len(row.description) > 40 else row.description
        lines.append(
            f"  {row.group:<{_COL_W}}  {row.days_open:>{_NUM_W}}  {desc}"
        )
    return lines


def _render_reviews(r: ReviewsResult) -> list[str]:
    lines: list[str] = []
    lines += _header_line("Reviews")
    pct = f"{r.completion_rate * 100:.0f}%"
    lines.append(f"  Scheduled          : {r.scheduled_count}")
    lines.append(f"  Overdue            : {r.overdue_count}")
    lines.append(f"  Completed in window: {r.completed_in_window}")
    lines.append(f"  Completion rate    : {pct}")
    if not r.rows:
        lines.append("")
        lines.append("  (no scheduled reviews)")
        return lines
    lines.append("")
    lines.append(
        f"  {'Node':<{_COL_W}}  {'Due':>10}  {'Overdue':>{_NUM_W}}"
    )
    lines.append("  " + "-" * (_COL_W + 10 + _NUM_W + 4))
    for row in r.rows:
        overdue_str = f"{row.days_overdue}d" if row.days_overdue > 0 else "-"
        lines.append(
            f"  {row.node_id:<{_COL_W}}  {row.scheduled_for:>10}  {overdue_str:>{_NUM_W}}"
        )
    return lines


def _render_evidence(e: EvidenceResult, group_by: str) -> list[str]:
    lines: list[str] = []
    lines += _header_line("Evidence")
    pct = f"{e.coverage_rate * 100:.0f}%"
    lines.append(f"  Nodes with specs   : {e.nodes_with_specs}")
    lines.append(f"  Nodes with gaps    : {e.nodes_with_gaps}")
    lines.append(f"  Coverage rate      : {pct}")
    if not e.rows:
        lines.append("")
        lines.append("  (no nodes with artifact specs)")
        return lines
    lines.append("")
    col_label = "Prefix" if group_by == "prefix" else "Track"
    lines.append(
        f"  {'Group (' + col_label + ')':<{_COL_W}}  {'State':<10}  {'Specs':>{_NUM_W}}  {'Accepted':>{_NUM_W}}  Gap"
    )
    lines.append("  " + "-" * (_COL_W + 10 + _NUM_W * 2 + 10))
    for row in e.rows:
        gap_str = "[GAP]" if row.gap else "ok"
        lines.append(
            f"  {row.group:<{_COL_W}}  {row.state:<10}  {row.spec_count:>{_NUM_W}}  {row.accepted_count:>{_NUM_W}}  {gap_str}"
        )
    return lines


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _load_view(ctx: Context) -> tuple[AnalyticsView | None, CommandResult | None]:
    """Load the joined view and derive the analytics model. Returns (view, None) on
    success or (None, CommandResult) on failure."""
    root = ctx.root
    try:
        joined = ctx.joined or load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"analytics: FAILED -- {exc}")
        return None, CommandResult(exit_code=1)

    window_days, group_by, state_filter, min_sessions = _resolve_params(
        Context(root=root, args=ctx.args, joined=joined, clock=ctx.clock)
    )
    today = datetime.date.today()

    view = derive_analytics(
        joined,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions,
    )
    return view, None


def analytics_umbrella(ctx: Context) -> CommandResult:
    """Print all four theme blocks stacked."""
    view, err = _load_view(ctx)
    if err is not None:
        return err

    lines: list[str] = []
    lines.append(render.section_kicker("Analytics"))
    lines.extend(
        render.section_brief(
            f"Rolling {view.window_days}-day window, grouped by {view.group_by}."
            + (f" Filtered to states: {', '.join(view.state_filter)}." if view.state_filter else "")
        )
    )

    if view.is_limited:
        lines.append(render.advisory(_limited_advisory(view)))

    for warning in analytics_warnings(ctx.root, view):
        lines.append(render.advisory(warning))

    lines += _render_velocity(view.velocity, view.group_by)
    lines += _render_blockers(view.blockers, view.group_by)
    lines += _render_reviews(view.reviews)
    lines += _render_evidence(view.evidence, view.group_by)

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


def analytics_velocity(ctx: Context) -> CommandResult:
    """Per-theme velocity table."""
    view, err = _load_view(ctx)
    if err is not None:
        return err

    lines: list[str] = []
    if view.is_limited:
        lines.append(render.advisory(_limited_advisory(view)))
    lines += _render_velocity(view.velocity, view.group_by)
    lines.append("")
    lines.extend(
        render.section_brief(
            f"Showing study activity for the last {view.window_days} days, "
            f"grouped by {view.group_by}."
        )
    )

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


def analytics_blockers(ctx: Context) -> CommandResult:
    """Per-theme blockers table."""
    view, err = _load_view(ctx)
    if err is not None:
        return err

    lines: list[str] = []
    if view.is_limited:
        lines.append(render.advisory(_limited_advisory(view)))
    lines += _render_blockers(view.blockers, view.group_by)
    lines.append("")
    if view.blockers.open_count > 0:
        lines.extend(
            render.section_brief(
                f"You have {view.blockers.open_count} open blocker(s). "
                "Run `skilltrace report blockers` for rescue nodes and remediation detail."
            )
        )
    else:
        lines.extend(render.section_brief("No open blockers — smooth sailing!"))

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


def analytics_reviews(ctx: Context) -> CommandResult:
    """Per-theme reviews table."""
    view, err = _load_view(ctx)
    if err is not None:
        return err

    lines: list[str] = []
    if view.is_limited:
        lines.append(render.advisory(_limited_advisory(view)))
    lines += _render_reviews(view.reviews)
    lines.append("")
    if view.reviews.overdue_count > 0:
        lines.extend(
            render.section_brief(
                f"You have {view.reviews.overdue_count} overdue review(s). "
                "Run `skilltrace suggest reviews` to see what is due."
            )
        )
    else:
        lines.extend(
            render.section_brief(
                f"Completion rate: {view.reviews.completion_rate * 100:.0f}% "
                f"over the last {view.window_days} days."
            )
        )

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


def analytics_evidence(ctx: Context) -> CommandResult:
    """Per-theme evidence-coverage table."""
    view, err = _load_view(ctx)
    if err is not None:
        return err

    lines: list[str] = []
    if view.is_limited:
        lines.append(render.advisory(_limited_advisory(view)))
    lines += _render_evidence(view.evidence, view.group_by)
    lines.append("")
    if view.evidence.nodes_with_gaps > 0:
        lines.extend(
            render.section_brief(
                f"{view.evidence.nodes_with_gaps} node(s) have required specs with no accepted evidence. "
                "Run `skilltrace report evidence` for the full proof trail."
            )
        )
    else:
        lines.extend(
            render.section_brief(
                f"Evidence coverage: {view.evidence.coverage_rate * 100:.0f}% — "
                "all nodes with specs have at least one accepted submission."
            )
        )

    for line in lines:
        print(line)
    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="analytics",
            kind=Kind.READ_ONLY,
            handler=analytics_umbrella,
            help="Event-log analytics: all four themes stacked (velocity, blockers, reviews, evidence).",
        )
    )
    registry.register(
        Command(
            name="analytics velocity",
            kind=Kind.READ_ONLY,
            handler=analytics_velocity,
            help="Study-velocity analytics: session cadence and node progress over the rolling window.",
        )
    )
    registry.register(
        Command(
            name="analytics blockers",
            kind=Kind.READ_ONLY,
            handler=analytics_blockers,
            help="Blocker analytics: active stuckness grouped by domain prefix or track.",
        )
    )
    registry.register(
        Command(
            name="analytics reviews",
            kind=Kind.READ_ONLY,
            handler=analytics_reviews,
            help="Review analytics: completion rate and overdue highlighting.",
        )
    )
    registry.register(
        Command(
            name="analytics evidence",
            kind=Kind.READ_ONLY,
            handler=analytics_evidence,
            help="Evidence-coverage analytics: per-node gap analysis.",
        )
    )
