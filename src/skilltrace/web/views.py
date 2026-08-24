"""Daily read-only pages — the mechanical HTML transform of Mentor output (T3).

The four GET routes (`/`, `/next`, `/nodes/{id}`, `/health`) translate the CLI
derivations into browser cards. The translation is deliberately mechanical
(ADR 0006 / G3#67): every page calls the same line-producers the CLI prints
(``derive_today`` / ``derive_next`` / ``derive_node_detail`` / ``health_report``)
and transforms those canonical lines — escape per line, ``[tag]`` prefixes to
banner classes, ``[pill]`` lines to pill classes, indentation to structure,
uppercase kickers to kickers, ``---`` separators to card breaks. No Mentor
prose is re-declared here, so CLI and serve cannot disagree; if the transform
outgrows line-shape text, the sanctioned escalation is refactoring
``render.py`` into structured data, never a parallel hand-written vocabulary.

Information architecture: P1 variant **A — Mentor-first linear** (decision on
issue #72). One column of reading-order cards; pressure excerpts and the
health strip follow the focus card instead of competing with it; drill-downs
are native ``<details>`` elements, so no JavaScript anywhere. Reads go through
the lenient ``JoinedView`` fresh per request; writes are not wired here.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path

from ..commands.health import health_report
from ..commands.node_detail import _unlocked_by, _unsatisfied_prereqs, derive_node_detail
from ..commands.recommend import derive_next
from ..commands.today import derive_today
from ..context import JoinedView, load_context_lenient
from ..evidence.eligibility import live_accepted_count
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError
from ..graph.state import ProgressStoreError
from ..resources.status import VerificationStatus, derive_status, stale_after_days


def _esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


_STYLE = """
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 46rem;
         padding: 0 1rem; line-height: 1.5; }
  h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 1.6rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #8884; }
  .mut { color: #888; font-size: 0.85rem; }
  ul { padding-left: 1.2rem; }
  .nav { font-size: 0.9rem; margin-bottom: 0.6rem; }
  .nav a { margin-right: 0.9rem; }
  .card { border: 1px solid #8884; border-radius: 12px; padding: 14px 16px; margin: 12px 0; }
  .kicker { font-size: 0.72rem; letter-spacing: 0.08em; font-weight: 700;
            opacity: 0.65; margin: 0.6rem 0 0.25rem; }
  .label { font-weight: 600; margin: 0.5rem 0 0.15rem; }
  .lead { font-weight: 600; font-size: 1.05rem; margin: 0.2rem 0; }
  .sub { margin: 0.15rem 0 0.15rem 0.9rem; }
  .pill { display: inline-block; border: 1px solid #8884; border-radius: 999px;
          padding: 0.05rem 0.55rem; font-size: 0.75rem; margin: 0.1rem 0.3rem 0.1rem 0; }
  .pill.locked, .pill.broken { border-color: #f87171aa; background: #ef44441a; }
  .pill.available, .pill.ready-to-start, .pill.verified { border-color: #4ade8088; background: #22c55e1a; }
  .pill.active, .pill.in-progress, .pill.advisory { border-color: #38bdf888; background: #0ea5e91a; }
  .pill.passed { border-color: #a78bfa88; background: #8b5cf61a; }
  .pill.mastered { border-color: #facc1588; background: #eab3081a; }
  .pill.stale { border-color: #fbbf2488; background: #f59e0b1a; }
  .banner { padding: 0.45rem 0.7rem; border-radius: 8px; margin: 0.4rem 0; }
  .banner.warning, .banner.stale-note { background: #f59e0b26; }
  .banner.error, .banner.fail { background: #ef444433; }
  .banner.advisory { background: #0ea5e926; }
  .banner.ok { background: #22c55e26; }
  details { margin: 0.5rem 0; }
  summary { cursor: pointer; font-weight: 600; }
  .filters label { margin-right: 0.9rem; }
"""


def page(title: str, body: str) -> str:
    """Wrap a body in the single shared layout (one inline style block)."""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{_esc(title)} — SkillTrace</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n<body>\n"
        f"<h1>{_esc(title)}</h1>\n{body}\n</body>\n</html>\n"
    )


_NAV = (
    '<div class="nav">'
    '<a href="/">Today</a>'
    '<a href="/next">Next</a>'
    '<a href="/health">Health</a>'
    "</div>\n"
)


def _error_body(message: str) -> str:
    return (
        f'{_NAV}<p class="banner error">{_esc(message)}</p>'
        '<p><a href="/">Back to Today</a></p>'
    )


def _status_page(status: int, message: str) -> tuple[str, int]:
    if status == 404:
        return _error_body(message), 404
    return _error_body(message), status


def _fresh_join(root) -> tuple[JoinedView | None, tuple[str, int] | None]:
    """One fresh lenient join per request.

    Returns ``(view, None)`` on success or ``(None, (body, status))`` when the
    strict graph/state half of the lenient seam re-raised.
    """
    try:
        return load_context_lenient(root), None
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        body = _error_body(
            f"The Skill graph or progress store failed to load: {exc}"
        )
        return None, (body, 500)


# --- Mechanical line -> HTML transform ----------------------------------------

_BANNER_PREFIXES = ("[warning] ", "[error] ", "[advisory] ")
_PILL_RE = re.compile(r"\[(.+)\]")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _is_kicker(text: str) -> bool:
    stripped = text.strip()
    return (
        bool(stripped)
        and stripped == stripped.upper()
        and any(ch.isalpha() for ch in stripped)
        and len(stripped) <= 80
    )


def lines_to_blocks(lines: list[str]) -> list[list[str]]:
    """Split canonical lines at ``---`` separators and standalone banners.

    Banners begin their own block so advisory callouts render as their own
    cards instead of gluing onto a neighbouring candidate card.
    """
    blocks: list[list[str]] = [[]]
    for raw in lines:
        stripped = raw.strip()
        if stripped == "---":
            blocks.append([])
            continue
        if any(stripped.startswith(prefix) for prefix in _BANNER_PREFIXES):
            blocks.append([raw])
            continue
        blocks[-1].append(raw)
    return [block for block in blocks if any(line.strip() for line in block)]


def _transform_block(block: list[str]) -> str:
    # Pre-strip blanks once so the label lookahead sees the real next line.
    substantive = [line for line in block if line.strip()]
    out: list[str] = []
    for index, raw in enumerate(substantive):
        stripped = raw.strip()

        banner = next(
            (p for p in _BANNER_PREFIXES if stripped.startswith(p)), None
        )
        if banner:
            kind = banner.strip("[] ")
            out.append(
                f'<p class="banner {_esc(kind)}">{_esc(stripped[len(banner):])}</p>'
            )
            continue

        if raw.startswith("  "):
            match = _PILL_RE.fullmatch(stripped)
            if match:
                label = match.group(1)
                out.append(
                    f'<span class="pill {_esc(_slug(label))}">{_esc(label)}</span>'
                )
            else:
                out.append(f'<div class="sub">{_esc(stripped)}</div>')
            continue

        if _is_kicker(stripped):
            out.append(f'<div class="kicker">{_esc(stripped)}</div>')
            continue

        css = ""
        if index:
            previous_is_sub = substantive[index - 1].startswith("  ")
            if not previous_is_sub and _is_kicker(substantive[index - 1].strip()):
                css = ' class="lead"'  # first prose under a kicker leads the card
        if (
            not css
            and index + 1 < len(substantive)
            and substantive[index + 1].startswith("  ")
            and len(stripped) <= 60
        ):
            css = ' class="label"'  # short callout heading above indented lines
        out.append(f"<p{css}>{_esc(stripped)}</p>")
    return "\n".join(out)


def cards_html(lines: list[str]) -> str:
    """The canonical lines as one card per block."""
    return "".join(
        f'<div class="card">\n{_transform_block(block)}\n</div>\n'
        for block in lines_to_blocks(lines)
    )


# --- Shared cards ---------------------------------------------------------------


def _pressure_card(model, view: JoinedView) -> str:
    """Pressure excerpts: overdue reviews, open blockers, availability counts.

    Advisory by construction — excerpts warn and link, they never gate.
    """
    counts = model.counts
    pills = [
        f'<span class="pill">{len(model.overdue)} overdue review'
        f'{"s" if len(model.overdue) != 1 else ""}</span>',
        f'<span class="pill">{len(model.open_blockers)} open blocker'
        f'{"s" if len(model.open_blockers) != 1 else ""}</span>',
        f'<span class="pill">{counts.get("available", 0)} available'
        f' &middot; {counts.get("locked", 0)} locked</span>',
    ]

    def _node_link(node_id: str) -> str:
        title = view.titles.get(node_id, node_id)
        return f'<a href="/nodes/{_esc(node_id)}">{_esc(title)}</a>'

    lists = ""
    if model.overdue:
        items = "".join(
            f"<li>{_node_link(r.node_id)} — due {_esc(str(r.scheduled_for)[:10])}</li>"
            for r in model.overdue
        )
        lists += f'<div class="kicker">OVERDUE REVIEWS</div><ul>{items}</ul>'
    if model.open_blockers:
        items = "".join(
            f"<li>{_node_link(b.node_id)} — {_esc(b.description)}</li>"
            for b in model.open_blockers
        )
        lists += f'<div class="kicker">OPEN BLOCKERS</div><ul>{items}</ul>'

    return (
        '<div class="card">\n'
        '<div class="kicker">STUDY DAY PRESSURE — ADVISORY, NEVER BLOCKS</div>\n'
        f'<p>{"".join(pills)}</p>\n'
        f"{lists}\n</div>\n"
    )


def _health_strip_card(root) -> str:
    report = health_report(Path(root))
    pills = "".join(
        f'<span class="pill {"verified" if layer.ok else "broken"}">'
        f"{_esc(layer.target)}: {'OK' if layer.ok else 'FAILED'}</span>"
        for layer in report.layers
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"
    return (
        '<div class="card">\n'
        '<div class="kicker">HEALTH STRIP</div>\n'
        f"<p>{pills}"
        f'<a href="/health">Full roll-up &rarr;</a></p>\n'
        f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        "</div>\n"
    )


# --- Route bodies ---------------------------------------------------------------


def home_body(root) -> tuple[str, str, int]:
    """GET `/` — the today dashboard (P1 variant A: Mentor-first linear).

    Returns ``(page_title, body_html, http_status)``.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_today(view, Path(root), minutes=30)

    focus_bar = ""
    if model.focus_node_id and model.focus_node_id in view.node_map:
        focus = view.node_map[model.focus_node_id]
        focus_bar = (
            f'<p class="mut">Focus: '
            f'<a href="/nodes/{_esc(focus.id)}">{_esc(focus.title)}</a></p>'
        )

    body = (
        _NAV
        + focus_bar
        + cards_html(model.lines)
        + _pressure_card(model, view)
        + _health_strip_card(root)
    )
    return "Today", body, 200


def _parse_int(query: dict, key: str, default: int) -> int | None:
    values = query.get(key)
    if not values:
        return default
    try:
        return int(values[0])
    except ValueError:
        return None


def next_body(root, query: dict) -> tuple[str, str, int]:
    """GET `/next?minutes=&limit=&locked=` — mirrors the CLI flags."""
    minutes = _parse_int(query, "minutes", 60)
    limit = _parse_int(query, "limit", 5)
    if minutes is None or limit is None:
        body, status = _status_page(400, "minutes and limit must be integers.")
        return "Next", body, status
    locked_values = query.get("locked", [""])
    show_locked = locked_values[0].lower() in {"1", "true", "on", "yes"} if locked_values else False

    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_next(
        view, Path(root), minutes=minutes, limit=limit, show_locked=show_locked
    )

    checked = " checked" if show_locked else ""
    toggle_params = f"minutes={minutes}&amp;limit={limit}" + ("" if show_locked else "&amp;locked=1")
    toggle_label = "Hide locked" if show_locked else "Show locked"
    filters = (
        '<div class="card">\n'
        '<form class="filters" method="get" action="/next">'
        f'<label>minutes <input type="number" name="minutes" value="{minutes}" min="1" size="4"></label>'
        f'<label>limit <input type="number" name="limit" value="{limit}" min="1" size="3"></label>'
        f'<label><input type="checkbox" name="locked" value="1"{checked}> show locked</label>'
        '<button type="submit">Apply</button>'
        "</form>\n"
        f'<p class="mut"><a href="/next?{toggle_params}">{toggle_label}</a> '
        '(mirrors <code>next --minutes --limit --show-locked</code>)</p>\n'
        "</div>\n"
    )

    return "Next", _NAV + filters + _candidate_cards(model), 200


def _why_details(rec) -> str:
    facts = "".join(
        f"<li>{_esc(label)}: {_esc(value)}</li>"
        for label, value in (
            ("score", rec.score),
            ("track weight", f"{rec.track} = {rec.track_weight:g}"),
            ("downstream leverage", f"{rec.leverage} unlock(s)"),
            ("fits session", "yes" if rec.fits_session else "no"),
            ("already active", "yes" if rec.is_active else "no"),
            ("remediation boost", "active" if rec.remediation_boosted else "none"),
            ("open blocker penalty", "applied" if rec.open_blocked else "none"),
        )
    )
    return (
        "<details>\n<summary>Why this?</summary>\n"
        f'<div class="sub">{_esc(rec.reason)}</div>\n'
        f"<ul>{facts}</ul>\n"
        '<p class="mut">Advisory reasoning — policies reorder recommendations; '
        "they never block a human-initiated action.</p>\n</details>\n"
    )


def _candidate_cards(model) -> str:
    """Candidate cards with a per-card collapsible "Why this?" attached.

    Candidate blocks are recognized by their canonical OPTION kickers; the k-th
    such block receives model.recommendations[k]'s reasoning. Other blocks
    (warnings, remediation advisories, the locked appendix) pass through.
    """
    rec_iter = iter(model.recommendations)
    html_out = []
    for block in lines_to_blocks(model.lines):
        first = next((line for line in block if line.strip()), "")
        inner = _transform_block(block)
        if first.strip().startswith("OPTION "):
            rec = next(rec_iter, None)
            if rec is not None:
                inner += _why_details(rec)
        html_out.append(f'<div class="card">\n{inner}\n</div>\n')
    return "".join(html_out)


def node_body(root, node_id: str) -> tuple[str, str, int]:
    """GET `/nodes/{id}` — primary Mentor card plus drill-down drawers."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    lines = derive_node_detail(view, node_id)
    if lines is None:
        body, status = _status_page(404, f"Unknown node {node_id}.")
        return "Not found", body, status

    drill = _drill_down_card(node_id, view, Path(root))
    title = view.node_map[node_id].title
    body = (
        _NAV
        + f'<p class="mut"><a href="/">Today</a> &middot; <a href="/next">Next</a></p>'
        + cards_html(lines)
        + drill
    )
    return title, body, 200


_STATUS_PILL_CLASSES = {
    VerificationStatus.BROKEN.value: "broken",
    VerificationStatus.STALE.value: "stale",
    VerificationStatus.VERIFIED.value: "verified",
}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def _drill_down_card(node_id: str, view: JoinedView, root: Path) -> str:
    """Read-only factual drill-downs. No Mentor vocabulary here — tables only."""
    store = view.store
    specs = view.specs_by_node.get(node_id, [])
    records_for_specs = [
        r for r in view.records if r.artifact_spec_id in {s.id for s in specs}
    ]
    superseded_ids = {r.supersedes for r in view.records if r.supersedes}

    evidence_rows = [
        [
            _esc(s.title),
            _esc(s.artifact_kind),
            "required" if s.required else "optional",
            _esc(s.minimum_count),
            _esc(live_accepted_count(view.records, s.id)),
        ]
        for s in specs
    ]
    record_rows = [
        [
            _esc(r.id),
            "accepted" if r.accepted else "rejected",
            "superseded" if r.id in superseded_ids else "live",
            _esc(r.location),
        ]
        for r in records_for_specs
    ]
    attempt_rows = [
        [_esc(a.id), _esc(a.outcome), _esc(str(a.created_at)[:10])]
        for a in view.attempts
        if a.node_id == node_id
    ]
    gate_line = "No validation gate."
    if node_id in view.has_gate:
        gate = next(g for g in view.gates if g.node_id == node_id)
        authority = gate.command if gate.command else f"{gate.authority} (learner-stated verdict)"
        gate_line = f"Gate: {_esc(gate.id)} — {_esc(authority)}."

    today = datetime.now(timezone.utc).date()
    window = stale_after_days(root)
    resource_rows = []
    for r in view.resources_by_node.get(node_id, []):
        status = derive_status(r, today=today, stale_after_days=window).value
        where = _esc(r.url or r.local_path or "")
        pill_class = _STATUS_PILL_CLASSES.get(status, "")
        resource_rows.append(
            [
                _esc(r.id),
                f'<a href="{where}">{where}</a>' if r.url else where,
                f'<span class="pill {pill_class}">{_esc(status)}</span>',
            ]
        )

    review_rows = [
        [
            _esc(rv.id),
            _esc(rv.status),
            _esc(str(rv.scheduled_for)[:10]),
            _esc(rv.outcome or rv.cancel_reason or ""),
        ]
        for rv in view.reviews
        if rv.node_id == node_id
    ]
    work_rows = [
        [
            _esc(w.session_id),
            _esc(w.minutes if w.minutes is not None else "—"),
            _esc(w.notes or ""),
        ]
        for w in view.work
        if w.node_id == node_id
    ]
    blocker_rows = [
        [_esc(b.id), _esc(b.status), _esc(b.description)]
        for b in view.blockers
        if b.node_id == node_id
    ]
    remediation_rows = [
        [_esc(ra.id), _esc(ra.status), _esc(ra.description)]
        for ra in view.remediations
        if ra.node_id == node_id
    ]

    unsatisfied = {(pid, pstate) for pid, pstate in _unsatisfied_prereqs(node_id, view.edges, store)}
    prereq_rows = [
        [
            f'<a href="/nodes/{_esc(pid)}">{_esc(view.titles.get(pid, pid))}</a>',
            _esc(pstate),
            "no — must pass first" if (pid, pstate) in unsatisfied else "yes",
        ]
        for edge in view.edges
        if edge.active and edge.edge_type == "hard_prerequisite" and edge.target == node_id
        for pid, pstate in ((edge.source, store.state_of(edge.source)),)
    ]
    unlock_rows = [
        [
            f'<a href="/nodes/{_esc(uid)}">{_esc(view.titles.get(uid, uid))}</a>',
        ]
        for uid in _unlocked_by(node_id, view.edges)
    ]

    event_rows = [
        [_esc(e.get("timestamp", ""))[:19], _esc(e.get("command", ""))]
        for e in reversed(view.events)
        if node_id in (e.get("records_touched") or [])
    ][:10]

    def section(label: str, inner: str) -> str:
        return f"<details>\n<summary>{label}</summary>\n{inner}\n</details>\n"

    parts = ['<div class="card">\n<div class="kicker">DRILL-DOWN — READ-ONLY FACTS</div>\n']
    parts.append(
        section(
            "Evidence",
            f"<p>{gate_line}</p>"
            + (_table(["Spec", "Kind", "Requirement", "Minimum", "Live accepted"], evidence_rows) if evidence_rows else '<p class="mut">No artifact specs.</p>')
            + (_table(["Record", "Verdict", "Standing", "Location"], record_rows) if record_rows else "")
            + (_table(["Attempt", "Outcome", "Date"], attempt_rows) if attempt_rows else ""),
        )
    )
    parts.append(
        section(
            "Resources",
            _table(["Resource", "Where", "Verification"], resource_rows)
            if resource_rows
            else '<p class="mut">(no resources linked to this skill)</p>',
        )
    )
    if review_rows:
        parts.append(section("Reviews", _table(["Review", "Status", "Scheduled", "Outcome"], review_rows)))
    execution_inner = ""
    if work_rows:
        execution_inner += _table(["Session", "Minutes", "Notes"], work_rows)
    if blocker_rows:
        execution_inner += _table(["Blocker", "Status", "Description"], blocker_rows)
    if remediation_rows:
        execution_inner += _table(["Remediation", "Status", "Description"], remediation_rows)
    if execution_inner:
        parts.append(section("Sessions, blockers, remediation", execution_inner))
    graph_inner = ""
    if prereq_rows:
        graph_inner += _table(["Hard prerequisite", "State", "Satisfied?"], prereq_rows)
    if unlock_rows:
        graph_inner += "<p>This unlocks:</p>" + _table(["Unlocks"], unlock_rows)
    if graph_inner:
        parts.append(section("Graph edges", graph_inner))
    if event_rows:
        parts.append(
            section(
                "Events (audit log)",
                _table(["Timestamp (UTC)", "Command"], event_rows)
                + '<p class="mut">Audit-only history — never read back to compute state.</p>',
            )
        )
    parts.append("</div>\n")
    return "".join(parts)


def health_body(root) -> tuple[str, str, int]:
    """GET `/health` — the five validators plus liveness, read-only."""
    report = health_report(Path(root))

    rows = [
        [
            _esc(layer.target),
            _esc(layer.counts),
            f'<span class="pill {"verified" if layer.ok else "broken"}">'
            f"{'OK' if layer.ok else 'FAILED'}</span>",
        ]
        for layer in report.layers
    ]
    error_banners = "".join(
        f'<p class="banner error">{_esc(line[len("[error] "):])}</p>'
        for layer in report.layers
        for line in layer.error_lines
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"

    body = (
        _NAV
        + '<div class="card">\n'
        + '<div class="kicker">HEALTH ROLL-UP — FIVE VALIDATORS + LIVENESS</div>\n'
        + _table(["Layer", "Counts", "Status"], rows)
        + error_banners
        + _transform_block(report.liveness_lines)
        + f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        + '<p class="mut">Read fresh from the truth files at request time — '
        "CLI edits appear on refresh.</p>\n</div>\n"
    )
    return "Health", body, 200
