"""
GET ``/operations`` — the Operations capability directory (spec-v3-study-day
§11.1, RT-13).

The home of deep inspection is a **capability directory**: Graph, Evidence,
Reviews, Health, Analytics and Portfolio are each reachable in their own
right and never collapsed behind a generic "More" (IA-3). The count cards
exist only on this home and link to their capability; every number is derived
from the same facts the destination view reads, so a card, its destination and
the fixture can never disagree (R7) — and Health's card is never a composite
score, only its two named projections.
"""

from __future__ import annotations

from ...execution.overdue import overdue_reviews, utc_today
from ._shared import _degraded_banner, _empty_side, _esc, plural
from .analytics import THEMES
from .sections import section
from .shell import _page_head


def _capability_cards(view) -> list[tuple[str, str, str, str, str]]:
    """One card per capability: label, route, count, one-line why, detail.

    Every count is derived from the same facts the destination view reads —
    the card is a pointer, never a second derivation with its own opinion.
    """
    nodes = view.nodes
    edges = view.edges
    available = len([n for n in nodes if view.store.state_of(n.id) == "available"])
    locked = len([n for n in nodes if view.store.state_of(n.id) == "locked"])

    return [
        (
            "Graph",
            "/graph",
            f"{len(nodes)} skill{plural(len(nodes))}",
            "The relationship truth behind the curriculum, from the edge "
            "table and nothing else.",
            f"{available} available · {locked} locked · "
            f"{len(edges)} relationship{plural(len(edges))}",
        ),
        (
            "Evidence",
            "/evidence",
            f"{len(view.records)} record{plural(len(view.records))}",
            "Every record in the repository, newest first — immutable; a "
            "correction supersedes, never edits.",
            "",
        ),
        (
            "Reviews",
            "/reviews",
            f"{len(view.reviews)} review{plural(len(view.reviews))}",
            "Scheduled, completed and cancelled checks — never retention "
            "suggestions.",
            "",
        ),
        (
            "Health",
            "/health",
            "Two projections",
            "Study guidance and repository diagnostics, kept apart — never "
            "a score.",
            "",
        ),
        (
            "Analytics",
            "/analytics",
            f"{len(THEMES)} themes",
            "Derived study facts, each with its table equivalent — no fake "
            "telemetry.",
            "",
        ),
        (
            "Portfolio",
            "/portfolio",
            "Export",
            "A dated, disposable snapshot you configure and preview — never "
            "live truth.",
            "",
        ),
    ]


def _cards_section(view) -> str:
    """The capability directory: one card per destination, each linked."""
    cards = []
    for label, route, value, why, detail in _capability_cards(view):
        cards.append(
            '<div class="capability-card">\n'
            f'<h3 class="capability-title"><a href="{_esc(route)}">'
            f"{_esc(label)}</a></h3>\n"
            f'<p class="capability-value">{_esc(value)}</p>\n'
            f'<p class="capability-why">{_esc(why)}</p>\n'
            + (
                f'<p class="capability-detail">{_esc(detail)}</p>\n'
                if detail
                else ""
            )
            + "</div>\n"
        )
    return section(
        "Capabilities",
        "Each capability is its own destination. Nothing here is hidden "
        "behind a generic menu.",
        '<div class="capability-grid">\n' + "".join(cards) + "</div>\n",
    )


def _recent_facts_section(view) -> str:
    """Recent relevant facts as links to where they live (§11.1).

    Every row is a fact the destination itself shows; a fact with nothing
    to link renders no row, so the section never pads itself with zeroes.
    """
    rows: list[str] = []

    live_records = [r for r in view.records if r.created_at]
    if live_records:
        newest = max(
            live_records, key=lambda r: (str(r.created_at), r.artifact_spec_id, r.id)
        )
        spec = next(
            (s for s in view.specs if s.id == newest.artifact_spec_id), None
        )
        node_id = spec.node_id if spec is not None else ""
        title = view.titles.get(node_id) if node_id else None
        if title:
            link = (
                f'<a href="/evidence?record={_esc(newest.id)}">{_esc(title)}</a>'
            )
        else:
            link = f'<a href="/evidence?record={_esc(newest.id)}"><code>{_esc(newest.id)}</code></a>'
        rows.append(
            '<div class="row"><span class="row-label">Newest evidence</span>'
            f'<span class="row-value">{link} '
            f'<span class="small mut">{_esc(str(newest.created_at)[:10])}</span>'
            "</span></div>"
        )

    overdue = overdue_reviews(view.reviews, today=utc_today())
    if overdue:
        rows.append(
            '<div class="row"><span class="row-label">Reviews overdue</span>'
            f'<span class="row-value"><a href="/reviews">{len(overdue)} '
            "overdue</a></span></div>"
        )

    open_blockers = [b for b in view.blockers if b.status == "open"]
    if open_blockers:
        links = []
        for blocker in open_blockers[:3]:
            title = view.titles.get(blocker.node_id)
            if title:
                links.append(
                    f'<a href="/nodes/{_esc(blocker.node_id)}">{_esc(title)}</a>'
                )
        shown = ", ".join(links) if links else str(len(open_blockers))
        extra = len(open_blockers) - min(len(open_blockers), 3)
        if extra > 0:
            shown += f" and {extra} more"
        rows.append(
            '<div class="row"><span class="row-label">Open blockers</span>'
            f'<span class="row-value">{shown}</span></div>'
        )

    if not rows:
        return ""
    return section(
        "Recent facts",
        "Where things stand right now, each fact linked to the capability "
        "that owns it.",
        '<div class="rows">\n' + "\n".join(rows) + "\n</div>\n",
    )


def _empty_curriculum_state() -> str:
    """The empty case: a fact about the curriculum, never about the learner."""
    follow = (
        '<p><a href="/find">Find a skill</a> once the curriculum has one — or '
        '<a href="/health">open Health</a> to see what the source check says.'
        "</p>\n"
    )
    return (
        '<section class="section">\n'
        + _empty_side(
            "The curriculum is empty",
            "No skills were found in the graph source, so there is nothing "
            "to inspect yet. This is a fact about the curriculum, not about "
            "your progress.",
            follow,
        )
        + "</section>\n"
    )


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

    body = (
        head
        + _degraded_banner(view)
        + (_empty_curriculum_state() if not view.nodes else "")
        + _cards_section(view)
        + _recent_facts_section(view)
    )
    return "Operations", body, 200
