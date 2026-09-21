"""
GET ``/`` — the unified single-page home (ADR 0009): hero focus
viewport plus the six-card bento.

"""

from __future__ import annotations

from datetime import (
    timezone,
    datetime,
    timedelta,
)
from pathlib import Path

from ...commands.recommend import derive_next
from ...commands.today import derive_today
from ...context import JoinedView
from ...execution.overdue import (
    utc_today,
    parse_date,
)
from ...execution.records import open_session
from ..interface.handoff import handoff_html
from ...mentor.cards import (
    Sub,
    Label,
)
from ._shared import (
    _degraded_banner,
    _esc,
    _flash_html,
    _normalize_pill_label,
)
from .shell import (
    _chrome,
    _fresh_join,
)
from .forms import (
    _start_confirm_form,
)


def _focus_resources(model) -> list[str]:
    """The focus node's resource lines, off the derivation's typed parts."""
    resources: list[str] = []
    section = ""
    for card in model.cards:
        for part in card.parts:
            if isinstance(part, Label):
                section = part.text.strip().lower()
                continue
            if isinstance(part, Sub) and section.startswith("where to learn"):
                resources.append(part.text)
    return resources


_STATE_REASONS = {
    "available": "Every hard prerequisite is behind you.",
    "active": "You're already working on this.",
    "passed": "The evidence requirements are met.",
    "mastered": "Retention is confirmed.",
    "locked": "A hard prerequisite still comes first.",
}


def _hero_why(next_model, focus_id: str | None) -> str:
    """The hero's top-pick why line — built from structured facts, title-free.

    The focus is named once as the heading; the why line never repeats it.
    """
    if not focus_id or next_model is None:
        return ""
    rec = next(
        (r for r in next_model.recommendations if r.node_id == focus_id), None
    )
    if rec is None:
        return ""
    why = "Top pick for a 30-minute session"
    if rec.leverage:
        why += (
            f", and it opens {rec.leverage} skill"
            f"{'s' if rec.leverage != 1 else ''} beyond it"
        )
    return why + "."


def _continue_cta(view: JoinedView, current, model) -> str:
    """The resumable primary CTA: continue on the node last worked (or focus)."""
    target = model.focus_node_id
    items = [w for w in view.work if w.session_id == current.id]
    for item in reversed(items):
        if item.node_id in view.node_map:
            target = item.node_id
            break
    if not target:
        return ""
    return (
        '<div class="actions"><a class="btn primary" '
        f'href="/nodes/{_esc(target)}">Continue where you left</a></div>\n'
    )


def _hero_block(view: JoinedView, model, next_model) -> str:
    """Home block 1 — the hero focus viewport (amended §A, S3).

    Double-weight by construction: full grid span, 30px display heading,
    28px padding, accent left border. The focus title appears once, as the
    heading; the CTA is pronoun + state-honest (P1.1a/P1.1b as amended) and
    is the page's only primary CTA. While a session is open a second start
    would be refused, so the start form is structurally omitted (P4.1) and
    the continue link carries the CTA.
    """
    focus_id = model.focus_node_id
    if not focus_id or focus_id not in view.node_map:
        return (
            '<div class="hero">\n'
            '<p class="display">What is today about?</p>\n'
            '<p class="mut">Nothing is queued for today. Sync your readiness or '
            'explore what to study from <a href="/next">Next</a>.</p>\n'
            "</div>\n"
        )
    focus = view.node_map[focus_id]
    state = view.store.state_of(focus.id)
    action = model.focus_action
    current = open_session(view.sessions)
    resources = _focus_resources(model)
    pill = (
        f'<span class="pill {_esc(state)}">'
        f"{_esc(_normalize_pill_label(state))}</span>"
    )
    parts = [
        '<div class="hero">\n',
        f'<p class="display">{_esc(focus.title)}</p>\n',
        '<p class="big">',
        pill,
        f" {_esc(_STATE_REASONS.get(state, ''))}</p>\n",
    ]
    why = _hero_why(next_model, focus_id)
    if why:
        parts.append(f'<p class="big">{_esc(why)}</p>\n')
    if resources:
        parts.append(f'<p class="mut">Where to learn: {_esc(resources[0])}</p>\n')
    if current is not None:
        parts.append(_continue_cta(view, current, model))
        started = _esc(str(current.started_at)[:16].replace("T", " "))
        parts.append(f'<p class="mut">Session open since {started}.</p>\n')
        parts.append(
            '<form class="inline" method="post" action="/session/close">'
            '<input type="hidden" name="next" value="/">'
            '<button type="submit" class="btn secondary">Close session</button>'
            "</form>\n"
        )
    elif action is not None and action.intent == "start" and state == "available":
        parts.append(
            _start_confirm_form(view, focus.id, button_label="Start studying")
        )
    elif action is not None:
        label = (
            "Continue where you left"
            if state == "active"
            else "Explore what this unlocks"
        )
        parts.append(
            '<div class="actions"><a class="btn primary" '
            f'href="/nodes/{_esc(focus.id)}">{_esc(label)}</a></div>\n'
        )
    parts.append("</div>\n")
    return "".join(parts)


def _queue_card(view: JoinedView, model, next_model) -> str:
    """Home block 2 — the queue card: ranked preview rows (amended P1.2).

    Rows name *other* nodes — ranked context, never the focus repetition and
    never the raw flat dump; the full ranking lives on ``/next``.
    """
    rows: list[str] = []
    if next_model is not None:
        for rec in next_model.recommendations:
            if rec.node_id == model.focus_node_id or rec.node_id not in view.node_map:
                continue
            node = view.node_map[rec.node_id]
            leverage = (
                f"opens {rec.leverage} skill{'s' if rec.leverage != 1 else ''}"
                if rec.leverage
                else ""
            )
            mut = f'<span class="mut">{_esc(leverage)}</span>' if leverage else ""
            rows.append(
                '<div class="queue-row">'
                f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>{mut}'
                "</div>"
            )
            if len(rows) == 4:
                break
    listing = "".join(f"{row}\n" for row in rows)
    if not listing:
        listing = '<p class="mut">The full ranking lives on Next.</p>\n'
    return (
        '<div class="bento-card queue">\n'
        '<p class="kicker">Queue</p>\n'
        "<h2>What comes after</h2>\n"
        + listing
        + '<p class="mut"><a href="/next">See the full ranking &rarr;</a></p>\n'
        "</div>\n"
    )


def _pressure_card(view: JoinedView, model) -> str:
    """Home block 3 — the pressure card: one calm line, honest blanks at zero.

    The count line never shames and never carries the raw backlog; what the
    pressure is *on* renders as linked node titles (capped), never as
    descriptions or ids.
    """
    overdue = list(model.overdue)
    blockers = list(model.open_blockers)
    if not overdue and not blockers:
        return (
            '<div class="bento-card pressure">\n'
            "<p class=\"kicker\">Pressure</p>\n"
            "<h2>Nothing is due</h2>\n"
            "<p>Nothing is waiting — no reviews due, no open blockers.</p>\n"
            "</div>\n"
        )
    bits: list[str] = []
    if overdue:
        bits.append(
            f"{len(overdue)} review{'s' if len(overdue) != 1 else ''} past due"
        )
    if blockers:
        bits.append(
            f"{len(blockers)} open blocker{'s' if len(blockers) != 1 else ''}"
        )
    linked: list[str] = []
    seen: set[str] = set()
    for record in (*overdue, *blockers):
        node_id = record.node_id
        if node_id in seen or node_id not in view.node_map:
            continue
        seen.add(node_id)
        node = view.node_map[node_id]
        linked.append(f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>')
        if len(linked) == 3:
            break
    links = ""
    if linked:
        links = "<p class=\"mut\">On " + ", ".join(linked) + ".</p>\n"
    handoff = ""
    if overdue:
        handoff = handoff_html("Catching up reviews")
    return (
        '<div class="bento-card pressure">\n'
        "<p class=\"kicker\">Pressure</p>\n"
        "<h2>What's waiting</h2>\n"
        f"<p>Waiting quietly: {_esc(', '.join(bits))}.</p>\n"
        + links
        + handoff
        + "</div>\n"
    )


_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


_MONTH_ABBREVS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _utc_day(timestamp: object):
    """The UTC calendar day of one ISO timestamp, or ``None`` when unusable."""
    if not timestamp:
        return None
    try:
        moment = datetime.fromisoformat(str(timestamp))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date()


def _date_label(day) -> str:
    """A readable short date — ``15 Sep`` — never an ISO dump."""
    return f"{day.day} {_MONTH_ABBREVS[day.month - 1]}"


def _spine_card(view: JoinedView, model) -> str:
    """Home block 4 — the spine card, pronoun-headed (§A).

    One locator repetition of the focus name is permitted here (P1.1a as
    amended — named-twice); the full pathway summaries ride on node detail
    and ``/next``.
    """
    focus_id = model.focus_node_id
    kids: list[str] = []
    if focus_id:
        for edge in view.edges:
            if (
                edge.source == focus_id
                and edge.active
                and edge.edge_type in ("hard_prerequisite", "soft_prerequisite")
                and edge.target in view.node_map
                and edge.target not in kids
            ):
                kids.append(edge.target)
    parts = [
        '<div class="bento-card spine">\n',
        "<p class=\"kicker\">Graph context</p>\n",
        "<h2>What your focus opens</h2>\n",
    ]
    if not kids:
        parts.append(
            "<p class=\"mut\">This skill doesn't unlock anything yet.</p>\n"
        )
    else:
        focus = view.node_map[focus_id]
        parts.append(f'<p class="small mut">From {_esc(focus.title)}:</p>\n')
        for target in kids[:4]:
            node = view.node_map[target]
            parts.append(
                '<div class="spine-row">'
                f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>'
                "</div>\n"
            )
        if len(kids) > 4:
            parts.append(
                f"<p class=\"mut\">And {len(kids) - 4} more — "
                f'<a href="/nodes/{_esc(focus.id)}">see them all</a>.</p>\n'
            )
    parts.append("</div>\n")
    return "".join(parts)


def _week_card(view: JoinedView, model) -> str:
    """Home block 5 — the week card: the strip + honest blanks (§A).

    A day without work is simply blank — never framed as a break or a miss
    (the days-practiced mirror, P1.4/P1.7 at week scale). No owed framing.
    """
    today = utc_today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    week_range = (
        f"{_WEEKDAY_NAMES[monday.weekday()]} {_date_label(monday)} - "
        f"{_WEEKDAY_NAMES[sunday.weekday()]} {_date_label(sunday)}"
    )
    days = [monday + timedelta(days=offset) for offset in range(7)]
    minutes_by_day: dict = {}
    for work in view.work:
        day = _utc_day(work.created_at)
        if day is None:
            continue
        minutes_by_day[day] = minutes_by_day.get(day, 0) + (work.minutes or 0)
    cells: list[str] = []
    for day in days:
        label = f"{_WEEKDAY_NAMES[day.weekday()]} {day.day}"
        minutes = minutes_by_day.get(day, 0)
        value = f"{minutes} min" if minutes else "\u2014"
        marker = ' class="day today"' if day == today else ' class="day"'
        cells.append(f"<div{marker}><b>{label}</b>{value}</div>")
    parts = [
        '<div class="bento-card week">\n',
        "<p class=\"kicker\">The week</p>\n",
        f"<h2>{_esc(week_range)}</h2>\n",
        '<div class="weekstrip">\n',
        "".join(cells),
        "\n</div>\n",
    ]
    total = model.days_practiced
    if total:
        parts.append(
            f"<p class=\"mut\">You've studied on {total} day"
            f"{'s' if total != 1 else ''} so far.</p>\n"
        )
    else:
        parts.append("<p class=\"mut\">Nothing logged yet.</p>\n")
    week_reviews = [
        review
        for review in view.reviews
        if review.status == "scheduled"
        and (due := parse_date(review.scheduled_for)) is not None
        and monday <= due <= monday + timedelta(days=6)
    ]
    if week_reviews:
        parts.append(
            f"<p class=\"mut\">{len(week_reviews)} review"
            f"{'s' if len(week_reviews) != 1 else ''} fall"
            f"{'s' if len(week_reviews) == 1 else ''} due this week.</p>\n"
        )
    parts.append('<p class="mut"><a href="/analytics">See the log &rarr;</a></p>\n')
    parts.append("</div>\n")
    return "".join(parts)


def _history_card(view: JoinedView) -> str:
    """Home block 6 — the session-history card (§A).

    At zero sessions: the empty state plus a format preview — no engine file
    paths (P3.1), no fake links. With sessions: readable lines — the date,
    the time spent, and what you worked on.
    """
    completed = sorted(
        (s for s in view.sessions if s.status == "completed"),
        key=lambda s: str(s.started_at),
        reverse=True,
    )
    if not completed:
        return (
            '<div class="bento-card history">\n'
            "<p class=\"kicker\">Session history</p>\n"
            "<h2>No sessions yet</h2>\n"
            '<p class="mut">When you study, each entry lands here as a readable '
            "line — the date, the time you spent, and what you worked on.</p>\n"
            "</div>\n"
        )
    work_by_session: dict = {}
    for work in view.work:
        work_by_session.setdefault(work.session_id, []).append(work)
    lines: list[str] = []
    for session in completed[:3]:
        started = _utc_day(session.started_at)
        segments = [_esc(_date_label(started) if started else "Earlier")]
        items = work_by_session.get(session.id, [])
        minutes = sum(w.minutes or 0 for w in items)
        if minutes:
            segments.append(f"{minutes} min")
        title_links: list[str] = []
        seen: set[str] = set()
        for work in items:
            if work.node_id in seen or work.node_id not in view.node_map:
                continue
            seen.add(work.node_id)
            node = view.node_map[work.node_id]
            title_links.append(
                f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>'
            )
        if title_links:
            segments.append(", ".join(title_links))
        lines.append('<p class="hist-row">' + " \u00b7 ".join(segments) + "</p>\n")
    more = ""
    if len(completed) > 3:
        extra = len(completed) - 3
        more = (
            f"<p class=\"mut\">And {extra} earlier session"
            f"{'s' if extra != 1 else ''}.</p>\n"
        )
    return (
        '<div class="bento-card history">\n'
        "<p class=\"kicker\">Session history</p>\n"
        "<h2>Recent sessions</h2>\n"
        + "".join(lines)
        + more
        + '<p class="mut"><a href="/analytics">See the full log &rarr;</a></p>\n'
        "</div>\n"
    )


def _browse_card(view: JoinedView, model) -> str:
    """Home block 7 — the browse card: the one blessed grouped-count table.

    The single grouped-count table permitted on the rich home (amended
    P2.1); totals and per-track counts are live reads off the store.
    """
    counts = model.counts
    ready_total = counts.get("available", 0)
    locked_total = counts.get("locked", 0)
    by_track: dict[str, tuple[int, int]] = {}
    for node in view.nodes:
        state = view.store.state_of(node.id)
        if state not in ("available", "locked"):
            continue
        ready, locked = by_track.get(node.track, (0, 0))
        if state == "available":
            ready += 1
        else:
            locked += 1
        by_track[node.track] = (ready, locked)
    rows = "".join(
        "<tr>"
        f"<td>{_esc(track.capitalize())}</td>"
        f"<td>{ready}</td><td>{locked}</td>"
        "</tr>"
        for track, (ready, locked) in sorted(by_track.items())
    )
    return (
        '<div class="bento-card browse">\n'
        "<p class=\"kicker\">Browse what is open</p>\n"
        f"<h2>{ready_total} ready, {locked_total} locked</h2>\n"
        '<table class="browsetable">'
        "<tr><th>Track</th><th>Ready</th><th>Locked</th></tr>"
        + rows
        + "</table>\n"
        '<p class="mut"><a href="/nodes/jump">Open the full list &rarr;</a></p>\n'
        "</div>\n"
    )


def home_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/` — the unified single-page home (amended §A, S3, map #252).

    The hero focus viewport (double-weight, the page's only primary CTA in
    the pronoun form) plus the six-card bento at the dense register — queue,
    pressure, spine, week, session history, browse — every bento card
    links-only, disclosures off the primary path, the raw backlog never
    rendered. Reads go through the lenient ``JoinedView`` fresh per request.

    Returns ``(page_title, body_html, http_status)``.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_today(view, Path(root), minutes=30)
    try:
        next_model = derive_next(view, Path(root), minutes=60, limit=6)
    except Exception:  # advisory preview only — never blocks the page
        next_model = None

    header_html = _chrome(root, current_view="today")

    body = (
        header_html
        + _flash_html(query or {}, "/")
        + _degraded_banner(view)
        + '<div class="home-rich">\n<div class="bento">\n'
        + _hero_block(view, model, next_model)
        + _queue_card(view, model, next_model)
        + _pressure_card(view, model)
        + _spine_card(view, model)
        + _week_card(view, model)
        + _history_card(view)
        + _browse_card(view, model)
        + "</div>\n</div>\n"
    )
    return "Today", body, 200

