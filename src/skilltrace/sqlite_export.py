"""`skilltrace export sqlite` — the boring mirror at `data/skilltrace.db`.

Per the #33 resolution: one table per record type, column names identical to
the YAML field names, no derived or joined tables. The sole exception is
`nodes.state`, which mirrors the state the progress store already persists —
everywhere else, a table is exactly the list a loader returned, in loader
(file) order, one row per record.

List and mapping fields (`tags`, `roadmap_anchors`, `supports`, event `args`,
…) have no native SQLite representation; each is stored as a JSON string
under its own YAML field name, which keeps "one table per record type" true
without inventing joined child tables. Rebuilt from scratch on every run: any
existing file at the destination is removed before the new one is built,
never opened-and-updated.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .export_data import ExportData
from .policy.loading import POLICY_FILES

SQLITE_EXPORT_RELPATH = Path("data") / "skilltrace.db"


def _v(value: Any) -> Any:
    """Adapt one Python value to something `sqlite3` can bind directly.

    `default=str` covers non-JSON-native scalars YAML hands back inside a
    nested structure (e.g. `datetime.date` in a policy document's cadence
    fields) without inventing per-field date handling.
    """
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), default=str)
    if isinstance(value, dict):
        return json.dumps(value, default=str)
    return value


def _create_and_fill(
    conn: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    rows: Iterable[tuple[Any, ...]],
) -> None:
    col_sql = ", ".join(columns)
    conn.execute(f"CREATE TABLE {table} ({col_sql})")
    rows = list(rows)
    if rows:
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})", rows)


_NODE_COLUMNS = (
    "id", "title", "summary", "domain", "track", "roadmap_anchors",
    "estimated_effort", "micro_session_fit", "competency_dimensions",
    "mastery_policy", "tags", "created_at", "updated_at", "state",
)
_EDGE_COLUMNS = (
    "id", "source", "target", "edge_type", "reason", "active",
    "created_at", "updated_at",
)
_SPEC_COLUMNS = (
    "id", "node_id", "title", "artifact_kind", "description", "required",
    "minimum_count", "expected_location_hint", "example_filename",
    "acceptance_summary", "created_at", "updated_at",
)
_GATE_COLUMNS = (
    "id", "node_id", "authority", "command", "title", "description",
    "created_at", "updated_at",
)
_RECORD_COLUMNS = (
    "id", "artifact_spec_id", "location", "note", "accepted", "accepted_by",
    "artifact_hash", "supersedes", "supersede_reason", "created_at",
)
_ATTEMPT_COLUMNS = ("id", "node_id", "outcome", "note", "created_at")
_SESSION_COLUMNS = ("id", "status", "started_at", "ended_at", "template")
_WORK_COLUMNS = (
    "id", "session_id", "node_id", "created_at", "blocked", "notes", "minutes",
)
_BLOCKER_COLUMNS = (
    "id", "node_id", "status", "description", "created_at", "resolved_at",
    "resolution_summary",
)
_REMEDIATION_COLUMNS = (
    "id", "node_id", "status", "description", "created_at", "blocker_id",
    "completed_at", "result_summary",
)
_REVIEW_COLUMNS = (
    "id", "node_id", "status", "scheduled_for", "created_at", "completed_at",
    "outcome", "result_summary", "cancelled_at", "cancel_reason",
)
_EVENT_COLUMNS = ("timestamp", "command", "args", "records_touched")
_RESOURCE_COLUMNS = (
    "id", "url", "local_path", "cost", "free_tier", "certificate", "license",
    "supports", "last_verified", "broken",
)
_POLICY_COLUMNS = ("filename", "policy_name", "document")


def write_sqlite_export(data: ExportData, path: Path | str) -> Path:
    """Rebuild the SQLite mirror at `path` from `data`. Returns the written path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    conn = sqlite3.connect(str(path))
    try:
        _create_and_fill(
            conn, "nodes", _NODE_COLUMNS,
            (
                (
                    n.id, n.title, n.summary, n.domain, n.track,
                    _v(n.roadmap_anchors), _v(n.estimated_effort),
                    _v(n.micro_session_fit), _v(n.competency_dimensions),
                    _v(n.mastery_policy), _v(n.tags), n.created_at, n.updated_at,
                    data.state.state_of(n.id),  # the sole derived column (module docstring)
                )
                for n in data.nodes
            ),
        )
        _create_and_fill(
            conn, "edges", _EDGE_COLUMNS,
            (
                (e.id, e.source, e.target, e.edge_type, e.reason, e.active,
                 e.created_at, e.updated_at)
                for e in data.edges
            ),
        )
        _create_and_fill(
            conn, "artifact_specs", _SPEC_COLUMNS,
            (
                (s.id, s.node_id, s.title, s.artifact_kind, s.description,
                 s.required, s.minimum_count, s.expected_location_hint,
                 s.example_filename, s.acceptance_summary, s.created_at,
                 s.updated_at)
                for s in data.artifact_specs
            ),
        )
        _create_and_fill(
            conn, "validation_gates", _GATE_COLUMNS,
            (
                (g.id, g.node_id, g.authority, g.command, g.title,
                 g.description, g.created_at, g.updated_at)
                for g in data.validation_gates
            ),
        )
        _create_and_fill(
            conn, "evidence_records", _RECORD_COLUMNS,
            (
                (r.id, r.artifact_spec_id, r.location, r.note, r.accepted,
                 r.accepted_by, r.artifact_hash, r.supersedes,
                 r.supersede_reason, r.created_at)
                for r in data.evidence_records
            ),
        )
        _create_and_fill(
            conn, "attempts", _ATTEMPT_COLUMNS,
            (
                (a.id, a.node_id, a.outcome, a.note, a.created_at)
                for a in data.attempts
            ),
        )
        _create_and_fill(
            conn, "sessions", _SESSION_COLUMNS,
            (
                (s.id, s.status, s.started_at, s.ended_at, s.template)
                for s in data.sessions
            ),
        )
        _create_and_fill(
            conn, "session_work", _WORK_COLUMNS,
            (
                (w.id, w.session_id, w.node_id, w.created_at, w.blocked,
                 w.notes, w.minutes)
                for w in data.session_work
            ),
        )
        _create_and_fill(
            conn, "blockers", _BLOCKER_COLUMNS,
            (
                (b.id, b.node_id, b.status, b.description, b.created_at,
                 b.resolved_at, b.resolution_summary)
                for b in data.blockers
            ),
        )
        _create_and_fill(
            conn, "remediation_actions", _REMEDIATION_COLUMNS,
            (
                (r.id, r.node_id, r.status, r.description, r.created_at,
                 r.blocker_id, r.completed_at, r.result_summary)
                for r in data.remediation_actions
            ),
        )
        _create_and_fill(
            conn, "reviews", _REVIEW_COLUMNS,
            (
                (r.id, r.node_id, r.status, r.scheduled_for, r.created_at,
                 r.completed_at, r.outcome, r.result_summary, r.cancelled_at,
                 r.cancel_reason)
                for r in data.reviews
            ),
        )
        _create_and_fill(
            conn, "events", _EVENT_COLUMNS,
            (
                (e.get("timestamp"), e.get("command"), _v(e.get("args") or {}),
                 _v(e.get("records_touched") or []))
                for e in data.events
            ),
        )
        _create_and_fill(
            conn, "resources", _RESOURCE_COLUMNS,
            (
                (r.id, r.url, r.local_path, r.cost, r.free_tier, r.certificate,
                 r.license, _v(r.supports), r.last_verified,
                 _v({"date": r.broken.date, "reason": r.broken.reason}) if r.broken else None)
                for r in data.resources
            ),
        )
        _create_and_fill(
            conn, "policies", _POLICY_COLUMNS,
            (
                (filename, POLICY_FILES[filename], _v(document))
                for filename, document in data.policies.items()
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path
