"""`skilltrace attempt record`: the wired mutate + audit path.

The decision logic is unit-tested in test_attempt_recording.py. Here we drive
the real command through the CLI on a temp copy of the seed repo, pinning the
things only the wired path can show: a recorded attempt appends exactly one
audit event and one row; a `failed` attempt is still a written, audited
mutation (exit 0, one event); an invalid outcome refuses and writes nothing;
existing attempts are never mutated; the attempt has zero effect on the evidence
trail eligibility reads from; and the appended attempt re-validates clean.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.evidence.attempts import load_assessment_attempts
from skilltrace.evidence.records import load_evidence_records
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"


def _seed_repo(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def _remove_gate(root: Path, node_id: str) -> None:
    path = root / "evidence" / "validation_gates.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["validation_gates"] = [g for g in doc["validation_gates"] if g["node_id"] != node_id]
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- The written, audited attempt ------------------------------------------


def test_passed_attempt_writes_one_row_and_one_event(tmp_path):
    root = _seed_repo(tmp_path)
    rc = cli.run(["attempt", "record", NODE, "--outcome", "passed"], root=root)
    assert rc == 0

    attempts = load_assessment_attempts(root)
    assert len(attempts) == 1
    assert attempts[0].node_id == NODE
    assert attempts[0].outcome == "passed"
    assert attempts[0].id == f"att.{NODE}.001"

    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "attempt record"
    assert events[0]["records_touched"] == [attempts[0].id]


def test_failed_attempt_is_a_written_audited_mutation(tmp_path):
    root = _seed_repo(tmp_path)
    # Failure is the record's content, not an error: exit 0, one row, one event.
    rc = cli.run(["attempt", "record", NODE, "--outcome", "failed", "--note", "stuck"], root=root)
    assert rc == 0
    attempts = load_assessment_attempts(root)
    assert len(attempts) == 1 and attempts[0].outcome == "failed"
    assert attempts[0].note == "stuck"
    assert len(load_events(root)) == 1


def test_invalid_outcome_refuses_writes_nothing_no_event(tmp_path):
    root = _seed_repo(tmp_path)
    rc = cli.run(["attempt", "record", NODE, "--outcome", "aced"], root=root)
    assert rc == 2
    assert load_assessment_attempts(root) == []
    assert load_events(root) == []


# --- Warnings never refuse -------------------------------------------------


def test_gateless_node_records_with_a_warning(tmp_path):
    root = _seed_repo(tmp_path)
    _remove_gate(root, NODE)
    rc = cli.run(["attempt", "record", NODE, "--outcome", "passed"], root=root)
    assert rc == 0
    assert len(load_assessment_attempts(root)) == 1
    assert len(load_events(root)) == 1


# --- Immutability + sequence -----------------------------------------------


def test_existing_attempts_never_mutated_by_a_later_record(tmp_path):
    root = _seed_repo(tmp_path)
    cli.run(["attempt", "record", NODE, "--outcome", "failed"], root=root)
    first = load_assessment_attempts(root)[0]

    cli.run(["attempt", "record", NODE, "--outcome", "passed"], root=root)
    attempts = load_assessment_attempts(root)
    assert len(attempts) == 2

    again = next(a for a in attempts if a.id == first.id)
    assert (again.id, again.outcome, again.note) == (first.id, first.outcome, first.note)
    # Sequence never reused: the second id is one past the first.
    assert sorted(a.id for a in attempts) == [f"att.{NODE}.001", f"att.{NODE}.002"]


# --- Zero effect on eligibility --------------------------------------------


def test_recording_an_attempt_does_not_touch_the_evidence_trail(tmp_path):
    root = _seed_repo(tmp_path)
    records_path = root / "evidence" / "evidence_records.yaml"
    before = records_path.read_bytes()
    records_before = load_evidence_records(root)

    cli.run(["attempt", "record", NODE, "--outcome", "passed"], root=root)
    cli.run(["attempt", "record", NODE, "--outcome", "failed"], root=root)

    # Eligibility (issue #14) reads only evidence records + specs, never attempts.
    # The structural guarantee is that recording attempts leaves the evidence
    # records byte-for-byte identical — so no eligibility computation can observe
    # them. (Issue #14 should add the direct eligibility-invariance assertion.)
    assert records_path.read_bytes() == before
    assert load_evidence_records(root) == records_before


def test_appended_attempt_revalidates_clean(tmp_path):
    root = _seed_repo(tmp_path)
    cli.run(["attempt", "record", NODE, "--outcome", "failed"], root=root)
    rc = cli.run(["validate", "evidence"], root=root)
    assert rc == 0
