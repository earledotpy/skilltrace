"""Review auto-scheduling on pass — the one sanctioned automation.

`pass` creates every cadence interval at once, dated from the pass date, and
its single audit event lists the created review ids alongside the node.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.reviews import load_reviews

from .conftest import NODE


def test_pass_schedules_every_cadence_interval(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)

    rc = cli.run(["pass", NODE], root=root)
    assert rc == 0

    reviews = load_reviews(root)
    assert len(reviews) == 3
    assert all(r.node_id == NODE and r.status == "scheduled" for r in reviews)

    today = datetime.now(timezone.utc).date()
    expected_dates = {(today + timedelta(days=n)).isoformat() for n in (1, 3, 7)}
    assert {r.scheduled_for for r in reviews} == expected_dates

    # One audit event for the one mutating command; the auto-scheduled
    # reviews ride in its records_touched.
    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "pass"
    assert set(events[0]["records_touched"]) == {NODE, *(r.id for r in reviews)}


def test_forbidding_schedule_review_skips_scheduling_but_pass_stands(
    mastery_repo, capsys
):
    import yaml

    root = mastery_repo(state="available", passed_at=None)
    path = root / "policy" / "automation_boundary.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for rule in doc["automation_boundary_policy"]["rules"]:
        if rule["action"] == "schedule_review":
            rule["permission"] = "forbidden"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    rc = cli.run(["pass", NODE], root=root)
    assert rc == 0  # the pass is a human command; the boundary gates only automation
    out = capsys.readouterr().out
    assert "now passed" in out
    assert "auto-scheduling skipped" in out
    assert load_reviews(root) == []
