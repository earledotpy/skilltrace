"""The pass and mastery journeys (spec-v3-study-day §10.7, §10.8).

What only this module shows: the two journeys are **separate decisions**.

* **Passing** restates the accepted evidence it rests on, and the result
  shows the visible Review-state consequence (R3).
* **Mastery** is a two-step journey, visibly distinct from passing, whose
  final confirmation revalidates eligibility against current truth
  (R3 extension).
* No surface anywhere offers a combined pass-and-master action (HB-1).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views

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


def test_the_two_journeys_have_different_titles(repo):
    """Different titles, so the learner never conflates them (C11)."""
    node_id = _eligible_node(repo)
    _, pass_title, _ = views.pass_body(repo, node_id)
    _, master_title, _ = views.master_body(repo, node_id)
    _, confirm_title, _ = views.master_confirm_body(repo, node_id)
    assert pass_title != master_title
    assert master_title != confirm_title
    assert "Mastery" in master_title or "mastered" in master_title.lower()


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
