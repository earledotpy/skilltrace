"""
GET ``/operations`` — the Operations capability directory (spec-v3-study-day
§11.1).

The home of deep inspection is a **capability directory**: Graph, Evidence,
Reviews, Health, Analytics and Portfolio are each reachable in their own
right and never collapsed behind a generic "More". The counts here are
home-only and link to their capability; their numbers must agree with the
destination views (R7) and never become a composite score.
"""

from __future__ import annotations

from ._shared import _esc
from .shell import _page_head


def _capability_counts(view) -> list[tuple[str, str, str, int]]:
    """One row per capability: label, route, one-line why, the count.

    Every count is derived from the same facts the destination view reads,
    so the home and the destination can never disagree (R7).
    """
    nodes = view.nodes
    edges = view.edges
    records = view.records
    reviews = view.reviews
    blockers = view.blockers

    passed = len([n for n in nodes if view.store.state_of(n.id) == "passed"])
    open_blockers = len([b for b in blockers if b.status == "open"])

    return [
        (
            "Graph",
            "/graph",
            "The relationship truth behind the curriculum.",
            len(nodes),
        ),
        (
            "Evidence",
            "/evidence",
            "Every evidence record in the repository, newest first.",
            len(records),
        ),
        (
            "Reviews",
            "/reviews",
            "Scheduled, completed and cancelled retention checks.",
            len(reviews),
        ),
        (
            "Health",
            "/health",
            "Study guidance and repository diagnostics, kept apart.",
            len(nodes) + len(edges),
        ),
        (
            "Analytics",
            "/analytics",
            "Derived study facts, each with its table equivalent.",
            passed,
        ),
        (
            "Portfolio",
            "/portfolio",
            "A dated, disposable snapshot you configure and export.",
            open_blockers,
        ),
    ]


def operations_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/operations` — the capability directory home."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/operations",
        current_view="operations",
        default_mode="operations",
        path="/operations",
    )
    if failure is not None:
        return failure

    rows = _capability_counts(view)
    section_rows = "".join(
        f'<div class="row"><span class="row-label">'
        f'<a href="{_esc(route)}">{_esc(label)}</a></span>'
        f'<span class="row-value">{_esc(why)}</span>'
        f'<span class="row-value">{count}</span></div>\n'
        for label, route, why, count in rows
    )

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">Capabilities</h2>\n'
        + '<p class="section-meta">Each capability is its own destination. '
        "Nothing here is hidden behind a generic menu.</p>\n"
        + "</div>\n"
        + f'<div class="rows">\n{section_rows}</div>\n'
        + "</section>\n"
    )
    return "Operations", body, 200
