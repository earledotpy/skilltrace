"""`skilltrace eligibility <node_id>`: the wired read-only verdict path.

The verdict arithmetic is unit-tested in test_eligibility.py. Here we drive the
real command through the CLI on a temp copy of the seed repo, pinning what only
the wired path can show: real loaders and node-existence resolve to the right
exit code (any verdict → 0, unknown node → non-zero), assessment attempts never
count, the passed-but-not-backed discrepancy is surfaced, and the command is
read-only (no audit event, ever).
"""

from __future__ import annotations

import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events

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


def _submit_accepted(root: Path, n: int) -> None:
    """Submit `n` accepted records against NODE's manual gate via the real CLI."""
    for i in range(n):
        relpath = f"evidence/math/set_{i:03d}.md"
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"worked solutions {i}", encoding="utf-8")
        rc = cli.run(
            ["evidence", "submit", NODE, "--location", relpath, "--accept"], root=root
        )
        assert rc == 0


def _set_state(root: Path, node_id: str, state: str) -> None:
    """Write a progress entry directly (test fixture, not an engine automation)."""
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    doc = doc or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Verdicts exit 0 --------------------------------------------------------


def test_fresh_node_reports_not_eligible_and_exits_zero(tmp_path):
    root = _seed_repo(tmp_path)
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "NOT ELIGIBLE" in out
    assert "0/3" in out


def test_node_becomes_eligible_after_enough_accepted_records(tmp_path):
    root = _seed_repo(tmp_path)
    _submit_accepted(root, 3)
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "ELIGIBLE" in out and "NOT ELIGIBLE" not in out
    assert "3/3" in out


def test_below_minimum_still_not_eligible(tmp_path):
    root = _seed_repo(tmp_path)
    _submit_accepted(root, 2)
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "NOT ELIGIBLE" in out
    assert "2/3" in out


# --- Attempts never count ---------------------------------------------------


def test_passing_attempts_do_not_make_a_node_eligible(tmp_path):
    root = _seed_repo(tmp_path)
    # Record passing attempts but submit no evidence: attempts are not evidence.
    for _ in range(5):
        assert cli.run(["attempt", "record", NODE, "--outcome", "passed"], root=root) == 0
    rc, out = _run(root, "eligibility", NODE)
    assert rc == 0
    assert "NOT ELIGIBLE" in out
    assert "0/3" in out


# --- Unknown node is an error ----------------------------------------------


def test_unknown_node_exits_nonzero(tmp_path):
    root = _seed_repo(tmp_path)
    rc, out = _run(root, "eligibility", "no.such.node_99")
    assert rc != 0
    assert "unknown node" in out.lower()


# --- passed-but-not-backed discrepancy -------------------------------------


def test_passed_but_unbacked_node_reports_discrepancy_and_exits_zero(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "passed")  # asserted pass with no backing evidence
    rc, out = _run(root, "eligibility", NODE)
    # The discrepancy is advisory — the pass stands, the command still answers.
    assert rc == 0
    assert "NOT ELIGIBLE" in out
    assert "not revoked" in out


# --- Read-only --------------------------------------------------------------


def test_eligibility_appends_no_audit_event(tmp_path):
    root = _seed_repo(tmp_path)
    _submit_accepted(root, 1)
    events_before = len(load_events(root))
    _run(root, "eligibility", NODE)
    assert len(load_events(root)) == events_before
