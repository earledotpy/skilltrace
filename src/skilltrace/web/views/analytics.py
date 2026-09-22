"""
GET ``/analytics`` — one read-only analytics theme per page
(ADR 0009), plus the granted tooltip-script budget (ADR 0008).

"""

from __future__ import annotations

from pathlib import Path

from ...analytics.derive import derive_analytics
from ...analytics.models import AnalyticsParams
from ...analytics.policy import limited_data_sentence
from ...analytics.sparkline import sparkline_svg
from ..analytics_tooltip import tooltip_script
from ...execution.overdue import utc_today
from ...policy.advisory import analytics_warnings
from ._shared import (
    _esc,
    _table,
)
from .shell import (
    _page_head,
    _status_page,
)


def _analytics_view(view, query: dict, root) -> tuple[object | None, tuple[str, str, int] | None]:
    policy = view.policy.analytics_policy
    default_days = policy.default_window_days
    raw_days = (query.get("days") or [str(default_days)])[0]
    try:
        days = int(raw_days)
    except (TypeError, ValueError):
        body, status = _status_page(400, "Analytics days must be a positive integer.", root)
        return None, ("Bad request", body, status)
    if days <= 0:
        body, status = _status_page(400, "Analytics days must be a positive integer.", root)
        return None, ("Bad request", body, status)
    group_by = (query.get("group-by") or [policy.default_group_by])[0]
    if group_by not in {"prefix", "track"}:
        body, status = _status_page(400, "Analytics group-by must be prefix or track.", root)
        return None, ("Bad request", body, status)
    min_sessions = policy.min_sessions_for_full_data
    # T6: the window/group/filter bundle is one value for every theme.
    params = AnalyticsParams(
        window_days=days,
        group_by=group_by,
        state_filter=(),
        min_sessions_for_full_data=min_sessions,
    )
    return (
        derive_analytics(
            view,
            today=utc_today(),
            params=params,
        ),
        None,
    )


def _analytics_export_form(days: int, group_by: str, theme: str) -> str:
    return (
        '<form method="post" action="/analytics/export" class="actions">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        f'<input type="hidden" name="days" value="{days}">'
        f'<input type="hidden" name="group_by" value="{_esc(group_by)}">'
        '<button class="btn secondary" type="submit" name="format" value="md">Export MD</button>'
        '<button class="btn secondary" type="submit" name="format" value="html">Export HTML</button>'
        '<button class="btn secondary" type="submit" name="format" value="json">Export JSON</button>'
        "</form>"
    )


def _analytics_card(
    title: str, summary: str, derivation: str, svg: str, detail: str, view, theme: str
) -> str:
    """One theme's page (T4 §H): a plain card; tables collapsed (P2.2)."""
    return (
        f'<div class="card analytics-card"><p class="lead">{_esc(title)}</p>'
        f'<p class="big">{_esc(summary)}</p><p class="mut">{_esc(derivation)}</p>{svg}'
        f"<details><summary>Details</summary>{detail}</details>"
        f"{_analytics_export_form(view.window_days, view.group_by, theme)}"
        "</div>"
    )


def analytics_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/analytics` - one read-only analytics theme per page (v2.4 S5).

    The ``theme`` query parameter selects the visible theme (default
    ``velocity``); the others are one plain-link away - a page shows one
    theme's chart, not four stacked charts. Charts are static inline SVG
    through the ``analytics/sparkline.py`` seam, real multi-point series
    only (P2.2 bans pseudo-sparklines: a single-point series renders no
    sparkline, just the labeled summary).
    """
    query = query or {}
    view, head, failure = _page_head(
        root, query, dismiss_path="/analytics", current_view="analytics"
    )
    if failure is not None:
        return failure
    model, failure = _analytics_view(view, query, Path(root))
    if model is None:
        return failure

    theme = (query.get("theme") or ["velocity"])[0]
    if theme not in {"velocity", "blockers", "reviews", "evidence"}:
        theme = "velocity"

    warnings = analytics_warnings(Path(root), model)
    overdue = (
        f'<p class="banner warning">Overdue reviews: {model.reviews.overdue_count} '
        "scheduled review(s) need attention.</p>"
        if model.reviews.overdue_count
        else ""
    )
    limited = ""
    if model.is_limited:
        sentence = limited_data_sentence(
            model.min_sessions_for_full_data, model.window_days
        )
        limited = f'<p class="banner advisory">{_esc(sentence)}</p>'
    days = model.window_days
    group_by = model.group_by
    options = "".join(
        f'<option value="{n}" {"selected" if n == days else ""}>{label}</option>'
        for n, label in ((7, "Last 7 days"), (30, "Last 30 days"), (90, "Last 90 days"))
    )
    controls = (
        '<div class="card analytics-controls"><form method="get" action="/analytics">'
        '<div class="form-row"><label>'
        "Date range</label>"
        f'<select name="days">{options}'
        f'<option value="{days}" {"selected" if days not in (7, 30, 90) else ""}>Policy default ({days}d)</option>'
        f'</select><input type="hidden" name="group-by" value="{_esc(group_by)}">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        '<p class="small mut">Which window the charts cover.</p>'
        '<button class="btn secondary" type="submit">Apply</button></div></form>'
        '<div class="form-row"><label>Group by</label>'
        '<p class="small mut">How sessions are bucketed in the charts.</p>'
        f'<a class="btn {"secondary" if group_by == "track" else ""}" href="/analytics?days={days}&amp;group-by=prefix&amp;theme={theme}">Prefix</a> '
        f'<a class="btn {"secondary" if group_by == "prefix" else ""}" href="/analytics?days={days}&amp;group-by=track&amp;theme={theme}">Track</a></div>'
        '</div>'
    )
    advisory = "".join(
        f'<p class="banner advisory">{_esc(warning)}</p>' for warning in warnings
    )

    velocity = model.velocity
    velocity_detail = _table(
        ["Group", "Sessions", "Nodes"],
        [[_esc(group), _esc(sessions), _esc(nodes)] for group, sessions, nodes in velocity.group_rows],
    ) if velocity.group_rows else '<p class="mut">No work items in this window.</p>'
    blockers = model.blockers
    blocker_detail = _table(
        ["Node", "Group", "Days open"],
        [[_esc(row.node_id), _esc(row.group), _esc(row.days_open)] for row in blockers.rows],
    ) if blockers.rows else '<p class="mut">No open blockers.</p>'
    reviews = model.reviews
    review_detail = _table(
        ["Node", "Due", "Days overdue"],
        [[_esc(row.node_id), _esc(row.scheduled_for), _esc(row.days_overdue)] for row in reviews.rows],
    ) if reviews.rows else '<p class="mut">No scheduled reviews.</p>'
    evidence = model.evidence
    evidence_detail = _table(
        ["Node", "Group", "State", "Gap"],
        [[_esc(row.node_id), _esc(row.group), _esc(row.state), "yes" if row.gap else "no"] for row in evidence.rows],
    ) if evidence.rows else '<p class="mut">No nodes with artifact specs.</p>'

    # Static charts: real multi-point series only (P2.2). A theme whose
    # series has a single point (blockers/reviews/evidence summaries)
    # renders the labeled summary without a pseudo-sparkline. The velocity
    # chart is the one surface carrying the granted tier-1 tooltip upgrade
    # (ADR 0008): focusable per-point markers plus the single inline
    # tooltip script, tier-0-complete without it via native titles.
    velocity_weeks = [(week.label, week.session_count) for week in velocity.weeks]
    velocity_interactive = len(velocity_weeks) >= 2
    velocity_svg = sparkline_svg(
        velocity_weeks, with_points=velocity_interactive
    )

    themes = {
        "velocity": (
            "Velocity",
            f"{velocity.sessions_in_window} sessions, {velocity.total_minutes} minutes",
            "Sessions and work items started in the selected window, bucketed by week.",
            velocity_svg,
            velocity_detail,
        ),
        "blockers": (
            "Blockers",
            f"{blockers.open_count} open, {blockers.resolved_in_window} resolved",
            "Open blockers are counted now; resolved blockers are counted when resolved in the window.",
            "",
            blocker_detail,
        ),
        "reviews": (
            "Reviews",
            f"{reviews.completed_in_window} completed, {reviews.overdue_count} overdue",
            "Completion rate is completed reviews divided by completed plus scheduled reviews.",
            "",
            review_detail,
        ),
        "evidence": (
            "Evidence",
            f"{evidence.nodes_with_gaps} nodes with gaps, {evidence.coverage_rate * 100:.0f}% coverage",
            "Coverage is the share of nodes with artifact specs that have no required-spec gap.",
            "",
            evidence_detail,
        ),
    }
    title, summary, derivation, svg, detail = themes[theme]
    theme_links = " ".join(
        '<a href="/analytics?days={d}&amp;group-by={g}&amp;theme={t}">{label}</a>'.format(
            d=days, g=group_by, t=name, label=_esc(label)
        )
        for name, (label, *_rest) in themes.items()
    )
    cards = _analytics_card(title, summary, derivation, svg, detail, model, theme)
    # The granted tooltip upgrade rides the velocity chart only: a real
    # multi-point series on this route. Every other theme and route renders
    # no executable markup (per-route budget, ADR 0008).
    tooltip = tooltip_script() if (theme == "velocity" and velocity_interactive) else ""
    body = (
        head
        + overdue
        + limited
        + advisory
        + controls
        + f'<nav class="nav" aria-label="Themes">{theme_links}</nav>'
        + f'<div class="analytics-grid">{cards}</div>'
        + tooltip
    )
    return "Analytics", body, 200

