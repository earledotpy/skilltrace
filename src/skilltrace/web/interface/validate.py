"""Sublayer validation — structure at import, bindings at serve boot.

``validate_structure`` (import time) checks internal consistency only:
every declared intent carries a human affordance label, every declared view
names a nav group that exists, and every declared affordance intent is a
``mentor.cards`` ``Intent`` literal (string-typed intents are a bug — the
contract grows by editing it, never by string-typing).

``validate_interface`` (serve boot) adds the binding checks: every view's
affordance set must name a registered dispatcher command, and every declared
view's route must match the frozen route table (``docs/spec-v3-study-day.md``
§6 — the normative table). An inconsistent sublayer refuses to start.
"""

from __future__ import annotations

from .cards import SublayerError  # re-exported: the one sublayer error type

__all__ = ["FROZEN_ROUTES", "SublayerError", "validate_structure", "validate_interface"]

# The frozen route table (docs/spec-v3-study-day.md §6, normative): view name
# → frozen route. The table is **flat and mode-neutral**: seventeen
# destinations, each existing exactly once, and mode is presentation context
# carried by a URL parameter — never a path prefix. Paths are frozen
# verbatim; a view whose route drifts from this table is a boot failure, not
# a silent 404.
#
# The table supersedes the v2.4 §C table by declaration (spec §20 SUP-2);
# the historical file keeps its history and is not edited.
FROZEN_ROUTES: dict[str, str] = {
    "today": "/",
    "next": "/next",
    "find": "/find",
    "node": "/nodes/{id}",
    "session": "/session",
    "session-close": "/session/close",
    "node-pass": "/nodes/{id}/pass",
    "node-master": "/nodes/{id}/master",
    "master-confirm": "/nodes/{id}/master/confirm",
    "evidence": "/nodes/{id}/evidence",
    "evidence-index": "/evidence",
    "reviews": "/reviews",
    "operations": "/operations",
    "graph": "/graph",
    "health": "/health",
    "analytics": "/analytics",
    "portfolio": "/portfolio",
}


def validate_structure() -> None:
    """Internal consistency (import time). Raises :class:`SublayerError`."""
    from typing import get_args

    # Every fact intent carries a human affordance label (the rendered
    # vocabulary — a fact's ``command`` string is never web-rendered).
    from ...mentor.cards import Intent
    from .affordances import (
        COMMAND_AFFORDANCE_LABELS,
        FACT_AFFORDANCE_LABELS,
    )
    from .cards import VIEWS

    for intent in get_args(Intent):
        if intent not in FACT_AFFORDANCE_LABELS:
            raise SublayerError(
                f"fact intent {intent!r} carries no human affordance label — "
                "add one to FACT_AFFORDANCE_LABELS"
            )

    for view in VIEWS.values():
        if view.group is not None and view.group not in ("guided", "operations"):
            raise SublayerError(
                f"view {view.name!r} names unknown nav group {view.group!r}"
            )
        if view.default_mode not in ("guided", "operations"):
            raise SublayerError(
                f"view {view.name!r} names unknown default mode {view.default_mode!r}"
            )
        for command in view.affordances:
            if command not in COMMAND_AFFORDANCE_LABELS:
                raise SublayerError(
                    f"view {view.name!r} affordance {command!r} carries no "
                    "human label — add one to COMMAND_AFFORDANCE_LABELS"
                )


def validate_interface(registry) -> list[str]:
    """Full check (serve boot): structure + registry bindings.

    ``registry`` is the live dispatcher registry (the serve shell builds it
    before calling). Returns the list of problems; empty = consistent.
    """
    from .affordances import COMMAND_AFFORDANCE_LABELS
    from .cards import VIEWS

    problems: list[str] = []
    try:
        validate_structure()
    except SublayerError as exc:
        problems.append(str(exc))
        return problems

    registered = set(registry.names())

    for name, frozen_route in FROZEN_ROUTES.items():
        view = VIEWS.get(name)
        if view is None:
            problems.append(
                f"frozen route {frozen_route!r} has no declared view {name!r} — "
                "the view table is incomplete against docs/spec-v3-study-day.md §6"
            )
            continue
        if view.route != frozen_route:
            problems.append(
                f"view {name!r} route {view.route!r} drifts from the frozen "
                f"table {frozen_route!r} (docs/spec-v3-study-day.md §6 — "
                "paths are frozen verbatim)"
            )
    for name in VIEWS:
        if name not in FROZEN_ROUTES:
            problems.append(
                f"view {name!r} is not in the frozen route table "
                "(docs/spec-v3-study-day.md §6 — new views only where the "
                "normative table names them)"
            )

    for view in VIEWS.values():
        for command in view.affordances:
            if command not in COMMAND_AFFORDANCE_LABELS:
                problems.append(
                    f"view {view.name!r} affordance {command!r} carries no human label"
                )
                continue
            if command not in registered:
                problems.append(
                    f"view {view.name!r} affordance {command!r} binds no "
                    "registered dispatcher command — the write path is dead"
                )
    return problems
