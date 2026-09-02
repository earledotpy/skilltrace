"""Analytics export — Markdown, HTML, and JSON formats (G7, issue #130).

Single entry point ``export_analytics`` driven from ``derive.py``.  All three
formats consume the same ``AnalyticsView`` derivation pipeline; no second
vocabulary (G7 resolution).

Signature::

    export_analytics(
        root, *, theme, fmt, days, group_by, state, output
    ) -> Path

``output=None``  → default path ``data/analytics-report-<theme>.<ext>``
                    (theme segment omitted for the all-themes summary).
``output=Path("-")`` → stdout.

Raises ``ExportError`` on any ``ExportData`` load error so the caller
(the command handler) can exit non-zero with a clear message without
writing a partial file.

Each call appends exactly one ``export_analytics`` audit event (MUTATING,
per G7); the dispatcher handles that via ``Kind.MUTATING`` — this module
does NOT write the event itself.
"""

from __future__ import annotations

import datetime
import html
import json
from pathlib import Path
from typing import Any

from ..context import JoinedView, load_context_strict
from ..policy.advisory import analytics_warnings
from .derive import derive_analytics
from .models import (
    AnalyticsView,
    BlockersResult,
    EvidenceResult,
    ReviewsResult,
    VelocityResult,
)
from .sparkline import sparkline_svg


# ---------------------------------------------------------------------------
# Public error type
# ---------------------------------------------------------------------------


class ExportError(Exception):
    """Raised when data cannot be loaded; export is refused."""


# ---------------------------------------------------------------------------
# Default path helpers
# ---------------------------------------------------------------------------

_DATA_DIR = Path("data")


def _default_path(theme: str, fmt: str) -> Path:
    ext = {"md": "md", "html": "html", "json": "json"}.get(fmt, fmt)
    if theme == "all":
        stem = "analytics-report"
    else:
        stem = f"analytics-report-{theme}"
    return _DATA_DIR / f"{stem}.{ext}"


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


def _load_view(
    root: Path,
    *,
    days: int,
    group_by: str,
    state: list[str],
    min_sessions: int,
) -> AnalyticsView:
    """Load the strict joined view and derive the analytics model.

    Raises ``ExportError`` on any load failure — never writes partial output.
    """
    joined: JoinedView = load_context_strict(root)
    if not joined.ok:
        raise ExportError(
            "Cannot export analytics — data load failed:\n"
            + "\n".join(f"  {e}" for e in joined.errors)
        )

    today = datetime.date.today()
    return derive_analytics(
        joined,
        today=today,
        window_days=days,
        group_by=group_by,
        state_filter=state,
        min_sessions_for_full_data=min_sessions,
    )


def _resolve_policy(root: Path) -> tuple[int, str, int]:
    """Read analytics policy defaults; fall back to module constants."""
    from ..policy.loading import PolicyLoadError, load_policy_doc

    try:
        doc = load_policy_doc(root, "analytics.yaml")
    except PolicyLoadError:
        doc = {}
    window_days = doc.get("default_window_days", 30)
    group_by = doc.get("default_group_by", "prefix")
    min_sessions = doc.get("min_sessions_for_full_data", 3)
    if not isinstance(window_days, int) or window_days <= 0:
        window_days = 30
    if group_by not in ("prefix", "track"):
        group_by = "prefix"
    if not isinstance(min_sessions, int) or min_sessions <= 0:
        min_sessions = 3
    return window_days, group_by, min_sessions


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

_MD_SEP = "---"


def _md_summary_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "| " + " | ".join("-" * w for w in col_widths) + " |"
    header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [header_row, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) + " |")
    return lines


def _render_md(
    view: AnalyticsView, warnings: list[str], generated_at: str, theme: str
) -> str:
    v, b, r, e = view.velocity, view.blockers, view.reviews, view.evidence
    lines: list[str] = []

    # Header
    lines += [
        "# Analytics Report",
        "",
        f"Generated: {generated_at}",
        f"Period: last {view.window_days} days",
        f"Group by: {view.group_by}",
    ]
    if view.state_filter:
        lines.append(f"State filter: {', '.join(view.state_filter)}")
    if view.is_limited:
        lines.append(
            f"\n[advisory] Limited data — {view.sessions_in_window} session(s) in window; "
            f"some metrics may be unreliable."
        )
    for w in warnings:
        lines.append(f"\n[advisory] {w}")

    lines += ["", _MD_SEP]

    themes = {theme} if theme != "all" else {"velocity", "blockers", "reviews", "evidence"}

    # Velocity
    if "velocity" in themes:
        lines += [
        "",
        "## Velocity",
        "",
        f"Sessions in window: {v.sessions_in_window}  ",
        f"Nodes touched: {v.nodes_touched}  ",
        f"Study time: {v.total_minutes} min ({v.total_minutes / 60:.1f} h)",
        "",
        ]
    if "velocity" in themes and v.weeks:
        lines += _md_summary_table(
            ["Week", "Sessions", "Nodes", "Minutes"],
            [[w.label, w.session_count, w.node_count, w.minutes] for w in v.weeks[-8:]],
        )
    if "velocity" in themes and v.group_rows:
        lines += [""]
        col = "Prefix" if view.group_by == "prefix" else "Track"
        lines += _md_summary_table(
            [col, "Sessions", "Nodes"],
            [[g, s, n] for g, s, n in v.group_rows[:10]],
        )

    if "velocity" in themes:
        lines += ["", _MD_SEP]

    # Blockers
    if "blockers" in themes:
        lines += ["", "## Blockers", "", f"Open: {b.open_count}  ", f"Resolved in window: {b.resolved_in_window}", ""]
    if "blockers" in themes and b.rows:
        col = "Prefix" if view.group_by == "prefix" else "Track"
        lines += _md_summary_table(
            [col, "Days open", "Description"],
            [[row.group, row.days_open, row.description[:60]] for row in b.rows[:10]],
        )

    if "blockers" in themes:
        lines += ["", _MD_SEP]

    # Reviews
    pct_r = f"{r.completion_rate * 100:.0f}%"
    if "reviews" in themes:
        lines += [
        "",
        "## Reviews",
        "",
        f"Scheduled: {r.scheduled_count}  ",
        f"Overdue: {r.overdue_count}  ",
        f"Completed in window: {r.completed_in_window}  ",
        f"Completion rate: {pct_r}",
        "",
        ]
    if "reviews" in themes and r.rows:
        lines += _md_summary_table(
            ["Node", "Due", "Days overdue"],
            [[row.node_id, row.scheduled_for, row.days_overdue or "-"] for row in r.rows[:10]],
        )

    if "reviews" in themes:
        lines += ["", _MD_SEP]

    # Evidence
    pct_e = f"{e.coverage_rate * 100:.0f}%"
    if "evidence" in themes:
        lines += [
        "",
        "## Evidence",
        "",
        f"Nodes with specs: {e.nodes_with_specs}  ",
        f"Nodes with gaps: {e.nodes_with_gaps}  ",
        f"Coverage rate: {pct_e}",
        "",
        ]
    if "evidence" in themes and e.rows:
        col = "Prefix" if view.group_by == "prefix" else "Track"
        lines += _md_summary_table(
            [col, "State", "Specs", "Accepted", "Gap"],
            [[row.group, row.state, row.spec_count, row.accepted_count, "GAP" if row.gap else "ok"]
             for row in e.rows[:10]],
        )

    if "evidence" in themes:
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_HTML_STYLE = """
body { font-family: system-ui, sans-serif; margin: 1rem 2rem; background: #fff; color: #222; }
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; margin-top: 1.5rem; border-bottom: 1px solid #ddd; padding-bottom: 0.2rem; }
table { border-collapse: collapse; font-size: 0.85rem; margin: 0.5rem 0; }
th, td { border: 1px solid #ccc; padding: 0.2rem 0.5rem; text-align: left; }
th { background: #f4f4f4; }
.meta { font-size: 0.8rem; color: #666; margin: 0.25rem 0; }
.advisory { background: #fff8e1; border-left: 3px solid #f0a500; padding: 0.3rem 0.6rem;
            margin: 0.4rem 0; font-size: 0.85rem; }
.sparkline { display: block; margin: 0.25rem 0; }
.footer { margin-top: 2rem; font-size: 0.75rem; color: #999; }
""".strip()


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def _render_html(
    view: AnalyticsView, warnings: list[str], generated_at: str, theme: str
) -> str:
    v, b, r, e = view.velocity, view.blockers, view.reviews, view.evidence

    def advisory_block(text: str) -> str:
        return f'<div class="advisory">[advisory] {html.escape(text)}</div>'

    sections: list[str] = []
    themes = {theme} if theme != "all" else {"velocity", "blockers", "reviews", "evidence"}

    # ---- Velocity -----------------------------------------------------------
    spark_v = sparkline_svg([(w.label, w.session_count) for w in v.weeks])
    vel_rows_html = ""
    if v.group_rows:
        col = "Prefix" if view.group_by == "prefix" else "Track"
        vel_rows_html = _html_table(
            [col, "Sessions", "Nodes"],
            [[g, s, n] for g, s, n in v.group_rows[:10]],
        )
    if "velocity" in themes:
        sections.append(
            "<h2>Velocity</h2>"
        f'<span class="sparkline">{spark_v}</span>'
        f"<p>Sessions: {v.sessions_in_window} &nbsp; Nodes touched: {v.nodes_touched} &nbsp; "
        f"Study time: {v.total_minutes} min ({v.total_minutes / 60:.1f} h)</p>"
        + vel_rows_html
        )

    # ---- Blockers -----------------------------------------------------------
    spark_b = sparkline_svg([("window", b.open_count)])
    blk_rows_html = ""
    if b.rows:
        col = "Prefix" if view.group_by == "prefix" else "Track"
        blk_rows_html = _html_table(
            [col, "Days open", "Description"],
            [[row.group, row.days_open, row.description[:60]] for row in b.rows[:10]],
        )
    if "blockers" in themes:
        sections.append(
            "<h2>Blockers</h2>"
        f'<span class="sparkline">{spark_b}</span>'
        f"<p>Open: {b.open_count} &nbsp; Resolved in window: {b.resolved_in_window}</p>"
        + blk_rows_html
        )

    # ---- Reviews ------------------------------------------------------------
    spark_r = sparkline_svg([("window", r.completed_in_window)])
    rev_rows_html = ""
    if r.rows:
        rev_rows_html = _html_table(
            ["Node", "Due", "Days overdue"],
            [[row.node_id, row.scheduled_for, row.days_overdue or "-"] for row in r.rows[:10]],
        )
    if "reviews" in themes:
        sections.append(
            "<h2>Reviews</h2>"
        f'<span class="sparkline">{spark_r}</span>'
        f"<p>Scheduled: {r.scheduled_count} &nbsp; Overdue: {r.overdue_count} &nbsp; "
        f"Completed: {r.completed_in_window} &nbsp; Rate: {r.completion_rate * 100:.0f}%</p>"
        + rev_rows_html
        )

    # ---- Evidence -----------------------------------------------------------
    spark_e = sparkline_svg(
        [("window", sum(row.accepted_count for row in e.rows))]
    )
    ev_rows_html = ""
    if e.rows:
        col = "Prefix" if view.group_by == "prefix" else "Track"
        ev_rows_html = _html_table(
            [col, "State", "Specs", "Accepted", "Gap"],
            [[row.group, row.state, row.spec_count, row.accepted_count, "GAP" if row.gap else "ok"]
             for row in e.rows[:10]],
        )
    if "evidence" in themes:
        sections.append(
            "<h2>Evidence</h2>"
        f'<span class="sparkline">{spark_e}</span>'
        f"<p>Nodes with specs: {e.nodes_with_specs} &nbsp; "
        f"Nodes with gaps: {e.nodes_with_gaps} &nbsp; "
        f"Coverage: {e.coverage_rate * 100:.0f}%</p>"
        + ev_rows_html
        )

    # ---- Assemble -----------------------------------------------------------
    meta_parts = [
        f'<p class="meta">Generated: {html.escape(generated_at)}</p>',
        f'<p class="meta">Period: last {view.window_days} days &nbsp; Group by: {view.group_by}</p>',
    ]
    if view.state_filter:
        meta_parts.append(f'<p class="meta">State filter: {html.escape(", ".join(view.state_filter))}</p>')

    advisory_blocks = ""
    if view.is_limited:
        advisory_blocks += advisory_block(
            f"Limited data — {view.sessions_in_window} session(s) in window; some metrics may be unreliable."
        )
    for w in warnings:
        advisory_blocks += advisory_block(w)

    body = (
        "<h1>Analytics Report</h1>"
        + "".join(meta_parts)
        + advisory_blocks
        + "".join(sections)
        + f'<p class="footer">Snapshot — not live. Generated {html.escape(generated_at)} UTC.</p>'
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Analytics Report</title>\n"
        f"<style>\n{_HTML_STYLE}\n</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# JSON renderer
# ---------------------------------------------------------------------------


def _render_json(
    view: AnalyticsView, warnings: list[str], generated_at: str, theme: str
) -> str:
    """Produce the curated published JSON subset (G7 resolution).

    Shape is the stable contract from the G7 resolution comment.  Empty
    themes are still included with zeros (omit only when literally nothing
    to report — but the spec says include with zeros, so we always include).
    """
    v, b, r, e = view.velocity, view.blockers, view.reviews, view.evidence

    # Derive period start/end from today and window_days
    today = datetime.date.today()
    start = today - datetime.timedelta(days=view.window_days)
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "period": {
            "start": start.isoformat(),
            "end": today.isoformat(),
            "days": view.window_days,
        },
        "group_by": view.group_by,
        "state": list(view.state_filter),
        "advisory_warnings": list(warnings),
        "velocity": {
            "work_items_count": v.nodes_touched,
            "minutes_logged": v.total_minutes,
            "node_progress": v.nodes_touched,
            "by_week": [
                {"week_start": w.label, "items": w.session_count}
                for w in v.weeks
            ],
            "by_group": [
                {"group": g, "items": s}
                for g, s, _n in v.group_rows
            ],
        },
        "blockers": {
            "active_count": b.open_count,
            "by_track": [
                {"track": row.group, "count": 1}
                for row in b.rows
            ] if view.group_by == "track" else [],
            "by_prefix": [
                {"prefix": row.group, "count": 1}
                for row in b.rows
            ] if view.group_by == "prefix" else [],
        },
        "reviews": {
            "scheduled": r.scheduled_count,
            "completed": r.completed_in_window,
            "overdue": r.overdue_count,
            "completion_rate": round(r.completion_rate, 4),
        },
        "evidence": {
            "total_records": sum(row.accepted_count for row in e.rows),
            "accepted": sum(row.accepted_count for row in e.rows),
            "rejected": 0,
            "nodes_with_gaps": e.nodes_with_gaps,
            "submission_rate": round(e.coverage_rate, 4),
        },
    }
    if theme != "all":
        payload = {
            key: value for key, value in payload.items()
            if key not in {"velocity", "blockers", "reviews", "evidence"} or key == theme
        }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def export_analytics(
    root: Path | str,
    *,
    theme: str,
    fmt: str,
    days: int | None = None,
    group_by: str | None = None,
    state: list[str] | None = None,
    output: Path | None = None,
) -> Path:
    """Derive and render analytics in the requested format.

    Parameters
    ----------
    root:
        Repository root.
    theme:
        One of ``"velocity"``, ``"blockers"``, ``"reviews"``, ``"evidence"``,
        or ``"all"`` (default umbrella).
    fmt:
        Output format: ``"md"``, ``"html"``, or ``"json"``.
    days:
        Rolling window in days (``None`` → policy default).
    group_by:
        ``"prefix"`` or ``"track"`` (``None`` → policy default).
    state:
        Node state filter list (``None`` or ``[]`` → all states).
    output:
        Destination path.  ``None`` → default ``data/analytics-report-<theme>.<ext>``.
        ``Path("-")`` → stdout (caller must handle the return value).

    Returns
    -------
    Path
        The path written (or ``Path("-")`` for stdout).

    Raises
    ------
    ExportError
        On any data load failure — never writes partial output.
    ValueError
        On an unknown ``fmt``.
    """
    root = Path(root)
    state = list(state or [])

    if fmt not in ("md", "html", "json"):
        raise ValueError(f"Unknown export format: {fmt!r} (expected md, html, or json)")

    # Resolve policy defaults for unspecified params
    policy_days, policy_group_by, min_sessions = _resolve_policy(root)
    if days is None:
        days = policy_days
    if group_by is None:
        group_by = policy_group_by

    # Load and derive
    view = _load_view(root, days=days, group_by=group_by, state=state, min_sessions=min_sessions)

    # Advisory warnings are part of the published export, so failures must
    # remain visible rather than silently producing an incomplete report.
    warnings = analytics_warnings(root, view)

    # Timestamp
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Render
    if fmt == "md":
        content = _render_md(view, warnings, generated_at, theme)
    elif fmt == "html":
        content = _render_html(view, warnings, generated_at, theme)
    else:
        content = _render_json(view, warnings, generated_at, theme)

    # Resolve output path
    if output is None:
        output = root / _default_path(theme, fmt)

    if output == Path("-"):
        import sys
        sys.stdout.write(content)
        return Path("-")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output
