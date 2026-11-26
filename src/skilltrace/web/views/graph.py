"""
GET ``/graph`` and ``/graph/{id}`` — the graph inspection capability
(spec-v3-study-day §11.4, RT-14).

``graph/edges.yaml`` is the sole relationship truth (HB-8): this view renders
it and never invents, hardcodes or implies a relationship. Normal rendering
includes only valid relationships — an edge whose endpoint names no real skill
renders nowhere here and is carried, with its exact reference, by the
Repository diagnostics on Health.

Two presentations of the same facts, both server-rendered:

* the **complete list equivalent** (``/graph``) — every node with its current
  state and prerequisite context, every relationship with its endpoints; each
  row carries the same read and navigation actions (AX-9), and there is no
  picture to hide a fact in (no pan, zoom or heatmap; no client-side tier-1);
* the **learning-neighborhood view** (``/graph/{id}``) — the selected skill,
  its immediate incoming and outgoing relationships, and its full
  hard-prerequisite ancestor closure behind an expandable disclosure. The full
  curriculum stays available explicitly, never the default burden.

Selecting a node or an edge opens the contextual inspector inside the route
(``?node=`` / ``?edge=``), with the selection carried on the URL so a shared
or reloaded link reproduces exactly what was seen.
"""

from __future__ import annotations

from urllib.parse import urlencode

from ._shared import (
    _edge_is_valid,
    _empty_side,
    _esc,
    _normalize_pill_label,
    _state_pill,
    _table,
)
from .inspector import (
    graph_edge_inspector,
    graph_node_inspector,
    graph_selection,
)
from .sections import section
from .shell import _page_head, _status_page

#: The five canonical node states — the filter's whole population (SUP-P7).
_STATES = ("locked", "available", "active", "passed", "mastered")


def _valid_edges(view) -> list:
    """The edges whose endpoints both name real skills.

    The sole relationship truth is rendered as the relationships it actually
    records between existing skills; a dangling endpoint is a data error that
    belongs to Repository diagnostics, never to a rendered relationship.
    """
    return [edge for edge in view.edges if _edge_is_valid(view, edge)]


def _edges_for(view, node_id: str):
    """The incoming and outgoing edges of one node, from the edge table.

    Only valid relationships — an edge whose endpoint names no real skill
    renders nowhere (it belongs to Repository diagnostics).
    """
    incoming = [
        e for e in view.edges if e.target == node_id and e.source in view.node_map
    ]
    outgoing = [
        e for e in view.edges if e.source == node_id and e.target in view.node_map
    ]
    return incoming, outgoing


def _ancestors(view, node_id: str, edges: list) -> list[str]:
    """The full hard-prerequisite ancestor closure of one node.

    Derived from the edge table only — the traversal never guesses a
    relationship the edge table does not carry. Only valid relationships
    are walked; a dangling endpoint names no skill to walk to.
    """
    seen: set[str] = set()
    order: list[str] = []
    frontier = [node_id]
    while frontier:
        current = frontier.pop(0)
        for edge in edges:
            if edge.target != current or edge.source in seen:
                continue
            if edge.source not in view.node_map:
                continue
            seen.add(edge.source)
            order.append(edge.source)
            frontier.append(edge.source)
    return order


def _graph_href(params: dict[str, str]) -> str:
    return f"/graph?{urlencode(params)}" if params else "/graph"


def _state_filter_form(state: str) -> str:
    """The labelled GET filter — the narrowed list has its own URL (IC-4)."""
    options = ['<option value="">All states</option>']
    for value in _STATES:
        chosen = " selected" if value == state else ""
        options.append(
            f'<option value="{value}"{chosen}>{_normalize_pill_label(value)}</option>'
        )
    return (
        '<form class="filters" method="get" action="/graph">\n'
        '<div class="form-row">'
        '<label for="graph-state">State</label>'
        f'<select name="state" id="graph-state">{"".join(options)}</select></div>\n'
        '<button type="submit">Apply filter</button>\n'
        "</form>\n"
    )


def _node_rows(view, edges, state_filter: str) -> str:
    """The complete list equivalent: every node, with its state and context.

    Each row carries the same read and navigation actions the graph offers
    (AX-9): the title opens the skill's detail, *Neighborhood* moves the
    learning-neighborhood view to that skill, and *Inspect* selects the
    node in the contextual inspector without leaving the route.
    """
    rows = []
    for node in sorted(view.nodes, key=lambda n: n.id):
        state = view.store.state_of(node.id)
        if state_filter and state != state_filter:
            continue
        incoming = [e for e in edges if e.target == node.id]
        prerequisites = ", ".join(
            view.titles.get(e.source) or e.source for e in incoming
        )
        inspect = _graph_href({"node": node.id, **({"state": state_filter} if state_filter else {})})
        rows.append(
            [
                f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>',
                _esc(node.id),
                _state_pill(state),
                _esc(prerequisites or "—"),
                f'<a href="/graph/{_esc(node.id)}">Neighborhood</a>',
                f'<a href="{_esc(inspect)}">Inspect</a>',
            ]
        )
    return _table(
        [
            "Skill",
            "Node ID",
            "State",
            "Prerequisites",
            "Neighborhood",
            "Inspect",
        ],
        rows,
    )


def _edge_rows(view, edges) -> str:
    """The complete edge list — the same facts the neighborhood shows."""
    rows = []
    for edge in sorted(edges, key=lambda e: (e.source, e.target)):
        rows.append(
            [
                f'<a href="/nodes/{_esc(edge.source)}">'
                f'{_esc(view.titles.get(edge.source) or edge.source)}</a>',
                f'<a href="/nodes/{_esc(edge.target)}">'
                f'{_esc(view.titles.get(edge.target) or edge.target)}</a>',
                _esc(edge.edge_type),
                "Yes" if edge.active else "No",
                f'<a href="{_esc(_graph_href({"edge": edge.id}))}">Inspect</a>',
            ]
        )
    return _table(["From", "To", "Relationship", "In force", "Inspect"], rows)


def _dangling_section(view) -> str:
    """What the graph does not render, said out loud and pointed at Health."""
    dangling = [
        edge
        for edge in view.edges
        if edge.source not in view.node_map or edge.target not in view.node_map
    ]
    if not dangling:
        return ""
    return (
        '<div class="banner advisory">'
        f"{len(dangling)} relationship{'' if len(dangling) == 1 else 's'} in the "
        "edge table name a skill that does not exist, so nothing is rendered "
        "for them here and they change nothing about what is ready. The exact "
        'references are in <a href="/health">Repository diagnostics</a>.</div>\n'
    )


def _neighborhood_rows(view, edges, direction: str) -> str:
    """One side of the neighborhood: readable rows with the same actions."""
    rows = []
    for edge in sorted(edges, key=lambda e: e.source if direction == "prerequisites" else e.target):
        other = edge.source if direction == "prerequisites" else edge.target
        rows.append(
            [
                f'<a href="/nodes/{_esc(other)}">'
                f'{_esc(view.titles.get(other) or other)}</a>',
                _esc(edge.edge_type),
                "Yes" if edge.active else "No",
                f'<a href="{_esc(_graph_href({"edge": edge.id}))}">Inspect</a>',
                f'<a href="/graph/{_esc(other)}">Neighborhood</a>',
            ]
        )
    return _table(
        ["Skill", "Relationship", "In force", "Inspect", "Neighborhood"], rows
    )


def graph_body(
    root, query: dict | None = None, *, node_id: str | None = None
) -> tuple[str, str, int]:
    """GET `/graph` (or `/graph/{id}`) — the graph, with its list equivalent."""
    path = "/graph" if node_id is None else f"/graph/{node_id}"
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/graph",
        current_view="graph",
        default_mode="operations",
        path=path,
    )
    if failure is not None:
        return failure

    query = query or {}
    state_filter = (query.get("state") or [""])[0].strip()
    if state_filter not in _STATES:
        state_filter = ""
    selection = graph_selection(query)

    if node_id is not None and node_id not in view.node_map:
        body, status = _status_page(
            404, "That skill is not in the curriculum.", root
        )
        return "Not found", body, status

    edges = _valid_edges(view)
    inspector = ""
    if selection is not None:
        kind, value = selection
        if node_id is not None:
            close = f"/graph/{node_id}"
        else:
            close = _graph_href({"state": state_filter} if state_filter else {})
        if kind == "node":
            inspector = graph_node_inspector(view, value, close)
        else:
            inspector = graph_edge_inspector(view, value, close)

    if not view.nodes:
        body = (
            head
            + '<section class="section">\n'
            + '<div class="state state-empty">\n'
            + '<p class="state-title">The curriculum is empty</p>\n'
            + '<p class="state-body">No skills were found in the graph source, '
            "so there are no relationships to show. This is a fact about the "
            "curriculum, not about your progress.</p>\n"
            + "</div>\n"
            + "</section>\n"
            + inspector
        )
        return "Graph", body, 200

    if node_id is not None:
        node = view.node_map[node_id]
        incoming, outgoing = _edges_for(view, node_id)
        facts = (
            '<div class="rows">\n'
            '<div class="row"><span class="row-label">State</span>'
            f'<span class="row-value">{_state_pill(view.store.state_of(node_id))}</span></div>\n'
            f'<div class="row"><span class="row-label">Node ID</span>'
            f'<span class="row-value"><code>{_esc(node_id)}</code></span></div>\n'
            + (
                f'<div class="row"><span class="row-label">Track</span>'
                f'<span class="row-value">{_esc(node.track)}</span></div>\n'
                if node.track
                else ""
            )
            + (
                f'<div class="row"><span class="row-label">Summary</span>'
                f'<span class="row-value">{_esc(node.summary)}</span></div>\n'
                if node.summary
                else ""
            )
            + "</div>\n"
        )
        ancestors = _ancestors(view, node_id, edges)
        ancestry = ""
        if ancestors:
            items = "".join(
                f'<li class="history-item"><a href="/nodes/{_esc(a)}">'
                f"{_esc(view.titles.get(a) or a)}</a></li>\n"
                for a in ancestors
            )
            ancestry = (
                '<details class="disclosure">\n'
                f"<summary>Full prerequisite ancestry ({len(ancestors)})</summary>\n"
                '<ul class="history-list">\n'
                f"{items}</ul>\n"
                "</details>\n"
            )
        else:
            ancestry = (
                '<p class="small mut">No prerequisites beyond the immediate '
                "ones.</p>\n"
            )
        body = (
            head
            + section(
                "This skill",
                "The selected skill's own facts, read fresh from the "
                "curriculum and the progress store.",
                facts,
            )
            + section(
                "Prerequisites",
                "The relationships that name this skill as their target — "
                "read from the edge table, the sole relationship truth.",
                _neighborhood_rows(view, incoming, "prerequisites")
                if incoming
                else _empty_side(
                    "No prerequisites",
                    "Nothing stands between this skill and being ready.",
                ),
            )
            + section(
                "Unlocks",
                "The relationships that name this skill as their source.",
                _neighborhood_rows(view, outgoing, "unlocks")
                if outgoing
                else _empty_side(
                    "Nothing builds on this skill yet",
                    "No relationship in the edge table names this skill as "
                    "its source.",
                ),
            )
            + section(
                "Ancestry",
                "Every hard prerequisite behind this skill, however far back "
                "the edge table goes.",
                ancestry,
            )
            + '<p class="command-bar"><a class="btn secondary" href="/graph">'
            "The full curriculum</a></p>\n"
            + inspector
        )
        return node.title, body, 200

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">Every skill</h2>\n'
        + '<p class="section-meta">The complete list equivalent — every node '
        "with its current state and its prerequisite context.</p>\n"
        + "</div>\n"
        + _state_filter_form(state_filter)
        + f"{_node_rows(view, edges, state_filter)}"
        + "</section>\n"
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">Every relationship</h2>\n'
        + '<p class="section-meta">Every relationship the edge table records, '
        "whatever the state filter above shows.</p>\n"
        + "</div>\n"
        + f"{_edge_rows(view, edges)}"
        + "</section>\n"
        + _dangling_section(view)
        + inspector
    )
    return "Graph", body, 200
