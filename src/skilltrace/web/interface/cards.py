"""View / Card / Command / Active-view-state (ADR 0007 + G-RouteSurface).

The sublayer's object vocabulary:

* **View** — a declared page with its frozen route, title and affordance
  set; a view's actions are *facts read from the dispatcher registry*, not
  re-derived (the web never reverse-engineers which action is possible).
* **Card** — a rendered card carrying at minimum ``{state, title, one-line
  why, resources, one next action, optional disclosure}`` (the Richer Card,
  v2.4 §E): ``why`` and ``disclosure`` are first-class fields and the next
  action is expressed as **intent + affordance**, never as a raw command
  string.
* **Command** — a dispatcher command binding: the write path (``POST``
  target), carried but **never rendered**.
* **Active-view-state** — the per-request state: which view is current, the
  active affordance set and the carried flash.

Validation: the structure is checked at import (``validate_structure``) and
the full binding check against the live registry + frozen route table runs in
``validate_interface`` before ``serve`` binds — an inconsistent sublayer
refuses to start.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ...mentor.cards import NextAction


@dataclass(frozen=True)
class Affordance:
    """A rendered affordance: intent + label + optional write binding.

    ``label`` is human copy with ``{title}`` placeholders filled by the
    composers; ``binding`` is the ``NextAction`` fact the affordance renders
    from (never its ``command`` string — that is CLI-printed only).
    """

    intent: str
    label: str
    binding: NextAction | None = None


@dataclass(frozen=True)
class Card:
    """The Richer Card (v2.4 §E) — minimum fields, no second vocabulary."""

    state: str
    title: str
    why: str  # one human sentence — never factor names
    resources: list[str] = field(default_factory=list)
    affordances: tuple[Affordance, ...] = ()
    disclosure: str | None = None  # the optional one-click facts
    node_id: str | None = None  # muted secondary text on detail only


@dataclass(frozen=True)
class View:
    """A declared page: frozen route, title, affordance set, nav group."""

    name: str
    route: str
    title: str
    group: Literal["daily", "diagnostics"] | None
    affordances: tuple[str, ...] = ()


# The frozen route table (G-RouteSurface): declared views with their routes.
# Each view's ``affordances`` name the registered dispatcher commands its
# page's write paths nest-dispatch — validated at serve boot (a dead write
# path refuses to start).
VIEWS: dict[str, View] = {
    view.name: view
    for view in (
        View(
            name="today",
            route="/",
            title="Today",
            group="daily",
            affordances=("start", "work", "session close"),
        ),
        View(name="next", route="/next", title="Next", group="daily"),
        View(name="node", route="/nodes/{id}", title="This skill", group=None),
        View(name="finder", route="/nodes/jump", title="Jump to a skill", group=None),
        View(
            name="health",
            route="/health",
            title="Health",
            group="diagnostics",
            affordances=("sync",),
        ),
        View(name="analytics", route="/analytics", title="Analytics", group="diagnostics"),
        View(
            name="node pass",
            route="/nodes/{id}/pass",
            title="Mark passed",
            group=None,
            affordances=("pass",),
        ),
        View(
            name="node master",
            route="/nodes/{id}/master",
            title="Mark mastered",
            group=None,
            affordances=("master",),
        ),
    )
}


def view_by_name(name: str) -> View:
    """The declared view for one name; unknown names fail loudly."""
    try:
        return VIEWS[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"unknown view {name!r} — declare it in interface.cards") from exc


@dataclass(frozen=True)
class ActiveViewState:
    """The per-request state: current view, affordance set, carried flash."""

    view: View
    affordances: tuple[Affordance, ...] = ()
    flash: tuple[tuple[str, str], ...] = ()
    current_node_id: str | None = None
