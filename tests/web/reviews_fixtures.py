"""The named Reviews states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the **same** named
Reviews states from the same kind of fixture, or a state could be pinned by
one gate and left unchecked by the other. This module owns the mutations
that turn a pinned repo into each state the Reviews contract names
(spec-v3-study-day §10.10, SC-00a):

* ``populated`` — the pinned repo unchanged: overdue, scheduled and
  completed checks plus the advisory group;
* ``empty`` — a one-skill curriculum the learner has **not** passed: no
  review-worthy node exists, so no check could ever watch anything (the
  empty state says why and preserves discovery);
* ``limited`` — a one-skill curriculum the learner **has** passed, with no
  review records: skills a check could watch exist, none is scheduled, and
  the advisory group keeps its values;
* ``derivation-failed`` — the retention model's policy is gone: the
  advisory half claims nothing (could-not-compute, never zeroes) while the
  records — records, not derivations — stay readable.

The single-skill curriculum itself is authored by :mod:`today_fixtures`
(one node, the whole population exact); the pass transition here is
authored fixture data, exactly as the other web suites seed state — no
engine pass/master path runs here (see AGENTS.md safety rule). Dates are
absolute so the fixtures are wall-clock independent, matching the
frozen-clock convention of the suites that consume them.
"""

from __future__ import annotations

from pathlib import Path

from fixture_repo import write_yaml
from today_fixtures import build_today_variant

#: The named Reviews states a fixture can be reshaped into. ``populated``
#: is the pinned repo itself, so it is not a mutation here.
REVIEWS_VARIANTS: tuple[str, ...] = ("empty", "limited", "derivation-failed")

_SINGLE_NODE = "demo.single_01"

#: The pass transition the *limited* fixture authors: a pass eleven days
#: before the suites' frozen day (2026-11-17), so the retention model can
#: anchor on it and derive a suggested check — a real value the limited
#: state retains while the scheduled queue stays empty.
_PASS_TRANSITIONS = {
    "active": "2026-10-25T09:00:00+00:00",
    "passed": "2026-11-06T09:00:00+00:00",
}


def _empty(root: Path) -> Path:
    """No review-worthy node: the one skill is locked, nothing is passed."""
    return build_today_variant(root, "refusal")


def _limited(root: Path) -> Path:
    """A passed skill, no review records: checkable, nothing scheduled."""
    variant = build_today_variant(root, "empty")
    write_yaml(
        variant,
        "graph/state.yaml",
        {
            "progress": {
                _SINGLE_NODE: {
                    "state": "passed",
                    "changed_at": _PASS_TRANSITIONS["passed"],
                    "transitions": _PASS_TRANSITIONS,
                }
            }
        },
    )
    return variant


def _derivation_failed(root: Path) -> Path:
    """The retention model's policy is gone; the records stay readable."""
    variant = _limited(root)
    (variant / "policy" / "retention_model.yaml").unlink()
    return variant


_MUTATIONS = {
    "empty": _empty,
    "limited": _limited,
    "derivation-failed": _derivation_failed,
}


def build_reviews_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one Reviews state.

    The pinned repo itself is never touched; each call materialises a fresh
    temporary copy, so a render is repeatable and the shared fixture stays
    read-only.
    """
    mutation = _MUTATIONS.get(kind)
    if mutation is None:
        raise ValueError(f"unknown Reviews variant: {kind!r}")
    return mutation(pinned)
