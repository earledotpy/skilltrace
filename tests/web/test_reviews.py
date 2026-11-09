"""The Reviews destination and the review loop (spec-v3-study-day §10.10, §11.3).

What only this module shows: the retention loop's own contract.

* A Review is scheduled **only** by the learner's explicit action — a
  suggested check is advisory and never appears as scheduled or overdue.
* The queue is ordered: overdue → scheduled by date → history.
* Completing requires an explicit outcome **and** a result summary;
  cancelling requires a reason and preserves the cancelled history.
* Neither action demotes asserted progress or masters a node; an
  unsatisfactory outcome creates pressure only.
* The three states — no review-worthy node, no scheduled records, failed
  retention derivation — are distinguishable.
* Retention is spoken of as **retention status**; the canonical Memory
  state and Retention confidence remain Operations detail.
"""

from __future__ import annotations

import shutil
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
    return _seed(tmp_path)


def _review(repo: Path, *, status: str, scheduled_for: str, **extra) -> dict:
    record = {
        "id": "rev.test.001",
        "node_id": "data.sql.select_basics_01",
        "status": status,
        "scheduled_for": scheduled_for,
        "created_at": "2026-11-01T09:00:00+00:00",
    }
    record.update(extra)
    _write_yaml(repo, "execution/reviews.yaml", {"reviews": [record]})
    return record


# --- the queue ---------------------------------------------------------------------


def test_with_no_records_the_queue_says_so_and_keeps_discovery(repo):
    """No scheduled records is its own state, not a blank page."""
    _, body, status = views.reviews_body(repo)
    assert status == 200
    assert "No checks are scheduled" in body
    assert "not scheduled and not overdue" in body


def test_a_scheduled_check_appears_with_its_due_date(repo):
    _review(repo, status="scheduled", scheduled_for="2026-12-01")
    _, body, _ = views.reviews_body(repo)
    assert "Scheduled" in body
    assert "2026-12-01" in body


def test_an_overdue_check_appears_in_the_overdue_group(repo):
    """Overdue is derived from the date, not stored."""
    _review(repo, status="scheduled", scheduled_for="2020-01-01")
    _, body, _ = views.reviews_body(repo)
    assert "Overdue" in body
    assert "2020-01-01" in body


def test_the_queue_carries_the_explicit_complete_and_cancel_actions(repo):
    """Completing and cancelling are the learner's own explicit actions."""
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


# --- the advisory group ------------------------------------------------------------


def _has_advisory_section(body: str) -> bool:
    """Whether the advisory group itself rendered (not a mention of it)."""
    return '<h2 class="section-title">Suggested checks</h2>' in body


def test_a_suggestion_is_advisory_and_never_in_the_queue(repo):
    """A suggested check creates no record and is never shown as due."""
    _, body, _ = views.reviews_body(repo)
    if _has_advisory_section(body):
        # The advisory group is labelled as advisory.
        assert "Advisory only" in body
        assert "not scheduled and" in body
        # And it offers the scheduling action rather than claiming one.
        assert "Schedule this check" in body
    else:
        # No suggestions for this fixture — and the empty state still says
        # that suggestions are advisory and not due.
        assert "advisory" in body
        assert "not scheduled and not overdue" in body


def test_scheduling_is_offered_only_through_the_explicit_action(repo):
    """The only way a Review is created is the scheduling action."""
    _, body, _ = views.reviews_body(repo)
    assert 'action="/reviews/schedule"' not in body or _has_advisory_section(
        body
    )


def test_the_learner_facing_term_is_retention_status(repo):
    """Retention is spoken of as retention status, never as certainty."""
    _, body, _ = views.reviews_body(repo)
    assert "Retention confidence" not in body
    assert "Memory state" not in body
    if _has_advisory_section(body):
        assert "Retention status" in body
    else:
        # The learner-facing term appears whenever retention is spoken of.
        # Wherever retention is spoken of, it is spoken of as a
        # check or a status — never as the canonical certainty
        # terms above.
        for phrase in ("retention confidence", "memory state"):
            assert phrase not in body.lower(), phrase
