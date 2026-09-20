"""Fixture/simulated clock dates engine-written records (issue #308, H1).

The fortnight simulation could not date the records the engine writes: the
fixture clock reached the read-side ``today`` derivations (via
``Context.clock`` and ``execution.overdue.utc_today``) but every mutating
command stamped its records from the wall clock, so simulated-day evidence
carried real dates. This module pins the fix end to end: one simulated
clock injected through ``cli.run(..., clock=)`` dates *every* engine-written
record — execution records, evidence records, attempts, progress-store
transitions, resource verification facts, readiness flips, the audit event,
and the disposable export/backup stamps — and the read-side derivations
follow the same clock.

The second test pins the safety side of the contract: a simulated run is a
throwaway fixture root, so the real repo's learner records are byte-identical
before and after.
"""

from __future__ import annotations

import json
import shutil
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import yaml

from skilltrace import cli

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"  # manual gate, one required spec, min 3
RESOURCE = "khan-arithmetic"

YEAR, MONTH = 2026, 9
_SIM_START = datetime(YEAR, MONTH, 1, 9, 0, 0, tzinfo=timezone.utc)


class SimulatedClock:
    """A mutable simulated-day clock injected through ``Context.clock``.

    ``day(n, hour=...)`` moves the simulation to that day of the month and
    returns the moment, so a test reads as a day-by-day journey and every
    recorded timestamp is checkable against the moment it was taken.
    """

    def __init__(self, start: datetime = _SIM_START) -> None:
        self.moment = start

    def __call__(self) -> datetime:
        return self.moment

    def day(self, day: int, *, hour: int = 9, minute: int = 0) -> datetime:
        self.moment = self.moment.replace(day=day, hour=hour, minute=minute, second=0)
        return self.moment


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def _repo(tmp_path: Path) -> Path:
    """A throwaway copy of the shipped data layers (never the live repo)."""
    for dirname in ("graph", "evidence", "execution", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _read_yaml(root: Path, relpath: str) -> dict:
    return yaml.safe_load((root / relpath).read_text(encoding="utf-8"))


def _records(root: Path, relpath: str, top_key: str, node_id: str = NODE) -> list[dict]:
    doc = _read_yaml(root, relpath) or {}
    return [r for r in doc.get(top_key, []) if r.get("node_id") == node_id]


def _all_records(root: Path, relpath: str, top_key: str) -> list[dict]:
    """Every row in a record list (evidence records key off `artifact_spec_id`)."""
    doc = _read_yaml(root, relpath) or {}
    return list(doc.get(top_key, []))


def _drop_state_entry(root: Path, node_id: str) -> None:
    """Remove one progress entry so the next `sync` must re-derive its readiness.

    A test fixture edit (never an engine path): the shipped store is already in
    sync, so sync has nothing to write until a node's entry is missing.
    """
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {}).pop(node_id, None)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _submit_accepted(root: Path, index: int, clock) -> None:
    relpath = f"evidence/math/fixture_clock_{index:03d}.md"
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"worked solutions {index}", encoding="utf-8")
    assert cli.run(
        ["evidence", "submit", NODE, "--location", relpath, "--accept"],
        root=root,
        clock=clock,
    ) == 0


def test_simulated_clock_dates_every_engine_written_record(tmp_path):
    """One simulated clock dates all records a simulated day writes."""
    root = _repo(tmp_path)
    sim = SimulatedClock()
    seed_event_count = len(_all_records(root, "execution/events.yaml", "events"))

    # Day 1 — readiness sync, then the session opens on the first simulated day.
    d1 = sim.day(1)
    _drop_state_entry(root, NODE)
    assert cli.run(["sync"], root=root, clock=sim) == 0
    state = _read_yaml(root, "graph/state.yaml")["progress"][NODE]
    assert state["state"] == "available"
    assert state["changed_at"] == _iso(d1), "sync did not stamp the simulated clock"

    assert cli.run(["start", NODE], root=root, clock=sim) == 0
    session = _read_yaml(root, "execution/sessions.yaml")["sessions"][0]
    assert session["started_at"] == _iso(d1)
    work = _read_yaml(root, "execution/session_work.yaml")["session_work"][0]
    assert work["created_at"] == _iso(d1)
    state = _read_yaml(root, "graph/state.yaml")["progress"][NODE]
    assert state["state"] == "active"
    assert state["transitions"]["active"] == _iso(d1)
    assert state["changed_at"] == _iso(d1)

    # Day 2 — a work item on the open session.
    d2 = sim.day(2, hour=20)
    assert cli.run(
        ["work", NODE, "--minutes", "25", "--notes", "simulated stint"],
        root=root,
        clock=sim,
    ) == 0
    work = _read_yaml(root, "execution/session_work.yaml")["session_work"][-1]
    assert work["created_at"] == _iso(d2)

    # Day 3 — three accepted evidence records + one attempt.
    d3 = sim.day(3, hour=18)
    for i in range(3):
        _submit_accepted(root, i, sim)
    records = _all_records(root, "evidence/evidence_records.yaml", "evidence_records")
    submitted = [
        r for r in records if r["location"].startswith("evidence/math/fixture_clock_")
    ]
    assert len(submitted) == 3
    assert {r["created_at"] for r in submitted} == {_iso(d3)}

    assert cli.run(
        ["attempt", "record", NODE, "--outcome", "passed"], root=root, clock=sim
    ) == 0
    attempt = _records(root, "evidence/attempts.yaml", "attempts")[-1]
    assert attempt["created_at"] == _iso(d3)

    # Day 4 — the pass, which also auto-schedules every cadence interval.
    d4 = sim.day(4, hour=11)
    assert cli.run(["pass", NODE], root=root, clock=sim) == 0
    state = _read_yaml(root, "graph/state.yaml")["progress"][NODE]
    assert state["state"] == "passed"
    assert state["transitions"]["passed"] == _iso(d4)
    reviews = _records(root, "execution/reviews.yaml", "reviews")
    assert len(reviews) == 3
    assert {r["created_at"] for r in reviews} == {_iso(d4)}
    assert {r["scheduled_for"] for r in reviews} == {
        (d4.date() + timedelta(days=n)).isoformat() for n in (1, 3, 7)
    }

    # Day 5 — complete the review due on the simulated day 5.
    d5 = sim.day(5, hour=21)
    first_review = next(
        r for r in reviews if r["scheduled_for"] == d5.date().isoformat()
    )
    assert cli.run(
        [
            "review", "complete", first_review["id"],
            "--outcome", "satisfactory",
            "--summary", "recalled the material",
        ],
        root=root,
        clock=sim,
    ) == 0
    completed = next(
        r for r in _records(root, "execution/reviews.yaml", "reviews")
        if r["id"] == first_review["id"]
    )
    assert completed["completed_at"] == _iso(d5)

    # Day 6/7 — a blocker, opened and resolved.
    d6 = sim.day(6, hour=10)
    assert cli.run(
        ["blocker", "create", NODE, "--description", "stuck on step 3"],
        root=root,
        clock=sim,
    ) == 0
    blocker = _records(root, "execution/blockers.yaml", "blockers")[-1]
    assert blocker["created_at"] == _iso(d6)

    d7 = sim.day(7, hour=10)
    assert cli.run(
        ["blocker", "resolve", blocker["id"], "--summary", "cleared with help"],
        root=root,
        clock=sim,
    ) == 0
    blocker = next(
        b for b in _records(root, "execution/blockers.yaml", "blockers")
        if b["id"] == blocker["id"]
    )
    assert blocker["resolved_at"] == _iso(d7)

    # Day 8/9 — a remediation action, logged and completed.
    d8 = sim.day(8, hour=10)
    assert cli.run(
        ["remediation", "create", NODE, "--description", "drill order of operations"],
        root=root,
        clock=sim,
    ) == 0
    action = _records(
        root, "execution/remediation_actions.yaml", "remediation_actions"
    )[-1]
    assert action["created_at"] == _iso(d8)

    d9 = sim.day(9, hour=10)
    assert cli.run(
        ["remediation", "complete", action["id"], "--summary", "drill finished"],
        root=root,
        clock=sim,
    ) == 0
    action = next(
        a
        for a in _records(
            root, "execution/remediation_actions.yaml", "remediation_actions"
        )
        if a["id"] == action["id"]
    )
    assert action["completed_at"] == _iso(d9)

    # Day 9 (later) — close the session with an honest simulated end time.
    assert cli.run(
        ["session", "close", "--end", _iso(d2)], root=root, clock=sim
    ) == 0
    session = _read_yaml(root, "execution/sessions.yaml")["sessions"][0]
    assert session["ended_at"] == _iso(d2)

    # Day 10 — the disposable stamps (backup name, markdown snapshot, html banner).
    d10 = sim.day(10, hour=15)
    assert cli.run(["backup"], root=root, clock=sim) == 0
    archives = sorted((root / "backups").glob("skilltrace-backup-*.zip"))
    assert [a.name for a in archives] == [
        "skilltrace-backup-" + d10.strftime("%Y%m%d-%H%M%S") + ".zip"
    ]

    assert cli.run(["export", "markdown"], root=root, clock=sim) == 0
    markdown = (root / "data" / "export.md").read_text(encoding="utf-8")
    assert f"generated: {_iso(d10)}" in markdown

    assert cli.run(["export", "html"], root=root, clock=sim) == 0
    html = (root / "data" / "export.html").read_text(encoding="utf-8")
    assert d10.date().isoformat() in html

    assert cli.run(
        ["analytics", "export", "--format", "json"], root=root, clock=sim
    ) == 0
    analytics = json.loads(
        (root / "data" / "analytics-report.json").read_text(encoding="utf-8")
    )
    assert analytics["generated_at"] == d10.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Day 11 — a resource verification is a *dated* simulated fact.
    d11 = sim.day(11, hour=12)
    assert cli.run(["verify-resource", RESOURCE], root=root, clock=sim) == 0
    resource = next(
        r
        for r in _read_yaml(root, "graph/resources.yaml")["resources"]
        if r["id"] == RESOURCE
    )
    assert resource["last_verified"] == d11.date().isoformat()

    # Every mutating command's audit event carries the simulated moment, never a
    # wall-clock timestamp. The shipped seed event log carries authored history,
    # so only the events this simulated run appended are inspected.
    events = _all_records(root, "execution/events.yaml", "events")[seed_event_count:]
    assert events
    simulated = {_iso(m) for m in (d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11)}
    stamped = {e["timestamp"] for e in events}
    assert stamped <= simulated, f"wall-clock event timestamp leaked: {stamped - simulated}"

    # Read-side derivations follow the same clock (day 12).
    d12 = sim.day(12)

    def capture(*argv: str) -> str:
        buffer = StringIO()
        with redirect_stdout(buffer):
            assert cli.run(list(argv), root=root, clock=sim) == 0
        return buffer.getvalue()

    retention = capture("retention", "status")
    assert f"today={d12.date().isoformat()}" in retention
    reviews_text = capture("suggest", "reviews")
    assert "overdue" in reviews_text


def test_simulated_run_never_touches_real_learner_records(tmp_path):
    """A simulated run is a throwaway root: the live repo stays byte-identical."""
    watched = [
        Path("graph") / "state.yaml",
        Path("execution") / "sessions.yaml",
        Path("execution") / "events.yaml",
        Path("evidence") / "evidence_records.yaml",
    ]
    before = {
        rel: (REPO_ROOT / rel).read_bytes() for rel in watched if (REPO_ROOT / rel).exists()
    }

    root = _repo(tmp_path)
    sim = SimulatedClock()
    sim.day(2)
    assert cli.run(["start", NODE], root=root, clock=sim) == 0
    assert cli.run(["session", "close"], root=root, clock=sim) == 0

    for rel, content in before.items():
        assert (REPO_ROOT / rel).read_bytes() == content, (
            f"{rel.as_posix()} changed — a simulated run wrote a real learner record"
        )
