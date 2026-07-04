"""Evidence/attempt ID shape validation and per-node sequence allocation.

Two record types carry IDs with a *defined* format (unlike specs and gates,
whose IDs are opaque curriculum strings):

- an EvidenceRecord ID is ``ev.<node_id>.NNN``
- an AssessmentAttempt ID is ``att.<node_id>.NNN``

where ``<node_id>`` is a well-formed node ID (validated with the same rule the
graph loader uses) and ``NNN`` is a numeric per-node sequence. The sequence is
allocated ``max + 1`` per node — never reused, never backfilled (issue #10,
decision 14): even if a middle record were somehow absent, the next ID is one
past the highest ever seen, not the first gap.

These are pure helpers. The file reads that supply ``existing_ids`` live in the
submit / attempt-record commands (issues #12, #13); nothing here touches disk.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..graph.nodes import is_valid_node_id

# Prefixes are the only fixed part of the two formats; the middle is a node ID
# and the tail is a sequence, both validated structurally below.
_EVIDENCE_PREFIX = "ev."
_ATTEMPT_PREFIX = "att."

# Width the allocator zero-pads new sequence numbers to. Validation stays
# lenient (any run of digits), so a hand-written wider sequence still loads.
_SEQUENCE_WIDTH = 3


def _split(record_id: str, prefix: str) -> tuple[str, int] | None:
    """Split ``<prefix><node_id>.NNN`` into ``(node_id, sequence)``.

    Returns ``None`` if `record_id` is not a string, lacks the prefix, has no
    numeric tail, or embeds an invalid node ID. Callers turn ``None`` into a
    typed load error naming the record.
    """
    if not isinstance(record_id, str) or not record_id.startswith(prefix):
        return None
    node_id, dot, sequence = record_id[len(prefix) :].rpartition(".")
    # `.isascii()` guards `int()` below: `str.isdigit()` is true for unicode
    # digits (e.g. a superscript) that `int()` then refuses, so isdigit alone
    # would turn a malformed id into a ValueError instead of a clean rejection.
    if not dot or not (sequence.isascii() and sequence.isdigit()):
        return None
    if not is_valid_node_id(node_id):
        return None
    return node_id, int(sequence)


def split_evidence_id(record_id: str) -> tuple[str, int] | None:
    """``ev.<node_id>.NNN`` → ``(node_id, sequence)``, or ``None`` if malformed."""
    return _split(record_id, _EVIDENCE_PREFIX)


def split_attempt_id(record_id: str) -> tuple[str, int] | None:
    """``att.<node_id>.NNN`` → ``(node_id, sequence)``, or ``None`` if malformed."""
    return _split(record_id, _ATTEMPT_PREFIX)


def is_valid_evidence_id(record_id: str) -> bool:
    """True if `record_id` is a well-formed ``ev.<node_id>.NNN`` ID."""
    return split_evidence_id(record_id) is not None


def is_valid_attempt_id(record_id: str) -> bool:
    """True if `record_id` is a well-formed ``att.<node_id>.NNN`` ID."""
    return split_attempt_id(record_id) is not None


def _next_sequence(node_id: str, existing_ids: Iterable[str], prefix: str) -> int:
    """Highest sequence for `node_id` across `existing_ids`, plus one (min 1)."""
    highest = 0
    for record_id in existing_ids:
        parsed = _split(record_id, prefix)
        if parsed is not None and parsed[0] == node_id:
            highest = max(highest, parsed[1])
    return highest + 1


def allocate_evidence_id(node_id: str, existing_ids: Iterable[str]) -> str:
    """Next unused ``ev.<node_id>.NNN`` for `node_id` (max seen + 1, never reused)."""
    sequence = _next_sequence(node_id, existing_ids, _EVIDENCE_PREFIX)
    return f"{_EVIDENCE_PREFIX}{node_id}.{sequence:0{_SEQUENCE_WIDTH}d}"


def allocate_attempt_id(node_id: str, existing_ids: Iterable[str]) -> str:
    """Next unused ``att.<node_id>.NNN`` for `node_id` (max seen + 1, never reused)."""
    sequence = _next_sequence(node_id, existing_ids, _ATTEMPT_PREFIX)
    return f"{_ATTEMPT_PREFIX}{node_id}.{sequence:0{_SEQUENCE_WIDTH}d}"
