"""Discovery matching for the `/nodes/jump` combination surface.

Implements the discovery amendment locked in `docs/spec-tier1-serve.md`
§C-bis (G-SubjectDiscovery #293 · handoff step 4 #297 · built in #310):
subject/track label + title words + a curated synonym seed list are the
primary matchers; node-ID matching (exact or fragment) is secondary only,
never the primary. Synonyms are seed data — this module's curated tables —
not engine stemming, and the web-only discovery surface reads the engine
(JoinedView) and never the reverse (ADR 0007).

Ranking: score first, then available before active before passed/mastered,
locked last — ambiguous queries show every match, never a silent top-1.
Nothing here mutates anything: a discovery card links to the node view and
never implicitly starts, passes, or opens a session.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "ENTRY_NODES",
    "DiscoveryCard",
    "SUBJECT_LABELS",
    "discover",
    "subject_label",
    "subject_of",
]

# --- Curated seed data ---------------------------------------------------------

# Curated synonym seed list: a learner word maps to the node-id prefixes it
# covers. Seed data, not stemming — extending this table is a data edit, not
# an engine change (spec §C-bis "Matching").
SYNONYMS: dict[str, tuple[str, ...]] = {
    "python": ("programming.python.",),
    "sql": ("data.sql.",),
    "pandas": ("data.pandas.",),
    "csv": ("data.csv.",),
    "charts": ("data.visualization.",),
    "algebra": ("math.algebra.",),
    "arithmetic": ("math.arithmetic.",),
    "calculus": ("math.calculus.",),
    "statistics": ("math.statistics.",),
}

# Human labels for the ID-prefix subjects. Unknown prefixes fall back to
# their capitalized form — the map is seed data, not an engine rule.
SUBJECT_LABELS: dict[str, str] = {
    "math": "Math",
    "data": "Data",
    "programming": "Python",
    "agents": "AI agents",
    "ml": "Machine learning",
    "tooling": "Tooling",
    "communication": "Communication",
    "consolidation": "Consolidation",
    "portfolio": "Portfolio",
}

# The fixed browse order: the three study subjects first, then the rest.
SUBJECT_ORDER: tuple[str, ...] = (
    "math",
    "data",
    "programming",
    "agents",
    "ml",
    "tooling",
    "communication",
    "consolidation",
    "portfolio",
)

# The three foundations entry nodes (math / data / Python) — the no-results
# pattern's links and the first card of each subject's browse list. Seed data,
# not derivation, so the links stay stable as the graph grows.
ENTRY_NODES: tuple[str, ...] = (
    "math.arithmetic.order_operations_01",
    "data.sql.select_basics_01",
    "programming.python.variables_01",
)

# The state chip pairs the canonical state word (P3.4) with its plain-language
# discovery label — no glossary fork (spec §C-bis "Card anatomy").
CHIP_LABELS: dict[str, str] = {
    "available": "Ready to start",
    "active": "In progress",
    "locked": "Locked",
    "passed": "Passed",
    "mastered": "Mastered",
}

# Ranking order within one score band: available first, locked last.
_STATE_ORDER = {"available": 0, "active": 1, "passed": 2, "mastered": 3, "locked": 9}

_DESCRIPTION_MAX = 140


def subject_of(node_id: str) -> str:
    """The ID-prefix subject of a node id (`data.sql.x_01` -> `data`)."""
    return node_id.split(".", 1)[0]


def subject_label(node_id: str) -> str:
    """The human subject label; unknown prefixes fall back to capitalized."""
    subject = subject_of(node_id)
    return SUBJECT_LABELS.get(subject, subject.capitalize())


@dataclass(frozen=True)
class DiscoveryCard:
    """One result card — the §C-bis anatomy, ready to render."""

    node_id: str
    title: str
    state: str
    description: str
    description_pending: bool
    entry: bool
    blocked_by_id: str | None = None
    blocked_by_title: str | None = None

    @property
    def chip(self) -> str:
        return CHIP_LABELS.get(self.state, self.state.capitalize())

    @property
    def locked(self) -> bool:
        return self.state == "locked"

    @property
    def subject(self) -> str:
        return subject_of(self.node_id)

    @property
    def subject_label(self) -> str:
        return subject_label(self.node_id)


def _first_sentence(summary: str) -> str:
    text = " ".join((summary or "").split())
    if not text:
        return ""
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0].strip()
    if len(first) <= _DESCRIPTION_MAX:
        return first
    clipped = first[:_DESCRIPTION_MAX].rsplit(" ", 1)[0].strip()
    return clipped + "…"


def _blocking_prerequisite(view, node_id: str) -> tuple[str, str] | None:
    """The first unsatisfied active hard prerequisite, in stable order.

    Locked is the only wall (CONTEXT.md): the card names and links it; the
    wall itself is never overridden — this is display only.
    """
    candidates = sorted(
        edge.source
        for edge in view.edges
        if edge.target == node_id
        and edge.edge_type == "hard_prerequisite"
        and getattr(edge, "active", True)
        and view.store.state_of(edge.source) not in ("passed", "mastered")
    )
    for source in candidates:
        title = view.titles.get(source)
        if title:
            return source, title
    return None


def _match_score(node, needle: str, tokens: list[str]) -> float | None:
    """The match score for one node, or None when it does not match.

    Title words weigh most; subject/track labels, summaries and synonyms
    weigh one; a whole-phrase title hit adds a phrase bonus. An ID exact or
    fragment hit alone is secondary (score 0.5) — never the primary.
    """
    title = (node.title or "").lower()
    summary = (node.summary or "").lower()
    subject = subject_of(node.id)
    track = (node.track or "").lower()
    score = 0.0
    matched = 0
    for token in tokens:
        best = 0.0
        if token in title:
            best = 2.0
        if token in summary and best < 1.0:
            best = 1.0
        if (token in subject or token in track) and best < 1.0:
            best = 1.0
        prefixes = SYNONYMS.get(token)
        if prefixes and node.id.startswith(tuple(prefixes)) and best < 1.0:
            best = 1.0
        if best:
            matched += 1
            score += best
    if tokens and needle in title:
        score += 3.0
        matched += 1
    if matched:
        return score
    fragment = needle.replace(" ", "_")
    if needle and (needle in node.id.lower() or fragment in node.id.lower()):
        return 0.5
    return None


def discover(view, query: str | None) -> list[DiscoveryCard]:
    """Match the query against the graph and return ranked discovery cards.

    Every match is returned — ambiguous titles show all matches with subject
    + description disambiguation, never a silent top-1. An empty/absent
    query returns an empty list (the caller renders the browse index).
    """
    needle = re.sub(r"\s+", " ", (query or "").strip()).lower()
    if not needle:
        return []
    tokens = [t for t in needle.split(" ") if t]
    scored: list[tuple[float, object]] = []
    for node in view.nodes:
        score = _match_score(node, needle, tokens)
        if score is not None:
            scored.append((score, node))

    def _rank(pair: tuple[float, object]) -> tuple[int, float, str]:
        score, node = pair
        state = view.store.state_of(node.id)
        # Available first, locked last (spec §C-bis Ranking) — the state band
        # dominates; score and title order within a band.
        return (_STATE_ORDER.get(state, 5), -score, (node.title or "").lower())

    scored.sort(key=_rank)
    return [card_for(view, node) for _, node in scored]


def card_for(view, node) -> DiscoveryCard:
    """One node's discovery card — the §C-bis anatomy off the joined view."""
    state = view.store.state_of(node.id)
    summary = _first_sentence(node.summary or "")
    blocked = _blocking_prerequisite(view, node.id) if state == "locked" else None
    return DiscoveryCard(
        node_id=node.id,
        title=node.title or node.id,
        state=state,
        description=summary,
        description_pending=not summary,
        entry=node.id in ENTRY_NODES,
        blocked_by_id=blocked[0] if blocked else None,
        blocked_by_title=blocked[1] if blocked else None,
    )


def browse_cards(view, subject: str) -> list[DiscoveryCard]:
    """One subject's browse list — entry nodes first, then the rest
    (available first, locked last), sharing the search card anatomy."""
    entry_ids = set(ENTRY_NODES)
    nodes = [n for n in view.nodes if subject_of(n.id) == subject]
    nodes.sort(
        key=lambda n: (
            0 if n.id in entry_ids else 1,
            _STATE_ORDER.get(view.store.state_of(n.id), 5),
            (n.title or "").lower(),
        )
    )
    return [card_for(view, node) for node in nodes]


def browse_subjects(view) -> list[tuple[str, str, int]]:
    """The browse index: (subject prefix, label, node count) in fixed order."""
    counts: dict[str, int] = {}
    for node in view.nodes:
        counts[subject_of(node.id)] = counts.get(subject_of(node.id), 0) + 1
    ordered = [s for s in SUBJECT_ORDER if s in counts]
    ordered += sorted(s for s in counts if s not in SUBJECT_ORDER)
    return [
        (subject, SUBJECT_LABELS.get(subject, subject.capitalize()), counts[subject])
        for subject in ordered
    ]