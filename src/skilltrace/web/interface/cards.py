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
from typing import Literal, get_args

from ...mentor.cards import NextAction

# The five canonical state words (P3.4) — the only values a rendered Card's
# ``state`` may carry. UI synonyms are a construction-time refusal, not a
# render-time normalization.
CANONICAL_STATES: frozenset[str] = frozenset(
    {"locked", "available", "active", "passed", "mastered"}
)

# The state chip pairing (P3.4 + spec §C-bis "Card anatomy"): the canonical
# state word with its plain-language discovery label — one map beside the
# words it pairs, no glossary fork. The discovery anatomy in ``render`` reads
# it for the pill (#319), so the label has exactly one home and the chip can
# never drift from the five canonical words.
CHIP_LABELS: dict[str, str] = {
    "available": "Ready to start",
    "active": "In progress",
    "locked": "Locked",
    "passed": "Passed",
    "mastered": "Mastered",
}


class SublayerError(Exception):
    """The sublayer is inconsistent; serve refuses to start.

    Defined here (the Richer Card's module) so both the declarations and
    the validators raise the one error type without an import cycle.
    """


@dataclass(frozen=True)
class Affordance:
    """A rendered affordance: intent + label + optional write binding.

    ``label`` is human copy filled from the intent's affordance label
    (:func:`interface.affordances.intent_label`) — **never** derived from a
    command string. ``binding`` is the ``NextAction`` fact the affordance
    renders from; its ``command`` field is the CLI's presentation and is
    carried for the write path only, never rendered.
    """

    intent: str
    label: str
    binding: NextAction | None = None

    def __post_init__(self) -> None:
        from ...mentor.cards import Intent

        if self.intent not in get_args(Intent):
            raise SublayerError(
                f"affordance intent {self.intent!r} is outside the closed "
                "Intent set — grow the contract in mentor.cards, never by "
                "string-typing"
            )
        if not self.label.strip():
            raise SublayerError(
                f"affordance intent {self.intent!r} carries no human label"
            )

    @classmethod
    def from_intent(
        cls,
        intent: str,
        *,
        binding: NextAction | None = None,
        title: str | None = None,
    ) -> "Affordance":
        """The affordance for one fact intent — the label derives from the
        intent only (never from ``binding.command``)."""
        from .affordances import intent_label

        return cls(
            intent=intent,
            label=intent_label(intent, title=title),
            binding=binding,
        )


@dataclass(frozen=True)
class Card:
    """The Richer Card (v2.4 §E) — minimum fields, no second vocabulary.

    Minimum fields, enforced at construction (a Card missing any of them
    is a :class:`SublayerError`, never a degraded render): ``state`` (one
    of the five canonical words), ``title``, one-line ``why``,
    ``resources`` (non-empty), and exactly **one** next action expressed
    as an intent + affordance. ``disclosure`` is the optional one-click
    facts; ``kicker`` is the card's section opener chrome; ``node_id`` is
    muted secondary text on detail pages only.
    """

    state: str
    title: str
    why: str
    resources: list[str] = field(default_factory=list)
    affordances: tuple[Affordance, ...] = ()
    disclosure: str | None = None
    kicker: str | None = None
    node_id: str | None = None

    def __post_init__(self) -> None:
        if self.state not in CANONICAL_STATES:
            raise SublayerError(
                f"card state {self.state!r} is not one of the five canonical "
                "state words (P3.4): " + ", ".join(sorted(CANONICAL_STATES))
            )
        if not self.title.strip():
            raise SublayerError("card carries no title")
        if not self.why.strip():
            raise SublayerError(f"card {self.title!r} carries no one-line why")
        if not any(line.strip() for line in self.resources):
            raise SublayerError(f"card {self.title!r} carries no resources")
        if len(self.affordances) != 1:
            raise SublayerError(
                f"card {self.title!r} must carry exactly one next action "
                f"(intent + affordance); got {len(self.affordances)}"
            )


@dataclass(frozen=True)
class View:
    """A declared page: frozen route, title, affordance set, nav group.

    ``group`` is the section the destination is a nav stop of — ``guided``
    (the task-led study day) or ``operations`` (the capability directory)
    — or ``None`` for pages that are not nav stops (node detail, the
    session cockpit, the safety panels).

    ``default_mode`` is the presentation mode a **bare deep link** renders
    (spec-v3-study-day IA-1): mode rides a URL parameter, so a link
    without one must still land on a sensible presentation.
    """

    name: str
    route: str
    title: str
    group: Literal["guided", "operations"] | None
    affordances: tuple[str, ...] = ()
    default_mode: Literal["guided", "operations"] = "guided"


# The frozen route table (spec-v3-study-day §6, normative): declared views
# with their routes. Paths are frozen verbatim — a view whose route drifts
# from this table is a boot failure, not a silent 404. The table is flat and
# mode-neutral: a destination exists once, and mode is presentation context
# carried by a URL parameter, never by a path prefix.
#
# The view *name* is the screen identity; the route is where it lives. The
# name is never derived from the path and the path is never derived from the
# name.
VIEWS: dict[str, View] = {
    view.name: view
    for view in (
        View(
            name="today",
            route="/",
            title="Today",
            group="guided",
            affordances=("start",),
        ),
        View(name="next", route="/next", title="Next", group="guided"),
        View(name="find", route="/find", title="Find a skill", group="guided"),
        View(
            name="reviews",
            route="/reviews",
            title="Reviews",
            group="guided",
            affordances=("review schedule", "review complete", "review cancel"),
        ),
        View(name="node", route="/nodes/{id}", title="This skill", group=None),
        View(
            name="session",
            route="/session",
            title="Study",
            group=None,
            affordances=(
                "start",
                "work",
                "session close",
                "blocker create",
                "blocker resolve",
                "evidence submit",
            ),
        ),
        View(
            name="session-close",
            route="/session/close",
            title="Close session",
            group=None,
            affordances=("session close",),
        ),
        View(
            name="node-pass",
            route="/nodes/{id}/pass",
            title="Mark passed",
            group=None,
            affordances=("pass",),
        ),
        View(
            name="node-master",
            route="/nodes/{id}/master",
            title="Mark mastered",
            group=None,
            affordances=("master",),
        ),
        View(
            name="master-confirm",
            route="/nodes/{id}/master/confirm",
            title="Confirm mastery",
            group=None,
            affordances=("master",),
        ),
        View(
            name="evidence",
            route="/nodes/{id}/evidence",
            title="Evidence",
            group=None,
            affordances=("evidence submit",),
        ),
        View(
            name="evidence-index",
            route="/evidence",
            title="Evidence",
            group="operations",
            default_mode="operations",
        ),
        View(
            name="operations",
            route="/operations",
            title="Operations",
            group="operations",
            default_mode="operations",
        ),
        View(
            name="graph",
            route="/graph",
            title="Graph",
            group="operations",
            default_mode="operations",
        ),
        View(
            name="health",
            route="/health",
            title="Health",
            group="operations",
            affordances=("sync",),
            default_mode="operations",
        ),
        View(
            name="analytics",
            route="/analytics",
            title="Analytics",
            group="operations",
            affordances=("analytics export",),
            default_mode="operations",
        ),
        View(
            name="portfolio",
            route="/portfolio",
            title="Portfolio",
            group="operations",
            affordances=("portfolio export",),
            default_mode="operations",
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
