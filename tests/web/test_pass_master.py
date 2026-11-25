"""The pass and mastery journeys (spec-v3-study-day §10.7, §10.8).

What only this module shows: the two journeys are **separate decisions**.

* **Passing** restates the accepted evidence it rests on, and the result
  shows the visible Review-state consequence (R3).
* **Mastery** is a two-step journey, visibly distinct from passing, whose
  final confirmation revalidates eligibility against current truth
  (R3 extension). Step 1 explains what mastery asks and why it is or is
  not eligible; step 2 is the permanent confirmation. A stale or
  ineligible confirmation refuses, preserves the learner's context,
  refreshes the facts, offers the next valid route, and writes nothing.
* No surface anywhere offers a combined pass-and-master action (HB-1).
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.views import Redirect

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's sweeps."""
    root = Path(tempfile.mkdtemp(prefix="t5-pass-master-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _write_yaml(path: Path, relpath: str, doc: dict) -> None:
    target = path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _eligible_node(root: Path) -> str:
    """A node the seed marks available and whose evidence is in place."""
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if view.store.state_of(node.id) == "available":
            return node.id
    raise AssertionError("the seed graph has no available node")


def _spec_id(root: Path, node_id: str) -> str:
    """The required artifact spec of one node — its own id, read from truth."""
    view = load_context_lenient(root)
    specs = [s for s in view.specs_by_node.get(node_id, []) if s.required]
    assert specs, f"{node_id} has no required artifact spec"
    return specs[0].id


def _panel_node(root: Path) -> str:
    """A skill the learner can work on: available, with a required spec.

    The panel sweeps need a node whose evidence the engine counts, so the
    seed's first available skill is not enough — some carry no artifact
    specification at all.
    """
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if view.store.state_of(node.id) != "available":
            continue
        if any(s.required for s in view.specs_by_node.get(node.id, [])):
            return node.id
    raise AssertionError("the seed graph has no available skill with a spec")


def _accept_records(
    root: Path,
    node_id: str,
    *,
    count: int = 3,
    accepted_by: str = "learner_manual",
    objective: bool = False,
) -> None:
    """Author accepted evidence records — fixture data, never an engine write.

    The records are what the engine's eligibility counts, so the panel's
    "evidence the engine accepts" table has something to show. An
    ``objective`` record carries the gate-run receipt an automatic check
    writes. No engine pass/master path runs here (see AGENTS.md safety
    rule).
    """
    spec_id = _spec_id(root, node_id)
    records = []
    for index in range(1, count + 1):
        record = {
            "id": f"ev.{node_id}.{index:03d}",
            "artifact_spec_id": spec_id,
            "location": f"evidence/artifacts/{node_id}_{index:03d}.md",
            "accepted": True,
            "accepted_by": accepted_by,
            "artifact_hash": "sha256:" + str(index) * 64,
            "created_at": f"2026-11-1{index}T09:00:00+00:00",
        }
        if objective:
            record["gate_run"] = {
                "command_argv": ["python", f"evidence/checks/{node_id}_check.py"],
                "inputs": [f"evidence/artifacts/{node_id}_{index:03d}.md"],
                "exit_class": "passed",
                "exit_code": 0,
                "stdout_hash": "sha256:" + str(index) * 64,
            }
        records.append(record)
    _write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": records})


# --- two separate journeys ------------------------------------------------------


def test_the_pass_journey_says_it_is_only_about_passing(repo):
    _, body, _ = views.pass_body(repo, _eligible_node(repo))
    assert "about passing only" in body
    assert "Mastering is a separate" in body


def test_the_mastery_journey_says_it_is_only_about_mastery(repo):
    _, body, _ = views.master_body(repo, _eligible_node(repo))
    assert "Mastering is a separate, later step from passing" in body
    assert "never combined with passing" in body


def test_no_surface_offers_a_combined_pass_and_master_action(repo):
    """HB-1: passing and mastering are never combined."""
    node_id = _eligible_node(repo)
    for body in (
        views.pass_body(repo, node_id)[1],
        views.master_body(repo, node_id)[1],
        views.master_confirm_body(repo, node_id)[1],
    ):
        # A single form may not carry both commands.
        assert not (
            'action="/nodes/' in body and "/master" in body and "/pass" in body
        ) or body.count("<form") == 1


def test_the_two_journeys_have_different_headings(repo):
    """Different panel headings, so the learner never conflates them (C11).

    The heading is the panel's own declared title — "Confirm pass" for the
    one-step pass journey, "Step 1 — Mastery facts" and "Step 2 — This is
    permanent" for the two-step mastery journey.
    """
    node_id = _eligible_node(repo)
    _, pass_body, _ = views.pass_body(repo, node_id)
    _, step1, _ = views.master_body(repo, node_id)
    _, step2, _ = views.master_confirm_body(repo, node_id)
    assert "Confirm pass" in pass_body
    assert "Step 1" in step1 and "Mastery" in step1
    assert "Step 2" in step2 and "permanent" in step2.lower()
    # The mastery journey's steps are its own — the pass journey's heading
    # names neither step.
    assert "Step 1" not in pass_body and "Step 2" not in pass_body


def test_the_mastery_journey_is_two_steps(repo):
    """Mastery is a two-step journey with its own second step."""
    node_id = _eligible_node(repo)
    _, step1, _ = views.master_body(repo, node_id)
    _, step2, _ = views.master_confirm_body(repo, node_id)
    assert "Step 1" in step1
    assert "Step 2" in step2
    # Step 2 re-renders the facts freshly.
    for fact in ("Passed on", "Live proof accepted", "Review spacing"):
        assert fact in step1
        assert fact in step2


def test_the_permanent_confirmation_states_its_permanence(repo):
    _, step2, _ = views.master_confirm_body(repo, _eligible_node(repo))
    assert "Mastered never moves backward — this is permanent" in step2
    assert "pressure" in step2


# --- the pass result shows the Review consequence ---------------------------------


def test_a_passed_node_renders_the_result_not_the_confirmation(repo):
    """After passing, the panel is the result (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-passed-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    # Mark the node passed in the store.
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    _, body, _ = views.pass_body(root, node_id)
    assert "What passing changed" in body
    assert "Mark " not in body.split("What passing changed")[0]


def test_the_result_names_the_scheduled_checks_when_there_are_any(repo):
    """Scheduled checks appear — the consequence is visible (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-result-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rev.result.001",
                    "node_id": node_id,
                    "status": "scheduled",
                    "scheduled_for": "2026-11-18",
                    "created_at": "2026-11-17T09:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.pass_body(root, node_id)
    assert "2026-11-18" in body
    assert "scheduled" in body


def test_the_result_says_when_scheduling_stays_manual(repo):
    """When policy leaves scheduling manual, the page says so (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-manual-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    _, body, _ = views.pass_body(root, node_id)
    assert "scheduling manual" in body
    # And the action is offered.
    assert 'href="/reviews"' in body


# --- the pass panel: the evidence, the gate's decision, and the way on ---------


@pytest.fixture
def panel_repo() -> Path:
    """A fresh seed copy for the panel sweeps — each test authors its own."""
    root = Path(tempfile.mkdtemp(prefix="t5-panel-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def test_the_pass_panel_shows_the_evidence_the_engine_accepts(panel_repo):
    """Before submitting, the panel shows the proof the pass rests on."""
    node_id = _panel_node(panel_repo)
    _accept_records(panel_repo, node_id, count=3)

    _, body, status = views.pass_body(panel_repo, node_id, {})
    assert status == 200
    assert "Evidence the engine accepts" in body
    assert "Evidence wanted" in body
    # The accepted records are named, with where they live and when.
    assert "evidence/artifacts/" in body
    assert "2026-11-13T09:00:00+00:00" in body
    # The requirement and its standing are shown as distinct facts (R2).
    assert "Minimum" in body and "Accepted live" in body
    assert "met" in body


def test_the_pass_panel_states_what_the_gate_decided(panel_repo):
    """The gate's decision is on the panel, in plain words."""
    node_id = _panel_node(panel_repo)
    _accept_records(panel_repo, node_id, count=3, accepted_by="learner_manual")
    _, body, _ = views.pass_body(panel_repo, node_id, {})
    assert "You accepted it." in body
    assert "Checked by you" in body

    other = Path(tempfile.mkdtemp(prefix="t5-panel-gate-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, other / dirname)
    _accept_records(
        other,
        node_id,
        count=3,
        accepted_by="objective_gate",
        objective=True,
    )
    _, body, _ = views.pass_body(other, node_id, {})
    assert "The automatic check passed it." in body


def test_the_ineligible_panel_names_the_next_valid_route(panel_repo):
    """A panel the learner cannot act on says what to do next (IC-8, R5)."""
    node_id = _panel_node(panel_repo)
    _, body, _ = views.pass_body(panel_repo, node_id, {})
    assert "Next step" in body
    assert "Record the missing evidence" in body
    assert f'href="/nodes/{node_id}/evidence"' in body
    # The reason is stated in plain words — never a raw record id (R1).
    assert "spec." not in body
    assert _spec_id(panel_repo, node_id) not in body


def test_the_pass_panel_is_a_full_page_route_with_its_own_path(panel_repo):
    """RT-07/IC-2: a full-page route, never an overlay."""
    node_id = _panel_node(panel_repo)
    _, body, _ = views.pass_body(panel_repo, node_id, {})
    lowered = body.lower()
    assert "<dialog" not in lowered
    assert "popover" not in lowered
    assert "backdrop" not in lowered
    assert "<script" not in lowered
    # Its write rides its own path.
    assert f'action="/nodes/{node_id}/pass"' in body
    # And the only command it offers is the pass itself (HB-1).
    assert "/master" not in body


def test_the_pass_panel_never_pre_disables_the_confirm_button(panel_repo):
    """The engine's refusal on click is the truth (G2) — never a greyed button."""
    node_id = _panel_node(panel_repo)
    _, body, _ = views.pass_body(panel_repo, node_id, {})
    button = body.split('type="submit"', 1)[1].split("</button>", 1)[0]
    assert "disabled" not in button


def test_a_locked_skill_omits_the_pass_action_entirely(panel_repo):
    """ADR 0007 §Validation: a structural wall omits the action.

    Passing a locked skill can never succeed as the record stands, so the
    action is absent markup — never a disabled control. The wall itself is
    still stated, with the next route named.
    """
    view = load_context_lenient(panel_repo)
    locked = next(
        node.id
        for node in sorted(view.nodes, key=lambda n: n.id)
        if view.store.state_of(node.id) == "locked"
    )
    _, body, _ = views.pass_body(panel_repo, locked, {})
    assert f'action="/nodes/{locked}/pass"' not in body
    assert 'type="submit"' not in body
    # The wall is not hidden: the panel says so and names the way forward.
    assert "cannot be passed yet" in body
    assert "Next step" in body


def test_the_panel_is_the_focus_target_after_a_write(panel_repo):
    """IC-5/AX-7: the fresh page lands on the panel, not at the top."""
    node_id = _panel_node(panel_repo)
    _, body, _ = views.pass_body(panel_repo, node_id, {})
    assert 'id="pass-panel"' in body
    assert 'tabindex="-1"' in body


def test_optional_evidence_never_counts_toward_the_pass(panel_repo):
    """An optional specification's records are kept, never counted (R2)."""
    node_id = _panel_node(panel_repo)
    _accept_records(panel_repo, node_id, count=3)
    optional_id = f"spec.{node_id.removesuffix('_01')}.optional"
    doc = yaml.safe_load(
        (panel_repo / "evidence" / "artifact_specs.yaml").read_text(encoding="utf-8")
    )
    doc["artifact_specs"].append(
        {
            "id": optional_id,
            "node_id": node_id,
            "title": "Optional worked notes",
            "artifact_kind": "note",
            "required": False,
            "minimum_count": 1,
        }
    )
    (panel_repo / "evidence" / "artifact_specs.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )
    _write_yaml(
        panel_repo,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{node_id}.001",
                    "artifact_spec_id": optional_id,
                    "location": "evidence/artifacts/optional_notes.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "9" * 64,
                    "created_at": "2026-11-14T09:00:00+00:00",
                }
            ]
        },
    )

    _, body, _ = views.pass_body(panel_repo, node_id, {})
    # The optional record is not listed as evidence the pass rests on.
    assert "optional_notes.md" not in body
    assert "Optional worked notes" not in body


# --- the mastery steps disclose what mastery asks (§10.8) -----------------------

MASTER_READY_PASS_DAY = "2026-11-07"


def _fresh_root(prefix: str) -> Path:
    root = Path(tempfile.mkdtemp(prefix=prefix))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _read_yaml(root: Path, relpath: str) -> dict:
    path = root / relpath
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _set_state(root: Path, node_id: str, state: str) -> None:
    doc = _read_yaml(root, "graph/state.yaml")
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


def _author_passed_state(root: Path, node_id: str, *, passed_on: str) -> None:
    """A passed skill with its transition trail — authored fixture data.

    The pass date is what the mastery derivation spaces the satisfactory
    review against, so the fixture authors it explicitly; no engine
    pass/master path runs here (see AGENTS.md safety rule).
    """
    doc = _read_yaml(root, "graph/state.yaml")
    doc.setdefault("progress", {})[node_id] = {
        "state": "passed",
        "changed_at": f"{passed_on}T09:00:00+00:00",
        "transitions": {
            "active": f"{passed_on}T08:00:00+00:00",
            "passed": f"{passed_on}T09:00:00+00:00",
        },
    }
    _write_yaml(root, "graph/state.yaml", doc)


def _author_spaced_satisfactory_review(
    root: Path, node_id: str, *, passed_on: str, days_after_pass: int
) -> None:
    """One satisfactory completed review, spaced after the pass."""
    from datetime import date, timedelta

    completed = date.fromisoformat(passed_on) + timedelta(days=days_after_pass)
    reviews = _read_yaml(root, "execution/reviews.yaml").get("reviews") or []
    reviews.append(
        {
            "id": f"rev.{node_id}.mastery",
            "node_id": node_id,
            "status": "completed",
            "scheduled_for": (date.fromisoformat(passed_on) + timedelta(days=1)).isoformat(),
            "created_at": f"{completed.isoformat()}T09:00:00+00:00",
            "completed_at": f"{completed.isoformat()}T10:00:00+00:00",
            "outcome": "satisfactory",
            "result_summary": "Recalled cleanly.",
        }
    )
    _write_yaml(root, "execution/reviews.yaml", {"reviews": reviews})


def _master_ready_root() -> tuple[Path, str]:
    """A passed skill with its proof on file and a spaced satisfactory review."""
    root = _fresh_root("t5-master-ready-")
    node_id = _panel_node(root)
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _accept_records(root, node_id, count=1)
    _author_spaced_satisfactory_review(
        root, node_id, passed_on=MASTER_READY_PASS_DAY, days_after_pass=3
    )
    return root, node_id


def test_step_one_discloses_the_satisfactory_review_and_its_date():
    """§10.8 facts: the satisfactory Review and its date, on the step."""
    root, node_id = _master_ready_root()
    _, body, _ = views.master_body(root, node_id, {})
    assert "Satisfactory review" in body
    assert "completed 2026-11-10, 3 day(s) after the pass" in body
    # The current passed state is a named fact, not just a pill.
    assert "Current state" in body
    _, step2, _ = views.master_confirm_body(root, node_id, {})
    assert "completed 2026-11-10, 3 day(s) after the pass" in step2


def test_step_one_explains_each_gap_in_the_learners_words():
    """The engine's verdict in plain words — never a raw node id (R1)."""
    node_id = _panel_node(_fresh_root("t5-master-avail-"))
    root = _fresh_root("t5-master-why-")
    _set_state(root, node_id, "available")
    _, body, _ = views.master_body(root, node_id, {})
    assert "mastery needs a passed skill first" in body
    # R1: the engine's raw "node <id>" phrasing never reaches the page;
    # the panel names the skill.
    assert f"node {node_id}" not in body

    # A passed skill with no recorded pass date: the spacing cannot be checked.
    root = _fresh_root("t5-master-nodate-")
    _set_state(root, node_id, "passed")
    _, body, _ = views.master_body(root, node_id, {})
    assert "The pass date is not recorded" in body
    assert f"node {node_id}" not in body

    # Passed with a date, but no accepted proof on file.
    root = _fresh_root("t5-master-noev-")
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _, body, _ = views.master_body(root, node_id, {})
    assert "Accepted evidence: 0 of 1 required records on file so far." in body

    # Proof on file, but no satisfactory spaced review yet.
    root = _fresh_root("t5-master-norev-")
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _accept_records(root, node_id, count=1)
    _, body, _ = views.master_body(root, node_id, {})
    assert (
        "No satisfactory review has been completed at least 3 day(s) "
        "after the pass yet." in body
    )


def test_the_ineligible_steps_name_the_next_valid_route():
    """IC-8/R5: each gap names the one route that actually moves forward."""
    node_id = _panel_node(_fresh_root("t5-master-route-"))

    # Not passed: the pass journey is the way toward mastery.
    root = _fresh_root("t5-master-route-a-")
    _set_state(root, node_id, "available")
    _, step1, _ = views.master_body(root, node_id, {})
    _, step2, _ = views.master_confirm_body(root, node_id, {})
    for body in (step1, step2):
        assert f'href="/nodes/{node_id}/pass"' in body

    # Passed but the proof is short: the evidence workspace.
    root = _fresh_root("t5-master-route-b-")
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _, body, _ = views.master_body(root, node_id, {})
    assert f'href="/nodes/{node_id}/evidence"' in body

    # Proof on file, review missing: Reviews.
    root = _fresh_root("t5-master-route-c-")
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _accept_records(root, node_id, count=1)
    _, body, _ = views.master_body(root, node_id, {})
    assert 'href="/reviews"' in body


def test_an_already_mastered_skill_shows_the_completed_journey():
    """A mastered skill has nothing left to confirm (mastered never demotes)."""
    root = _fresh_root("t5-master-done-")
    node_id = _panel_node(root)
    _set_state(root, node_id, "mastered")
    _, step1, _ = views.master_body(root, node_id, {})
    _, step2, _ = views.master_confirm_body(root, node_id, {})
    for body in (step1, step2):
        assert "already mastered" in body
        assert 'type="submit"' not in body
        assert f'action="/nodes/{node_id}/master/confirm"' not in body


def test_step_two_omits_the_confirmation_on_a_structural_wall():
    """RT-09: no confirmation is offered where mastery can never succeed."""
    root = _fresh_root("t5-master-wall-")
    node_id = _panel_node(root)
    _set_state(root, node_id, "available")
    _, body, _ = views.master_confirm_body(root, node_id, {})
    assert 'type="submit"' not in body
    assert "Confirming is unavailable" in body
    assert f'href="/nodes/{node_id}/pass"' in body


def test_step_two_keeps_the_confirmation_live_when_passed_but_not_yet_eligible():
    """The engine's refusal on click is the truth — never a greyed button."""
    root = _fresh_root("t5-master-live-")
    node_id = _panel_node(root)
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _accept_records(root, node_id, count=1)
    _, body, _ = views.master_confirm_body(root, node_id, {})
    assert f'action="/nodes/{node_id}/master/confirm"' in body
    button = body.split('type="submit"', 1)[1].split("</button>", 1)[0]
    assert "disabled" not in button
    # And the step still names what is missing and the way forward.
    assert "No satisfactory review" in body
    assert 'href="/reviews"' in body


# --- the permanent confirmation refuses without writing (IC-9, R4, R5) ----------


def _form(**fields) -> dict:
    return {key: [str(value)] for key, value in fields.items()}


def _notice_of(redirect: Redirect) -> tuple[str, str]:
    query = parse_qs(redirect.location.partition("?")[2].partition("#")[0])
    return (query.get("notice") or [""])[0], (query.get("kind") or [""])[0]


def _events(root: Path) -> list[dict]:
    return _read_yaml(root, "execution/events.yaml").get("events") or []


def test_an_ineligible_confirmation_refuses_preserves_context_and_writes_nothing():
    """§10.8: a stale or ineligible confirmation refuses with no partial state.

    The refusal lands back on the confirmation step, in the presentation
    the learner was reading, on the panel itself; the refreshed step states
    the facts and names the next valid route. Nothing is written.
    """
    from skilltrace.web.interface import forbidden_matches

    root, node_id = _master_ready_root()
    # The world moves under the open panel: the satisfactory review vanishes.
    _write_yaml(root, "execution/reviews.yaml", {"reviews": []})

    result = views.post_master_confirm(root, node_id, _form(mode="operations"))
    assert isinstance(result, Redirect)
    assert result.location.startswith(f"/nodes/{node_id}/master/confirm?")
    assert "mode=operations" in result.location
    assert result.location.endswith("#master-confirm")
    notice, kind = _notice_of(result)
    assert kind == "warning"
    assert notice
    assert forbidden_matches(notice) == []
    assert node_id not in notice  # R1: the skill, never a raw id

    # No partial state change: the state stands, no event, no record moved.
    view = load_context_lenient(root)
    assert view.store.state_of(node_id) == "passed"
    assert _events(root) == []
    records = _read_yaml(root, "evidence/evidence_records.yaml")
    assert records["evidence_records"]

    # The refreshed confirmation step names the next valid route.
    _, body, _ = views.master_confirm_body(root, node_id, {"mode": ["operations"]})
    assert "No satisfactory review" in body
    assert 'href="/reviews"' in body


def test_the_mastery_refusal_carries_the_clis_own_refusal_text():
    """The flash is the dispatcher's refusal, rendered — not web prose.

    The notice is the command's own refusal line through the one
    translation module (P3.1): the web never invents its own refusal.
    """
    from skilltrace.web.interface import translate
    from skilltrace.web.views.writes import _dispatch_web

    root = _fresh_root("t5-master-verbatim-")
    node_id = _panel_node(root)
    _author_passed_state(root, node_id, passed_on=MASTER_READY_PASS_DAY)
    _accept_records(root, node_id, count=1)

    result = views.post_master_confirm(root, node_id, _form())
    assert isinstance(result, Redirect)
    notice, kind = _notice_of(result)
    assert kind == "warning"

    exit_code, lines = _dispatch_web(root, "master", node_id=node_id)
    assert exit_code == 2
    cli_line = next(line for line in lines if "is not mastery-eligible" in line)
    stripped = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", cli_line).strip()
    assert translate(stripped) in notice
    # The refusal names the skill, never a raw node id (R1).
    assert node_id not in notice
    assert "Nothing was mastered." in notice
