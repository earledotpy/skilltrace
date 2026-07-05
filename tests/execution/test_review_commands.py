"""`skilltrace review schedule` / `complete` / `cancel`.

A Review is a retention check on a passed or mastered node — never on a node
with nothing to retain. Lifecycle: scheduled -> completed (outcome + result
summary) | cancelled (learner-only, reason required, record kept).
"""

from __future__ import annotations

import pytest

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.reviews import load_reviews

NODE = "testing.execution.retained_node_01"


def test_review_schedule_on_a_passed_node(exec_repo):
    root = exec_repo({NODE: "passed"})

    rc = cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root)
    assert rc == 0

    reviews = load_reviews(root)
    assert len(reviews) == 1
    review = reviews[0]
    assert review.id == f"rev.{NODE}.001"
    assert review.node_id == NODE
    assert review.status == "scheduled"
    assert review.scheduled_for == "2026-07-10"
    assert [e["command"] for e in load_events(root)] == ["review schedule"]


@pytest.mark.parametrize("state", ["locked", "available", "active"])
def test_review_schedule_refuses_nodes_with_nothing_to_retain(exec_repo, state):
    root = exec_repo({NODE: state})

    rc = cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root)
    assert rc != 0
    assert load_reviews(root) == []
    assert load_events(root) == []


def test_review_schedule_is_legal_on_a_mastered_node(exec_repo):
    root = exec_repo({NODE: "mastered"})
    assert cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root) == 0
    assert load_reviews(root)[0].status == "scheduled"


def test_review_complete_records_outcome_and_summary(exec_repo):
    root = exec_repo({NODE: "passed"})
    assert cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root) == 0
    review_id = f"rev.{NODE}.001"

    rc = cli.run(
        ["review", "complete", review_id, "--outcome", "satisfactory",
         "--summary", "recalled the full derivation"],
        root=root,
    )
    assert rc == 0

    review = load_reviews(root)[0]
    assert review.status == "completed"
    assert review.outcome == "satisfactory"
    assert review.result_summary == "recalled the full derivation"


def test_review_complete_refuses_an_invalid_outcome(exec_repo):
    root = exec_repo({NODE: "passed"})
    assert cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root) == 0

    rc = cli.run(
        ["review", "complete", f"rev.{NODE}.001", "--outcome", "great", "--summary", "s"],
        root=root,
    )
    assert rc != 0
    assert load_reviews(root)[0].status == "scheduled"


def test_review_cancel_requires_a_reason_and_is_terminal(exec_repo):
    root = exec_repo({NODE: "passed"})
    assert cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root) == 0
    review_id = f"rev.{NODE}.001"

    rc = cli.run(["review", "cancel", review_id, "--reason", "scheduled the wrong node"], root=root)
    assert rc == 0

    review = load_reviews(root)[0]
    assert review.status == "cancelled"
    assert review.cancel_reason == "scheduled the wrong node"

    # Terminal both ways: a cancelled review cannot be completed, and vice versa.
    rc = cli.run(
        ["review", "complete", review_id, "--outcome", "satisfactory", "--summary", "s"],
        root=root,
    )
    assert rc != 0
    assert load_reviews(root)[0].status == "cancelled"
