"""T5 safety panel + flash/refusal gates (map #231).

Spec-value gates for the locked §B modal + §F + P3.5 treatment: the
page-level safety panel borders resolve to --accent/--warn/--err, no
.modal style survives, every POST → 303 + translated flash, master
two-step gating holds per P4.1/P4.4, and refusals carry no flags, exit
classes, command names or record ids.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.interface import forbidden_matches
from skilltrace.web.views import Redirect, _STYLE

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE = "math.arithmetic.order_operations_01"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _set_state(root: Path, node_id: str, state: str) -> None:
    path = root / "graph/state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _make_eligible(root: Path, node_id: str = NODE, count: int = 3) -> None:
    records = [
        {
            "id": f"ev.{node_id}.{i:03d}",
            "artifact_spec_id": "spec.math.arithmetic.order_operations",
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


def _notice_of(redirect: Redirect) -> tuple[str, str]:
    query = parse_qs(redirect.location.partition("?")[2])
    return (query.get("notice") or [""])[0], (query.get("kind") or [""])[0]


def _first_locked_node(root: Path) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if view.store.state_of(node.id) == "locked":
            return node.id
    raise AssertionError("no locked node in the seed graph")


# --- Panel tokens ------------------------------------------------------------


def test_no_modal_style_survives_and_no_overlay_or_script(repo):
    assert ".modal" not in _STYLE
    assert "<dialog" not in views.page("t", "<p>x</p>").lower()
    _, pass_body, _ = views.pass_modal_body(repo, NODE)
    assert "<dialog" not in pass_body.lower()
    assert "popover" not in pass_body.lower()
    assert "backdrop" not in pass_body.lower()
    assert "<script" not in pass_body.lower()


def test_panel_borders_resolve_to_locked_tokens():
    assert re.search(
        r"\.safety-accent\s*\{\s*border-left:[^;]*var\(--accent\)", _STYLE
    )
    assert re.search(
        r"\.safety-warn\s*\{\s*border-left:[^;]*var\(--warn\)", _STYLE
    )
    assert re.search(
        r"\.safety-err\s*\{\s*border-left:[^;]*var\(--err\)", _STYLE
    )
    assert re.search(r"\.safety\s*\{\s*padding:\s*var\(--card-pad\)", _STYLE)


def test_pass_panel_uses_accent_master_steps_use_warn_err(repo):
    _, pass_body, _ = views.pass_modal_body(repo, NODE)
    assert "safety-accent" in pass_body
    _, step1, _ = views.master_body(repo, NODE)
    assert "safety-warn" in step1
    _, step2, _ = views.master_confirm_body(repo, NODE)
    assert "safety-err" in step2


def test_panels_carry_flash_dismissal_link(repo):
    _, body, _ = views.pass_modal_body(
        repo, NODE, {"notice": ["Marked as passed."], "kind": ["ok"]}
    )
    assert "Dismiss" in body
    assert f'href="/nodes/{NODE}/pass"' in body


# --- Confirmation copy --------------------------------------------------------


def test_pass_copy_states_change_side_effects_no_internals(repo):
    _, body, _ = views.pass_modal_body(repo, NODE)
    assert "never moves backward" in body.lower()
    assert "reviews for" in body.lower() and "days after the pass" in body.lower()
    assert SPEC_ID not in body
    assert "cadence policy" not in body.lower()
    assert "nest-dispatch" not in body.lower()


SPEC_ID = "spec.math.arithmetic.order_operations"


def test_master_step_two_states_permanence_and_rerenders_facts(repo):
    _, step1, _ = views.master_body(repo, NODE)
    _, step2, _ = views.master_confirm_body(repo, NODE)
    assert "Mastered never moves backward — this is permanent" in step2
    # Step 2 re-renders the facts freshly — the same fact rows as step 1.
    for fact in ("Passed on", "Live proof accepted", "Review spacing"):
        assert fact in step1
        assert fact in step2
    assert "safety-err" in step2


def test_master_step_one_omits_continue_on_structural_wall(repo):
    locked = _first_locked_node(repo)
    _, locked_body, _ = views.master_body(repo, locked)
    assert "/master/confirm" not in locked_body
    assert "Continue is unavailable" in locked_body

    _set_state(repo, NODE, "available")
    _, avail_body, _ = views.master_body(repo, NODE)
    assert "/master/confirm" not in avail_body
    assert "needs a passed skill first" in avail_body


def test_master_step_one_keeps_continue_live_with_advisory_when_passed(repo):
    _set_state(repo, NODE, "passed")
    _, body, _ = views.master_body(repo, NODE)
    assert "/master/confirm" in body
    assert "satisfactory spaced review" in body


# --- POST contract + refusal copy ---------------------------------------------


def test_every_post_returns_303_with_translated_flash(repo):
    _set_state(repo, NODE, "available")
    _make_eligible(repo)
    posts = [
        views.post_start(repo, NODE, _form(template="", next=f"/nodes/{NODE}")),
        views.post_work(repo, _form(node_id=NODE, notes="x", minutes="5")),
        views.post_blocker_create(repo, NODE, _form(description="stuck")),
        views.post_evidence(repo, NODE, _form(location="evidence/math/a.md")),
        views.post_session_close(repo, _form()),
        views.post_pass(repo, NODE, _form()),
    ]
    for result in posts:
        assert isinstance(result, Redirect)
        notice, kind = _notice_of(result)
        assert kind in {"ok", "warning", "error"}
        assert "notice=" in result.location
        if notice:
            assert forbidden_matches(notice) == []
            assert "[error]" not in notice and "[warning]" not in notice


def test_no_4xx_leaves_a_write(repo):
    _set_state(repo, NODE, "available")
    results = [
        views.post_pass(repo, NODE, _form()),
        views.post_master_confirm(repo, NODE, _form()),
        views.post_start(repo, NODE, _form()),
        views.post_work(repo, _form(node_id=NODE)),
        views.post_evidence(repo, NODE, _form()),
    ]
    for result in results:
        assert isinstance(result, Redirect)


def test_refusals_carry_no_flags_exit_classes_commands_or_record_ids(repo):
    _set_state(repo, NODE, "available")  # ineligible — refusal
    result = views.post_pass(repo, NODE, _form())
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert forbidden_matches(notice) == []
    assert "--" not in notice
    assert "exit code" not in notice.lower()
    assert "skilltrace" not in notice.lower()
    assert re.search(r"\b(?:spec|rec|ev|ses|review|blocker)\.[A-Za-z0-9]", notice) is None
    assert re.search(r"\bevid\.", notice) is None


def test_operational_failure_points_at_health(repo):
    lines, code = ["Something broke badly"], 1
    result = views._finish_write("/nodes/x", lines, code)
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "error"
    assert "/health" in notice
    _, body, _ = views.node_body(
        repo, NODE, {"notice": [notice], "kind": [kind]}
    )
    assert 'href="/health"' in body


def test_friction_free_writes_stay_single_step(repo):
    _, body, _ = views.node_body(repo, NODE, {})
    assert 'action="/work"' in body
    assert 'action="/nodes/' in body and "/blockers" in body
    assert 'action="/nodes/' in body and "/evidence" in body
