"""Pure retention-model derivation (Tier 2).

The retention model is a read-only overlay on the existing review system:
it recomputes per-node memory state from review history + the policy seed
and never writes. Per ``docs/spec-tier2-retention-analytics.md`` §1 and
the G-Storage decision, all values are derived on demand, never stored,
and the engine never reads ``data/skilltrace.db``.

The math is the policy seed's exponential decay with multiplicative
updates:

* anchor = last completed review date, or the pass date if no post-pass
  completion exists (cancelled reviews contribute nothing)
* half-life starts at ``default_half_life_days`` and is multiplied by
  ``satisfactory_growth_factor`` (satisfactory) or
  ``unsatisfactory_reduction_factor`` (unsatisfactory) on each
  completed review, in history order
* retention confidence ``R(t) = 0.5^(t / h)`` where ``t = (today - anchor).days``
* suggested next review = anchor + current half-life (or pass date +
  default half-life when the pass-date fallback anchor applies)
* below threshold = ``R(t) < attention_threshold`` OR suggested date
  has arrived

The derivation takes ``today`` as a required keyword argument so tests
can pin the clock (T-Clock D1). The CLI layer is the only
``datetime.date.today()`` call site; the export's rebuild pass is the
documented exception (it runs once per ``export sqlite`` and is the
mirror's only allowed reader of the formula).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from ..execution.reviews import Review
from ..graph.state import ProgressEntry

# States the retention model derives memory state for (per spec §5.2).
RETAINED_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass(frozen=True)
class RetentionPolicySeed:
    """The four numeric seeds of the decay model, validated by ``validate policy``."""

    default_half_life_days: float
    satisfactory_growth_factor: float
    unsatisfactory_reduction_factor: float
    attention_threshold: float


@dataclass(frozen=True)
class MemoryState:
    """One node's retention picture at read time — never persisted."""

    node_id: str
    asserted_state: str
    anchor_kind: str  # "last_completed_review" or "pass"
    anchored_at: date
    half_life_days: float
    confidence: float
    suggested_next_review: date
    below_threshold: bool

    @property
    def has_completed_reviews(self) -> bool:
        return self.anchor_kind == "last_completed_review"


def _parse_iso_date(value: str | None) -> date | None:
    """Parse a stored ISO date/timestamp string into a ``date``.

    Returns ``None`` for missing or unparseable values so callers can fall
    through to the pass-date anchor (G-Rating D2).
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def pass_date_for_entry(entry: ProgressEntry | None) -> date | None:
    """Extract the pass date from a progress entry's transitions.

    Public so the CLI handler and the SQLite export's rebuild pass can
    read the same value without re-implementing the parsing or reaching
    into the entry's private mapping.
    """
    if entry is None or not entry.transitions:
        return None
    return _parse_iso_date(entry.transitions.get("passed"))


# Backward-compat alias for the previous private name; new code should use
# ``pass_date_for_entry`` directly.
_pass_date = pass_date_for_entry


def _completed_reviews_for_node(
    reviews: Iterable[Review], node_id: str
) -> list[Review]:
    """The completed reviews for one node, in created_at order (oldest first).

    Sort is stable and explicit so multiplier application is deterministic
    regardless of how the loader returned the records.
    """
    items = [r for r in reviews if r.node_id == node_id and r.status == "completed"]
    items.sort(key=lambda r: (r.created_at, r.id))
    return items


def _anchor_and_half_life(
    completed: list[Review],
    pass_at: date | None,
    seed: RetentionPolicySeed,
    today: date,
) -> tuple[date, str, float]:
    """Return (anchor_date, anchor_kind, half_life) for a node.

    Per G-Rating D2: anchor on the last completed review if any post-pass
    completion exists, otherwise fall back to the pass date at the default
    half-life. Cancelled reviews contribute nothing.
    """
    half_life = seed.default_half_life_days
    anchor: date | None = None
    for review in completed:
        completed_at = _parse_iso_date(review.completed_at)
        if completed_at is None:
            continue
        anchor = completed_at
        if review.outcome == "satisfactory":
            half_life *= seed.satisfactory_growth_factor
        elif review.outcome == "unsatisfactory":
            half_life *= seed.unsatisfactory_reduction_factor
        # Unknown outcomes are ignored — the binary enum is closed (CONTEXT.md).

    if anchor is not None:
        return anchor, "last_completed_review", half_life

    if pass_at is not None:
        return pass_at, "pass", seed.default_half_life_days

    # No pass date and no completed reviews — the node shouldn't be in this
    # view at all, but the function still returns a sane default so the
    # caller can render an empty/zero confidence picture if it asks.
    return today, "pass", seed.default_half_life_days


def compute_memory_state(
    node_id: str,
    *,
    asserted_state: str,
    pass_at: date | None,
    reviews: Iterable[Review],
    seed: RetentionPolicySeed,
    today: date,
) -> MemoryState:
    """Derive one node's memory state from review history and the policy seed.

    ``today`` is required and the only clock input. No module-level
    default, no ``datetime.now()`` call in this module.
    """
    completed = _completed_reviews_for_node(reviews, node_id)
    anchor_at, anchor_kind, half_life = _anchor_and_half_life(
        completed, pass_at, seed, today
    )
    elapsed = (today - anchor_at).total_seconds() / 86400.0
    confidence = 0.5 ** (elapsed / half_life) if half_life > 0 else 0.0
    suggested_next_review = anchor_at + timedelta(days=int(half_life))
    below_threshold = (
        confidence < seed.attention_threshold
        or suggested_next_review <= today
    )
    return MemoryState(
        node_id=node_id,
        asserted_state=asserted_state,
        anchor_kind=anchor_kind,
        anchored_at=anchor_at,
        half_life_days=half_life,
        confidence=confidence,
        suggested_next_review=suggested_next_review,
        below_threshold=below_threshold,
    )


def retention_seed_from_doc(doc: dict) -> RetentionPolicySeed:
    """Materialize a ``RetentionPolicySeed`` from a loaded policy document.

    ``validate policy`` already enforces the value ranges; this is a
    plain construction for callers that want the typed object. The
    umbrella validator's checks are the contract; this function trusts
    whatever it is given (the test suite uses it to exercise the math
    with non-default seeds).
    """
    return RetentionPolicySeed(
        default_half_life_days=float(doc["default_half_life_days"]),
        satisfactory_growth_factor=float(doc["satisfactory_growth_factor"]),
        unsatisfactory_reduction_factor=float(doc["unsatisfactory_reduction_factor"]),
        attention_threshold=float(doc["attention_threshold"]),
    )


def derive_memory_states(
    *,
    nodes: Iterable,
    store,
    reviews: Iterable[Review],
    seed: RetentionPolicySeed,
    today: date,
) -> list[MemoryState]:
    """Derive memory state for every passed/mastered node in a joined view.

    One helper used by ``retention status`` (CLI), ``suggest reviews``
    (CLI), and the SQLite mirror's rebuild pass — the live surfaces and
    the disposable mirror share the formula by construction (spec §1.3).

    ``nodes`` is any iterable of objects that expose ``.id`` (e.g.
    ``SkillNode``). ``store`` exposes ``.entries`` and ``.state_of``.
    Only nodes whose progress state is in ``RETAINED_STATES`` are
    included in the result.
    """
    states: list[MemoryState] = []
    for node in nodes:
        entry = store.entries.get(node.id)
        state_name = entry.state if entry is not None else store.state_of(node.id)
        if state_name not in RETAINED_STATES:
            continue
        states.append(
            compute_memory_state(
                node.id,
                asserted_state=state_name,
                pass_at=pass_date_for_entry(entry),
                reviews=reviews,
                seed=seed,
                today=today,
            )
        )
    return states
