"""`skilltrace master <node_id>` — the learner's explicit mastery assertion.

The only writer of `mastered`; refuses (exit 2) unless mastery eligibility
holds, and mastered state never moves backward afterward.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.graph.state import load_state

from .conftest import NODE, review_dict


def test_master_asserts_mastered_when_eligible(mastery_repo, capsys):
    root = mastery_repo(reviews=[review_dict()])

    rc = cli.run(["master", NODE], root=root)
    assert rc == 0
    assert "mastered" in capsys.readouterr().out
    assert load_state(root).state_of(NODE) == "mastered"

    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "master"
    assert events[0]["records_touched"] == [NODE]


def test_master_refuses_without_eligibility(mastery_repo, capsys):
    # Passed, but the only review is on the pass day — spacing unmet.
    root = mastery_repo(reviews=[review_dict(completed_at="2026-07-01T18:00:00+00:00")])

    rc = cli.run(["master", NODE], root=root)
    assert rc == 2
    out = capsys.readouterr().out
    assert "refused" in out
    assert load_state(root).state_of(NODE) == "passed"
    assert load_events(root) == []  # refusal writes nothing, logs nothing


def test_mastered_state_survives_sync(mastery_repo, capsys):
    root = mastery_repo(reviews=[review_dict()])
    (root / "graph" / "edges.yaml").write_text("edges: []\n", encoding="utf-8")
    assert cli.run(["master", NODE], root=root) == 0

    assert cli.run(["sync"], root=root) == 0
    assert load_state(root).state_of(NODE) == "mastered"


def test_master_refuses_a_second_time(mastery_repo, capsys):
    root = mastery_repo(reviews=[review_dict()])
    assert cli.run(["master", NODE], root=root) == 0

    rc = cli.run(["master", NODE], root=root)
    assert rc == 2
    assert "already mastered" in capsys.readouterr().out
    assert load_state(root).state_of(NODE) == "mastered"
