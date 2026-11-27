"""
GET ``/analytics`` — one read-only analytics theme per page
(ADR 0009), plus the granted tooltip-script budget (ADR 0008).

Four canonical themes over real derived facts (spec-v3-study-day §11.6):
Study velocity (the entry theme), Blockers by domain, Review completion and
Evidence coverage. Every theme states its derivation, its time window, its
grouping and the records it read; values stay visible under a limited-data
warning when the policy threshold is not met; a failed derivation is a
distinct could-not-compute state that claims no zero. Tables are
authoritative, and the one chart (velocity) carries an accessible name plus
a table of the exact same weekly values.

Analytics never blocks, records or transitions domain state: rendering a
theme reads truth, and the only write on the route is the explicit,
disposable export action.

Card ownership (#317): this module's two ``card`` producers —
``_analytics_card`` (the theme card) and ``_analytics_controls`` (the
window/group-by chrome) — are blessed non-Card producers, named and
justified in ``web/interface/render.SANCTIONED_CARD_PRODUCERS``; they do
not compose :class:`interface.cards.Card`.

"""

from __future__ import annotations

from pathlib import Path

from ...analytics.derive import derive_analytics
from ...analytics.models import AnalyticsParams
from ...analytics.policy import limited_data_sentence
from ...analytics.sparkline import sparkline_svg
from ...execution.overdue import utc_today
from ...policy.advisory import analytics_warnings
from ..analytics_tooltip import tooltip_script
from ._shared import (
    ASSURANCE,
    _esc,
    _table,
)
from .sections import section
from .shell import (
    _page_head,
    _status_page,
)

#: The four canonical analytics themes, in entry order (spec-v3-study-day
#: §11.6). One source for the page's theme set and the Operations home's
#: count card, so the two surfaces can never disagree (R7).
THEMES: tuple[str, ...] = ("velocity", "blockers", "reviews", "evidence")

#: The node states the analytics state filter may name (mirrors the CLI's
#: ``--state`` values; OR semantics). The filter narrows rows; it never
#: redefines a metric.
_ANALYTICS_STATES: tuple[str, ...] = (
    "locked",
    "available",
    "active",
    "passed",
    "mastered",
)

#: The records every theme derivation reads. If any of them degraded to an
#: empty collection, every number on the page would turn into a fabricated
#: zero (SC-00a): the page is a could-not-compute state instead.
_ANALYTICS_SOURCES = frozenset(
    {"sessions", "work", "blockers", "reviews", "specs", "records", "policies"}
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
    states = tuple(dict.fromkeys(query.get("state") or ()))
    invalid_states = sorted(set(states) - set(_ANALYTICS_STATES))
    if invalid_states:
        body, status = _status_page(
            400,
            "Analytics state filter must name locked, available, active, "
            "passed or mastered.",
            root,
        )
        return None, ("Bad request", body, status)
    min_sessions = policy.min_sessions_for_full_data
    # T6: the window/group/filter bundle is one value for every theme.
    params = AnalyticsParams(
        window_days=days,
        group_by=group_by,
        state_filter=states,
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


def _analytics_failure_section(unavailable: list[str]) -> str:
    """Could-not-compute: claim nothing, never turn a failure into a zero.

    The wording names the records that did not load and gives the recovery
    path this same page offers. It never reads as a learner problem: an
    unreadable store is an operational failure of the repository.
    """
    names = ", ".join(unavailable)
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Analytics could not be worked out</h2>\n'
        "</div>\n"
        '<div class="state state-failure">\n'
        '<p class="state-title">No numbers are being claimed</p>\n'
        '<p class="state-body">Some of the records behind these themes did not '
        "load, so the page shows no counts, no rates and no chart — not even "
        "that any of them are zero. Nothing about your progress changed.</p>\n"
        f'<p class="state-body">Records unavailable: <code>{_esc(names)}</code></p>\n'
        '<p>Once the records are readable, <a href="/analytics">load the themes '
        "again</a>. Repository diagnostics on <a href=\"/health\">Health</a> "
        "name the source and its error.</p>\n"
        "</div>\n"
        "</section>\n"
    )


def _computation_failure_section(detail: str) -> str:
    """A failed derivation is distinct from a limited one and writes no zero."""
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Analytics could not be worked out</h2>\n'
        "</div>\n"
        '<div class="state state-failure">\n'
        '<p class="state-title">No numbers are being claimed</p>\n'
        '<p class="state-body">The derivation failed, so this page shows no '
        "counts, no rates and no chart. Nothing was written and nothing about "
        "your progress changed.</p>\n"
        f'<p class="state-body">The reason: <code>{_esc(detail)}</code></p>\n'
        '<p><a href="/analytics">Try the themes again</a>.</p>\n'
        "</div>\n"
        "</section>\n"
    )


def _has_any_data(model) -> bool:
    """True when at least one theme has a real population to describe.

    An all-empty fixture must not turn policy advisory warnings into
    statements about the learner (SC-00a): there is no value to warn about.
    """
    return bool(
        model.velocity.sessions_in_window
        or model.velocity.group_rows
        or model.blockers.rows
        or model.blockers.resolved_in_window
        or model.reviews.rows
        or model.reviews.completed_in_window
        or model.evidence.nodes_with_specs
    )


def _data_note(model) -> str:
    """The text that distinguishes available data from limited data.

    Below the policy threshold the valid values stay visible (SC-00a): the
    warning states the threshold and never replaces, rounds or hides the
    numbers. Above it the same position says the threshold was met.
    """
    sessions = model.sessions_in_window
    threshold = model.min_sessions_for_full_data
    window = model.window_days
    if model.is_limited:
        return (
            f"{limited_data_sentence(threshold, window)} "
            "The recorded values are shown below."
        )
    return (
        f"Available data — {sessions} sessions in the last {window} days, "
        f"meeting the {threshold}-session threshold."
    )


def _empty_state(title: str, body: str, *, link: str, link_label: str) -> str:
    """One honest empty state: explain why, preserve a way forward."""
    return (
        '<div class="state state-empty">\n'
        f'<p class="state-title">{_esc(title)}</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        f'<p><a href="{_esc(link)}">{_esc(link_label)}</a></p>\n'
        "</div>\n"
    )


def _analytics_export_form(
    days: int, group_by: str, theme: str, state_filter: tuple[str, ...] = ()
) -> str:
    states = "".join(
        f'<input type="hidden" name="state" value="{_esc(state)}">'
        for state in state_filter
    )
    return (
        '<form method="post" action="/analytics/export" class="actions">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        f'<input type="hidden" name="days" value="{days}">'
        f'<input type="hidden" name="group_by" value="{_esc(group_by)}">'
        f"{states}"
        '<button class="btn secondary" type="submit" name="format" value="md">Export MD</button>'
        '<button class="btn secondary" type="submit" name="format" value="html">Export HTML</button>'
        '<button class="btn secondary" type="submit" name="format" value="json">Export JSON</button>'
        "</form>"
    )


def _analytics_controls(
    days: int, group_by: str, theme: str, state_filter: tuple[str, ...] = ()
) -> str:
    """The controls panel — the window/state/grouping chrome, blessed (#317).

    Page chrome, not a card of engine facts: one GET form plus plain
    theme-toggle links, named and justified in
    ``interface.render.SANCTIONED_CARD_PRODUCERS``. The window and the
    node-state filter are selects, the grouping two plain links, all
    keeping the visible theme and the active filter (IA-5), so a control
    never has to be recounted by hand and the page stays tier-0.
    """
    options = "".join(
        f'<option value="{n}" {"selected" if n == days else ""}>{label}</option>'
        for n, label in ((7, "Last 7 days"), (30, "Last 30 days"), (90, "Last 90 days"))
    )
    state_options = "".join(
        f'<option value="{state}"{" selected" if state in state_filter else ""}>'
        f"{state}</option>"
        for state in _ANALYTICS_STATES
    )
    state_query = "".join(
        f"&amp;state={_esc(state)}" for state in state_filter
    )
    return (
        '<div class="card analytics-controls"><form method="get" action="/analytics">'
        '<div class="form-row">'
        '<label for="analytics-days">Date range</label>'
        f'<select name="days" id="analytics-days">{options}'
        f'<option value="{days}" {"selected" if days not in (7, 30, 90) else ""}>Policy default ({days}d)</option>'
        f'</select><input type="hidden" name="group-by" value="{_esc(group_by)}">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        '<p class="small mut">Which window the charts cover.</p>'
        '</div><div class="form-row">'
        '<label for="analytics-state">Node state</label>'
        f'<select name="state" id="analytics-state" multiple size="5">{state_options}'
        "</select><p class=\"small mut\">Narrow rows to these states (OR). "
        "Leave all unselected for every state.</p>"
        '<button class="btn secondary" type="submit">Apply</button></div></form>'
        '<div class="form-row"><label>Group by</label>'
        '<p class="small mut">How sessions are bucketed in the charts.</p>'
        f'<a class="btn {"secondary" if group_by == "track" else ""}" href="/analytics?days={days}&amp;group-by=prefix&amp;theme={_esc(theme)}{state_query}">Prefix</a> '
        f'<a class="btn {"secondary" if group_by == "prefix" else ""}" href="/analytics?days={days}&amp;group-by=track&amp;theme={_esc(theme)}{state_query}">Track</a></div>'
        "</div>"
    )


def _analytics_card(
    title: str,
    summary: str,
    derivation: str,
    svg: str,
    detail: str,
    view,
    theme: str,
    *,
    data_note: str,
    state_html: str,
    state_filter: tuple[str, ...] = (),
) -> str:
    """One theme's page (T4 §H): a plain card; tables collapsed (P2.2).

    A chart panel, blessed in ``interface.render.SANCTIONED_CARD_PRODUCERS``
    (#317) rather than migrated: the chart SVG and the export form have no
    Richer-Card slot, and the panel's fact shape — one theme's numbers — is
    not a skill card's.

    ``data_note`` is the available/limited sentence, and ``state_html`` is
    a purpose-built empty or limited state. Both are required: every theme
    says whether its data is available or limited, and an empty theme says
    why it is empty.
    """
    note = (
        f'<p class="small mut data-note">{_esc(data_note)}</p>'
        if data_note
        else ""
    )
    detail_html = (
        f"<details><summary>Details</summary>{detail}</details>" if detail else ""
    )
    return (
        f'<div class="card analytics-card"><p class="lead">{_esc(title)}</p>'
        f'<p class="big">{_esc(summary)}</p><p class="mut">{_esc(derivation)}</p>'
        f"{note}{state_html}{svg}{detail_html}"
        f"{_analytics_export_form(view.window_days, view.group_by, theme, state_filter)}"
        "</div>"
    )


def _weekly_table(velocity) -> str:
    """The velocity chart's exact values, as the authoritative table (AX-9)."""
    return _table(
        ["Week", "Sessions with work", "Work items", "Minutes"],
        [
            [
                _esc(week.label),
                _esc(week.session_count),
                _esc(week.work_item_count),
                _esc(week.minutes),
            ]
            for week in velocity.weeks
        ],
    )


def _velocity_chart(velocity) -> tuple[str, bool]:
    """The velocity chart, only for a real multi-point trend.

    The chart supplements the visible weekly table and encodes exactly its
    session counts. A series with fewer than two weeks of activity is not a
    trend, so no chart is drawn (P2.2: no fake trend).
    """
    active_weeks = sum(1 for week in velocity.weeks if week.session_count > 0)
    if active_weeks < 2:
        return "", False
    first = velocity.weeks[0].label
    last = velocity.weeks[-1].label
    total = sum(week.session_count for week in velocity.weeks)
    label = (
        f"Weekly sessions with work from {first} to {last}: {total} in the "
        "selected window. The table below carries the same values."
    )
    return (
        sparkline_svg(
            [(week.label, week.session_count) for week in velocity.weeks],
            with_points=True,
            label=label,
        )
        + _weekly_table(velocity),
        True,
    )


def _theme_page(
    view, model, theme: str
) -> tuple[str, str, str, str, str, str, bool]:
    """One theme's title, summary, derivation, chart/table and detail."""
    velocity = model.velocity
    blockers = model.blockers
    reviews = model.reviews
    evidence = model.evidence
    group_by = model.group_by

    if theme == "velocity":
        empty = not velocity.group_rows
        if empty:
            summary = (
                f"{velocity.sessions_in_window} sessions started, but no work "
                "items were recorded"
                if velocity.sessions_in_window
                else "No study sessions in this window."
            )
        else:
            summary = (
                f"{velocity.sessions_in_window} sessions, "
                f"{velocity.total_minutes} minutes"
            )
        derivation = (
            "Sessions and SessionWork records inside the selected window, "
            f"bucketed by ISO week and grouped by {group_by}. Source records: "
            "Session, SessionWork."
        )
        if not empty:
            state = ""
        elif velocity.sessions_in_window:
            state = _empty_state(
                "No work items in this window",
                "Sessions were started, but no SessionWork was recorded. Widen "
                "the window, or log work in the study cockpit.",
                link="/session",
                link_label="Go to the study cockpit",
            )
        else:
            state = _empty_state(
                "No study activity in this window",
                "No sessions or work items were recorded in the selected window. "
                "Widen the window, or start a study session.",
                link="/session",
                link_label="Go to the study cockpit",
            )
        chart, interactive = ("", False) if empty else _velocity_chart(velocity)
        if not empty and not chart:
            chart = _weekly_table(velocity)
        detail = (
            _table(
                ["Group", "Sessions", "Nodes"],
                [
                    [_esc(group), _esc(sessions), _esc(nodes)]
                    for group, sessions, nodes in velocity.group_rows
                ],
            )
            if velocity.group_rows
            else ""
        )
        return "Velocity", summary, derivation, chart, detail, state, interactive

    if theme == "blockers":
        empty = blockers.open_count == 0 and blockers.resolved_in_window == 0
        summary = (
            "No blockers in this window."
            if empty
            else f"{blockers.open_count} open now, {blockers.resolved_in_window} resolved"
        )
        derivation = (
            "Open Blocker records now, plus Blocker records resolved inside "
            f"the selected window, grouped by {group_by}. Source records: Blocker."
        )
        state = (
            _empty_state(
                "No blockers recorded in this window",
                "No blocker is open now and none was resolved in the selected "
                "window. Blocked work in a session is not a Blocker.",
                link="/session",
                link_label="Return to the study cockpit",
            )
            if empty
            else ""
        )
        detail = (
            _table(
                ["Skill", "Group", "Days open"],
                [
                    [
                        _esc(view.titles.get(row.node_id, row.node_id)),
                        _esc(row.group),
                        _esc(row.days_open),
                    ]
                    for row in blockers.rows
                ],
            )
            if blockers.rows
            else ""
        )
        return "Blockers", summary, derivation, "", detail, state, False

    if theme == "reviews":
        total = reviews.completed_in_window + reviews.scheduled_count
        empty = total == 0
        summary = (
            "No reviews in this window."
            if empty
            else (
                f"{reviews.completed_in_window} completed, "
                f"{reviews.scheduled_count} scheduled, {reviews.overdue_count} overdue"
            )
        )
        derivation = (
            f"{model.window_days}-day window; grouping is not applied (the "
            "Review queue is one list). No Review records fall in the window, "
            "so no completion rate is computed. Source records: Review."
            if empty
            else (
                f"{model.window_days}-day window; grouping is not applied (the "
                "Review queue is one list). Completed reviews in the window ÷ "
                "(completed in the window + scheduled-plus-overdue now): "
                f"{reviews.completed_in_window} ÷ {total} = "
                f"{reviews.completion_rate * 100:.0f}%. Source records: Review."
            )
        )
        state = (
            _empty_state(
                "No reviews in this window",
                "No review was scheduled or completed in the selected window. "
                "A retention suggestion is not a scheduled review.",
                link="/reviews",
                link_label="Open the review queue",
            )
            if empty
            else ""
        )
        detail = (
            _table(
                ["Skill", "Due", "Days overdue"],
                [
                    [
                        _esc(view.titles.get(row.node_id, row.node_id)),
                        _esc(row.scheduled_for),
                        _esc(row.days_overdue),
                    ]
                    for row in reviews.rows
                ],
            )
            if reviews.rows
            else ""
        )
        return "Reviews", summary, derivation, "", detail, state, False

    # Evidence coverage.
    specs = evidence.nodes_with_specs
    gaps = evidence.nodes_with_gaps
    empty = specs == 0
    summary = (
        "No skills have evidence requirements yet."
        if empty
        else f"{gaps} of {specs} skills with a required-evidence gap"
    )
    derivation = (
        f"{model.window_days}-day window (coverage is current, not date-"
        f"bucketed); grouped by {group_by}. No skill has an ArtifactSpec, so "
        "no coverage rate is computed. Source records: ArtifactSpec, "
        "EvidenceRecord."
        if empty
        else (
            f"{model.window_days}-day window (coverage is current, not date-"
            f"bucketed); grouped by {group_by}. Coverage = (skills with "
            "artifact specs − skills with a required-spec gap) ÷ skills with "
            f"artifact specs: ({specs} − {gaps}) ÷ {specs} = "
            f"{evidence.coverage_rate * 100:.0f}%. Source records: "
            "ArtifactSpec, live EvidenceRecord."
        )
    )
    state = (
        _empty_state(
            "No evidence requirements in this window",
            "No skill has an artifact specification, so there is no coverage "
            f"to report. {ASSURANCE}",
            link="/evidence",
            link_label="Open the evidence index",
        )
        if empty
        else ""
    )
    detail = (
        _table(
            ["Skill", "Group", "State", "Gap"],
            [
                [
                    _esc(view.titles.get(row.node_id, row.node_id)),
                    _esc(row.group),
                    _esc(row.state),
                    "yes" if row.gap else "no",
                ]
                for row in evidence.rows
            ],
        )
        if evidence.rows
        else ""
    )
    return "Evidence", summary, derivation, "", detail, state, False


def analytics_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/analytics` - one read-only analytics theme per page (v2.4 S5).

    The ``theme`` query parameter selects the visible theme (default
    ``velocity``); the others are one plain-link away - a page shows one
    theme's chart, not four stacked charts. Charts are static inline SVG
    through the ``analytics/sparkline.py`` seam, real multi-point series
    only (P2.2 bans pseudo-sparklines: a single-point series renders no
    sparkline, just the labeled summary and its table).

    Every theme states its derivation, window, grouping and source records;
    a required source that failed to load is a could-not-compute state that
    claims no zero; and the only write on the route is the explicit export
    action.
    """
    query = query or {}
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/analytics",
        current_view="analytics",
        default_mode="operations",
        path="/analytics",
    )
    if failure is not None:
        return failure

    unavailable = sorted(_ANALYTICS_SOURCES & set(view.degraded))
    if unavailable:
        return "Analytics", head + _analytics_failure_section(unavailable), 200

    try:
        model, failure = _analytics_view(view, query, Path(root))
    except Exception as exc:  # noqa: BLE001 — a failed derivation claims no zero
        return "Analytics", head + _computation_failure_section(str(exc)), 200
    if model is None:
        return failure

    theme = (query.get("theme") or ["velocity"])[0]
    if theme not in THEMES:
        theme = "velocity"

    warnings = analytics_warnings(Path(root), model) if _has_any_data(model) else []
    overdue = (
        f'<p class="banner warning">Overdue reviews: {model.reviews.overdue_count} '
        "scheduled review(s) need attention.</p>"
        if model.reviews.overdue_count
        else ""
    )
    days = model.window_days
    group_by = model.group_by
    state_filter = tuple(model.state_filter)
    controls = _analytics_controls(days, group_by, theme, state_filter)
    advisory = "".join(
        f'<p class="banner advisory">{_esc(warning)}</p>' for warning in warnings
    )
    title, summary, derivation, chart, detail, state, interactive = _theme_page(
        view, model, theme
    )
    labels = {
        "velocity": "Velocity",
        "blockers": "Blockers",
        "reviews": "Reviews",
        "evidence": "Evidence",
    }
    state_query = "".join(
        f"&amp;state={_esc(state)}" for state in state_filter
    )
    theme_links = " ".join(
        '<a href="/analytics?days={d}&amp;group-by={g}&amp;theme={t}{states}"{current}>{label}</a>'.format(
            d=days,
            g=group_by,
            t=name,
            states=state_query,
            current=' aria-current="page"' if name == theme else "",
            label=_esc(label),
        )
        for name, label in labels.items()
    )
    # An empty population has no value to retain, so it never carries the
    # limited-data warning (SC-00a: empty and limited are different states).
    data_note = "" if state else _data_note(model)
    card = _analytics_card(
        title,
        summary,
        derivation,
        chart,
        detail,
        model,
        theme,
        data_note=data_note,
        state_html=state,
        state_filter=state_filter,
    )
    # The granted tooltip upgrade rides the velocity chart only: a real
    # multi-point series on this route. Every other theme and route renders
    # no executable markup (per-route budget, ADR 0008).
    tooltip = tooltip_script() if (theme == "velocity" and interactive) else ""
    body = (
        head
        + overdue
        + advisory
        + section(
            title,
            f"{days}-day window, grouped by {group_by}"
            + (
                f", states: {', '.join(state_filter)}"
                if state_filter
                else ""
            )
            + ".",
            controls
            + f'<nav class="nav" aria-label="Themes">{theme_links}</nav>'
            + f'<div class="analytics-grid">{card}</div>',
            anchor="theme",
        )
        + tooltip
    )
    return "Analytics", body, 200
