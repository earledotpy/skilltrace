"""v0.4 exit gate — the composed evidence sequence on fresh seed data.

The per-command CLI tests each drive one command on a temp copy. This is the
RC-level proof that the evidence commands *compose* into the lifecycle the
roadmap's v0.4 test list names, on a fresh copy of the shipped seed data:

    submit accepted evidence to the minimum count
        → `eligibility` verdict flips (NOT ELIGIBLE → ELIGIBLE)
        → `pass` succeeds (state → passed)
        → supersede one accepted record with a *rejected* correction
        → `eligibility` drops (ELIGIBLE → NOT ELIGIBLE)
        → the passed-but-not-backed discrepancy surfaces
        → the asserted pass is unchanged (ADR 0003: it stands, never revoked).

The linchpin is the *rejected* superseder: superseding an accepted record with
another *accepted* one keeps the live count at 3 (the old drops out, the new
counts in). Only a rejected correction lowers the live accepted count below the
minimum — which is exactly the "evidence turned out wrong, but the pass stands"
case ADR 0003 protects.

Everything runs in-process against a temp copy (no network, no install step); the
only thing "fresh" is the seed-data copy, so the run proves the offline
fresh-clone property the acceptance criterion names.
"""

from __future__ import annotations

import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.evidence.records import load_evidence_records
from skilltrace.graph.state import load_state

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"  # manual gate, one required spec, min 3


def _seed_repo(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def _run(root: Path, *argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.run(list(argv), root=root)
    return rc, buf.getvalue()


def _set_available(root: Path, node_id: str) -> None:
    """Set a node's derived readiness to `available` via a direct store write.

    A pass precondition (a locked node refuses), established through the store —
    never a command — mirroring the graph suite's `set_asserted` convention. Pass
    reads *stored* state, so an absent node would resolve to the `locked` floor.
    """
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    doc = doc or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "available"}
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _submit_accepted(root: Path, n: int) -> None:
    for i in range(n):
        relpath = f"evidence/math/set_{i:03d}.md"
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"worked solutions {i}", encoding="utf-8")
        assert cli.run(
            ["evidence", "submit", NODE, "--location", relpath, "--accept"], root=root
        ) == 0


def _state_of(root: Path, node_id: str) -> str:
    return load_state(root).state_of(node_id)


def test_evidence_lifecycle_sequence(tmp_path):
    root = _seed_repo(tmp_path)
    _set_available(root, NODE)

    # 1. Fresh node: no records → NOT ELIGIBLE.
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "NOT ELIGIBLE" in out and "0/3" in out

    # 2. Submit accepted evidence to the minimum count → eligibility flips.
    _submit_accepted(root, 3)
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "ELIGIBLE" in out and "NOT ELIGIBLE" not in out
    assert "3/3" in out

    # 3. Pass succeeds; the node becomes asserted-passed.
    rc, out = _run(root, "pass", NODE)
    assert rc == 0
    assert "is now passed" in out
    assert _state_of(root, NODE) == "passed"

    # 4. Supersede one accepted record with a *rejected* correction → the live
    #    accepted count drops to 2 (< 3).
    target = load_evidence_records(root)[0]
    spec_id = target.artifact_spec_id
    correction = root / "evidence" / "math" / "correction.md"
    correction.write_text("this attempt was actually flawed", encoding="utf-8")
    rc, out = _run(
        root,
        "evidence",
        "submit",
        NODE,
        "--spec",
        spec_id,
        "--location",
        "evidence/math/correction.md",
        "--reject",
        "--supersedes",
        target.id,
        "--reason",
        "recount: solution had a recurring sign error",
    )
    assert rc == 0, out

    # 5. Eligibility drops, and the discrepancy is surfaced — but the pass stands.
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "NOT ELIGIBLE" in out and "2/3" in out
    assert "not revoked" in out  # passed-but-not-backed discrepancy

    # 6. The asserted pass is unchanged (never demoted by a lost backing).
    assert _state_of(root, NODE) == "passed"


def test_seed_exit_gate_commands_exit_zero(tmp_path):
    # The roadmap's v0.4 exit-gate commands, on the shipped seed: validate evidence
    # and eligibility both answer cleanly (exit 0) with no records submitted.
    root = _seed_repo(tmp_path)
    assert cli.run(["validate", "evidence"], root=root) == 0
    assert cli.run(["eligibility", NODE], root=root) == 0
