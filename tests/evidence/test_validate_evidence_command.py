"""`skilltrace validate evidence`: the end-to-end read-only validation path.

The cross-record rules are unit-tested in test_validation.py. Here we drive the
real command through the CLI on a temp copy of the seed repo, pinning the three
things only the wired path can show: the seed validates clean, the command is
read-only (no audit event) and state-independent (output stable across any
`graph/state.yaml`), loader failures are reported rather than raised, and real
artifact drift surfaces as a warning.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from skilltrace import cli
from skilltrace.evidence.artifacts import hash_artifact
from skilltrace.evidence.validation import load_and_validate_evidence
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    """Copy graph/ + evidence/ into a temp repo so edits are isolated."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def test_seed_validates_clean_and_logs_no_event(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["validate", "evidence"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "validate evidence: OK" in out
    # Read-only: the dispatcher appends no audit event.
    assert load_events(root) == []


def test_load_and_validate_seed_has_no_warnings():
    # The seed covers all 47 nodes with a gate + required spec and ships no
    # records, so a correct run emits zero warnings — asserting that (not merely
    # `ok`) catches a coverage check that spuriously warns on covered nodes.
    result = load_and_validate_evidence(REPO_ROOT)
    assert result.ok
    assert result.warnings == []
    assert result.spec_count == 55
    assert result.gate_count == 55


def test_output_is_independent_of_progress_store(tmp_path):
    root = _seed_repo(tmp_path)
    before = load_and_validate_evidence(root)

    # Create and then mutate graph/state.yaml with arbitrary learner progress.
    state_path = root / "graph" / "state.yaml"
    state_path.write_text(
        "progress:\n"
        "  math.arithmetic.order_operations_01:\n"
        "    state: mastered\n",
        encoding="utf-8",
    )
    after = load_and_validate_evidence(root)

    assert (after.errors, after.warnings) == (before.errors, before.warnings)


def test_loader_failure_is_reported_not_raised(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    # An attempt with an outcome outside the two values is a loader schema error;
    # validate evidence must surface it as an error and exit non-zero.
    (root / "evidence" / "attempts.yaml").write_text(
        "attempts:\n"
        "  - id: att.math.arithmetic.order_operations_01.001\n"
        "    node_id: math.arithmetic.order_operations_01\n"
        "    outcome: partial\n"
        "    created_at: 2026-07-03\n",
        encoding="utf-8",
    )
    rc = cli.run(["validate", "evidence"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate evidence: FAILED" in out
    assert "partial" in out


def _write_record(root: Path, *, location: str, artifact_hash: str) -> None:
    (root / "evidence" / "evidence_records.yaml").write_text(
        "evidence_records:\n"
        "  - id: ev.math.arithmetic.order_operations_01.001\n"
        "    artifact_spec_id: spec.math.arithmetic.order_operations\n"
        f"    location: {location}\n"
        "    accepted: true\n"
        "    accepted_by: learner_manual\n"
        f"    artifact_hash: {artifact_hash}\n"
        "    created_at: 2026-07-03\n",
        encoding="utf-8",
    )


def test_real_artifact_drift_surfaces_as_warning(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    artifact = root / "evidence" / "math" / "set_001.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("worked solutions, as submitted", encoding="utf-8")
    frozen = hash_artifact(artifact)
    _write_record(root, location="evidence/math/set_001.md", artifact_hash=frozen)

    # Matching file → clean.
    assert cli.run(["validate", "evidence"], root=root) == 0
    assert "warning" not in capsys.readouterr().out

    # Drift the file → warning, still exit 0 (advisory).
    artifact.write_text("edited after submission", encoding="utf-8")
    assert cli.run(["validate", "evidence"], root=root) == 0
    out = capsys.readouterr().out
    assert "artifact drift" in out
    assert "no longer matches" in out


def test_missing_artifact_surfaces_as_warning(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_record(root, location="evidence/math/never_created.md", artifact_hash="sha256:whatever")
    assert cli.run(["validate", "evidence"], root=root) == 0
    out = capsys.readouterr().out
    assert "artifact drift" in out
    assert "is missing" in out
