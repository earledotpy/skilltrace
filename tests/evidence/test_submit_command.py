"""`skilltrace evidence submit`: the wired mutate + audit + judgment path.

The decision logic is unit-tested in test_submission.py. Here we drive the real
command through the CLI on a temp copy of the seed repo, pinning the things only
the wired path can show: a written submit appends exactly one audit event and one
record; a rejected record (manual *or* a failing objective gate) is still a
written, audited submit; an unrunnable objective gate writes nothing and logs no
event; existing records are never mutated; and the appended record re-validates
clean through `validate evidence`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.evidence.records import load_evidence_records
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"


def _seed_repo(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def _make_artifact(root: Path, relpath: str = "evidence/math/set_001.md") -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("worked solutions, as submitted", encoding="utf-8")
    return relpath


def _set_objective_gate(root: Path, node_id: str, command: str) -> None:
    """Turn `node_id`'s gate into an objective gate running `command`.

    The seed ships only manual gates; a test needing the objective path rewrites
    one node's single gate in place (not a second gate, which would be a
    validate-evidence error).
    """
    path = root / "evidence" / "validation_gates.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for gate in doc["validation_gates"]:
        if gate["node_id"] == node_id:
            gate["authority"] = "objective"
            gate["command"] = command
            break
    else:  # pragma: no cover - fixture guard
        raise AssertionError(f"no gate for {node_id}")
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _remove_gate(root: Path, node_id: str) -> None:
    path = root / "evidence" / "validation_gates.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["validation_gates"] = [g for g in doc["validation_gates"] if g["node_id"] != node_id]
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Manual authority, end to end ------------------------------------------


def test_manual_accept_writes_one_record_and_one_event(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    rc = cli.run(["evidence", "submit", NODE, "--location", loc, "--accept"], root=root)
    assert rc == 0

    records = load_evidence_records(root)
    assert len(records) == 1
    assert records[0].accepted is True
    assert records[0].accepted_by == "learner_manual"
    assert records[0].artifact_hash.startswith("sha256:")

    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "evidence submit"
    assert events[0]["records_touched"] == [records[0].id]


def test_manual_without_verdict_refuses_writes_nothing_no_event(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    rc = cli.run(["evidence", "submit", NODE, "--location", loc], root=root)
    assert rc == 2
    assert load_evidence_records(root) == []
    assert load_events(root) == []


def test_manual_reject_writes_rejected_record_and_logs_event(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    rc = cli.run(["evidence", "submit", NODE, "--location", loc, "--reject"], root=root)
    # A rejection is a written, audited submit — exit 0, record on file, one event.
    assert rc == 0
    records = load_evidence_records(root)
    assert len(records) == 1 and records[0].accepted is False
    assert len(load_events(root)) == 1


# --- Objective authority, end to end ---------------------------------------


def test_objective_gate_pass_writes_accepted_record(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    _set_objective_gate(root, NODE, 'python -c "import sys; sys.exit(0)"')
    rc = cli.run(["evidence", "submit", NODE, "--location", loc], root=root)
    assert rc == 0
    records = load_evidence_records(root)
    assert len(records) == 1
    assert records[0].accepted is True
    assert records[0].accepted_by == "objective_gate"
    assert len(load_events(root)) == 1


def test_objective_gate_fail_writes_rejected_record_and_logs_event(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    _set_objective_gate(root, NODE, 'python -c "import sys; sys.exit(1)"')
    rc = cli.run(["evidence", "submit", NODE, "--location", loc], root=root)
    # Non-zero gate exit is the verdict, not a submit failure: rejected record
    # written, exactly one event logged.
    assert rc == 0
    records = load_evidence_records(root)
    assert len(records) == 1 and records[0].accepted is False
    assert records[0].accepted_by == "objective_gate"
    assert len(load_events(root)) == 1


def test_objective_flags_refused_before_running(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    _set_objective_gate(root, NODE, 'python -c "import sys; sys.exit(0)"')
    rc = cli.run(["evidence", "submit", NODE, "--location", loc, "--accept"], root=root)
    assert rc == 2
    assert load_evidence_records(root) == []
    assert load_events(root) == []


def test_objective_gate_unrunnable_writes_nothing_no_event(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    _set_objective_gate(root, NODE, "no_such_exe_skilltrace_xyz")
    rc = cli.run(["evidence", "submit", NODE, "--location", loc], root=root)
    # Unable to run at all is an error, not a verdict — nothing written, no event.
    assert rc == 1
    assert load_evidence_records(root) == []
    assert load_events(root) == []


# --- Gateless refusal ------------------------------------------------------


def test_gateless_node_refuses(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    _remove_gate(root, NODE)
    rc = cli.run(["evidence", "submit", NODE, "--location", loc, "--accept"], root=root)
    assert rc == 2
    assert load_evidence_records(root) == []
    assert load_events(root) == []


# --- Immutability ----------------------------------------------------------


def test_existing_records_never_mutated_by_a_later_submit(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    cli.run(["evidence", "submit", NODE, "--location", loc, "--accept"], root=root)
    first = load_evidence_records(root)[0]

    loc2 = _make_artifact(root, "evidence/math/set_002.md")
    cli.run(["evidence", "submit", NODE, "--location", loc2, "--reject"], root=root)

    records = load_evidence_records(root)
    assert len(records) == 2
    # The first record is byte-for-byte the same after the second submit.
    again = next(r for r in records if r.id == first.id)
    assert (again.id, again.location, again.accepted, again.artifact_hash) == (
        first.id,
        first.location,
        first.accepted,
        first.artifact_hash,
    )
    # Sequence never reused: the second id is one past the first.
    assert sorted(r.id for r in records) == [
        f"ev.{NODE}.001",
        f"ev.{NODE}.002",
    ]


def test_appended_record_revalidates_clean(tmp_path):
    root = _seed_repo(tmp_path)
    loc = _make_artifact(root)
    cli.run(["evidence", "submit", NODE, "--location", loc, "--accept"], root=root)
    # The record we just wrote must pass validate evidence (shape + cross-record).
    rc = cli.run(["validate", "evidence"], root=root)
    assert rc == 0
