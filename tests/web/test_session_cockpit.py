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
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The moment every cockpit render in this module is read against.
NOW = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _frozen_now(monkeypatch):
    """Pin the cockpit's clock reads and the shared resource-status date."""
    from skilltrace.web.views import _clock, _shared

    monkeypatch.setattr(_clock, "now_utc", lambda: NOW)
    monkeypatch.setattr(_shared, "utc_today", lambda: NOW.date())
    return NOW


def _seed(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(path: Path, relpath: str, doc: dict) -> None:
    target = path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _read_yaml(path: Path, relpath: str) -> dict:
    target = path / relpath
    return yaml.safe_load(target.read_text(encoding="utf-8")) or {}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A seed copy with no session at all."""
    return _seed(tmp_path)


@pytest.fixture
def with_session(tmp_path: Path) -> Path:
    """A seed copy with one open session and one work item against it."""
    root = _seed(tmp_path)
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(root)
    candidates = sorted(
        node.id
        for node in view.nodes
        if view.store.state_of(node.id) == "available"
    )
    # Prefer a skill with an evidence requirement and a gate, so the
    # cockpit's wanted-vs-recorded and eligibility facts are part of the
    # ordinary fixture.
    node_id = next(
        (
            candidate
            for candidate in candidates
            if view.specs_by_node.get(candidate) and candidate in view.has_gate
        ),
        candidates[0],
    )
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
    # The obstacle description is required, and its control is labelled —
    # an unassociated label leaves the field unnamed to a screen reader.
    assert 'name="description"' in body
    assert "required" in body
    assert 'for="blocker-description"' in body
    assert 'id="blocker-description"' in body
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


def test_an_open_blocker_shows_its_obstacle_study_material_and_interventions(
    with_session,
):
    """An open Blocker shows its options without claiming any of them resolves it."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    resources = view.resources_by_node.get(node_id, [])
    assert resources, "the fixture skill must have study material to show"
    _write_yaml(
        with_session,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.cockpit.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "groupby output keeps surprising me",
                    "created_at": "2026-11-16T08:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        with_session,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{node_id}.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "rebuild the drill from the docs",
                    "created_at": "2026-11-16T09:00:00+00:00",
                    "blocker_id": "blk.cockpit.001",
                },
                {
                    "id": f"rem.{node_id}.002",
                    "node_id": node_id,
                    "status": "completed",
                    "description": "an intervention that is no longer available",
                    "created_at": "2026-11-15T09:00:00+00:00",
                    "completed_at": "2026-11-16T09:00:00+00:00",
                    "result_summary": "done",
                },
            ]
        },
    )
    _, body, _ = views.session_body(with_session)

    # The obstacle itself, not just the skill label.
    assert "groupby output keeps surprising me" in body
    # The available study material, rendered as advisory pointers.
    where = resources[0].url or resources[0].local_path
    assert where in body
    assert "Study material" in body
    assert "Deliberate interventions" in body
    assert "rebuild the drill from the docs" in body
    assert "recorded for this blocker" in body
    # A completed action is history, never listed as an available intervention.
    assert "an intervention that is no longer available" not in body
    # The options are never presented as a resolution or an unlock.
    assert "Neither clears this blocker" in body
    assert "unlocks anything" in body
    # Resolving is the explicit action, and it requires a summary.
    assert 'action="/blockers/blk.cockpit.001/resolve"' in body
    assert 'name="summary"' in body
    assert "required" in body
    # A clear path back to the work that is already in progress.
    assert 'href="#work"' in body


def test_an_open_blocker_names_missing_material_and_interventions(with_session):
    """The empty branches are pinned too: no material and no remediation."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.cockpit.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "no options recorded",
                    "created_at": "2026-11-16T08:00:00+00:00",
                }
            ]
        },
    )
    resources = _read_yaml(with_session, "graph/resources.yaml")
    for resource in resources.get("resources") or []:
        supports = resource.get("supports") or []
        resource["supports"] = [n for n in supports if n != node_id]
    _write_yaml(with_session, "graph/resources.yaml", resources)

    _, body, _ = views.session_body(with_session)
    assert "No usable study material is registered" in body
    assert "No remediation action is recorded" in body


def test_a_resolved_blocker_is_terminal_history_not_an_open_record(with_session):
    """Resolution is terminal: the record stays visible, with its summary."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.cockpit.001",
                    "node_id": node_id,
                    "status": "resolved",
                    "description": "the same stuckness",
                    "created_at": "2026-11-15T08:00:00+00:00",
                    "resolved_at": "2026-11-16T08:00:00+00:00",
                    "resolution_summary": "re-read the docs and re-ran the drills",
                }
            ]
        },
    )
    _, body, _ = views.session_body(with_session)
    assert "No blockers are open" in body
    assert "Resolved" in body
    assert "re-read the docs and re-ran the drills" in body
    # A resolved record is never offered for resolving again.
    assert "/resolve" not in body
    assert "Resolution is terminal" in body


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


# --- the timer is shown, and it is still presentation only ------------------------


def test_the_cockpit_shows_a_presentation_only_timer(with_session):
    """The elapsed time is visible — orientation, never a record (IC-3)."""
    _, body, _ = views.session_body(with_session)
    assert "Timer" in body
    assert "Open for 2 hours" in body
    assert "orientation only" in body
    assert "never recorded and never becomes work" in body


def test_an_unparseable_start_shows_no_invented_elapsed_time(with_session):
    """A bad timestamp is validate's concern — the page invents nothing."""
    _write_yaml(
        with_session,
        "execution/sessions.yaml",
        {"sessions": [{"id": "ses.cockpit.001", "status": "open", "started_at": "not-a-date"}]},
    )
    _, body, status = views.session_body(with_session)
    assert status == 200
    assert "Open for unknown" in body


# --- the stale Session warns, and never blocks ------------------------------------


def _make_stale(root: Path) -> None:
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.cockpit.001",
                    "status": "open",
                    "started_at": "2026-11-14T09:00:00+00:00",
                }
            ]
        },
    )


def test_a_stale_session_warns_but_still_allows_work(with_session):
    """Staleness warns; it is never a dead end (R4, §10.5)."""
    _make_stale(with_session)
    _, body, _ = views.session_body(with_session)
    assert "This session has been open for 3 days" in body
    assert "Nothing is blocked by that" in body
    assert "close it with the time you actually stopped" in body
    # The work form is still there: a warning is not a block.
    assert 'action="/work"' in body


def test_a_stale_session_can_be_closed_with_an_honest_past_end_time(with_session):
    """A forgotten Session may record the time the learner actually stopped."""
    _make_stale(with_session)
    _, body, _ = views.session_close_body(with_session)
    assert "This session has been open for 3 days" in body
    assert 'name="end"' in body
    assert "before the session started" in body
    assert "nothing you recorded is lost" in body


def test_a_current_session_gets_no_end_time_field(with_session):
    """A current close records the current end — the field is not offered."""
    _, body, _ = views.session_close_body(with_session)
    assert 'name="end"' not in body
    assert '<span class="row-label">Open for</span>' in body
    assert '<span class="row-value">2 hours</span>' in body


def test_the_cockpit_names_pass_eligibility_and_the_next_action(with_session):
    """§10.5: eligibility is a derived fact; passing stays a separate decision."""
    _, body, _ = views.session_body(with_session)
    assert "Pass eligibility" in body
    assert "Not yet" in body
    assert "Next: record the work you did below" in body


def test_an_eligible_skill_says_passing_is_separate_and_links_the_panel(with_session):
    """Eligibility never pushes a pass; it names the explicit panel instead."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    spec = view.specs_by_node[node_id][0]
    _write_yaml(
        with_session,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{node_id}.{i:03d}",
                    "artifact_spec_id": spec.id,
                    "location": "evidence/artifacts/session_fixture.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "0" * 64,
                    "created_at": "2026-11-17T08:00:00+00:00",
                }
                for i in range(1, spec.minimum_count + 1)
            ]
        },
    )
    _, body, _ = views.session_body(with_session)
    assert "Ready — passing is a separate decision" in body
    assert f'href="/nodes/{node_id}/pass"' in body
    assert "Closing does neither" in body


def test_the_close_panel_names_what_remains_after_closure(with_session):
    """§10.6: unresolved Blockers, the state and the evidence survive closure."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _write_yaml(
        with_session,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.cockpit.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "still stuck on the join",
                    "created_at": "2026-11-16T08:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.session_close_body(with_session)
    assert "Open blockers" in body
    assert "1 open — closing resolves none of them" in body
    assert "State after closing" in body
    assert (
        f"{view.store.state_of(node_id).capitalize()} — unchanged by closing"
        in body
    )
    assert "Evidence afterwards" in body
    assert "unchanged by closing" in body


# --- the refused second start lands on the cockpit -------------------------------


def test_a_refused_second_start_lands_on_the_cockpit_with_both_options(with_session):
    """The fresh page names the two real options and the way back (R5)."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    bound = view.work[0].node_id
    result = views.post_start(with_session, bound, {"next": ["/"]})
    assert isinstance(result, views.Redirect)
    assert result.location.startswith("/session?")
    query = parse_qs(result.location.partition("?")[2])
    _, body, _ = views.session_body(with_session, query)
    assert "already open" in body.lower()
    assert "A second session cannot be started while this one is open" in body
    assert "close this session first" in body
    assert 'href="/session/close"' in body


# --- starting is announced before it records --------------------------------------


def test_today_announces_exactly_what_starting_records(repo):
    """R6: no silent timing — the start copy names the session and the state."""
    _, body, _ = views.home_body(repo, {})
    assert "Starting opens a session, records the start of this session" in body
    assert "marks the skill active" in body
    assert "No minutes or notes are recorded until you log work" in body


def test_the_node_page_announces_exactly_what_starting_records(repo):
    """The same announcement on the node page — one explicit start, one truth."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(repo)
    available = sorted(
        node.id for node in view.nodes if view.store.state_of(node.id) == "available"
    )[0]
    _, body, _ = views.node_body(repo, available, {})
    assert "Starting opens a session, records the start of this session" in body
    assert "marks the skill active" in body
    assert "No minutes or notes are recorded until you log work" in body


def test_a_session_with_no_bound_skill_offers_no_work_form(with_session):
    """Never render a form the domain would always refuse — name the recovery."""
    _write_yaml(with_session, "execution/session_work.yaml", {"session_work": []})
    _, body, _ = views.session_body(with_session)
    assert "No skill is bound to this session" in body
    assert 'action="/work"' not in body
    assert 'href="/session/close"' in body
    assert 'href="/"' in body


# --- evidence requirements are visible before work -------------------------------


def test_the_cockpit_shows_wanted_and_recorded_as_distinct_facts(with_session):
    """R2: evidence wanted and recorded are never one ambiguous number."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    node_id = view.work[0].node_id
    _, body, _ = views.session_body(with_session)
    assert "Evidence wanted" in body
    assert "Evidence recorded" in body
    assert f'href="/nodes/{node_id}/evidence"' in body


# --- inspecting another SkillNode never touches the Session ----------------------


def _read_yaml(root: Path, relpath: str) -> dict:
    path = root / relpath
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_inspecting_another_node_never_closes_replaces_or_extends_the_session(with_session):
    """Browsing is safe: viewing a skill is not a session command (IC-3)."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    bound = view.work[0].node_id
    other = sorted(
        node.id
        for node in view.nodes
        if node.id != bound and view.store.state_of(node.id) == "available"
    )[0]

    sessions_before = _read_yaml(with_session, "execution/sessions.yaml")
    work_before = _read_yaml(with_session, "execution/session_work.yaml")

    views.node_body(with_session, other, {})
    views.session_body(with_session, {})
    views.session_close_body(with_session, {})
    views.home_body(with_session, {})

    assert _read_yaml(with_session, "execution/sessions.yaml") == sessions_before
    assert _read_yaml(with_session, "execution/session_work.yaml") == work_before
    assert _read_yaml(with_session, "execution/events.yaml") == {}

    # And the other node offers no start: it cannot replace the Session.
    _, body, _ = views.node_body(with_session, other, {})
    assert 'data-intent="start"' not in body
    assert "Start this session" not in body


def test_work_on_a_locked_node_is_refused_on_the_page(with_session):
    """A locked skill renders no work form — the engine would refuse it."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    locked = sorted(n.id for n in view.nodes if view.store.state_of(n.id) == "locked")[0]
    _, body, _ = views.node_body(with_session, locked, {})
    assert "This skill is locked" in body
    assert 'action="/work"' not in body
    assert 'href="/session"' in body


def test_work_on_a_passed_node_is_offered_as_honest_history(with_session):
    """Work on a passed skill stays history; it never demotes the state."""
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(with_session)
    bound = view.work[0].node_id
    passed = sorted(
        node.id
        for node in view.nodes
        if node.id != bound and view.store.state_of(node.id) != "locked"
    )[0]
    doc = _read_yaml(with_session, "graph/state.yaml")
    doc.setdefault("progress", {})[passed] = {"state": "passed"}
    _write_yaml(with_session, "graph/state.yaml", doc)

    _, body, _ = views.node_body(with_session, passed, {})
    assert 'action="/work"' in body
    assert "stays honest history" in body
    assert "never changes that state" in body
