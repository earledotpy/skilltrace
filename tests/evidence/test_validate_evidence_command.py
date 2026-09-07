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
    # The seed covers 81 nodes with a gate + required spec and ships no
    # records; the 7 v1.8 ML seed nodes plus the 12 v1.9 agent seed nodes are
    # gateless by design (gates land with their evidence specs in a later
    # slice), so a correct run emits exactly those nineteen
    # curriculum-quality warnings — asserting that (not merely `ok`) catches
    # a coverage check that spuriously warns on covered nodes while pinning
    # the known gateless set.
    result = load_and_validate_evidence(REPO_ROOT)
    assert result.ok
    # v1.8 ML seed nodes (gateless by design — gates land with evidence slice)
    ml_gateless = (
        "ml.capstone.house_prices_integration_01",
        "ml.classification.logistic_regression_01",
        "ml.evaluation.validation_metrics_01",
        "ml.framing.ml_workflow_01",
        "ml.practice.titanic_baseline_01",
        "ml.regression.linear_regression_01",
        "ml.trees.ensembles_01",
    )
    # v1.9 agent seed nodes (gateless by design — gates land with evidence slice)
    agent_gateless = (
        "agents.capstone.deployed_agent_integration_01",
        "agents.concepts.agent_fundamentals_01",
        "agents.data.llamaindex_rag_01",
        "agents.deploy.docker_engine_build_run_01",
        "agents.deploy.fastapi_minimal_01",
        "agents.frameworks.langgraph_01",
        "agents.frameworks.ms_agent_framework_01",
        "agents.frameworks.openai_agents_sdk_01",
        "agents.frameworks.pydanticai_01",
        "agents.frameworks.smolagents_01",
        "agents.optimization.dspy_01",
        "agents.protocol.mcp_01",
    )
    gateless = ml_gateless + agent_gateless
    expected = [
        f"node {node_id} has no gate — it cannot accept evidence "
        "and is never pass-eligible."
        for node_id in gateless
    ] + [
        f"node {node_id} has no required artifact spec — it is never pass-eligible."
        for node_id in gateless
    ]
    assert sorted(result.warnings) == sorted(expected)
    assert result.spec_count == 81
    assert result.gate_count == 81


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

    # Matching file → clean (aside from the 38 known v1.8 + v1.9
    # gateless-seed warnings, which are curriculum-quality, not drift).
    assert cli.run(["validate", "evidence"], root=root) == 0
    assert "artifact drift" not in capsys.readouterr().out

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
