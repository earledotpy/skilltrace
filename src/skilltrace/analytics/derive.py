"""Pure derivation functions for the four analytics themes (v1.6).

Every function that produces time-keyed output takes ``today: datetime.date``
as a required keyword argument (T-TestArch D1). The CLI layer is the only
place that calls ``datetime.date.today()``; these functions are clock-free.

No I/O of any kind in this module — callers pass already-loaded collections.
Filters are applied before grouping so unit tests can assert exact counts
without constructing a full joined view.

The shared scaffolding — windowing (rolling cutoff), state filtering,
grouping, limited-data detection, and result construction — lives in
``derive_theme``. Each analytics theme is a declarative configuration of
three callbacks over that framework:

* ``filter_item(item, ctx)`` — does this record belong in the result set
  (window membership + state match)?
* ``build_row(item, ctx)`` — turn one accepted record into a typed row
  (or a counting marker, or ``None`` to skip).
* ``aggregate(rows, ctx)`` — combine rows into the theme's result object.

Public surface:
  derive_theme(items, *, today, window_days, group_by, state_filter, nodes, store, sessions_in_window, ...) -> Any
  derive_velocity(sessions, work, *, today, window_days, group_by, state_filter, nodes, store) -> VelocityResult
  derive_blockers(blockers, *, today, window_days, group_by, state_filter, nodes, store) -> BlockersResult
  derive_reviews(reviews, sessions, *, today, window_days, state_filter) -> ReviewsResult
  derive_evidence(specs, records, nodes, store, *, today, window_days, group_by, state_filter, min_sessions, sessions) -> EvidenceResult
  derive_analytics(joined, *, today, window_days, group_by, state_filter, min_sessions_for_full_data) -> AnalyticsView
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable

from ..execution.overdue import days_overdue as _days_overdue, is_overdue as _is_overdue, parse_date
from .models import (
    AnalyticsView,
    BlockerRow,
    BlockersResult,
    EvidenceResult,
    EvidenceRow,
    ReviewRow,
    ReviewsResult,
    VelocityResult,
    WeekBucket,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _window_start(today: date, window_days: int) -> date:
    return today - timedelta(days=window_days)


def _node_prefix(node_id: str) -> str:
    """Return the dot-delimited prefix (first two segments) of a node ID.

    ``math.arithmetic.order_operations_01`` -> ``math.arithmetic``.
    For IDs with fewer than two segments the whole ID is returned.
    """
    parts = node_id.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else node_id


def _node_track(node_id: str, nodes: Any, store: Any) -> str:
    """Look up a node's track attribute; fall back to the node-ID prefix."""
    node_map: dict[str, Any] = getattr(nodes, "__node_map", None)
    if node_map is None:
        # nodes is a plain list — build the map lazily via the parameter
        if isinstance(nodes, list):
            node_map = {n.id: n for n in nodes}
        else:
            node_map = {}
    node = node_map.get(node_id)
    if node is not None and hasattr(node, "track") and node.track:
        return str(node.track)
    return _node_prefix(node_id)


def _group_value(node_id: str, group_by: str, nodes_list: list, store: Any) -> str:
    """Return the grouping key for a node according to *group_by*."""
    if group_by == "track":
        return _node_track(node_id, nodes_list, store)
    return _node_prefix(node_id)


def _node_state(node_id: str, store: Any) -> str:
    if store is None:
        return "available"
    return store.state_of(node_id)


def _state_matches(node_id: str, state_filter: list[str], store: Any) -> bool:
    """True when state_filter is empty (all states) or matches the node's state."""
    if not state_filter:
        return True
    return _node_state(node_id, store) in state_filter


def _iso_week_label(d: date) -> str:
    """Return an ISO-year-week label, e.g. '2026-W35'."""
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _build_week_buckets(start: date, today: date) -> dict[str, WeekBucket]:
    """Pre-build one bucket per ISO week from *start* to *today* (inclusive)."""
    buckets: dict[str, WeekBucket] = {}
    d = start
    while d <= today:
        label = _iso_week_label(d)
        if label not in buckets:
            buckets[label] = WeekBucket(
                label=label, session_count=0, node_count=0, work_item_count=0, minutes=0
            )
        d += timedelta(days=1)
    return buckets


# ---------------------------------------------------------------------------
# Framework: derive_theme
# ---------------------------------------------------------------------------


@dataclass
class _ThemeContext:
    """Shared scaffolding state handed to every theme callback.

    ``cutoff`` is the rolling window start (``today - window_days``);
    ``is_limited`` is True when ``sessions_in_window`` is below the
    ``min_sessions_for_full_data`` threshold. ``extra`` carries
    theme-specific precomputed state (e.g. velocity's ``window_sessions``
    set or evidence's spec indexes) so the module-level filter/row
    callbacks stay directly unit-testable.
    """

    today: date
    cutoff: date
    window_days: int
    group_by: str
    state_filter: list[str]
    nodes: list
    store: Any
    sessions_in_window: int
    min_sessions_for_full_data: int
    extra: dict = field(default_factory=dict)

    @property
    def is_limited(self) -> bool:
        return self.sessions_in_window < self.min_sessions_for_full_data

    def state_matches(self, node_id: str) -> bool:
        return _state_matches(node_id, self.state_filter, self.store)

    def group_value(self, node_id: str) -> str:
        return _group_value(node_id, self.group_by, self.nodes, self.store)

    def node_state(self, node_id: str) -> str:
        return _node_state(node_id, self.store)


def derive_theme(
    items: list,
    *,
    today: date,
    window_days: int,
    group_by: str,
    state_filter: list[str],
    min_sessions_for_full_data: int,
    nodes: list,
    store: Any,
    sessions_in_window: int,
    filter_item: Callable[[Any, _ThemeContext], bool],
    build_row: Callable[[Any, _ThemeContext], Any | None],
    aggregate: Callable[[list, _ThemeContext], Any],
    extra: dict | None = None,
) -> Any:
    """Run one analytics theme over *items* through the shared scaffolding.

    Applies the per-item *filter_item* (windowing + state match), turns
    each accepted item into a row with *build_row* (``None`` rows are
    skipped), and combines rows into the theme's typed result with
    *aggregate*. Limited-data detection (``sessions_in_window`` vs
    ``min_sessions_for_full_data``) is computed once here and exposed
    to the aggregator as ``ctx.is_limited`` so all themes stay consistent.
    """
    ctx = _ThemeContext(
        today=today,
        cutoff=_window_start(today, window_days),
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        nodes=nodes,
        store=store,
        sessions_in_window=sessions_in_window,
        min_sessions_for_full_data=min_sessions_for_full_data,
        extra=dict(extra or {}),
    )
    rows: list = []
    for item in items:
        if filter_item(item, ctx):
            row = build_row(item, ctx)
            if row is not None:
                rows.append(row)
    return aggregate(rows, ctx)


# ---------------------------------------------------------------------------
# 1. Velocity
# ---------------------------------------------------------------------------


@dataclass
class _VelocityIntermediate:
    """One filtered work item with its week bucket and group key resolved."""

    session_id: str
    node_id: str
    minutes: int
    week_label: str | None
    group: str


def _velocity_filter(item: Any, ctx: _ThemeContext) -> bool:
    """Accept work items in a window session whose node matches the state filter."""
    if item.session_id not in ctx.extra["window_sessions"]:
        return False
    return ctx.state_matches(item.node_id)


def _velocity_build_row(item: Any, ctx: _ThemeContext) -> _VelocityIntermediate:
    item_date = parse_date(item.created_at)
    return _VelocityIntermediate(
        session_id=item.session_id,
        node_id=item.node_id,
        minutes=item.minutes or 0,
        week_label=_iso_week_label(item_date) if item_date is not None else None,
        group=ctx.group_value(item.node_id),
    )


def _velocity_aggregate(rows: list[_VelocityIntermediate], ctx: _ThemeContext) -> VelocityResult:
    nodes_touched = len({r.node_id for r in rows})
    total_minutes = sum(r.minutes for r in rows)

    weekly_sessions: dict[str, set[str]] = defaultdict(set)
    weekly_nodes: dict[str, set[str]] = defaultdict(set)
    weekly_work_items: dict[str, int] = defaultdict(int)
    weekly_minutes: dict[str, int] = defaultdict(int)
    for r in rows:
        if r.week_label is not None:
            weekly_sessions[r.week_label].add(r.session_id)
            weekly_nodes[r.week_label].add(r.node_id)
            weekly_work_items[r.week_label] += 1
            weekly_minutes[r.week_label] += r.minutes

    raw_buckets = _build_week_buckets(ctx.cutoff, ctx.today)
    for wk, bucket in raw_buckets.items():
        bucket.session_count = len(weekly_sessions.get(wk, set()))
        bucket.node_count = len(weekly_nodes.get(wk, set()))
        bucket.work_item_count = weekly_work_items.get(wk, 0)
        bucket.minutes = weekly_minutes.get(wk, 0)
    weeks = sorted(raw_buckets.values(), key=lambda b: b.label)

    group_sessions: dict[str, set[str]] = defaultdict(set)
    group_nodes: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        group_sessions[r.group].add(r.session_id)
        group_nodes[r.group].add(r.node_id)
    group_rows = sorted(
        [(grp, len(group_sessions[grp]), len(group_nodes[grp])) for grp in group_sessions],
        key=lambda r: r[1],
        reverse=True,
    )

    return VelocityResult(
        sessions_in_window=ctx.sessions_in_window,
        nodes_touched=nodes_touched,
        total_minutes=total_minutes,
        weeks=weeks,
        group_rows=group_rows,
        is_limited=ctx.is_limited,
    )


def derive_velocity(
    sessions: list,
    work: list,
    *,
    today: date,
    window_days: int,
    group_by: str,
    state_filter: list[str],
    nodes: list,
    store: Any,
    min_sessions_for_full_data: int,
) -> VelocityResult:
    """Derive study-velocity metrics over a rolling window.

    ``today`` is required; the CLI is the only ``datetime.date.today()`` call
    site. ``state_filter`` is applied per work-item node (OR semantics).
    """
    cutoff = _window_start(today, window_days)

    # Sessions in window (completed or open, started on/after cutoff).
    window_sessions: set[str] = set()
    for s in sessions:
        started = parse_date(s.started_at)
        if started is not None and started >= cutoff:
            window_sessions.add(s.id)

    return derive_theme(
        work,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        nodes=nodes,
        store=store,
        sessions_in_window=len(window_sessions),
        filter_item=_velocity_filter,
        build_row=_velocity_build_row,
        aggregate=_velocity_aggregate,
        extra={"window_sessions": window_sessions},
    )


# ---------------------------------------------------------------------------
# 2. Blockers
# ---------------------------------------------------------------------------


@dataclass
class _ResolvedInWindow:
    """Counting marker for a blocker resolved within the window (no table row)."""


def _blockers_filter(item: Any, ctx: _ThemeContext) -> bool:
    """Accept open blockers (any age) and blockers resolved in the window."""
    if not ctx.state_matches(item.node_id):
        return False
    if item.status == "open":
        return True
    if item.status in ("resolved", "closed"):
        resolved_at = parse_date(getattr(item, "resolved_at", None))
        return resolved_at is not None and resolved_at >= ctx.cutoff
    return False


def _blockers_build_row(item: Any, ctx: _ThemeContext) -> BlockerRow | _ResolvedInWindow:
    if item.status == "open":
        created = parse_date(item.created_at)
        days_open = (ctx.today - created).days if created else 0
        return BlockerRow(
            node_id=item.node_id,
            group=ctx.group_value(item.node_id),
            description=item.description,
            days_open=days_open,
            status="open",
        )
    return _ResolvedInWindow()


def _blockers_aggregate(rows: list, ctx: _ThemeContext) -> BlockersResult:
    open_rows = [r for r in rows if isinstance(r, BlockerRow)]
    resolved_in_window = sum(1 for r in rows if isinstance(r, _ResolvedInWindow))
    open_rows.sort(key=lambda r: r.days_open, reverse=True)
    return BlockersResult(
        open_count=len(open_rows),
        resolved_in_window=resolved_in_window,
        rows=open_rows,
        is_limited=ctx.is_limited,
    )


def derive_blockers(
    blockers: list,
    *,
    today: date,
    window_days: int,
    group_by: str,
    state_filter: list[str],
    nodes: list,
    store: Any,
    min_sessions_for_full_data: int,
    sessions_in_window: int,
) -> BlockersResult:
    """Derive blocker metrics, grouped by *group_by* dimension.

    Open blockers are always included (they have no end date). Resolved
    blockers are included when resolved within the window. State filter
    applies to the blocker's node.
    """
    return derive_theme(
        blockers,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        nodes=nodes,
        store=store,
        sessions_in_window=sessions_in_window,
        filter_item=_blockers_filter,
        build_row=_blockers_build_row,
        aggregate=_blockers_aggregate,
    )


# ---------------------------------------------------------------------------
# 3. Reviews
# ---------------------------------------------------------------------------


@dataclass
class _CompletedInWindow:
    """Counting marker for a review completed within the window (no table row)."""


def _reviews_filter(item: Any, ctx: _ThemeContext) -> bool:
    """Accept scheduled reviews (any age — overdue can be old) and reviews
    completed within the window."""
    if not ctx.state_matches(item.node_id):
        return False
    if item.status == "scheduled":
        return True
    if item.status == "completed":
        completed_at = parse_date(getattr(item, "completed_at", None))
        return completed_at is not None and completed_at >= ctx.cutoff
    return False


def _reviews_build_row(item: Any, ctx: _ThemeContext) -> ReviewRow | _CompletedInWindow:
    if item.status == "scheduled":
        return ReviewRow(
            node_id=item.node_id,
            status="scheduled",
            scheduled_for=str(item.scheduled_for),
            days_overdue=_days_overdue(item, today=ctx.today),
            outcome=None,
        )
    return _CompletedInWindow()


def _reviews_aggregate(rows: list, ctx: _ThemeContext) -> ReviewsResult:
    scheduled_rows = [r for r in rows if isinstance(r, ReviewRow)]
    completed_in_window = sum(1 for r in rows if isinstance(r, _CompletedInWindow))
    scheduled_count = len(scheduled_rows)
    overdue_count = sum(1 for r in scheduled_rows if r.days_overdue > 0)

    # Sort: overdue first (most overdue at top), then by scheduled_for ascending.
    scheduled_rows.sort(key=lambda r: (-r.days_overdue, r.scheduled_for))

    total_relevant = completed_in_window + scheduled_count
    completion_rate = completed_in_window / total_relevant if total_relevant > 0 else 0.0

    return ReviewsResult(
        scheduled_count=scheduled_count,
        overdue_count=overdue_count,
        completed_in_window=completed_in_window,
        completion_rate=completion_rate,
        rows=scheduled_rows,
        is_limited=ctx.is_limited,
    )


def derive_reviews(
    reviews: list,
    sessions: list,
    *,
    today: date,
    window_days: int,
    state_filter: list[str],
    min_sessions_for_full_data: int,
    sessions_in_window: int,
    store: Any,
) -> ReviewsResult:
    """Derive review completion-rate and overdue highlighting.

    Scheduled reviews from all time are included (overdue can be old).
    Completed reviews are counted when completed_at falls in the window.
    State filter applies to the review's node.
    """
    return derive_theme(
        reviews,
        today=today,
        window_days=window_days,
        group_by="prefix",
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        nodes=[],
        store=store,
        sessions_in_window=sessions_in_window,
        filter_item=_reviews_filter,
        build_row=_reviews_build_row,
        aggregate=_reviews_aggregate,
    )


# ---------------------------------------------------------------------------
# 4. Evidence
# ---------------------------------------------------------------------------


def _evidence_filter(node: Any, ctx: _ThemeContext) -> bool:
    """Accept nodes that own at least one spec and match the state filter."""
    if not ctx.extra["specs_by_node"].get(node.id, []):
        return False
    return ctx.state_matches(node.id)


def _evidence_build_row(node: Any, ctx: _ThemeContext) -> EvidenceRow:
    node_specs = ctx.extra["specs_by_node"][node.id]
    accepted_by_spec: dict[str, int] = ctx.extra["accepted_by_spec"]
    accepted_count = sum(accepted_by_spec.get(s.id, 0) for s in node_specs)
    has_gap = any(s.required and accepted_by_spec.get(s.id, 0) == 0 for s in node_specs)
    return EvidenceRow(
        node_id=node.id,
        group=ctx.group_value(node.id),
        state=ctx.node_state(node.id),
        spec_count=len(node_specs),
        accepted_count=accepted_count,
        gap=has_gap,
    )


def _evidence_aggregate(rows: list[EvidenceRow], ctx: _ThemeContext) -> EvidenceResult:
    rows.sort(key=lambda r: (0 if r.gap else 1, r.group, r.node_id))
    nodes_with_specs = len(rows)
    nodes_with_gaps = sum(1 for r in rows if r.gap)
    coverage_rate = (
        (nodes_with_specs - nodes_with_gaps) / nodes_with_specs if nodes_with_specs > 0 else 0.0
    )
    return EvidenceResult(
        nodes_with_specs=nodes_with_specs,
        nodes_with_gaps=nodes_with_gaps,
        coverage_rate=coverage_rate,
        rows=rows,
        is_limited=ctx.is_limited,
        accepted_count=ctx.extra["total_accepted"],
        rejected_count=ctx.extra["total_rejected"],
    )


def derive_evidence(
    specs: list,
    records: list,
    nodes: list,
    store: Any,
    *,
    today: date,
    window_days: int,
    group_by: str,
    state_filter: list[str],
    min_sessions_for_full_data: int,
    sessions_in_window: int,
) -> EvidenceResult:
    """Derive evidence-coverage per node and gap analysis.

    A 'gap' is a node that has at least one required spec with no accepted
    (non-superseded) evidence record. ``today`` is accepted for interface
    consistency (T-TestArch D1) even though evidence coverage is not
    date-windowed.
    """
    # Index: spec_id -> live (non-superseded) record counts.
    superseded_ids: set[str] = {r.supersedes for r in records if r.supersedes is not None}
    accepted_by_spec: dict[str, int] = defaultdict(int)
    rejected_by_spec: dict[str, int] = defaultdict(int)
    for r in records:
        if r.id in superseded_ids:
            continue
        if r.accepted:
            accepted_by_spec[r.artifact_spec_id] += 1
        else:
            rejected_by_spec[r.artifact_spec_id] += 1

    # Index: node_id -> specs.
    specs_by_node: dict[str, list] = defaultdict(list)
    for spec in specs:
        specs_by_node[spec.node_id].append(spec)

    return derive_theme(
        list(nodes),
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        nodes=nodes,
        store=store,
        sessions_in_window=sessions_in_window,
        filter_item=_evidence_filter,
        build_row=_evidence_build_row,
        aggregate=_evidence_aggregate,
        extra={
            "specs_by_node": specs_by_node,
            "accepted_by_spec": accepted_by_spec,
            "total_accepted": sum(accepted_by_spec.values()),
            "total_rejected": sum(rejected_by_spec.values()),
        },
    )


# ---------------------------------------------------------------------------
# Umbrella
# ---------------------------------------------------------------------------


def derive_analytics(
    joined: Any,
    *,
    today: date,
    window_days: int,
    group_by: str,
    state_filter: list[str],
    min_sessions_for_full_data: int,
) -> AnalyticsView:
    """Derive all four themes and wrap them in an AnalyticsView.

    ``joined`` is a ``JoinedView`` from ``context.load_context_lenient``.
    The CLI layer passes ``datetime.date.today()`` as ``today``; tests pass
    a frozen date. Each theme is derived through the ``derive_theme``
    framework via its thin ``derive_*`` wrapper.
    """
    velocity = derive_velocity(
        joined.sessions,
        joined.work,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        nodes=joined.nodes,
        store=joined.store,
        min_sessions_for_full_data=min_sessions_for_full_data,
    )
    sessions_in_window = velocity.sessions_in_window

    blockers = derive_blockers(
        joined.blockers,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        nodes=joined.nodes,
        store=joined.store,
        min_sessions_for_full_data=min_sessions_for_full_data,
        sessions_in_window=sessions_in_window,
    )
    reviews = derive_reviews(
        joined.reviews,
        joined.sessions,
        today=today,
        window_days=window_days,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        sessions_in_window=sessions_in_window,
        store=joined.store,
    )
    evidence = derive_evidence(
        joined.specs,
        joined.records,
        joined.nodes,
        joined.store,
        today=today,
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        min_sessions_for_full_data=min_sessions_for_full_data,
        sessions_in_window=sessions_in_window,
    )

    is_limited = (
        velocity.is_limited or blockers.is_limited or reviews.is_limited or evidence.is_limited
    )

    return AnalyticsView(
        window_days=window_days,
        group_by=group_by,
        state_filter=state_filter,
        velocity=velocity,
        blockers=blockers,
        reviews=reviews,
        evidence=evidence,
        is_limited=is_limited,
        sessions_in_window=sessions_in_window,
        min_sessions_for_full_data=min_sessions_for_full_data,
    )
