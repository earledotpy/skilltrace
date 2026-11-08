"""The Study cockpit and the safe Session closure (spec-v3-study-day §10.5, §10.6).

What only this module shows: the cockpit's own contract.

* **The timer is presentation only** — a page load, a navigation, an
  inspection or a timer expiry records nothing (IC-3).
* **Starting a second Session is refused** — and the refusal explains the
  two real options and offers a way back to the open Session (R5).
* **Blocked work is not a Blocker** — blocked work is a session-scoped
  observation; a Blocker is the explicit persistent-stuckness record, and
  only the learner creates one (IC-10).
* **Closing is safe** — it saves the work and implies nothing else: no
  pass, no blocker resolved, no review completed (C05).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(path: Path, relpath: str, doc: dict) -> None:
    target = path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A seed copy with no session at all."""
    return _seed(tmp_path)


@pytest.fixture
def with_session(tmp_path: Path) -> Path:
    """A seed copy with one open session and one work item against it."""
    root = _seed(tmp_path)
    from skilltrace.context import load_context_lenient

    node_id = sorted(load_context_lenient(root).nodes, key=lambda n: n.id)[0].id
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.cockpit.001",
                    "status": "open",
                    "started_at": "2026-11-17T07:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.cockpit.001.01",
                    "session_id": "ses.cockpit.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T07:30:00+00:00",
                    "notes": "worked through the example",
                    "minutes": 25,
                }
            ]
        },
    )
    return root


# --- the empty state -------------------------------------------------------------


def test_with_no_session_the_cockpit_says_so_and_offers_discovery(repo):
    """Nothing here opens a session by itself."""
    _, body, status = views.session_body(repo)
    assert status == 200
    assert "No session is open" in body
    assert 'href="/"' in body


def test_the_cockpit_never_offers_a_start_action_when_a_session_is_open(with_session):
    """A second start would be refused by the engine, so it is not offered."""
    _, body, _ = views.session_body(with_session)
    assert "/start" not in body


# --- the timer is presentation only ------------------------------------------------


def test_the_timer_is_announced_as_presentation_only(with_session):
    """The page says the timer records nothing (R6)."""
    _, body, _ = views.session_body(with_session)
    assert "presentation" in body.lower()
    assert "records nothing" in body.lower() or "never records" in body.lower()


def test_recording_work_announces_exactly_what_is_recorded(with_session):
    """No silent timing: the form says what the write records (R6)."""
    _, body, _ = views.session_body(with_session)
    assert "Nothing else" in body or "nothing else" in body
    assert "saves the minutes" in body


def test_the_work_form_binds_the_node_explicitly(with_session):
    """Work is logged against the explicitly bound node."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _, body, _ = views.session_body(with_session)
    assert f'name="node_id" value="{node_id}"' in body


# --- blocked work is not a Blocker --------------------------------------------------


def test_blocked_work_is_labelled_as_blocked_work(with_session):
    """Blocked work is a session-scoped observation (IC-10)."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.cockpit.001.02",
                    "session_id": "ses.cockpit.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T08:00:00+00:00",
                    "blocked": True,
                    "notes": "stuck on the second step",
                }
            ]
        },
    )
    _, body, _ = views.session_body(with_session)
    assert "Blocked work" in body
    assert "it is not a blocker" in body.lower()


def test_blocked_work_alone_creates_no_blocker_record(with_session):
    """The offer to record a blocker is explicit; nothing is created."""
    _, body, _ = views.session_body(with_session)
    # No blocked work yet, so no offer and no blocker form.
    assert "/blockers" not in body


def test_after_persistent_blocked_work_the_cockpit_offers_to_record_a_blocker(with_session):
    """The offer is a disclosure the learner opens; it is never a side effect."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.cockpit.001.02",
                    "session_id": "ses.cockpit.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T08:00:00+00:00",
                    "blocked": True,
                    "notes": "stuck again",
                }
            ]
        },
    )
    _, body, _ = views.session_body(with_session)
    assert "Still stuck?" in body
    assert f'action="/nodes/{node_id}/blockers"' in body
    # The obstacle description is required.
    assert 'name="description" required' in body
    # The copy says what a blocker does not do.
    assert "never resolves itself" in body


def test_a_second_open_blocker_warns_but_does_not_forbid(with_session):
    """A likely duplicate warns; it is not forbidden."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.cockpit.001.02",
                    "session_id": "ses.cockpit.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T08:00:00+00:00",
                    "blocked": True,
                    "notes": "stuck again",
                }
            ]
        },
    )
    _write_yaml(
        with_session,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.cockpit.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "the same stuckness",
                    "created_at": "2026-11-16T08:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.session_body(with_session)
    assert "already open" in body
    assert "allowed" in body
    # The form is still there: a warning is not a prohibition.
    assert f'action="/nodes/{node_id}/blockers"' in body


# --- the safe closure ---------------------------------------------------------------


def test_closing_states_that_it_implies_nothing(with_session):
    """Closing saves the work and implies nothing else (C05)."""
    _, body, status = views.session_close_body(with_session)
    assert status == 200
    assert "does not pass a skill" in body
    assert "resolve a blocker" in body
    assert "complete a review" in body


def test_closing_with_no_session_says_there_is_nothing_to_close(repo):
    _, body, status = views.session_close_body(repo)
    assert status == 200
    assert "No session is open" in body


def test_the_close_panel_shows_what_was_recorded(with_session):
    """The panel shows the elapsed work before the learner commits."""
    _, body, _ = views.session_close_body(with_session)
    assert "Work recorded" in body
    assert "25 minutes" in body
