"""
Derived readiness — the stale check, in one place.

A node's *readiness* (``locked`` / ``available``) is derived from the
curriculum graph, not asserted by the learner (CONTEXT.md "Derived
readiness"). The progress store keeps the last computed value, so a
curriculum edit made since that computation leaves the saved value out of
date: the saved readiness of some node no longer matches what the graph
says today.

:func:`stale_readiness` answers exactly that question — *which skills may
be shown with the wrong readiness?* — by asking the engine's own
:func:`~skilltrace.graph.readiness.derive_readiness` what each node's
readiness **would** be and comparing it with what is saved.

Why one module: ``/next``, ``/`` (Today) and ``/find`` all report stale
readiness, and they must never disagree about which skills are affected.
The rule lives here once; every surface reads it.

Asserted progress (``active`` / ``passed`` / ``mastered``) is never
compared. A refresh recomputes readiness; it never moves asserted
progress backward (HB-3), so a stale readiness never puts a started or
finished skill back in the queue.
"""

from __future__ import annotations

from ...graph.readiness import derive_readiness
from ...graph.state import ASSERTED_STATES
from ._shared import _esc, plural


def hard_prerequisite_sources(edges) -> dict[str, list[str]]:
    """Map each node id to the sources of its active hard-prerequisite edges.

    Only ``active`` ``hard_prerequisite`` edges index a lock — soft and
    remediation edges, and parked (inactive) hard edges, never lock a node.
    """
    sources: dict[str, list[str]] = {}
    for edge in edges:
        if edge.active and edge.edge_type == "hard_prerequisite":
            sources.setdefault(edge.target, []).append(edge.source)
    return sources


def stale_readiness(view) -> list[str]:
    """The node ids whose **saved** readiness no longer matches the curriculum.

    The readiness rule is the engine's, not a page's: the page asks the
    engine what each skill's readiness *would* be and compares it with
    what is saved. Asserted progress is never compared — a refresh never
    moves it.

    Returns the affected node ids, sorted, so two surfaces reading this
    helper report the same set in the same order.
    """
    sources = hard_prerequisite_sources(view.edges)
    stale: list[str] = []
    for node in view.nodes:
        current = view.store.state_of(node.id)
        if current in ASSERTED_STATES:
            continue
        if derive_readiness(node.id, sources, view.store) != current:
            stale.append(node.id)
    return sorted(stale)


def every_skill_locked(view) -> bool:
    """True when every not-yet-finished skill's *derived* readiness is locked.

    Readiness is derived from the curriculum, so this is the truth about
    whether anything can be started — not what a possibly stale store
    says. Asserted progress (``active`` / ``passed`` / ``mastered``) is
    excluded: a finished skill is finished, not waiting.
    """
    sources = hard_prerequisite_sources(view.edges)
    unfinished = 0
    locked = 0
    for node in view.nodes:
        if view.store.state_of(node.id) in ASSERTED_STATES:
            continue
        unfinished += 1
        if derive_readiness(node.id, sources, view.store) == "locked":
            locked += 1
    return unfinished > 0 and locked == unfinished


def stale_readiness_section(view, *, reload_href: str, reload_label: str) -> str:
    """The stale-readiness recovery section — one wording for every surface.

    Returns the whole ``<section>`` frame, not just the state inside it, so
    a surface places it like any other section of the page. Empty when
    nothing is stale.

    The dependency is **named, never hidden behind silence**: refreshing
    readiness happens on the command line, this page never changes saved
    readiness, and a refresh never moves asserted progress. ``reload_href``
    and ``reload_label`` are the surface's own way back (``/next`` reloads
    its list; Today and Find reload the page).
    """
    stale = stale_readiness(view)
    if not stale:
        return ""
    return (
        '<section class="section">\n'
        '<div class="state state-recovery">\n'
        '<p class="state-title">Your saved readiness is out of date</p>\n'
        '<p class="state-body">The curriculum changed since your '
        f"readiness was last computed, so {len(stale)} skill"
        f"{plural(len(stale))} may be shown as locked or available "
        "incorrectly. Refreshing readiness happens on the command line — "
        "this page never changes your saved readiness, and a refresh never "
        "moves your recorded progress: active, passed and mastered stay "
        "exactly as they are.</p>\n"
        '<p class="state-body">Refresh your readiness, then '
        f'<a href="{_esc(reload_href)}">{_esc(reload_label)}</a>.</p>\n'
        "</div>\n"
        "</section>\n"
    )
