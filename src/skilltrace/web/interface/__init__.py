"""The web presentation sublayer.

The page layer (``web.views``) reads *out* through the dispatcher registry and
*in* through this package and nothing else. Modules here may not import the
page layer or the cli at module level — ``commands.register_all`` lazily loads
the web presentation while the cli builds its registry, so a module-level
import in either direction is a cycle.

Boot contract: the sublayer's structure validates at import (unresolvable
view/command/affordance bindings raise there); the full binding check against
the live dispatcher registry and the frozen route table runs in
``validate_interface``, which ``serve`` calls before it binds — an inconsistent
sublayer refuses to start.
"""

from __future__ import annotations

from .affordances import COMMAND_AFFORDANCE_LABELS, intent_label
from .cards import CANONICAL_STATES, ActiveViewState, Affordance, VIEWS, Card, SublayerError, View, view_by_name
from .render import banner_html, render_rich_cards
from .translate import (
    banners,
    forbidden_in_lines,
    forbidden_matches,
    rich_cards,
    translate,
    translate_lines,
)

__all__ = [
    "CANONICAL_STATES",
    "COMMAND_AFFORDANCE_LABELS",
    "ActiveViewState",
    "Affordance",
    "Card",
    "SublayerError",
    "View",
    "VIEWS",
    "banner_html",
    "banners",
    "forbidden_in_lines",
    "forbidden_matches",
    "intent_label",
    "render_rich_cards",
    "rich_cards",
    "translate",
    "translate_lines",
    "validate_interface",
    "view_by_name",
]


def _validate_at_import() -> None:
    """Structural validation, run at import.

    Checks the sublayer's internal consistency only: every card's view-binding
    must name a declared view, and every declared intent must carry a human
    affordance label. Binding checks against the live dispatcher registry and
    the frozen route table are ``validate_interface``'s job (serve boot).
    """
    from .validate import SublayerError, validate_structure

    try:
        validate_structure()
    except SublayerError as exc:  # pragma: no cover - defensive
        raise SublayerError(str(exc)) from exc


_validate_at_import()


def validate_interface(registry) -> list[str]:
    """Full sublayer check: structure + dispatcher registry bindings.

    Called by ``serve`` before it binds (an inconsistent sublayer refuses to
    start) and by the tests. ``registry`` is the live dispatcher registry the
    serve shell built. Returns the list of problems found; an empty list means
    the sublayer is consistent.
    """
    from .validate import validate_interface as _validate

    return _validate(registry)
