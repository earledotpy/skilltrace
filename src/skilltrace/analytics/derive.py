"""Pure derivation functions for the four analytics themes (v1.6).

Every function that produces time-keyed output takes ``today: datetime.date``
as a required keyword argument (T-TestArch D1). The CLI layer is the only
place that calls ``datetime.date.today()``; these functions are clock-free.

No I/O of any kind in this module — callers pass already-loaded collections.
Filters are applied before grouping so unit tests can assert exact counts
without constructing a full joined view.

Public surface:
  derive_velocity(sessions, work, *, today, window_days, group_by, state_filter, nodes, store) -> VelocityResult
  derive_blockers(blockers, *, today, window_days, group_by, state_filter, nodes, store) -> BlockersResult
  derive_reviews(reviews, sessions, *, today, window_days, state_filter) -> ReviewsResult
  derive_evidence(specs, records, nodes, store, *, today, window_days, group_by, state_filter, min_sessions, sessions) -> EvidenceResult
  derive_analytics(joined, *, today, window_days, group_by, state_filter, min_sessions_for_full_data) -> AnalyticsView
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

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


def _parse_date(val: Any) -> date | None:
    """Safely parse a stored ISO date or timestamp string into a date."""
    if val is None:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None


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
            buckets[label] = WeekBucket(label=label, session_count=0, node_count=0, minutes=0)
        d += timedelta(days=1)
    return buckets


# ---------------------------------------------------------------------------
# 1. Velocity
# ---------------------------------------------------------------------------


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
        started = _parse_date(s.started_at)
        if started is not None and started >= cutoff:
            window_sessions.add(s.id)

    sessions_in_window = len(window_sessions)
    is_limited = sessions_in_window < min_sessions_for_full_data

    # Work items in window, optionally filtered by node state.
    nodes_touched_set: set[str] = set()
    total_minutes = 0
    weekly_sessions: dict[str, set[str]] = defaultdict(set)  # week -> session ids
    weekly_nodes: dict[str, set[str]] = defaultdict(set)
    weekly_minutes: dict[str, int] = defaultdict(int)

    for item in work:
        if item.session_id not in window_sessions:
            continue
        if not _state_matches(item.node_id, state_filter, store):
            continue
        nodes_touched_set.add(item.node_id)
        minutes = item.minutes or 0
        total_minutes += minutes

        # Bucket by the item's created_at date.
        item_date = _parse_date(item.created_at)
        if item_date is not None:
            wk = _iso_week_label(item_date)
            weekly_sessions[wk].add(item.session_id)
            weekly_nodes[wk].add(item.node_id)
            weekly_minutes[wk] += minutes

    nodes_touched = len(nodes_touched_set)

    # Build chronological weekly buckets.
    raw_buckets = _build_week_buckets(cutoff, today)
    for wk, bucket in raw_buckets.items():
        bucket.session_count = len(weekly_sessions.get(wk, set()))
        bucket.node_count = len(weekly_nodes.get(wk, set()))
        bucket.minutes = weekly_minutes.get(wk, 0)
    weeks = sorted(raw_buckets.values(), key=lambda b: b.label)

    # Group rows: (group, session_count, node_count) sorted by session_count desc.
    group_sessions: dict[str, set[str]] = defaultdict(set)
    group_nodes: dict[str, set[str]] = defaultdict(set)
    for item in work:
        if item.session_id not in window_sessions:
            continue
        if not _state_matches(item.node_id, state_filter, store):
            continue
        grp = _group_value(item.node_id, group_by, nodes, store)
        group_sessions[grp].add(item.session_id)
        group_nodes[grp].add(item.node_id)

    group_rows = sorted(
        [
            (grp, len(group_sessions[grp]), len(group_nodes[grp]))
            for grp in group_sessions
        ],
        key=lambda r: r[1],
        reverse=True,
    )

    return VelocityResult(
        sessions_in_window=sessions_in_window,
        nodes_touched=nodes_touched,
        total_minutes=total_minutes,
        weeks=weeks,
        group_rows=group_rows,
        is_limited=is_limited,
    )


# ---------------------------------------------------------------------------
# 2. Blockers
# ---------------------------------------------------------------------------


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
    cutoff = _window_start(today, window_days)
    is_limited = sessions_in_window < min_sessions_for_full_data

    open_blockers = []
    resolved_in_window = 0

    for b in blockers:
        if not _state_matches(b.node_id, state_filter, store):
            continue
        if b.status == "open":
            created = _parse_date(b.created_at)
            days_open = (today - created).days if created else 0
            grp = _group_value(b.node_id, group_by, nodes, store)
            open_blockers.append(
                BlockerRow(
                    node_id=b.node_id,
                    group=grp,
                    description=b.description,
                    days_open=days_open,
                    status="open",
                )
            )
        elif b.status in ("resolved", "closed"):
            resolved_at = _parse_date(getattr(b, "resolved_at", None))
            if resolved_at is not None and resolved_at >= cutoff:
                resolved_in_window += 1

    open_blockers.sort(key=lambda r: r.days_open, reverse=True)

    return BlockersResult(
        open_count=len(open_blockers),
        resolved_in_window=resolved_in_window,
        rows=open_blockers,
        is_limited=is_limited,
    )


# ---------------------------------------------------------------------------
# 3. Reviews
# ---------------------------------------------------------------------------


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
    cutoff = _window_start(today, window_days)
    is_limited = sessions_in_window < min_sessions_for_full_data

    scheduled_rows: list[ReviewRow] = []
    scheduled_count = 0
    overdue_count = 0
    completed_in_window = 0

    for r in reviews:
        if not _state_matches(r.node_id, state_filter, store):
            continue

        if r.status == "scheduled":
            due = _parse_date(r.scheduled_for)
            is_overdue = due is not None and due < today
            days_overdue = (today - due).days if is_overdue and due else 0
            scheduled_count += 1
            if is_overdue:
                overdue_count += 1
            scheduled_rows.append(
                ReviewRow(
                    node_id=r.node_id,
                    status="scheduled",
                    scheduled_for=str(r.scheduled_for),
                    days_overdue=days_overdue,
                    outcome=None,
                )
            )
        elif r.status == "completed":
            completed_at = _parse_date(getattr(r, "completed_at", None))
            if completed_at is not None and completed_at >= cutoff:
                completed_in_window += 1

    # Sort: overdue first (most overdue at top), then by scheduled_for ascending.
    scheduled_rows.sort(key=lambda r: (-r.days_overdue, r.scheduled_for))

    total_relevant = completed_in_window + scheduled_count
    completion_rate = (
        completed_in_window / total_relevant if total_relevant > 0 else 0.0
    )

    return ReviewsResult(
        scheduled_count=scheduled_count,
        overdue_count=overdue_count,
        completed_in_window=completed_in_window,
        completion_rate=completion_rate,
        rows=scheduled_rows,
        is_limited=is_limited,
    )


# ---------------------------------------------------------------------------
# 4. Evidence
# ---------------------------------------------------------------------------


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
    is_limited = sessions_in_window < min_sessions_for_full_data

    # Index: spec_id -> list of records (non-superseded accepted).
    superseded_ids: set[str] = {r.supersedes for r in records if r.supersedes is not None}
    accepted_by_spec: dict[str, int] = defaultdict(int)
    for r in records:
        if r.accepted and r.id not in superseded_ids:
            accepted_by_spec[r.artifact_spec_id] += 1

    # Index: node_id -> specs.
    specs_by_node: dict[str, list] = defaultdict(list)
    for spec in specs:
        specs_by_node[spec.node_id].append(spec)

    rows: list[EvidenceRow] = []
    nodes_with_specs = 0
    nodes_with_gaps = 0

    for node in nodes:
        node_specs = specs_by_node.get(node.id, [])
        if not node_specs:
            continue
        if not _state_matches(node.id, state_filter, store):
            continue

        nodes_with_specs += 1
        accepted_count = sum(accepted_by_spec.get(s.id, 0) for s in node_specs)
        has_gap = any(
            s.required and accepted_by_spec.get(s.id, 0) == 0
            for s in node_specs
        )
        if has_gap:
            nodes_with_gaps += 1

        grp = _group_value(node.id, group_by, nodes, store)
        node_state = _node_state(node.id, store)
        rows.append(
            EvidenceRow(
                node_id=node.id,
                group=grp,
                state=node_state,
                spec_count=len(node_specs),
                accepted_count=accepted_count,
                gap=has_gap,
            )
        )

    rows.sort(key=lambda r: (0 if r.gap else 1, r.group, r.node_id))

    coverage_rate = (
        (nodes_with_specs - nodes_with_gaps) / nodes_with_specs
        if nodes_with_specs > 0
        else 0.0
    )

    return EvidenceResult(
        nodes_with_specs=nodes_with_specs,
        nodes_with_gaps=nodes_with_gaps,
        coverage_rate=coverage_rate,
        rows=rows,
        is_limited=is_limited,
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
    a frozen date.
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
        velocity.is_limited
        or blockers.is_limited
        or reviews.is_limited
        or evidence.is_limited
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
