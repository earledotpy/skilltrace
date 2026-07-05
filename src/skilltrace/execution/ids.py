"""Execution record IDs.

Same `<prefix>.<scope>.<seq>` shape as the evidence layer (`evidence/ids.py`),
with the scope chosen per type: a session's scope is its UTC date
(`ses.2026-07-04.01`) — sessions have no parent node, and the date plays that
role; a work item's scope is its session (`wk.ses.2026-07-04.01.01`).
Sequences are allocated from the existing ids, so they are stable under
deletion-free append-only files.
"""

from __future__ import annotations

from collections.abc import Iterable


def _next_sequence(prefix: str, existing_ids: Iterable[str]) -> int:
    highest = 0
    for record_id in existing_ids:
        if not isinstance(record_id, str) or not record_id.startswith(prefix):
            continue
        tail = record_id[len(prefix) :]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return highest + 1


def allocate_session_id(date: str, existing_ids: Iterable[str]) -> str:
    """Next `ses.<date>.NN` id (NN restarts per date)."""
    prefix = f"ses.{date}."
    return f"{prefix}{_next_sequence(prefix, existing_ids):02d}"


def allocate_work_id(session_id: str, existing_ids: Iterable[str]) -> str:
    """Next `wk.<session_id>.NN` id (NN restarts per session)."""
    prefix = f"wk.{session_id}."
    return f"{prefix}{_next_sequence(prefix, existing_ids):02d}"


def allocate_blocker_id(node_id: str, existing_ids: Iterable[str]) -> str:
    """Next `blk.<node_id>.NNN` id (matches the evidence layer's node-scoped shape)."""
    prefix = f"blk.{node_id}."
    return f"{prefix}{_next_sequence(prefix, existing_ids):03d}"


def allocate_remediation_id(node_id: str, existing_ids: Iterable[str]) -> str:
    """Next `rem.<node_id>.NNN` id."""
    prefix = f"rem.{node_id}."
    return f"{prefix}{_next_sequence(prefix, existing_ids):03d}"


def allocate_review_id(node_id: str, existing_ids: Iterable[str]) -> str:
    """Next `rev.<node_id>.NNN` id."""
    prefix = f"rev.{node_id}."
    return f"{prefix}{_next_sequence(prefix, existing_ids):03d}"
