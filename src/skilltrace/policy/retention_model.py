"""Pure retention-model derivation (Tier 2 + v2.1 adaptive sequencing overlay).

The retention model is a read-only overlay on the existing review system:
it recomputes per-node memory state from review history + the policy seed
and never writes. Per ``docs/spec-tier2-retention-analytics.md`` §1 and the
G-Storage decision, all values are derived on demand, never stored, and the
engine never reads ``data/skilltrace.db``.

The math is the policy seed's exponential decay with multiplicative
updates using **delay-aware multipliers** (v2.1):

* anchor = last completed review date, or the pass date if no post-pass
  completion exists (cancelled reviews contribute nothing)
* half-life starts at ``default_half_life_days`` scaled by a per-node base
  scale (domain grouping + evidence-coverage + study-velocity modifiers),
  then multiplied by a delay-bucket multiplier on each completed review:
  the multiplier depends on ``(completed_at - scheduled_for).days``
  bucketed as early/on-time/late × the binary outcome. When no delay table
  is seeded the flat ``satisfactory_growth_factor`` /
  ``unsatisfactory_reduction_factor`` fallback reproduces Tier 2 exactly
  (on-time reviews are the strict superset's base case).
* retention confidence ``R(t) = 0.5^(t / h)`` where ``t = (today - anchor).days``
* suggested next review = anchor + current half-life (or pass date +
  default half-life when the pass-date fallback anchor applies)
* below threshold = ``R(t) < attention_threshold`` OR suggested date
  has arrived

The derivation takes ``today`` as a required keyword argument so tests can
pin the clock (T-Clock D1). The CLI layer is the only
``datetime.date.today()`` call site; the export's rebuild pass is the
documented exception (it runs once per ``export sqlite`` and is the
mirror's only allowed reader of the formula).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable, Iterable

from ..execution.records import Review
from ..graph.state import ProgressEntry

# States the retention model derives memory state for (per spec §5.2).
RETAINED_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass(frozen=True)
class RetentionPolicySeed:
    """The decay model's numeric seeds, validated by ``validate policy``.

    ``delay_aware_multipliers`` is the v2.1 delay-bucket table
    (``bucket -> outcome -> multiplier``). When ``None`` the flat
    ``satisfactory_growth_factor`` / ``unsatisfactory_reduction_factor``
    fallback is used, which treats every completed review as on-time and
    reproduces Tier 2 exactly. ``domain_half_life_scales`` and the two
    analytics scales default to 1.0 (no-op) so existing callers that do not
    supply analytics inputs keep their exact behaviour.
    """

    default_half_life_days: float
    satisfactory_growth_factor: float = 2.0
    unsatisfactory_reduction_factor: float = 0.5
    attention_threshold: float = 0.5
    delay_aware_multipliers: dict[str, dict[str, float]] | None = None
    on_time_window_days: int = 2
    domain_half_life_scales: dict[str, float] = field(default_factory=dict)
    low_velocity_scale: float = 1.0
    incomplete_evidence_scale: float = 1.0
    min_half_life_days: float = 1.0
    max_half_life_days: float = 365.0


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


def _node_prefix(node_id: str) -> str:
    """The dot-delimited prefix (first two segments) of a node ID.

    ``math.arithmetic.order_operations_01`` -> ``math.arithmetic``. For IDs
    with fewer than two segments the whole ID is returned. This is the key
    used for ``domain_half_life_scales`` grouping.
    """
    parts = node_id.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else node_id


def _delay_days(review: Review) -> int:
    """Days between a completed review and its scheduled date (0 on unknown)."""
    completed = _parse_iso_date(review.completed_at)
    scheduled = _parse_iso_date(review.scheduled_for) if isinstance(review.scheduled_for, str) else None
    if completed is None or scheduled is None:
        return 0
    return (completed - scheduled).days


def _multiplier(review: Review, seed: RetentionPolicySeed) -> float:
    """The per-review half-life multiplier (delay-aware table or flat fallback)."""
    if seed.delay_aware_multipliers is not None:
        delay = _delay_days(review)
        if delay < -seed.on_time_window_days:
            bucket = "early"
        elif delay > seed.on_time_window_days:
            bucket = "late"
        else:
            bucket = "on_time"
        row = seed.delay_aware_multipliers.get(bucket) or {}
        return float(row.get(review.outcome, 1.0))
    if review.outcome == "satisfactory":
        return seed.satisfactory_growth_factor
    if review.outcome == "unsatisfactory":
        return seed.unsatisfactory_reduction_factor
    # Unknown outcomes are ignored — the binary enum is closed (CONTEXT.md).
    return 1.0


def _clamp_half_life(value: float, seed: RetentionPolicySeed) -> float:
    """Bound half-life to the seed's [min, max] window for sane math."""
    return min(max(value, seed.min_half_life_days), seed.max_half_life_days)


def _anchor_and_half_life(
    completed: list[Review],
    pass_at: date | None,
    seed: RetentionPolicySeed,
    today: date,
    base_scale: float = 1.0,
) -> tuple[date, str, float]:
    """Return (anchor_date, anchor_kind, half_life) for a node.

    Per G-Rating D2: anchor on the last completed review if any post-pass
    completion exists, otherwise fall back to the pass date at the default
    half-life. Cancelled reviews contribute nothing. ``base_scale`` folds
    the domain/coverage/velocity modifiers onto the default half-life.
    """
    half_life = _clamp_half_life(seed.default_half_life_days * base_scale, seed)
    anchor: date | None = None
    for review in completed:
        completed_at = _parse_iso_date(review.completed_at)
        if completed_at is None:
            continue
        anchor = completed_at
        half_life *= _multiplier(review, seed)
        half_life = _clamp_half_life(half_life, seed)

    if anchor is not None:
        return anchor, "last_completed_review", half_life

    if pass_at is not None:
        return pass_at, "pass", _clamp_half_life(seed.default_half_life_days * base_scale, seed)

    # No pass date and no completed reviews — the node shouldn't be in this
    # view at all, but the function still returns a sane default so the
    # caller can render an empty/zero confidence picture if it asks.
    return today, "pass", _clamp_half_life(seed.default_half_life_days * base_scale, seed)


def compute_memory_state(
    node_id: str,
    *,
    asserted_state: str,
    pass_at: date | None,
    reviews: Iterable[Review],
    seed: RetentionPolicySeed,
    today: date,
    base_scale: float = 1.0,
) -> MemoryState:
    """Derive one node's memory state from review history and the policy seed.

    ``today`` is required and the only clock input. No module-level
    default, no ``datetime.now()`` call in this module. ``base_scale`` is
    the per-node modifier (domain + analytics) folded onto the default
    half-life; it defaults to 1.0 so callers that supply none reproduce the
    Tier 2 formula exactly.
    """
    completed = _completed_reviews_for_node(reviews, node_id)
    anchor_at, anchor_kind, half_life = _anchor_and_half_life(
        completed, pass_at, seed, today, base_scale
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


def _base_scale(
    node,
    seed: RetentionPolicySeed,
    evidence_gaps,
    sessions_per_domain,
    min_domain_sessions: int | None,
    domain_of,
) -> float:
    """Folded per-node half-life modifier (domain + analytics), default 1.0."""
    scale = seed.domain_half_life_scales.get(_node_prefix(node.id), 1.0)
    if evidence_gaps and node.id in evidence_gaps:
        scale *= seed.incomplete_evidence_scale
    if min_domain_sessions is not None and sessions_per_domain is not None:
        dom = domain_of(node) if domain_of else None
        if not dom:
            dom = _node_prefix(node.id)
        if sessions_per_domain.get(dom, 0) < min_domain_sessions:
            scale *= seed.low_velocity_scale
    return scale


def retention_seed_from_doc(doc: dict) -> RetentionPolicySeed:
    """Materialize a ``RetentionPolicySeed`` from a loaded policy document.

    ``validate policy`` already enforces the value ranges; this is a
    plain construction for callers that want the typed object. The
    umbrella validator's checks are the contract; this function trusts
    whatever it is given (the test suite uses it to exercise the math
    with non-default seeds). Missing v2.1 extras fall back to no-op values.
    """
    raw_table = doc.get("delay_aware_multipliers")
    table: dict[str, dict[str, float]] | None = None
    if isinstance(raw_table, dict):
        table = {}
        for bucket in ("early", "on_time", "late"):
            row = raw_table.get(bucket)
            table[bucket] = {
                str(k): float(v)
                for k, v in row.items()
                if k in ("satisfactory", "unsatisfactory")
            } if isinstance(row, dict) else {}
        if not table["on_time"]:
            table = None
    return RetentionPolicySeed(
        default_half_life_days=float(doc["default_half_life_days"]),
        satisfactory_growth_factor=float(doc.get("satisfactory_growth_factor", 2.0)),
        unsatisfactory_reduction_factor=float(doc.get("unsatisfactory_reduction_factor", 0.5)),
        attention_threshold=float(doc.get("attention_threshold", 0.5)),
        delay_aware_multipliers=table,
        on_time_window_days=int(doc.get("on_time_window_days", 2)),
        domain_half_life_scales={
            str(k): float(v)
            for k, v in (doc.get("domain_half_life_scales") or {}).items()
        },
        low_velocity_scale=float(doc.get("low_velocity_scale", 1.0)),
        incomplete_evidence_scale=float(doc.get("incomplete_evidence_scale", 1.0)),
        min_half_life_days=float(doc.get("min_half_life_days", 1.0)),
        max_half_life_days=float(doc.get("max_half_life_days", 365.0)),
    )


def derive_memory_states(
    *,
    nodes: Iterable,
    store,
    reviews: Iterable[Review],
    seed: RetentionPolicySeed,
    today: date,
    evidence_gaps: set[str] | None = None,
    sessions_per_domain: dict[str, int] | None = None,
    min_domain_sessions: int | None = None,
    domain_of: Callable[[object], str] | None = None,
) -> list[MemoryState]:
    """Derive memory state for every passed/mastered node in a joined view.

    One helper used by ``retention status`` (CLI), ``suggest reviews``
    (CLI), and the SQLite mirror's rebuild pass — the live surfaces and
    the disposable mirror share the formula by construction (spec §1.3).

    ``nodes`` is any iterable of objects that expose ``.id`` (e.g.
    ``SkillNode``). ``store`` exposes ``.entries`` and ``.state_of``.
    Only nodes whose progress state is in ``RETAINED_STATES`` are
    included in the result. The optional v2.1 inputs (``evidence_gaps``,
    ``sessions_per_domain`` / ``min_domain_sessions`` / ``domain_of``)
    fold the evidence-coverage and study-velocity modifiers into each
    node's half-life; when omitted they are no-ops (Tier 2 exact).
    """
    states: list[MemoryState] = []
    for node in nodes:
        entry = store.entries.get(node.id)
        state_name = entry.state if entry is not None else store.state_of(node.id)
        if state_name not in RETAINED_STATES:
            continue
        scale = _base_scale(
            node, seed, evidence_gaps, sessions_per_domain, min_domain_sessions, domain_of
        )
        states.append(
            compute_memory_state(
                node.id,
                asserted_state=state_name,
                pass_at=pass_date_for_entry(entry),
                reviews=reviews,
                seed=seed,
                today=today,
                base_scale=scale,
            )
        )
    return states
