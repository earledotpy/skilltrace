"""The placeholder body — a destination that exists but has no surface yet.

SL1 of the v3 build gives every destination in the normative route table
(docs/spec-v3-study-day.md §6) a URL that renders, so the route contract
has exactly one source of truth from the moment it is adopted. A
destination still awaiting its own slice renders this placeholder: an
honest "not built yet" state, never a fake screen that looks like a real
one.

Each surface's own slice replaces this body with the real screen; the
placeholder disappears with it (MIG-1 — the replaced surface's code dies in
the slice that replaces it).
"""

from __future__ import annotations

from ._shared import _esc
from .shell import _page_head


def placeholder_body(
    root,
    query: dict | None,
    *,
    title: str,
    view_name: str,
    what: str,
) -> tuple[str, str, int]:
    """One placeholder destination: the shell plus an honest empty state."""
    view, head, failure = _page_head(root, query, current_view=view_name)
    if failure is not None:
        return failure
    body = (
        head
        + '<section class="section">\n'
        + '<div class="state state-empty">\n'
        + f'<p class="state-title">{_esc(title)} is not built yet</p>\n'
        + f'<p class="state-body">{_esc(what)}</p>\n'
        + '<p class="state-body">This destination exists so the route table has one '
        "source of truth. Its screen arrives with the slice that owns it.</p>\n"
        + "</div>\n"
        + "</section>\n"
    )
    return title, body, 200
