"""The Reviews destination and the review loop (spec-v3-study-day §10.10, §11.3).

What only this module shows: the retention loop's own contract.

* A Review is scheduled **only** by the learner's explicit action — a
  suggested check is advisory and never appears as scheduled or overdue.
* The queue is ordered: overdue → scheduled by date → unsatisfactory
  follow-up → history.
* Completing requires an explicit outcome **and** a result summary;
  cancelling requires a reason and preserves the cancelled history.
* Neither action demotes asserted progress or masters a node; an
  unsatisfactory outcome creates pressure only.
* The three states — no review-worthy node, no scheduled records, failed
  retention derivation — are distinguishable, and a degraded record layer
  claims nothing (SC-00a).
* Retention is spoken of as **retention status**; the canonical Memory
  state and Retention confidence remain Operations detail.
"""

from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

#: A node the seed curriculum carries, used as the stand-in passed skill.
NODE = "data.sql.select_basics_01"


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
    return _seed(tmp_path)


def _pass_node(repo: Path, node_id: str = NODE, *, days_ago: int = 30) -> None:
    """Author a passed skill with a pass date ``days_ago`` before *now*.

    Fixture data through the store's own file shape (no engine pass path
    runs here); the date is relative to the wall clock so the test stays
    durable and the retention derivation sees the same today it derives
    with.
    """
    passed = date.today() - timedelta(days=days_ago)
    doc = _read_state(repo)
    doc.setdefault("progress", {})[node_id] = {
        "state": "passed",
        "changed_at": passed.isoformat(),
        "transitions": {"passed": passed.isoformat()},
    }
    _write_yaml(repo, "graph/state.yaml", doc)


def _read_state(repo: Path) -> dict:
    path = repo / "graph" / "state.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _review(repo: Path, *, status: str, scheduled_for: str, **extra) -> dict:
    record = {
        "id": "rev.test.001",
        "node_id": NODE,
        "status": status,
        "scheduled_for": scheduled_for,
        "created_at": "2026-11-01T09:00:00+00:00",
    }
    record.update(extra)
    _write_yaml(repo, "execution/reviews.yaml", {"reviews": [record]})
    return record


def _passed_state(repo: Path, node_id: str = NODE) -> None:
    """Mark the node passed without a transition trail (no derivation anchor)."""
    doc = _read_state(repo)
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    _write_yaml(repo, "graph/state.yaml", doc)


# --- the queue ---------------------------------------------------------------------


def test_with_no_review_worthy_node_the_queue_says_why(repo):
    """Nothing is passed: no check could watch anything — the empty state."""
    _, body, status = views.reviews_body(repo)
    assert status == 200
    assert "Nothing to check yet" in body
    assert "No checks are scheduled" not in body
    # Discovery survives the empty queue.
    assert 'href="/find"' in body


def test_with_a_passed_skill_but_no_records_the_queue_says_so(repo):
    """A checkable skill exists, nothing is scheduled — a distinct state."""
    _passed_state(repo)
    _, body, _ = views.reviews_body(repo)
    assert "No checks are scheduled" in body
    assert "Nothing to check yet" not in body
    assert "only by your own scheduling action" in body


def test_a_scheduled_check_appears_with_its_due_date(repo):
    _passed_state(repo)
    _review(repo, status="scheduled", scheduled_for="2026-12-01")
    _, body, _ = views.reviews_body(repo)
    assert "Scheduled" in body
    assert "2026-12-01" in body


def test_an_overdue_check_appears_in_the_overdue_group(repo):
    """Overdue is derived from the date, not stored."""
    _passed_state(repo)
    _review(repo, status="scheduled", scheduled_for="2020-01-01")
    _, body, _ = views.reviews_body(repo)
    assert "Overdue" in body
    assert "2020-01-01" in body


def test_the_queue_carries_the_explicit_complete_and_cancel_actions(repo):
    """Completing and cancelling are the learner's own explicit actions."""
    _passed_state(repo)
    _review(repo, status="scheduled", scheduled_for="2026-12-01")
    _, body, _ = views.reviews_body(repo)
    assert "Complete this review" in body
    assert "Cancel this review" in body
    # Both require what the contract requires.
    assert 'name="summary" required' in body
    assert 'name="reason" required' in body
    # And an explicit outcome, with no default.
    assert 'value="satisfactory"' in body
    assert 'value="unsatisfactory"' in body
    assert 'name="outcome" value="satisfactory" checked' not in body


def test_history_keeps_the_cancelled_record_and_its_reason(repo):
    """Cancelling preserves the cancelled history (the record stays)."""
    _passed_state(repo)
    _review(
        repo,
        status="cancelled",
        scheduled_for="2026-12-01",
        cancel_reason="the material moved",
        cancelled_at="2026-11-10T09:00:00+00:00",
    )
    _, body, _ = views.reviews_body(repo)
    assert "History" in body
    assert "cancelled" in body
    assert "the material moved" in body


def test_a_completed_check_records_its_outcome_and_summary(repo):
    _passed_state(repo)
    _review(
        repo,
        status="completed",
        scheduled_for="2026-12-01",
        outcome="unsatisfactory",
        result_summary="forgot the second half",
        completed_at="2026-12-02T09:00:00+00:00",
    )
    _, body, _ = views.reviews_body(repo)
    assert "unsatisfactory" in body
    assert "forgot the second half" in body


def test_an_unsatisfactory_check_is_its_own_band_never_history(repo):
    """The unsatisfactory follow-up band: pressure, named as never demotion."""
    _passed_state(repo)
    _review(
        repo,
        status="completed",
        scheduled_for="2020-01-01",
        outcome="unsatisfactory",
        result_summary="forgot the second half",
        completed_at="2026-12-02T09:00:00+00:00",
    )
    _, body, _ = views.reviews_body(repo)
    assert "Did not stick" in body
    assert "never demotes a skill you have passed" in body
    assert "never masters one" in body
    # The record left the completed/cancelled history for its own band.
    assert "History" not in body


def test_a_satisfactory_check_stays_in_history(repo):
    _passed_state(repo)
    _review(
        repo,
        status="completed",
        scheduled_for="2020-01-01",
        outcome="satisfactory",
        result_summary="recalled it cold",
        completed_at="2026-12-02T09:00:00+00:00",
    )
    _, body, _ = views.reviews_body(repo)
    assert "Did not stick" not in body
    assert "History" in body
    assert "recalled it cold" in body


# --- the three states, never merged --------------------------------------------------


def test_the_two_empty_cases_render_two_different_states(repo):
    """No review-worthy node and no scheduled records are distinct facts."""
    _, without_skill, _ = views.reviews_body(repo)
    _passed_state(repo)
    _, with_skill, _ = views.reviews_body(repo)
    assert "Nothing to check yet" in without_skill
    assert "No checks are scheduled" in with_skill
    assert "Nothing to check yet" not in with_skill
    assert "No checks are scheduled" not in without_skill


def test_a_failed_retention_derivation_is_distinct_from_no_suggestions(
    repo, monkeypatch
):
    """A derivation that cannot run claims nothing — never zeroes (SC-00a)."""
    import skilltrace.policy.retention_model as retention_model

    _pass_node(repo, days_ago=30)

    def _boom(*args, **kwargs):
        raise RuntimeError("the decay table could not be read")

    monkeypatch.setattr(retention_model, "derive_memory_states", _boom)
    _, body, _ = views.reviews_body(repo)
    assert "could not be worked out" in body
    # The failure says what is *not* claimed: not even that there are none.
    assert "not even that there are none" in body
    assert 'href="/health"' in body
    # And the records — not derivations — stay readable.
    assert "No checks are scheduled" in body


def test_a_missing_retention_policy_is_the_derivation_failure_state(repo):
    """Without the policy seed the advisory half fails, never silently empties."""
    _pass_node(repo, days_ago=30)
    (repo / "policy" / "retention_model.yaml").unlink()
    _, body, _ = views.reviews_body(repo)
    assert "could not be worked out" in body
    assert "No checks are scheduled" in body


def test_degraded_review_records_claim_nothing(repo):
    """A record layer that did not load is could-not-compute, never empty."""
    (repo / "execution").mkdir(exist_ok=True)
    (repo / "execution" / "reviews.yaml").write_text(
        "reviews: [ { broken", encoding="utf-8"
    )
    _, body, _ = views.reviews_body(repo)
    assert "did not load" in body
    assert "not even a" in body
    # No empty claim, no zero, no scheduler promising what is not known.
    assert "No checks are scheduled" not in body
    assert "Nothing to check yet" not in body
    assert "Schedule a check" not in body


# --- the advisory group --------------------------------------------------------------


def _has_advisory_section(body: str) -> bool:
    """Whether the advisory group itself rendered (not a mention of it)."""
    return '<h2 class="section-title">Suggested checks</h2>' in body


def test_a_suggestion_is_advisory_and_never_in_the_queue(repo):
    """A suggested check creates no record and is never shown as due."""
    _pass_node(repo, days_ago=30)
    _, body, _ = views.reviews_body(repo)
    assert _has_advisory_section(body)
    # The advisory group is labelled as advisory.
    assert "Advisory only" in body
    assert "never scheduled or overdue" in body
    # It offers the scheduling action rather than claiming one.
    assert "Schedule this check" in body
    # And nothing rendered it as a queue row: no overdue, no scheduled band.
    assert "Overdue" not in body
    assert '<h2 class="section-title">Scheduled</h2>' not in body


def test_the_scheduler_lists_only_review_worthy_skills(repo):
    """The scheduling form offers exactly the skills a check can watch."""
    _pass_node(repo, days_ago=30)
    _, body, _ = views.reviews_body(repo)
    assert '<h2 class="section-title">Schedule a check</h2>' in body
    assert f'<option value="{NODE}">' in body
    # A skill with nothing to retain is not offered — the engine would
    # refuse it, and the page does not offer an action it knows will be
    # refused.
    assert 'option value="math.arithmetic' not in body


def test_the_scheduler_is_omitted_when_nothing_can_be_scheduled(repo):
    """No review-worthy node: no scheduling affordance is offered."""
    _, body, _ = views.reviews_body(repo)
    assert 'action="/reviews/schedule"' not in body


def test_scheduling_is_offered_only_through_the_explicit_action(repo):
    """The only way a Review is created is a scheduling POST form."""
    _pass_node(repo, days_ago=30)
    _, body, _ = views.reviews_body(repo)
    occurrences = body.count("/reviews/schedule")
    assert occurrences > 0
    # Every occurrence rides inside an explicit POST form's action.
    for _ in range(occurrences):
        head, _, rest = body.partition('action="/reviews/schedule"')
        assert 'method="post"' in head[-200:]
        body = rest


def test_the_learner_facing_term_is_retention_status(repo):
    """Retention is spoken of as retention status, never as certainty."""
    _pass_node(repo, days_ago=30)
    _, body, _ = views.reviews_body(repo)
    assert "Retention confidence" not in body
    assert "Memory state" not in body
    assert _has_advisory_section(body)
    assert "Retention status" in body
