"""Mastery eligibility (CONTEXT.md): passed + accepted evidence + a
satisfactory post-pass review with the policy-configured day spacing.

Exercised through `skilltrace eligibility <node> --mastery` — the derivation
is on-demand; nothing is stored.
"""

from __future__ import annotations

from skilltrace import cli

from .conftest import NODE, review_dict


def test_spaced_satisfactory_review_makes_node_mastery_eligible(mastery_repo, capsys):
    # Pass on 07-01, satisfactory review on 07-04 — spacing (3 days) satisfied.
    root = mastery_repo(reviews=[review_dict(completed_at="2026-07-04T10:00:00+00:00")])

    rc = cli.run(["eligibility", NODE, "--mastery"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MASTERY ELIGIBLE" in out


def _verdict(root, capsys) -> str:
    rc = cli.run(["eligibility", NODE, "--mastery"], root=root)
    assert rc == 0  # a verdict, positive or not, answers the question
    return capsys.readouterr().out


def test_unpassed_node_is_not_mastery_eligible(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)
    out = _verdict(root, capsys)
    assert "NOT MASTERY ELIGIBLE" in out
    assert "requires a passed node" in out


def test_review_on_pass_day_fails_spacing(mastery_repo, capsys):
    root = mastery_repo(reviews=[review_dict(completed_at="2026-07-01T18:00:00+00:00")])
    out = _verdict(root, capsys)
    assert "NOT MASTERY ELIGIBLE" in out
    assert "day(s) after the pass" in out


def test_unsatisfactory_review_does_not_feed_eligibility(mastery_repo, capsys):
    root = mastery_repo(reviews=[review_dict(outcome="unsatisfactory")])
    out = _verdict(root, capsys)
    assert "NOT MASTERY ELIGIBLE" in out


def test_without_accepted_evidence_not_mastery_eligible(mastery_repo, capsys):
    root = mastery_repo(accepted=False, reviews=[review_dict()])
    out = _verdict(root, capsys)
    assert "NOT MASTERY ELIGIBLE" in out
    assert "accepted evidence" in out


def test_mastered_node_reports_already_mastered(mastery_repo, capsys):
    root = mastery_repo(state="mastered", reviews=[review_dict()])
    out = _verdict(root, capsys)
    assert "NOT MASTERY ELIGIBLE" in out
    assert "already mastered" in out
