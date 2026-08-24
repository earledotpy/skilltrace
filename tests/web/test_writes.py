"""Browser writes — Tier-1 slice T4 (issue #73): safety modals + daily writes.

What only the wired write surface can show: every mutation nests-dispatch
through the *same* registry the CLI uses (`Context.source="web"`, canonical
command name, one audit event), hard-boundary refusals match the CLI's own
output verbatim, the pass/master modals render server-fresh facts and never
pre-disable (a stale modal is proven unable to assert what eligibility no
longer supports), heavyweight confirmation stays exclusive to pass/master,
and the G5 daily writes round-trip through their forms with redirect-after-POST.
"""

from __future__ import annotations

import shutil
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


# --- Pass flow: modal facts, forward-only write, verbatim refusals -----------------


def test_pass_modal_renders_server_fresh_facts(repo):
    _make_eligible(repo)
    title, body, status = views.pass_modal_body(repo, NODE)
    assert status == 200
    assert title != ""
    assert NODE in body
    assert SPEC in body  # per-required-spec breakdown present
    assert "Confirm pass" in body
    assert 'method="post"' in body
    # No pre-disabled state — the button is always clickable.
    assert "disabled" not in body.split('type="submit"')[0].rsplit("<button", 1)[-1]


def _notice_of(redirect: Redirect) -> tuple[str, str]:
    query = parse_qs(redirect.location.partition("?")[2])
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


def test_pass_refusal_stays_in_modal_verbatim_and_writes_nothing(repo):
    _set_state(repo, NODE, "available")  # no evidence — ineligible
    result = views.post_pass(repo, NODE, _form())
    assert not isinstance(result, Redirect)
    title, body, status = result
    assert status == 200  # modal stays open
    assert "is not pass-eligible" in body
    assert "nothing passed" in body
    assert _state_of(repo, NODE) == "available"
    assert _events(repo) == []


def test_locked_node_refusal_names_the_hard_boundary(repo):
    node_id = next(
        n.id
        for n in sorted(load_context_lenient(repo).nodes, key=lambda n: n.id)
        if load_context_lenient(repo).store.state_of(n.id) == "locked"
    )
    result = views.post_pass(repo, node_id, _form())
    _, body, status = result
    assert status == 200
    assert "locked" in body
    assert "no hard-prerequisite override" in body


def test_stale_modal_cannot_assert_what_eligibility_no_longer_supports(repo):
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    _, before, _ = views.pass_modal_body(repo, NODE)
    assert "currently holds" in before

    # The world moves under the open modal: two of three records vanish.
    _make_eligible(repo, count=2)
    result = views.post_pass(repo, NODE, _form())
    _, body, _ = result
    assert "below minimum" in body  # refusal rendered verbatim inline
    assert _state_of(repo, NODE) == "available"
    assert _events(repo) == []


def test_web_refusal_matches_cli_output_verbatim(repo):
    from skilltrace.cli import run as cli_run
    from contextlib import redirect_stdout
    from io import StringIO

    buffer = StringIO()
    with redirect_stdout(buffer):
        cli_run(["pass", NODE], root=repo)
    cli_lines = [line for line in buffer.getvalue().splitlines() if line.strip()]

    _, web_lines = views._dispatch_web(repo, "pass", node_id=NODE)
    assert [line.strip() for line in web_lines if line.strip()] == [
        line.strip() for line in cli_lines if line.strip()
    ]


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
    assert "MASTERY FACTS" in body
    assert "Review spacing policy" in body


def test_master_requires_two_posts_and_refuses_in_step_two(repo):
    _set_state(repo, NODE, "available")
    result = views.post_master_confirm(repo, NODE, _form())
    _, body, status = result
    assert status == 200  # confirm step re-renders with the refusal
    assert "mastery" in body.lower()
    assert "never moves backward" in body or "not mastery-eligible" in body
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


def test_work_blocked_requires_notes_verbatim(repo):
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    result = views.post_work(
        repo, _form(node_id=NODE, blocked="1", minutes="", next="/")
    )
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "blocked work requires --notes" in notice

    ok = views.post_work(
        repo, _form(node_id=NODE, blocked="1", notes="stuck on X", minutes="25")
    )
    assert isinstance(ok, Redirect)
    work_rows = _read_yaml(repo, "execution/session_work.yaml").get("session_work") or []
    assert work_rows[-1]["blocked"] is True
    assert work_rows[-1]["minutes"] == 25


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


def test_session_close_honest_end_refuses_future(repo):
    _set_state(repo, NODE, "available")
    views.post_start(repo, NODE, _form())
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(
        timespec="seconds"
    )
    result = views.post_session_close(repo, _form(end=future))
    notice = parse_qs(result.location.partition("?")[2])["notice"][0]
    assert "in the future" in notice

    ok = views.post_session_close(repo, _form())
    assert isinstance(ok, Redirect)
    sessions = _read_yaml(repo, "execution/sessions.yaml").get("sessions") or []
    assert sessions[0]["status"] == "completed"


def test_blocker_create_then_resolve_round_trip(repo):
    result = views.post_blocker_create(
        repo, NODE, _form(description="stuck on recursion", next=f"/nodes/{NODE}")
    )
    assert isinstance(result, Redirect)
    blockers = _read_yaml(repo, "execution/blockers.yaml").get("blockers") or []
    assert blockers[0]["status"] == "open"

    again = views.post_blocker_create(repo, NODE, _form(description="still stuck"))
    notice = parse_qs(again.location.partition("?")[2])["notice"][0]
    assert "already has an open blocker" in notice

    resolved = views.post_blocker_resolve(
        repo, blockers[0]["id"], _form(summary="it clicked", next="/")
    )
    assert isinstance(resolved, Redirect)
    blockers = _read_yaml(repo, "execution/blockers.yaml").get("blockers") or []
    assert blockers[0]["status"] == "resolved"

    terminal = views.post_blocker_resolve(
        repo, blockers[0]["id"], _form(summary="again")
    )
    notice = parse_qs(terminal.location.partition("?")[2])["notice"][0]
    assert "already resolved" in notice


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
    from skilltrace.evidence.records import load_evidence_records

    records = load_evidence_records(repo)
    from skilltrace.evidence.eligibility import live_accepted_count

    assert live_accepted_count(records, SPEC) == 1
    assert records[-1].supersedes == f"ev.{NODE}.001"


def test_missing_location_warns_instead_of_crashing(repo):
    result = views.post_evidence(repo, NODE, _form(verdict="accept"))
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert "location is required" in notice


# --- Host pages carry the forms; degradation warns but never blocks ----------------


def test_home_carries_session_strip_and_top_pick_start(repo):
    _, body, status = views.home_body(repo, {})
    assert status == 200
    assert "SESSION STRIP" in body
    assert 'action="/work"' in body
    assert 'action="/session/close"' in body
    assert "START HERE" in body
    assert "progress never moves backward" in body


def test_node_page_carries_write_actions_and_forms(repo):
    _, body, _ = views.node_body(repo, NODE, {})
    assert "WRITE ACTIONS" in body
    assert f'action="/nodes/{NODE}/start"' in body
    assert 'action="/work"' in body
    assert f'href="/nodes/{NODE}/pass"' in body
    assert f'href="/nodes/{NODE}/master"' in body
    assert 'action="/work"' in body
    assert f'action="/nodes/{NODE}/blockers"' in body
    assert f'action="/nodes/{NODE}/evidence"' in body


def test_degraded_layers_warn_advisory_but_forms_stay_enabled(repo):
    (repo / "evidence" / "artifact_specs.yaml").write_text(
        "::: not yaml [", encoding="utf-8"
    )
    _, body, status = views.node_body(repo, NODE, {})
    assert status == 200
    assert "failed to load" in body
    assert "forms stay enabled" in body
    assert f'action="/nodes/{NODE}/start"' in body


def test_flash_notice_escapes_hostile_text(repo):
    hostile = "<script>alert(1)</script>"
    query = {"notice": [hostile], "kind": ["ok"]}
    _, body, _ = views.node_body(repo, NODE, query)
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


# --- Full HTTP round-trip: PRG, modal stays, audit source --------------------------

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
    from skilltrace.web.server import make_server
    import threading

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


def test_http_refusal_keeps_modal_open_without_an_event(running_server):
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"
    other = "math.algebra.variables_expressions_01"  # no evidence submitted

    status, _, body = _http_post(base + f"/nodes/{other}/pass", {})
    assert status == 200
    assert "is not pass-eligible" in body
    assert _events(root) == []
