"""
GET ``/graph`` and ``/graph/{id}`` — the graph inspection capability
(spec-v3-study-day §11.4).

``graph/edges.yaml`` is the sole relationship truth: this view renders it
and never invents, hardcodes or implies a relationship. The node-centred
view shows the selected SkillNode, its immediate incoming and outgoing
edges, and the complete ancestor closure behind a disclosure.

The **list equivalent** is not an optional extra: every node and edge is
reachable by keyboard with a meaningful name, its current state and its
prerequisite context (AX-9). No fact exists only in a picture — there is no
picture: the graph is a table plus a list, both server-rendered.
"""

from __future__ import annotations

from ._shared import _esc, _table
from .sections import INLINE, NONE, section
from .shell import _page_head


def _edges_for(view, node_id: str):
    """The incoming and outgoing edges of one node, from the edge table."""
    incoming = [e for e in view.edges if e.target == node_id]
    outgoing = [e for e in view.edges if e.source == node_id]
    return incoming, outgoing


def _ancestors(view, node_id: str) -> list[str]:
    """The full hard-prerequisite ancestor closure of one node.

    Derived from the edge table only — the traversal never guesses a
    relationship the edge table does not carry.
    """
    seen: set[str] = set()
    order: list[str] = []
    frontier = [node_id]
    while frontier:
        current = frontier.pop(0)
        for edge in view.edges:
            if edge.target != current or edge.source in seen:
                continue
            seen.add(edge.source)
            order.append(edge.source)
            frontier.append(edge.source)
    return order


def _node_rows(view, edges) -> str:
    """The complete list equivalent: every node, with its state and context."""
    rows = []
    for node in sorted(view.nodes, key=lambda n: n.id):
        state = view.store.state_of(node.id)
        incoming = [e for e in edges if e.target == node.id]
        prerequisites = ", ".join(
            view.titles.get(e.source) or e.source for e in incoming
        )
        rows.append(
            [
                f'<a href="/nodes/{_esc(node.id)}">{_esc(node.title)}</a>',
                _esc(node.id),
                _esc(state),
                _esc(prerequisites or "—"),
            ]
        )
    return _table(["Skill", "Node ID", "State", "Prerequisites"], rows)


def _edge_rows(view) -> str:
    """The complete edge list — the same facts the neighbourhood shows."""
    rows = []
    for edge in sorted(view.edges, key=lambda e: (e.source, e.target)):
        rows.append(
            [
                f'<a href="/nodes/{_esc(edge.source)}">'
                f'{_esc(view.titles.get(edge.source) or edge.source)}</a>',
                f'<a href="/nodes/{_esc(edge.target)}">'
                f'{_esc(view.titles.get(edge.target) or edge.target)}</a>',
                _esc(edge.edge_type),
                "yes" if edge.active else "no",
            ]
        )
    return _table(["From", "To", "Relationship", "Affects readiness"], rows)


def graph_body(
    root, query: dict | None = None, *, node_id: str | None = None
) -> tuple[str, str, int]:
    """GET `/graph` (or `/graph/{id}`) — the graph, with its list equivalent."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/graph",
        current_view="graph",
        default_mode="operations",
        path="/graph" if node_id is None else f"/graph/{node_id}",
    )
    if failure is not None:
        return failure

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
        )
        return "Graph", body, 200

    if node_id is not None and node_id in view.node_map:
        incoming, outgoing = _edges_for(view, node_id)
        title = view.node_map[node_id].title
        neighbours = []
        for edge in outgoing:
            neighbours.append(
                [
                    _esc(view.titles.get(edge.target) or edge.target),
                    _esc(edge.edge_type),
                    "yes" if edge.active else "no",
                ]
            )
        for edge in incoming:
            neighbours.append(
                [
                    _esc(view.titles.get(edge.source) or edge.source),
                    _esc(edge.edge_type),
                    "yes" if edge.active else "no",
                ]
            )
        ancestors = _ancestors(view, node_id)
        ancestor_rows = "".join(
            f'<li><a href="/nodes/{_esc(a)}">'
            f"{_esc(view.titles.get(a) or a)}</a></li>\n" for a in ancestors
        )
        body = (
            head
            + section(
                title,
                "The selected skill, its immediate relationships, and its "
                "full prerequisite ancestry.",
                '<h3>Immediate relationships</h3>\n'
                + (
                    _table(
                        ["Related skill", "Relationship", "Affects readiness"],
                        neighbours,
                    )
                    if neighbours
                    else '<div class="state state-empty"><p class="state-title">'
                    "No relationships</p><p class=\"state-body\">This skill has no "
                    "incoming or outgoing relationships in the edge table.</p></div>"
                ),
                frame=INLINE,
            )
            + section(
                "",
                "",
                "<h3>Full prerequisite ancestry</h3>\n"
                + (
                    f'<ul class="history-list">{ancestor_rows}</ul>'
                    if ancestors
                    else '<div class="state state-empty"><p class="state-title">'
                    "No prerequisites</p><p class=\"state-body\">Nothing stands "
                    "between this skill and being ready.</p></div>"
                ),
                frame=NONE,
            )
        )
        return title, body, 200

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">Every skill</h2>\n'
        + '<p class="section-meta">The complete list equivalent — every node '
        "with its current state and its prerequisite context.</p>\n"
        + "</div>\n"
        + f"{_node_rows(view, view.edges)}"
        + "</section>\n"
        + '<section class="section">\n'
        + "<h2 class=\"section-title\">Every relationship</h2>\n"
        + f"{_edge_rows(view)}"
        + "</section>\n"
    )
    return "Graph", body, 200
