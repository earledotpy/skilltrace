"""The Study cockpit and Session-close states as fixture repos.

The golden snapshot suite and the axe harness render the *same* cockpit
states from the same fixture, or a state could be pinned by one gate and
left unchecked by the other. This module owns those states
(spec-v3-study-day §10.5, §10.6):

* ``populated`` — the pinned repo unchanged (its open Session, two hours
  old, with recorded work);
* ``stale`` — the same Session started three days before the frozen
  moment, past the policy staleness window, so the warning and the honest
  past-end closure are visible;
* ``no-blocker`` — the same Session with no Blocker record at all, so the
  cockpit's empty state is pinned;
* ``open-blocker`` — the pinned Blocker on the Session's skill, so its
  obstacle and its advisory options are visible;
* ``blocked-work`` — a blocked SessionWork row, so the distinct blocked-work
  observation and the explicit Create Blocker offer are pinned;
* ``blocker-resolved`` — that Blocker resolved with its summary, so the
  terminal history is visible instead of an open record;
* ``refusal`` — the fresh page after a **refused second start**: the
  submission is real (it goes through the dispatcher), it writes nothing,
  and the cockpit it lands on states the two real options and the way back
  to the existing Session (R5).

The stale mutation is fixture data, exactly as the other web suites seed
state. The refusal page is produced by the write path itself, which is the
point of the state: a refusal writes no records.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs

import yaml
from fixture_repo import materialise_variant, write_yaml

#: Three days before the suites' frozen moment (2026-11-17T09:00Z) — well
#: past the 12-hour default staleness window.
STALE_STARTED_AT = "2026-11-14T09:00:00+00:00"

#: The fixed moment a resolved Blocker carries in these fixtures.
BLOCKER_RESOLVED_AT = "2026-11-16T18:00:00+00:00"

#: The fixed moment an open action and a blocked work item carry in these fixtures.
FIXTURE_MOMENT = "2026-11-16T09:00:00+00:00"


def _make_session_stale(root: Path) -> None:
    """Start the open Session three days ago — a forgotten Session."""
    path = root / "execution" / "sessions.yaml"

    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sessions = doc.get("sessions") or []
    for session in sessions:
        if session.get("status") == "open":
            session["started_at"] = STALE_STARTED_AT
    write_yaml(root, "execution/sessions.yaml", {"sessions": sessions})


def _bound_node(root: Path) -> str:
    """The SkillNode the open Session is bound to (the engine's own derivation)."""
    from skilltrace.context import load_context_lenient
    from skilltrace.execution.records import open_session
    from skilltrace.web.views._shared import _session_node_id

    view = load_context_lenient(root)
    return _session_node_id(view, open_session(view.sessions))


def _open_session_id(root: Path) -> str:
    """The id of the one open Session in the pinned fixture."""
    sessions = (
        yaml.safe_load(
            (root / "execution" / "sessions.yaml").read_text(encoding="utf-8")
        )
        or {}
    ).get("sessions") or []
    return next(s["id"] for s in sessions if s.get("status") == "open")


def _blockers_doc(root: Path) -> dict:
    path = root / "execution" / "blockers.yaml"
    if not path.exists():
        return {"blockers": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"blockers": []}


def _make_session_blockers_empty(root: Path) -> None:
    """No Blocker record at all — the cockpit's empty state."""
    write_yaml(root, "execution/blockers.yaml", {"blockers": []})
    write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {"remediation_actions": []},
    )


def _make_session_blocker_open(root: Path) -> None:
    """The Blocker on the Session's skill, open — its options are visible.

    One open ``RemediationAction`` is authored here so the Blocker's
    deliberate-intervention list is pinned; it names the Blocker it
    addresses, exactly as the engine's optional link allows.
    """
    node_id = _bound_node(root)
    doc = _blockers_doc(root)
    blocker_id = None
    for blocker in doc.get("blockers") or []:
        if blocker.get("node_id") == node_id:
            blocker["status"] = "open"
            blocker.pop("resolved_at", None)
            blocker.pop("resolution_summary", None)
            blocker_id = blocker.get("id")
    write_yaml(root, "execution/blockers.yaml", {"blockers": doc.get("blockers") or []})
    if blocker_id is None:
        raise ValueError("the pinned fixture has no blocker on the session skill")
    write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{node_id}.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "rebuild the groupby drill from the docs",
                    "created_at": FIXTURE_MOMENT,
                    "blocker_id": blocker_id,
                }
            ]
        },
    )


def _make_session_blocked_work(root: Path) -> None:
    """A blocked SessionWork row — the distinct "blocked work" state.

    Blocked work is a session-scoped observation, and it is what offers the
    explicit **Create Blocker** disclosure. It never creates a Blocker on its
    own: the pinned fixture's Blocker is authored separately.
    """
    node_id = _bound_node(root)
    session_id = _open_session_id(root)
    path = root / "execution" / "session_work.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    work = doc.get("session_work") or []
    work.append(
        {
            "id": f"wk.{session_id}.99",
            "session_id": session_id,
            "node_id": node_id,
            "created_at": FIXTURE_MOMENT,
            "blocked": True,
            "notes": "stuck on the second step",
        }
    )
    write_yaml(root, "execution/session_work.yaml", {"session_work": work})


def _make_session_blocker_resolved(root: Path) -> None:
    """Resolve the Session's Blocker — terminal history, nothing open."""
    node_id = _bound_node(root)
    doc = _blockers_doc(root)
    resolved = False
    for blocker in doc.get("blockers") or []:
        if blocker.get("node_id") == node_id and blocker.get("status") == "open":
            blocker["status"] = "resolved"
            blocker["resolved_at"] = BLOCKER_RESOLVED_AT
            blocker["resolution_summary"] = (
                "re-read the docs and re-ran the drills"
            )
            resolved = True
    if not resolved:
        raise ValueError("the pinned fixture has no open blocker to resolve")
    write_yaml(root, "execution/blockers.yaml", {"blockers": doc.get("blockers") or []})


_MUTATIONS = {
    "stale": _make_session_stale,
    "no-blocker": _make_session_blockers_empty,
    "open-blocker": _make_session_blocker_open,
    "blocked-work": _make_session_blocked_work,
    "blocker-resolved": _make_session_blocker_resolved,
}


def build_session_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one named cockpit state."""
    return materialise_variant(
        pinned, kind, prefix=f"session-{kind}", mutations=_MUTATIONS
    )


def refused_start_body(
    root: Path, node_id: str
) -> tuple[str, str, int]:
    """The served cockpit after a refused second start — the refusal state.

    Drives the real write path: the engine refuses (a Session is already
    open), writes no record, and redirects to the cockpit with the
    translated refusal. Rendering the redirect target pins exactly what the
    learner sees at the moment the refusal fires (IC-8, R5).
    """
    from skilltrace.web import views
    from skilltrace.web.views import Redirect

    result = views.post_start(root, node_id, {"next": ["/session"]})
    assert isinstance(result, Redirect), "a second start must be refused"
    query = parse_qs(result.location.partition("?")[2])
    return views.session_body(root, query)
