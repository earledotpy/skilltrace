"""Deep execution record loader — one module for all execution YAML I/O.

Collapses five shallow loader modules (sessions, work, blockers, remediation,
reviews) into a single deep module that owns:

* reading all five execution YAML files in one pass
* shape-checking each record type against its schema
* mapping to typed dataclasses
* returning a single structured result ``ExecutionRecords``

The per-type load helpers (``load_sessions`` etc.) remain public for direct
callers (validation, commands) that need a single type and expect an
``ExecutionLoadError`` on shape failure. The combined ``load_execution``
aggregates per-type results and never raises for expected shape/YAML errors;
instead it populates ``ExecutionRecords.errors`` so the joined-view seam can
decide whether to collect errors (strict) or degrade (lenient) per record
type.

Mutation helpers (``complete_session``, ``resolve_blocker``, etc.) and
append helpers live here as well — one place fixes all record types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ._store import ExecutionLoadError, append_record, check_record_shape, read_records, write_records

# ---------------------------------------------------------------------------
# File / top-key / kind descriptors — one descriptor per record type
# ---------------------------------------------------------------------------

_SESSIONS_RELPATH = Path("execution") / "sessions.yaml"
_SESSIONS_TOP_KEY = "sessions"
_SESSIONS_KIND = "session"

_WORK_RELPATH = Path("execution") / "session_work.yaml"
_WORK_TOP_KEY = "session_work"
_WORK_KIND = "work item"

_BLOCKERS_RELPATH = Path("execution") / "blockers.yaml"
_BLOCKERS_TOP_KEY = "blockers"
_BLOCKERS_KIND = "blocker"

_REMEDIATION_RELPATH = Path("execution") / "remediation_actions.yaml"
_REMEDIATION_TOP_KEY = "remediation_actions"
_REMEDIATION_KIND = "remediation action"

_REVIEWS_RELPATH = Path("execution") / "reviews.yaml"
_REVIEWS_TOP_KEY = "reviews"
_REVIEWS_KIND = "review"

# ---------------------------------------------------------------------------
# Schema descriptors
# ---------------------------------------------------------------------------

SESSION_STATUSES = ("open", "completed")
SESSION_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "status", "started_at", "ended_at", "template"})
SESSION_REQUIRED_FIELDS: tuple[str, ...] = ("id", "status", "started_at")

WORK_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "session_id", "node_id", "created_at", "blocked", "notes", "minutes"})
WORK_REQUIRED_FIELDS: tuple[str, ...] = ("id", "session_id", "node_id", "created_at")

BLOCKER_STATUSES = ("open", "resolved")
BLOCKER_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "node_id", "status", "description", "created_at", "resolved_at", "resolution_summary"})
BLOCKER_REQUIRED_FIELDS: tuple[str, ...] = ("id", "node_id", "status", "description", "created_at")

REMEDIATION_STATUSES = ("open", "completed")
REMEDIATION_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "node_id", "status", "description", "created_at", "blocker_id", "completed_at", "result_summary"})
REMEDIATION_REQUIRED_FIELDS: tuple[str, ...] = ("id", "node_id", "status", "description", "created_at")

REVIEW_STATUSES = ("scheduled", "completed", "cancelled")
REVIEW_OUTCOMES = ("satisfactory", "unsatisfactory")
REVIEW_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "node_id", "status", "scheduled_for", "created_at", "completed_at", "outcome", "result_summary", "cancelled_at", "cancel_reason"})
REVIEW_REQUIRED_FIELDS: tuple[str, ...] = ("id", "node_id", "status", "scheduled_for", "created_at")

# Backward-compat aliases — old modules exposed these names
STATUSES = SESSION_STATUSES  # for sessions; blockers/remediation/reviews have own
OUTCOMES = REVIEW_OUTCOMES

# ---------------------------------------------------------------------------
# Dataclasses — schema, shape-checker, and factory co-located
# ---------------------------------------------------------------------------

@dataclass
class Session:
    id: str
    status: str
    started_at: str
    ended_at: str | None = None
    template: str | None = None


@dataclass
class SessionWork:
    id: str
    session_id: str
    node_id: str
    created_at: str
    blocked: bool = False
    notes: str | None = None
    minutes: int | None = None


@dataclass
class Blocker:
    id: str
    node_id: str
    status: str
    description: str
    created_at: str
    resolved_at: str | None = None
    resolution_summary: str | None = None


@dataclass
class RemediationAction:
    id: str
    node_id: str
    status: str
    description: str
    created_at: str
    blocker_id: str | None = None
    completed_at: str | None = None
    result_summary: str | None = None


@dataclass
class Review:
    id: str
    node_id: str
    status: str
    scheduled_for: str
    created_at: str
    completed_at: str | None = None
    outcome: str | None = None
    result_summary: str | None = None
    cancelled_at: str | None = None
    cancel_reason: str | None = None


@dataclass
class ExecutionRecords:
    """Structured result of loading all execution YAML files.

    ``errors`` maps the JoinedView attribute name (``"sessions"``, ``"work"``,
    ``"blockers"``, ``"remediations"``, ``"reviews"``) to the
    ``ExecutionLoadError`` message for that file. A missing or malformed file
    yields an empty list for that attribute and an entry in ``errors``; a
    missing file that is legitimately absent (fresh repo) yields an empty list
    with no error — ``read_records`` already returns ``[]`` for missing files.
    """

    sessions: list[Session] = field(default_factory=list)
    work: list[SessionWork] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    remediations: list[RemediationAction] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Per-type loaders — shape-check + map, raise ExecutionLoadError on failure
# ---------------------------------------------------------------------------

def load_sessions(root: Path | str) -> list[Session]:
    """Load and shape-check every session; missing file -> empty history."""
    sessions: list[Session] = []
    raw = read_records(root, _SESSIONS_RELPATH, top_key=_SESSIONS_TOP_KEY, kind=_SESSIONS_KIND)
    path = Path(root) / _SESSIONS_RELPATH
    for index, data in enumerate(raw):
        check_record_shape(
            data,
            kind=_SESSIONS_KIND,
            allowed=SESSION_ALLOWED_FIELDS,
            required=SESSION_REQUIRED_FIELDS,
            path=path,
            index=index,
        )
        if data["status"] not in SESSION_STATUSES:
            raise ExecutionLoadError(
                f"{path}: session {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(SESSION_STATUSES)} (there is no planned session)."
            )
        sessions.append(
            Session(
                id=str(data["id"]),
                status=str(data["status"]),
                started_at=str(data["started_at"]),
                ended_at=data.get("ended_at"),
                template=data.get("template"),
            )
        )
    return sessions


def load_session_work(root: Path | str) -> list[SessionWork]:
    """Load and shape-check every work item; missing file -> empty history."""
    items: list[SessionWork] = []
    raw = read_records(root, _WORK_RELPATH, top_key=_WORK_TOP_KEY, kind=_WORK_KIND)
    path = Path(root) / _WORK_RELPATH
    for index, data in enumerate(raw):
        check_record_shape(
            data,
            kind=_WORK_KIND,
            allowed=WORK_ALLOWED_FIELDS,
            required=WORK_REQUIRED_FIELDS,
            path=path,
            index=index,
        )
        items.append(
            SessionWork(
                id=str(data["id"]),
                session_id=str(data["session_id"]),
                node_id=str(data["node_id"]),
                created_at=str(data["created_at"]),
                blocked=bool(data.get("blocked", False)),
                notes=data.get("notes"),
                minutes=data.get("minutes"),
            )
        )
    return items


def load_blockers(root: Path | str) -> list[Blocker]:
    """Load and shape-check every blocker; missing file -> empty history."""
    blockers: list[Blocker] = []
    raw = read_records(root, _BLOCKERS_RELPATH, top_key=_BLOCKERS_TOP_KEY, kind=_BLOCKERS_KIND)
    path = Path(root) / _BLOCKERS_RELPATH
    for index, data in enumerate(raw):
        check_record_shape(
            data,
            kind=_BLOCKERS_KIND,
            allowed=BLOCKER_ALLOWED_FIELDS,
            required=BLOCKER_REQUIRED_FIELDS,
            path=path,
            index=index,
        )
        if data["status"] not in BLOCKER_STATUSES:
            raise ExecutionLoadError(
                f"{path}: blocker {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(BLOCKER_STATUSES)}."
            )
        blockers.append(
            Blocker(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                description=str(data["description"]),
                created_at=str(data["created_at"]),
                resolved_at=data.get("resolved_at"),
                resolution_summary=data.get("resolution_summary"),
            )
        )
    return blockers


def load_remediation_actions(root: Path | str) -> list[RemediationAction]:
    """Load and shape-check every remediation action; missing file -> empty history."""
    actions: list[RemediationAction] = []
    raw = read_records(root, _REMEDIATION_RELPATH, top_key=_REMEDIATION_TOP_KEY, kind=_REMEDIATION_KIND)
    path = Path(root) / _REMEDIATION_RELPATH
    for index, data in enumerate(raw):
        check_record_shape(
            data,
            kind=_REMEDIATION_KIND,
            allowed=REMEDIATION_ALLOWED_FIELDS,
            required=REMEDIATION_REQUIRED_FIELDS,
            path=path,
            index=index,
        )
        if data["status"] not in REMEDIATION_STATUSES:
            raise ExecutionLoadError(
                f"{path}: remediation action {data['id']!r} has invalid status "
                f"{data['status']!r} — expected one of {', '.join(REMEDIATION_STATUSES)}."
            )
        actions.append(
            RemediationAction(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                description=str(data["description"]),
                created_at=str(data["created_at"]),
                blocker_id=data.get("blocker_id"),
                completed_at=data.get("completed_at"),
                result_summary=data.get("result_summary"),
            )
        )
    return actions


def load_reviews(root: Path | str) -> list[Review]:
    """Load and shape-check every review; missing file -> empty history."""
    reviews: list[Review] = []
    raw = read_records(root, _REVIEWS_RELPATH, top_key=_REVIEWS_TOP_KEY, kind=_REVIEWS_KIND)
    path = Path(root) / _REVIEWS_RELPATH
    for index, data in enumerate(raw):
        check_record_shape(
            data,
            kind=_REVIEWS_KIND,
            allowed=REVIEW_ALLOWED_FIELDS,
            required=REVIEW_REQUIRED_FIELDS,
            path=path,
            index=index,
        )
        if data["status"] not in REVIEW_STATUSES:
            raise ExecutionLoadError(
                f"{path}: review {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(REVIEW_STATUSES)}."
            )
        reviews.append(
            Review(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                scheduled_for=str(data["scheduled_for"]),
                created_at=str(data["created_at"]),
                completed_at=data.get("completed_at"),
                outcome=data.get("outcome"),
                result_summary=data.get("result_summary"),
                cancelled_at=data.get("cancelled_at"),
                cancel_reason=data.get("cancel_reason"),
            )
        )
    return reviews


# ---------------------------------------------------------------------------
# Combined loader — one call, many records, per-type error aggregation
# ---------------------------------------------------------------------------

def load_execution(root: Path | str) -> ExecutionRecords:
    """Load all five execution record types in one pass.

    Each file is attempted independently; an ``ExecutionLoadError`` for one
    type degrades that type to an empty list and records the error in
    ``ExecutionRecords.errors`` without aborting the other four. Missing files
    are empty without error (fresh repo). Unexpected exceptions propagate.

    This is the single seam for the joined-view execution layer — one call,
    many records, per-type lenient degradation captured for the caller to
    decide (strict -> errors, lenient -> degraded).
    """
    records = ExecutionRecords()
    errors: dict[str, str] = {}

    try:
        records.sessions = load_sessions(root)
    except ExecutionLoadError as exc:
        errors["sessions"] = str(exc)
        records.sessions = []

    try:
        records.work = load_session_work(root)
    except ExecutionLoadError as exc:
        errors["work"] = str(exc)
        records.work = []

    try:
        records.blockers = load_blockers(root)
    except ExecutionLoadError as exc:
        errors["blockers"] = str(exc)
        records.blockers = []

    try:
        records.remediations = load_remediation_actions(root)
    except ExecutionLoadError as exc:
        errors["remediations"] = str(exc)
        records.remediations = []

    try:
        records.reviews = load_reviews(root)
    except ExecutionLoadError as exc:
        errors["reviews"] = str(exc)
        records.reviews = []

    records.errors = errors
    return records


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def open_session(sessions: list[Session]) -> Session | None:
    """The single open session, or None. (Multiple opens is a validation error.)"""
    for session in sessions:
        if session.status == "open":
            return session
    return None


# ---------------------------------------------------------------------------
# Append helpers — preserve existing rows
# ---------------------------------------------------------------------------

def append_session(root: Path | str, record: dict) -> None:
    append_record(root, _SESSIONS_RELPATH, top_key=_SESSIONS_TOP_KEY, kind=_SESSIONS_KIND, record=record)


def append_work(root: Path | str, record: dict) -> None:
    append_record(root, _WORK_RELPATH, top_key=_WORK_TOP_KEY, kind=_WORK_KIND, record=record)


def append_blocker(root: Path | str, record: dict) -> None:
    append_record(root, _BLOCKERS_RELPATH, top_key=_BLOCKERS_TOP_KEY, kind=_BLOCKERS_KIND, record=record)


def append_remediation_action(root: Path | str, record: dict) -> None:
    append_record(root, _REMEDIATION_RELPATH, top_key=_REMEDIATION_TOP_KEY, kind=_REMEDIATION_KIND, record=record)


def append_review(root: Path | str, record: dict) -> None:
    append_record(root, _REVIEWS_RELPATH, top_key=_REVIEWS_TOP_KEY, kind=_REVIEWS_KIND, record=record)


# ---------------------------------------------------------------------------
# Mutation helpers — read-modify-write, other rows untouched
# ---------------------------------------------------------------------------

def complete_session(root: Path | str, session_id: str, *, ended_at: str) -> None:
    """Flip one session ``open -> completed``, stamping its end."""
    records = read_records(root, _SESSIONS_RELPATH, top_key=_SESSIONS_TOP_KEY, kind=_SESSIONS_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == session_id:
            record["status"] = "completed"
            record["ended_at"] = ended_at
            break
    else:
        raise ExecutionLoadError(f"session {session_id!r} not found — cannot complete.")
    write_records(root, _SESSIONS_RELPATH, top_key=_SESSIONS_TOP_KEY, records=records)


def resolve_blocker(
    root: Path | str, blocker_id: str, *, resolution_summary: str, resolved_at: str
) -> None:
    """Flip one blocker ``open -> resolved`` with its summary; other rows untouched."""
    records = read_records(root, _BLOCKERS_RELPATH, top_key=_BLOCKERS_TOP_KEY, kind=_BLOCKERS_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == blocker_id:
            record["status"] = "resolved"
            record["resolution_summary"] = resolution_summary
            record["resolved_at"] = resolved_at
            break
    else:
        raise ExecutionLoadError(f"blocker {blocker_id!r} not found — cannot resolve.")
    write_records(root, _BLOCKERS_RELPATH, top_key=_BLOCKERS_TOP_KEY, records=records)


def complete_remediation_action(
    root: Path | str, action_id: str, *, result_summary: str, completed_at: str
) -> None:
    """Flip one action ``open -> completed`` with its result; other rows untouched."""
    records = read_records(root, _REMEDIATION_RELPATH, top_key=_REMEDIATION_TOP_KEY, kind=_REMEDIATION_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == action_id:
            record["status"] = "completed"
            record["result_summary"] = result_summary
            record["completed_at"] = completed_at
            break
    else:
        raise ExecutionLoadError(f"remediation action {action_id!r} not found — cannot complete.")
    write_records(root, _REMEDIATION_RELPATH, top_key=_REMEDIATION_TOP_KEY, records=records)


def _update_review(root: Path | str, review_id: str, fields: dict) -> None:
    records = read_records(root, _REVIEWS_RELPATH, top_key=_REVIEWS_TOP_KEY, kind=_REVIEWS_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == review_id:
            record.update(fields)
            break
    else:
        raise ExecutionLoadError(f"review {review_id!r} not found.")
    write_records(root, _REVIEWS_RELPATH, top_key=_REVIEWS_TOP_KEY, records=records)


def complete_review(
    root: Path | str, review_id: str, *, outcome: str, result_summary: str, completed_at: str
) -> None:
    """Flip one review ``scheduled -> completed`` with outcome and summary."""
    _update_review(
        root,
        review_id,
        {
            "status": "completed",
            "outcome": outcome,
            "result_summary": result_summary,
            "completed_at": completed_at,
        },
    )


def cancel_review(
    root: Path | str, review_id: str, *, cancel_reason: str, cancelled_at: str
) -> None:
    """Flip one review ``scheduled -> cancelled``; the record stays as history."""
    _update_review(
        root,
        review_id,
        {"status": "cancelled", "cancel_reason": cancel_reason, "cancelled_at": cancelled_at},
    )
