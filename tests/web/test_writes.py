"""Browser writes — Tier-1 slice T4 (issue #73): safety panels + daily writes.

What only the wired write surface can show: every mutation nests-dispatch
through the *same* registry the CLI uses (`Context.source="web"`, canonical
command name, one audit event), hard-boundary refusals match the CLI's own
output verbatim, the pass/master panels render server-fresh facts and never
pre-disable (a stale panel is proven unable to assert what eligibility no
longer supports), heavyweight confirmation stays exclusive to pass/master,
and the G5 daily writes round-trip through their forms with redirect-after-POST.
"""

from __future__ import annotations

import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import pytest
import yaml

from skilltrace.commands.eligibility import passed_at_of
from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.views import Redirect

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE = "math.arithmetic.order_operations_01"
SPEC = "spec.math.arithmetic.order_operations"


# --- Seeded repos ----------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _read_yaml(root: Path, relpath: str) -> dict:
    path = root / relpath
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _set_state(root: Path, node_id: str, state: str) -> None:
    doc = _read_yaml(root, "graph/state.yaml")
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


def _state_of(root: Path, node_id: str) -> str:
    view = load_context_lenient(root)
    return view.store.state_of(node_id)


def _first_locked_node(root: Path) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if view.store.state_of(node.id) == "locked":
            return node.id
    raise AssertionError("no locked node in the seed graph")


def _events(root: Path) -> list[dict]:
    doc = _read_yaml(root, "execution/events.yaml")
    return doc.get("events") or []


def _make_eligible(root: Path, node_id: str = NODE, spec_id: str = SPEC, count: int = 3):
    """Three live accepted records against the node's required manual-gate spec."""
    records = [
        {
            "id": f"ev.{node_id}.{i:03d}",
            "artifact_spec_id": spec_id,
            "location": f"evidence/math/set_{i:03d}.md",
            "accepted": True,
            "accepted_by": "learner_manual",
            "artifact_hash": "sha256:" + "0" * 64,
            "created_at": "2026-08-20T10:00:00+00:00",
        }
        for i in range(1, count + 1)
    ]
    _write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": records})


def _form(**fields) -> dict:
    return {key: [str(value)] for key, value in fields.items()}


def _make_objective_gate(
    root: Path, command: str, node_id: str = NODE, gate_id: str | None = None
) -> None:
    """Turn the node's gate into an objective gate running ``command``."""
    doc = _read_yaml(root, "evidence/validation_gates.yaml")
    for gate in doc.get("validation_gates") or []:
        if gate.get("node_id") != node_id:
            continue
        if gate_id is not None and gate.get("id") != gate_id:
            continue
        gate["authority"] = "objective"
        gate["command"] = command
        _write_yaml(root, "evidence/validation_gates.yaml", doc)
        return
    raise AssertionError(f"no gate for {node_id}")


def _gate_script(root: Path, *, exit_code: int, output: str = "") -> str:
    """An executable gate script outside the repo — a stable command for tests."""
    path = root / "gate-script.py"
    body = "import sys\n"
    if output:
        body += f"print({output!r})\n"
    body += f"sys.exit({exit_code})\n"
    path.write_text(body, encoding="utf-8")
    return f"{sys.executable} {path}"


def _evidence_records(root: Path) -> list[dict]:
    return _read_yaml(root, "evidence/evidence_records.yaml").get(
        "evidence_records"
    ) or []


# --- Pass flow: panel facts, forward-only write, verbatim refusals ------------------


def test_pass_panel_renders_server_fresh_facts(repo):
    _make_eligible(repo)
    title, body, status = views.pass_body(repo, NODE)
    assert status == 200
    assert title != ""
    # T5 §F: confirmation copy uses the human title; raw spec ids never render.
    assert "Confirm pass" in body
    # The panel's status rides the v3 semantic status tokens (the v2.4
    # ``safety-accent`` class is superseded history).
    assert "status-label info" in body
    assert SPEC not in body
    assert 'method="post"' in body
    # No pre-disabled state — the button is always clickable.
    assert "disabled" not in body.split('type="submit"')[0].rsplit("<button", 1)[-1]


def _notice_of(redirect: Redirect) -> tuple[str, str]:
    query = parse_qs(redirect.location.partition("?")[2].partition("#")[0])
    return (query.get("notice") or [""])[0], (query.get("kind") or [""])[0]


def test_pass_round_trip_writes_forward_only_with_web_source(repo):
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}")
    _, kind = _notice_of(result)
    assert kind == "ok"

    assert _state_of(repo, NODE) == "passed"
    events = _events(repo)
    assert [e["command"] for e in events] == ["pass"]
    assert events[0]["args"]["node_id"] == NODE
    assert events[0]["args"]["source"] == "web"


def test_pass_refusal_redirects_to_step_with_warning_and_writes_nothing(repo):
    """T5 §D1: every POST → 303 — refusals flash back to the pass step."""
    from skilltrace.web.interface import forbidden_matches

    _set_state(repo, NODE, "available")  # no evidence — ineligible
    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/pass?")
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert notice
    assert forbidden_matches(notice) == []
    assert "--" not in notice and "exit code" not in notice.lower()
    assert _state_of(repo, NODE) == "available"
    assert _events(repo) == []


def test_locked_node_refusal_names_the_hard_boundary(repo):
    node_id = next(
        n.id
        for n in sorted(load_context_lenient(repo).nodes, key=lambda n: n.id)
        if load_context_lenient(repo).store.state_of(n.id) == "locked"
    )
    result = views.post_pass(repo, node_id, _form())
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "locked" in notice
    assert "no hard-prerequisite override" in notice


def test_stale_panel_cannot_assert_what_eligibility_no_longer_supports(repo):
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    _, before, _ = views.pass_body(repo, NODE)
    assert "ready to mark as passed" in before

    # The world moves under the open panel: two of three records vanish.
    _make_eligible(repo, count=2)
    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "below the minimum" in notice  # refusal flashes back to the step
    assert _state_of(repo, NODE) == "available"
    assert _events(repo) == []


def test_the_pass_refusal_carries_the_clis_own_refusal_text(repo):
    """The flash is the dispatcher's refusal, rendered — not web prose (#357).

    The notice is the command's own refusal line through the one
    translation module (P3.1): the web never invents its own refusal.
    """
    from skilltrace.web.interface import translate
    from skilltrace.web.views.writes import _dispatch_web

    _set_state(repo, NODE, "available")  # no evidence — ineligible
    result = views.post_pass(repo, NODE, _form())
    notice, kind = _notice_of(result)
    assert kind == "warning"

    exit_code, lines = _dispatch_web(repo, "pass", node_id=NODE)
    assert exit_code == 2
    cli_line = next(line for line in lines if "is not pass-eligible" in line)
    stripped = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", cli_line).strip()
    assert translate(stripped) in notice
    # The refusal names the skill, never a raw record id (R1).
    assert NODE not in notice
    assert SPEC not in notice


def test_a_refused_pass_keeps_the_context_and_refreshes_the_facts(repo):
    """IC-9/R4/R5: the refusal returns to the step, in the same context.

    The learner is put back where they were — the pass step, in the
    presentation they were reading — with the facts re-read from current
    truth and the next valid route named. Nothing changed on disk.
    """
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    _, before, _ = views.pass_body(repo, NODE, {"mode": ["operations"]})
    assert "ready to mark as passed" in before

    # The world moves under the open panel: the proof falls short.
    _make_eligible(repo, count=2)
    result = views.post_pass(repo, NODE, _form(mode="operations"))
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/pass?")
    assert "mode=operations" in result.location
    _, kind = _notice_of(result)
    assert kind == "warning"

    # No partial state change: the state stands, no event, no record.
    assert _state_of(repo, NODE) == "available"
    assert _events(repo) == []
    assert _evidence_records(repo)

    # The refreshed panel states the current facts and names the next route.
    _, after, _ = views.pass_body(repo, NODE, {"mode": ["operations"]})
    assert "ready to mark as passed" not in after
    assert "Next step" in after
    assert f'href="/nodes/{NODE}/evidence"' in after


def test_a_pass_refusal_never_lands_on_the_host_page(repo):
    """The refusal flashes back to the pass step, not to the skill page."""
    _set_state(repo, NODE, "available")
    result = views.post_pass(repo, NODE, _form(next=f"/nodes/{NODE}"))
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/pass?")
    assert f"/nodes/{NODE}?" not in result.location


def test_the_pass_write_lands_the_learner_on_the_panel(repo):
    """IC-5/AX-7: the fresh page starts at the panel, not at the top."""
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    assert result.location.endswith("#pass-panel")
    # And the panel the redirect lands on carries that anchor.
    _, body, _ = views.pass_body(repo, NODE, {})
    assert 'id="pass-panel"' in body


def test_a_pass_operational_failure_writes_nothing(repo):
    """An unreadable store is an operational failure, never a silent pass."""
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    (repo / "graph" / "state.yaml").write_text("progress: [oops\n", encoding="utf-8")

    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "error"
    assert "/health" in notice
    assert _events(repo) == []


def test_web_refusal_is_translated_not_verbatim_cli(repo):
    """T5 P3.5: refusals are translated human copy — no CLI voice in the flash."""
    from skilltrace.web.interface import forbidden_matches

    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    notice, _ = _notice_of(result)
    assert notice
    assert forbidden_matches(notice) == []
    assert "skilltrace" not in notice.lower()
    assert "exit code" not in notice.lower()


# --- Master flow: two steps, friction matches irreversibility ----------------------


def _complete_spaced_review(repo: Path, node_id: str, *, days_after_pass: int) -> None:
    store = load_context_lenient(repo).store
    pass_day = datetime.fromisoformat(passed_at_of(store, node_id)[:10]).date()
    completed = pass_day + timedelta(days=days_after_pass)
    _write_yaml(
        repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{node_id}.001",
                    "node_id": node_id,
                    "status": "completed",
                    "scheduled_for": (pass_day + timedelta(days=1)).isoformat(),
                    "created_at": f"{completed.isoformat()}T09:00:00+00:00",
                    "completed_at": f"{completed.isoformat()}T10:00:00+00:00",
                    "outcome": "satisfactory",
                    "result_summary": "Recalled cleanly.",
                }
            ]
        },
    )


def test_master_step_one_shows_mastery_facts(repo):
    title, body, status = views.master_body(repo, NODE)
    assert status == 200
    assert "Step 1" in body
    assert "Mastery facts" in body
    assert "status-label warning" in body
    assert "Review spacing" in body


def test_master_requires_two_posts_and_refuses_in_step_two(repo):
    """T5 §D1+P4.4: master refusal is a 303 back to the confirm step."""
    _set_state(repo, NODE, "available")
    result = views.post_master_confirm(repo, NODE, _form())
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/master/confirm?")
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "mastery" in notice.lower()
    assert _state_of(repo, NODE) == "available"


def test_master_round_trip_through_permanent_confirm(repo):
    _write_yaml(
        repo,
        "policy/mastery_promotion.yaml",
        {
            "mastery_promotion_policy": {
                "min_accepted_evidence": 1,
                "min_days_pass_to_review": 3,
            }
        },
    )
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    assert isinstance(views.post_pass(repo, NODE, _form()), Redirect)

    _complete_spaced_review(repo, NODE, days_after_pass=3)
    result = views.post_master_confirm(repo, NODE, _form())
    assert isinstance(result, Redirect)
    assert _state_of(repo, NODE) == "mastered"

    commands = [e["command"] for e in _events(repo)]
    assert commands == ["pass", "master"]
    assert all(e["args"]["source"] == "web" for e in _events(repo))


# --- G5 daily writes: lightweight forms over the same registry ---------------------


def test_start_round_trip_marks_active_lightweight(repo):
    _set_state(repo, NODE, "available")
    result = views.post_start(repo, NODE, _form(template="", next=f"/nodes/{NODE}"))
    assert isinstance(result, Redirect)
    notice, _ = _notice_of(result)
    assert "opened session" in notice
    assert _state_of(repo, NODE) == "active"
    sessions = _read_yaml(repo, "execution/sessions.yaml").get("sessions") or []
    assert len(sessions) == 1 and sessions[0]["status"] == "open"


def test_second_start_refuses_with_single_open_session_copy(repo):
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    result = views.post_start(repo, NODE, _form())
    assert isinstance(result, Redirect)  # plain write: warning flash back home
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "already open" in notice
    sessions = _read_yaml(repo, "execution/sessions.yaml").get("sessions") or []
    assert len(sessions) == 1


def test_a_refused_second_start_lands_on_the_cockpit_and_names_both_options(repo):
    """R5: the refusal itself is recoverable — no hint ladder, no raw ids."""
    from skilltrace.web.interface import forbidden_matches

    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    events_before = _events(repo)
    assert [event["command"] for event in events_before] == ["start"]
    assert events_before[0]["args"]["source"] == "web"
    work_before = _read_yaml(repo, "execution/session_work.yaml")
    sessions_before = _read_yaml(repo, "execution/sessions.yaml")

    result = views.post_start(repo, NODE, _form(next="/"))
    assert isinstance(result, Redirect)
    assert result.location.startswith("/session?")
    notice, kind = _notice_of(result)
    assert kind == "warning"
    # The CLI's own refusal (a Session is already open), translated to the
    # two real options; no CLI voice leaks through.
    assert "already open" in notice
    assert "Add work to it, or close it first." in notice
    assert forbidden_matches(notice) == []
    # Pin the source: the notice is the dispatcher's own refusal line, not a
    # hand-written web sentence (exit 2, no event).
    from skilltrace.web.interface import translate
    from skilltrace.web.views.writes import _dispatch_web

    exit_code, lines = _dispatch_web(repo, "start", node_id=NODE, template=None)
    assert exit_code == 2
    cli_line = next(line for line in lines if "is already open" in line)
    stripped = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", cli_line).strip()
    assert translate(stripped) == notice
    # A refusal writes nothing: one start event, one session, one work row.
    assert _events(repo) == events_before
    assert _read_yaml(repo, "execution/sessions.yaml") == sessions_before
    assert _read_yaml(repo, "execution/session_work.yaml") == work_before


def test_work_blocked_requires_notes_translated(repo):
    """T5 P3.5: the blocked-work refusal names the requirement with no flags."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    result = views.post_work(
        repo, _form(node_id=NODE, blocked="1", minutes="", next="/")
    )
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "blocked work requires" in notice
    assert "--notes" not in notice

    ok = views.post_work(
        repo, _form(node_id=NODE, blocked="1", notes="stuck on X", minutes="25")
    )
    assert isinstance(ok, Redirect)
    work_rows = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert work_rows[-1]["blocked"] is True
    assert work_rows[-1]["minutes"] == 25


def test_blocked_work_never_creates_a_blocker(repo):
    """Blocked work is a session observation; only the explicit command records one."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())

    result = views.post_work(
        repo,
        _form(node_id=NODE, blocked="1", notes="stuck on X", minutes="25"),
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "ok"

    assert _read_yaml(repo, "execution/blockers.yaml").get("blockers") in (
        None,
        [],
    )
    assert [e["command"] for e in _events(repo)] == ["start", "work"]
    work_rows = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert work_rows[-1]["blocked"] is True


def test_work_without_open_session_refuses_like_cli(repo):
    result = views.post_work(repo, _form(node_id=NODE))
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "no session is open" in notice


def test_work_bad_minutes_is_a_warning_flash(repo):
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    result = views.post_work(repo, _form(node_id=NODE, minutes="abc"))
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "minutes must be an integer." in notice


def test_work_on_a_locked_node_is_refused_without_a_record(repo):
    """HB-4: no override; the refusal names the lock and writes nothing."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    locked = _first_locked_node(repo)
    work_before = _read_yaml(repo, "execution/session_work.yaml")
    events_before = _events(repo)

    result = views.post_work(repo, _form(node_id=locked, notes="x", next="/session"))
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "locked" in notice
    assert "no work can be recorded" in notice
    assert locked not in notice  # R1: a readable sentence, not a raw id
    assert _read_yaml(repo, "execution/session_work.yaml") == work_before
    assert _events(repo) == events_before


@pytest.mark.parametrize("asserted_state", ["passed", "mastered"])
def test_work_on_an_asserted_node_stays_history_and_never_demotes(repo, asserted_state):
    """HB-3: the work row is honest history; the asserted state stands."""
    _set_state(repo, NODE, asserted_state)
    views.post_start(repo, NODE, _form())
    assert _state_of(repo, NODE) == asserted_state

    result = views.post_work(
        repo, _form(node_id=NODE, notes="revisited the examples", minutes="10")
    )
    assert isinstance(result, Redirect)
    _, kind = _notice_of(result)
    assert kind == "ok"
    assert _state_of(repo, NODE) == asserted_state
    work_rows = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert work_rows[-1]["node_id"] == NODE
    assert work_rows[-1]["notes"] == "revisited the examples"
    commands = [e["command"] for e in _events(repo)]
    assert commands == ["start", "work"]
    assert all(e["args"]["source"] == "web" for e in _events(repo))


def test_work_operational_failure_writes_nothing_and_points_at_health(repo):
    """SC-00a/IC-8: a failure is not a refusal and never fabricates a record."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    work_before = _read_yaml(repo, "execution/session_work.yaml")
    events_before = _events(repo)
    # The record store becomes unreadable — an operational failure, not a
    # domain refusal.
    (repo / "execution" / "sessions.yaml").write_text(
        "sessions: [oops\n", encoding="utf-8"
    )

    result = views.post_work(repo, _form(node_id=NODE, notes="x", next="/session"))
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "error"
    assert "/health" in notice
    assert _read_yaml(repo, "execution/session_work.yaml") == work_before
    assert _events(repo) == events_before


# --- #343: the Log work form carries the canonical node id ----------------------


def _work_form_of(body: str) -> str | None:
    """The rendered Log work form — the exact markup the learner submits.

    ``None`` when the page carries no work form, which is the honest
    answer for a page with no open session.
    """
    match = re.search(r'<form method="post" action="/work">.*?</form>', body, re.S)
    return match.group(0) if match else None


def test_rendered_log_work_form_carries_the_canonical_node_id(repo):
    """#343: the id rides a hidden input — the learner never infers or types it.

    The work form lives in the cockpit, and the node page carries it only
    while a session is open (R6, IC-3): a page load records nothing.
    """
    # The work form exists only while a session is open (R6, IC-3).
    _, body, _ = views.session_body(repo)
    assert _work_form_of(body) is None

    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.work.001",
                    "status": "open",
                    "started_at": "2026-09-10T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.work.001.01",
                    "session_id": "ses.work.001",
                    "node_id": NODE,
                    "created_at": "2026-09-10T10:30:00+00:00",
                    "minutes": 20,
                }
            ]
        },
    )
    _, body, _ = views.session_body(repo)
    form = _work_form_of(body)
    assert form is not None
    assert f'<input type="hidden" name="node_id" value="{NODE}">' in form


def test_work_missing_node_id_refuses_without_writing(repo):
    """#343: no node id → warning flash, no SessionWork row, no event."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    work_before = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []

    result = views.post_work(repo, _form(notes="x", minutes="5", next=f"/nodes/{NODE}"))

    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "node id" in notice
    work_after = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert len(work_after) == len(work_before)
    assert [e["command"] for e in _events(repo)] == ["start"]


def test_work_unknown_node_id_refuses_without_writing(repo):
    """#343: an id the graph does not know refuses through the dispatcher, no write."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    work_before = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []

    result = views.post_work(repo, _form(node_id="no.such.node", notes="x"))

    assert isinstance(result, Redirect)
    _, kind = _notice_of(result)
    assert kind == "warning"
    work_after = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert len(work_after) == len(work_before)
    assert [e["command"] for e in _events(repo)] == ["start"]


def test_session_close_honest_end_refuses_future(repo):
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    events_before = _events(repo)
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(
        timespec="seconds"
    )
    result = views.post_session_close(repo, _form(end=future))
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "in the future" in notice
    # §10.6: a refused close discards nothing and keeps closure available.
    assert result.location.startswith("/session/close?")
    assert _events(repo) == events_before
    sessions = _read_yaml(repo, "execution/sessions.yaml").get("sessions") or []
    assert sessions[0]["status"] == "open"
    _, body, _ = views.session_close_body(repo)
    assert "Close the session" in body

    ok = views.post_session_close(repo, _form())
    assert isinstance(ok, Redirect)
    sessions = _read_yaml(repo, "execution/sessions.yaml").get("sessions") or []
    assert sessions[0]["status"] == "completed"
    # Closing implies no progress change at all (C05, HB-3).
    assert _state_of(repo, NODE) == "active"
    commands = [e["command"] for e in _events(repo)]
    assert commands == ["start", "session close"]
    assert all(e["args"]["source"] == "web" for e in _events(repo))


def test_a_stale_session_closes_with_an_honest_past_end_time(repo):
    """A forgotten Session may record when the learner actually stopped."""
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    sessions = _read_yaml(repo, "execution/sessions.yaml")
    started = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(
        timespec="seconds"
    )
    sessions["sessions"][0]["started_at"] = started
    _write_yaml(repo, "execution/sessions.yaml", sessions)
    ended = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(
        timespec="seconds"
    )

    result = views.post_session_close(repo, _form(end=ended))
    assert isinstance(result, Redirect)
    _, kind = _notice_of(result)
    assert kind == "ok"
    session = (_read_yaml(repo, "execution/sessions.yaml").get("sessions") or [])[0]
    assert session["status"] == "completed"
    assert session["ended_at"] == ended
    assert _state_of(repo, NODE) == "active"
    assert [e["command"] for e in _events(repo)] == ["start", "session close"]


def test_blocker_create_then_resolve_round_trip(repo):
    """Each explicit action writes one audit event; a refusal writes nothing."""
    result = views.post_blocker_create(
        repo, NODE, _form(description="stuck on recursion", next=f"/nodes/{NODE}")
    )
    assert isinstance(result, Redirect)
    blockers = _read_yaml(repo, "execution/blockers.yaml").get("blockers") or []
    assert blockers[0]["status"] == "open"
    events = _events(repo)
    assert [e["command"] for e in events] == ["blocker create"]
    assert events[0]["args"]["source"] == "web"
    assert events[0]["records_touched"] == [blockers[0]["id"]]

    before = _read_yaml(repo, "execution/blockers.yaml")
    again = views.post_blocker_create(repo, NODE, _form(description="still stuck"))
    notice = parse_qs(again.location.partition("?")[2])["notice"][0]
    assert "already has an open blocker" in notice
    # A duplicate warns but is not forbidden: the second record is written,
    # and it is its own explicit action with its own audit event.
    blockers = _read_yaml(repo, "execution/blockers.yaml").get("blockers") or []
    assert len(blockers) == len(before.get("blockers") or []) + 1
    events = _events(repo)
    assert [e["command"] for e in events] == ["blocker create", "blocker create"]

    resolved = views.post_blocker_resolve(
        repo, blockers[0]["id"], _form(summary="it clicked", next="/")
    )
    assert isinstance(resolved, Redirect)
    blockers = _read_yaml(repo, "execution/blockers.yaml").get("blockers") or []
    assert blockers[0]["status"] == "resolved"
    events = _events(repo)
    assert [e["command"] for e in events] == [
        "blocker create",
        "blocker create",
        "blocker resolve",
    ]
    assert events[-1]["args"]["source"] == "web"
    assert events[-1]["records_touched"] == [blockers[0]["id"]]

    before = _read_yaml(repo, "execution/blockers.yaml")
    terminal = views.post_blocker_resolve(
        repo, blockers[0]["id"], _form(summary="again")
    )
    notice = parse_qs(terminal.location.partition("?")[2])["notice"][0]
    assert "already resolved" in notice
    # Resolution is terminal: the second attempt writes no record and no event.
    assert _events(repo) == events
    assert _read_yaml(repo, "execution/blockers.yaml") == before


def test_blocker_create_requires_an_obstacle_description(repo):
    """A Blocker names its own obstacle; an empty refusal writes nothing."""
    result = views.post_blocker_create(repo, NODE, _form(description=""))
    assert isinstance(result, Redirect)
    _, kind = _notice_of(result)
    assert kind == "warning"
    assert _read_yaml(repo, "execution/blockers.yaml").get("blockers") in (None, [])
    assert _events(repo) == []


def test_blocker_create_is_refused_on_a_locked_node(repo):
    """What cannot be started cannot be stuck; the refusal writes nothing."""
    locked = _first_locked_node(repo)
    result = views.post_blocker_create(
        repo, locked, _form(description="stuck before starting")
    )
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "locked" in notice
    assert _read_yaml(repo, "execution/blockers.yaml").get("blockers") in (None, [])
    assert _events(repo) == []


def test_blocker_resolve_requires_a_summary_and_writes_nothing(repo):
    """Resolution names what changed; without it the record stays open."""
    views.post_blocker_create(repo, NODE, _form(description="stuck"))
    blocker = (_read_yaml(repo, "execution/blockers.yaml").get("blockers") or [])[0]
    before = _read_yaml(repo, "execution/blockers.yaml")

    result = views.post_blocker_resolve(repo, blocker["id"], _form(summary=""))
    assert isinstance(result, Redirect)
    _, kind = _notice_of(result)
    assert kind == "warning"
    assert _read_yaml(repo, "execution/blockers.yaml") == before
    assert [e["command"] for e in _events(repo)] == ["blocker create"]


def test_a_blocker_failure_writes_no_record_and_no_event(repo):
    """An unreadable store is an operational failure, never a silent write."""
    (repo / "execution").mkdir()
    (repo / "execution" / "blockers.yaml").write_text(
        "blockers: not-a-list\n", encoding="utf-8"
    )
    created = views.post_blocker_create(repo, NODE, _form(description="stuck"))
    assert isinstance(created, Redirect)
    assert _notice_of(created)[1] == "error"
    resolved = views.post_blocker_resolve(repo, "blk.nope.001", _form(summary="x"))
    assert isinstance(resolved, Redirect)
    assert _notice_of(resolved)[1] == "error"
    assert _events(repo) == []


def test_resolving_a_blocker_closes_no_session_completes_no_work_and_passes_no_node(
    repo,
):
    """Resolution touches exactly one record: the Blocker."""
    _set_state(repo, NODE, "available")
    started = views.post_start(repo, NODE, _form())
    assert isinstance(started, Redirect)
    assert _notice_of(started)[1] == "ok"
    created = views.post_blocker_create(
        repo, NODE, _form(description="stuck halfway")
    )
    assert isinstance(created, Redirect)
    assert _notice_of(created)[1] == "ok"
    blocker = (_read_yaml(repo, "execution/blockers.yaml").get("blockers") or [])[0]

    sessions_before = _read_yaml(repo, "execution/sessions.yaml")
    work_before = _read_yaml(repo, "execution/session_work.yaml")

    result = views.post_blocker_resolve(
        repo, blocker["id"], _form(summary="it clicked", next="/session")
    )
    assert isinstance(result, Redirect)

    # The Session is untouched, the recorded work is untouched, and the node
    # keeps its asserted state (HB-3).
    assert _read_yaml(repo, "execution/sessions.yaml") == sessions_before
    assert _read_yaml(repo, "execution/session_work.yaml") == work_before
    assert _state_of(repo, NODE) == "active"
    assert [e["command"] for e in _events(repo)] == [
        "start",
        "blocker create",
        "blocker resolve",
    ]


def test_evidence_submit_manual_accept_freezes_record(repo):
    _set_state(repo, NODE, "available")
    result = views.post_evidence(
        repo,
        NODE,
        _form(location="evidence/math/set_001.md", verdict="accept"),
    )
    assert isinstance(result, Redirect)
    records = _read_yaml(repo, "evidence/evidence_records.yaml")["evidence_records"]
    assert records[0]["accepted"] is True
    assert records[0]["accepted_by"] == "learner_manual"
    assert records[0]["artifact_hash"].startswith("sha256:")


def test_evidence_submit_rejected_verdict_writes_and_exit_zero(repo):
    _set_state(repo, NODE, "available")
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_002.md", verdict="reject")
    )
    assert isinstance(result, Redirect)  # a written rejection is a success
    assert "rejected" in result.location
    records = _read_yaml(repo, "evidence/evidence_records.yaml")["evidence_records"]
    assert records[0]["accepted"] is False


def test_evidence_submit_supersede_drops_old_from_live_count(repo):
    _set_state(repo, NODE, "available")
    views.post_evidence(repo, NODE, _form(location="evidence/math/a.md", verdict="accept"))
    result = views.post_evidence(
        repo,
        NODE,
        _form(
            location="evidence/math/b.md",
            verdict="accept",
            supersedes=f"ev.{NODE}.001",
            reason="wrong file first",
        ),
    )
    assert isinstance(result, Redirect)
    from skilltrace.evidence.evidence import load_evidence_records

    records = load_evidence_records(repo)
    from skilltrace.evidence.eligibility import live_accepted_count

    assert live_accepted_count(records, SPEC) == 1
    assert records[-1].supersedes == f"ev.{NODE}.001"


def test_missing_location_warns_instead_of_crashing(repo):
    result = views.post_evidence(repo, NODE, _form(verdict="accept"))
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "artifact location" in notice


# --- Evidence write round-trips: one record, one canonical audit event -------------


def test_manual_accept_writes_one_record_and_one_canonical_event(repo):
    _set_state(repo, NODE, "available")
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_001.md", verdict="accept")
    )
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/evidence?")
    assert _notice_of(result)[1] == "ok"

    records = _evidence_records(repo)
    assert len(records) == 1
    assert records[0]["accepted"] is True
    assert records[0]["accepted_by"] == "learner_manual"

    events = _events(repo)
    assert len(events) == 1
    assert events[0]["command"] == "evidence submit"
    assert events[0]["args"]["source"] == "web"
    assert events[0]["records_touched"] == [records[0]["id"]]


def test_manual_reject_is_an_honest_record_not_a_failure(repo):
    _set_state(repo, NODE, "available")
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_002.md", verdict="reject")
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "ok"

    records = _evidence_records(repo)
    assert len(records) == 1 and records[0]["accepted"] is False
    events = _events(repo)
    assert len(events) == 1
    assert events[0]["command"] == "evidence submit"


def test_manual_submit_without_a_verdict_refuses_and_writes_nothing(repo):
    _set_state(repo, NODE, "available")
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_003.md")
    )
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "explicit verdict" in notice
    assert _evidence_records(repo) == []
    assert _events(repo) == []


def test_correction_requires_a_reason_and_writes_nothing_without_one(repo):
    _set_state(repo, NODE, "available")
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/a.md", verdict="accept")
    )
    events_before = list(_events(repo))
    result = views.post_evidence(
        repo,
        NODE,
        _form(
            location="evidence/math/b.md",
            verdict="accept",
            supersedes=f"ev.{NODE}.001",
        ),
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "warning"
    assert len(_evidence_records(repo)) == 1
    assert _events(repo) == events_before


def test_correction_supersedes_visibly_and_keeps_the_prior_record(repo):
    _set_state(repo, NODE, "available")
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/a.md", verdict="accept")
    )
    original = _evidence_records(repo)[0]

    result = views.post_evidence(
        repo,
        NODE,
        _form(
            location="evidence/math/b.md",
            verdict="accept",
            supersedes=original["id"],
            reason="the first file was the wrong attempt",
        ),
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "ok"

    records = _evidence_records(repo)
    assert len(records) == 2
    assert records[0] == original  # immutable: the prior record is untouched
    assert records[1]["supersedes"] == original["id"]
    assert records[1]["supersede_reason"]

    from skilltrace.evidence.eligibility import live_accepted_count
    from skilltrace.evidence.evidence import load_evidence_records

    assert live_accepted_count(load_evidence_records(repo), SPEC) == 1

    events = _events(repo)
    assert [event["command"] for event in events] == [
        "evidence submit",
        "evidence submit",
    ]
    assert events[-1]["records_touched"] == [records[1]["id"]]


def test_objective_gate_accepts_and_freezes_the_receipt(repo):
    _set_state(repo, NODE, "available")
    _make_objective_gate(repo, _gate_script(repo, exit_code=0, output="ok"))
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_004.md")
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "ok"

    record = _evidence_records(repo)[0]
    assert record["accepted"] is True
    assert record["accepted_by"] == "objective_gate"
    receipt = record["gate_run"]
    assert receipt["exit_class"] == "passed"
    assert receipt["exit_code"] == 0
    assert receipt["command_argv"][0] == sys.executable
    assert "evidence/math/set_004.md" in receipt["inputs"]
    assert receipt["stdout_hash"].startswith("sha256:")
    assert len(_events(repo)) == 1


def test_failing_objective_gate_records_a_rejection_not_a_command_failure(repo):
    _set_state(repo, NODE, "available")
    _make_objective_gate(repo, _gate_script(repo, exit_code=1, output="bad"))
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_005.md")
    )
    assert isinstance(result, Redirect)
    assert _notice_of(result)[1] == "ok"

    record = _evidence_records(repo)[0]
    assert record["accepted"] is False
    assert record["gate_run"]["exit_class"] == "failed"
    events = _events(repo)
    assert len(events) == 1
    assert events[0]["command"] == "evidence submit"


def test_unrunnable_gate_writes_no_record_and_names_the_recovery(repo):
    _set_state(repo, NODE, "available")
    _make_objective_gate(repo, "skilltrace-no-such-gate-command")
    result = views.post_evidence(
        repo, NODE, _form(location="evidence/math/set_006.md")
    )
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{NODE}/evidence?")
    notice, kind = _notice_of(result)
    assert kind == "error"
    assert "Nothing was recorded" in notice
    assert "submit again" in notice
    assert _evidence_records(repo) == []
    assert _events(repo) == []


# --- Evidence workspace: the wanted/recorded split, gates and corrections ----------


def test_evidence_workspace_shows_wanted_and_recorded_as_distinct_facts(repo):
    _set_state(repo, NODE, "available")
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/a.md", verdict="accept")
    )
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/b.md", verdict="reject")
    )
    _, body, status = views.node_evidence_body(repo, NODE, {})
    assert status == 200
    assert "Evidence wanted" in body
    assert "Evidence recorded" in body
    assert "3 records wanted" in body
    assert "1 accepted, 1 rejected, 0 superseded" in body
    assert "Some required evidence is still short" in body


def test_manual_gate_form_demands_a_verdict_with_no_default(repo):
    _set_state(repo, NODE, "available")
    _, body, _ = views.node_evidence_body(repo, NODE, {})
    verdict_radios = re.findall(
        r'<input type="radio" name="verdict"[^>]*>', body
    )
    assert len(verdict_radios) == 2
    assert all("required" in radio for radio in verdict_radios)
    assert all("checked" not in radio for radio in verdict_radios)
    assert "There is no default verdict" in body


def test_correction_is_a_separate_action_with_a_required_reason(repo):
    _set_state(repo, NODE, "available")
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/a.md", verdict="accept")
    )
    _, body, _ = views.node_evidence_body(repo, NODE, {})
    assert "Correct earlier evidence" in body
    assert 'name="supersedes"' in body
    reason_field = re.search(
        r'<input type="text" name="reason" id="correction-reason"[^>]*>', body
    )
    assert reason_field is not None
    assert "required" in reason_field.group(0)
    # No edit or delete affordance exists anywhere (HB-5).
    assert 'action="/evidence/delete' not in body
    assert 'action="/evidence/edit' not in body
    assert "edit record" not in body.lower()
    assert "delete record" not in body.lower()


def test_evidence_workspace_and_inspector_show_the_gate_run_receipt(repo):
    _set_state(repo, NODE, "available")
    _make_objective_gate(repo, _gate_script(repo, exit_code=0, output="ok"))
    views.post_evidence(
        repo, NODE, _form(location="evidence/math/receipt.md")
    )
    record = _evidence_records(repo)[0]

    _, body, _ = views.node_evidence_body(repo, NODE, {})
    assert "How the gate judged" in body
    assert "evidence/checks" not in body  # no invented receipt
    assert "evidence/math/receipt.md" in body
    assert record["gate_run"]["exit_class"] in body
    assert record["gate_run"]["stdout_hash"] in body

    _, index_body, _ = views.evidence_index_body(
        repo, {"record": [record["id"]]}
    )
    assert "Gate-run receipt" in index_body
    assert record["gate_run"]["stdout_hash"] in index_body


def test_an_optional_spec_never_becomes_an_eligibility_gap(repo):
    _set_state(repo, NODE, "available")
    doc = _read_yaml(repo, "evidence/artifact_specs.yaml")
    optional = {
        "id": f"{SPEC}.optional",
        "node_id": NODE,
        "title": "Optional worked notes",
        "artifact_kind": "note",
        "required": False,
        "minimum_count": 1,
    }
    doc["artifact_specs"].append(optional)
    _write_yaml(repo, "evidence/artifact_specs.yaml", doc)

    view = load_context_lenient(repo)
    figures = views.evidence_figures(view, NODE)
    assert figures.wanted_specs == 1
    assert figures.wanted_records == 3
    assert figures.optional_specs == 1

    _, body, _ = views.node_evidence_body(repo, NODE, {})
    assert "1 optional specification, not counted" in body
    assert "3 records wanted" in body


def test_optional_evidence_never_counts_toward_pass_eligibility(repo):
    _set_state(repo, NODE, "available")
    doc = _read_yaml(repo, "evidence/artifact_specs.yaml")
    optional_id = f"{SPEC}.optional"
    doc["artifact_specs"].append(
        {
            "id": optional_id,
            "node_id": NODE,
            "title": "Optional worked notes",
            "artifact_kind": "note",
            "required": False,
            "minimum_count": 1,
        }
    )
    _write_yaml(repo, "evidence/artifact_specs.yaml", doc)

    views.post_evidence(
        repo,
        NODE,
        _form(location="evidence/math/notes.md", spec=optional_id, verdict="accept"),
    )

    view = load_context_lenient(repo)
    from skilltrace.evidence.eligibility import live_accepted_count

    assert live_accepted_count(view.records, optional_id) == 1
    eligibility = views.compute_eligibility(
        NODE,
        view.specs_by_node[NODE],
        has_gate=NODE in view.has_gate,
        records=view.records,
        node_state=view.store.state_of(NODE),
    )
    assert eligibility.eligible is False
    assert [spec.spec_id for spec in eligibility.specs] == [SPEC]


# --- Host pages carry the forms; degradation warns but never blocks ----------------


def test_home_carries_the_top_pick_start_and_resumable_close(repo):
    """v2.4 S3: Today = focus CTA + count set; close rides the resumable line."""
    _, body, status = views.home_body(repo, {})
    assert status == 200
    # The queue's dominant action is the start of the top pick.
    assert 'action="/nodes/' in body and "/start" in body
    assert "Start studying" in body
    # No session is open on the fresh seed: the close affordance is absent.
    assert "SESSION STRIP" not in body
    assert 'action="/session/close"' not in body


def test_home_resumable_line_carries_close_while_a_session_is_open(repo):
    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.2026-09-10.001",
                    "status": "open",
                    "started_at": "2026-09-10T10:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.home_body(repo)
    # The resume action leads to the cockpit; closing is an explicit
    # command with its own panel, not an affordance on the home page.
    assert 'href="/session"' in body
    assert "Resume your session" in body
    # The session's raw id never reaches the learner.
    assert "ses.2026-09-10.001" not in body


def test_node_page_carries_write_actions_and_forms(repo):
    """The node page reaches each write in one step.

    It links to the destinations that own the writes — the evidence
    workspace, the pass panel, the mastery panel — and offers the start
    action for an available skill. The work form appears only while a
    session is open (R6, IC-3).
    """
    _, body, _ = views.node_body(repo, NODE, {})
    assert f'action="/nodes/{NODE}/start"' in body
    assert f'href="/nodes/{NODE}/evidence"' in body
    assert f'href="/nodes/{NODE}/pass"' in body
    assert f'href="/nodes/{NODE}/master"' in body
    # No work form without an open session.
    assert 'action="/work"' not in body


def test_a_locked_node_offers_no_start_and_no_wall_bypass(repo):
    """A locked skill offers nothing that could start it (HB-4).

    The pass and mastery panels are *linked* — the panel itself states
    the refusal, which is where the truth lives — but there is no start
    action and no way to begin the work.
    """
    locked = _first_locked_node(repo)
    _, locked_body, _ = views.node_body(repo, locked, {})
    assert f'action="/nodes/{locked}/start"' not in locked_body
    assert "No session is open" in locked_body


def test_the_mastery_panel_refuses_until_the_skill_is_passed(repo):
    """Mastering requires a passed skill; the panel says so and stops.

    The link is present — the panel is where the truth lives, and it
    states the refusal rather than the page hiding the destination.
    """
    _, body, _ = views.node_body(repo, NODE, {})
    assert f'href="/nodes/{NODE}/master"' in body
    _, panel, _ = views.master_body(repo, NODE)
    assert "Continue is unavailable" in panel
    assert "/master/confirm" not in panel


def _hrefs(body: str) -> str:
    import re

    return " ".join(re.findall(r'href="([^"]+)"', body))


def test_degraded_layers_warn_advisory_but_forms_stay_enabled(repo):
    (repo / "evidence" / "artifact_specs.yaml").write_text(
        "::: not yaml [", encoding="utf-8"
    )
    _, body, status = views.node_body(repo, NODE, {})
    assert status == 200
    assert "failed to load" in body
    assert "still works" in body  # advisory only — no P3.1 engine voice (T2/T4)
    assert f'action="/nodes/{NODE}/start"' in body


def test_flash_notice_escapes_hostile_text(repo):
    hostile = "<script>alert(1)</script>"
    query = {"notice": [hostile], "kind": ["ok"]}
    _, body, _ = views.node_body(repo, NODE, query)
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


# --- Full HTTP round-trip: PRG, the panel stays, audit source ------------------------

REVIEW_REASONS = {"min_accepted_evidence": 1, "min_days_pass_to_review": 3}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        return None


def _http_post(url: str, data: dict) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url, data=urlencode(data).encode("utf-8"), method="POST"
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request) as response:
            return (
                response.status,
                response.headers.get("Location", ""),
                response.read().decode("utf-8"),
            )
    except urllib.error.HTTPError as err:
        return (
            err.code,
            err.headers.get("Location", ""),
            err.read().decode("utf-8"),
        )


def _http_get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


@pytest.fixture
def running_server(tmp_path):
    import threading

    from skilltrace.web.server import make_server

    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    _make_eligible(tmp_path)
    _set_state(tmp_path, NODE, "available")
    server, failure = make_server(tmp_path, 0)
    assert server is not None, failure
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, tmp_path
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_http_pass_flow_redirects_refreshes_and_audits_web(running_server):
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"

    status, body = _http_get(f"{base}/nodes/{NODE}/pass")
    assert status == 200
    assert "Confirm pass" in body

    status, location, _ = _http_post(base + f"/nodes/{NODE}/pass", {})
    assert status == 303
    assert location.startswith(f"/nodes/{NODE}")

    status, body = _http_get(f"{base}/nodes/{NODE}")
    assert '<span class="pill passed">Passed</span>' in body

    events = _events(root)
    assert events[0]["command"] == "pass"
    assert events[0]["args"]["source"] == "web"


def test_http_refusal_redirects_to_step_without_an_event(running_server):
    """T5 §D1: HTTP refusal is a 303 back to the acceptance step, no event."""
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"
    other = "math.algebra.variables_expressions_01"  # no evidence submitted

    status, location, _ = _http_post(base + f"/nodes/{other}/pass", {})
    assert status == 303
    assert location.startswith(f"/nodes/{other}/pass?")
    assert _events(root) == []


def _submitted_fields(form_html: str) -> dict:
    """The fields a browser would submit for ``form_html`` — rendered values only.

    Inputs contribute their ``value`` (absent ``value`` → empty string, so a
    blank minutes field posts blank); an unchecked checkbox is omitted; a
    textarea contributes its rendered text content.
    """
    fields: dict = {}
    for tag in re.findall(r"<input\b[^>]*>", form_html):
        name = re.search(r'name="([^"]+)"', tag)
        if name is None:
            continue
        if 'type="checkbox"' in tag and "checked" not in tag:
            continue
        value = re.search(r'value="([^"]*)"', tag)
        fields[name.group(1)] = value.group(1) if value else ""
    for name, text in re.findall(
        r'<textarea name="([^"]+)">(.*?)</textarea>', form_html, re.S
    ):
        fields[name] = text
    return fields


def test_http_rendered_log_work_form_round_trips_into_session_work(running_server):
    """#343: submit the *rendered* Log work form — SessionWork lands via the dispatcher.

    The route-level write tests hand ``post_work`` a node id; this one proves
    the rendered form contract itself: GET the node page, take the fields the
    learner would actually submit, POST them, and find the work row (plus the
    ``work`` audit event with ``source: web``) in the seeded repo.
    """
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"

    status, location, _ = _http_post(base + f"/nodes/{NODE}/start", {"next": f"/nodes/{NODE}"})
    assert status == 303

    status, body = _http_get(base + f"/nodes/{NODE}")
    assert status == 200
    form = _work_form_of(body)
    fields = _submitted_fields(form)
    assert fields.get("node_id") == NODE  # the canonical id, never typed by the learner

    fields["notes"] = "rendered-form round trip"
    fields["minutes"] = "15"
    status, location, _ = _http_post(base + "/work", fields)
    assert status == 303
    assert location.startswith(f"/nodes/{NODE}")

    work_rows = _read_yaml(root, "execution/session_work.yaml").get("session_work") or []
    assert work_rows[-1]["node_id"] == NODE
    assert work_rows[-1]["notes"] == "rendered-form round trip"
    assert work_rows[-1]["minutes"] == 15

    events = _events(root)
    assert events[-1]["command"] == "work"
    assert events[-1]["args"]["source"] == "web"
    assert events[-1]["args"]["node_id"] == NODE


def test_http_cockpit_loads_record_nothing(running_server):
    """#354: page loads and inspections are not commands — no events, no work."""
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"

    for path in ("/session", "/session/close", "/"):
        status, _ = _http_get(base + path)
        assert status == 200
    assert _events(root) == []
    assert _read_yaml(root, "execution/session_work.yaml") == {}


def test_http_refused_second_start_lands_on_the_cockpit_without_an_event(running_server):
    """#354/R5: the refusal is a fresh cockpit page naming the two options."""
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"

    status, _, _ = _http_post(base + f"/nodes/{NODE}/start", {"next": f"/nodes/{NODE}"})
    assert status == 303
    events_before = _events(root)
    assert [event["command"] for event in events_before] == ["start"]

    status, location, _ = _http_post(
        base + f"/nodes/{NODE}/start", {"next": f"/nodes/{NODE}"}
    )
    assert status == 303
    assert location.startswith("/session?")
    status, body = _http_get(base + location)
    assert status == 200
    # The CLI's own refusal, translated: the session is open and the two
    # real options are named, with the cockpit itself one line below.
    assert "A session is already open" in body
    assert "Add work to it, or close it first" in body
    assert "A second session cannot be started while this one is open" in body
    # A refusal writes nothing: still one start event, one session.
    assert _events(root) == events_before
    sessions = _read_yaml(root, "execution/sessions.yaml").get("sessions") or []
    assert len(sessions) == 1
