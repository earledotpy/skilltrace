"""`skilltrace sync` command: the end-to-end persist + audit path.

The pure readiness rule is tested in test_readiness.py. Here we drive the real
command through the CLI on a temp copy of the seed repo, asserting the store is
persisted and exactly one audit event carries the changed node ids — the path
the v0.3 exit gate actually runs.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.graph.state import load_state

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    """Copy the real graph/ into a temp repo so a mutating sync is isolated."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    return tmp_path


def _read_state_yaml(root: Path) -> dict:
    return yaml.safe_load((root / "graph" / "state.yaml").read_text(encoding="utf-8"))


def test_sync_on_seed_is_clean_and_logs_one_empty_event(tmp_path):
    root = _seed_repo(tmp_path)
    rc = cli.run(["sync"], root=root)
    assert rc == 0
    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "sync"
    assert events[0]["records_touched"] == []  # seed already in sync


def test_sync_flips_target_available_after_source_passed(tmp_path):
    root = _seed_repo(tmp_path)

    # Pass a source out-of-band by editing the store directly (a fixture stand-in
    # for the pass command, which lands in v0.4). variables_expressions has a
    # single hard prereq: order_operations.
    store = load_state(root)
    store.write_asserted("math.arithmetic.order_operations_01", "passed")
    from skilltrace.graph.state import save_state

    save_state(store, root)

    rc = cli.run(["sync"], root=root)
    assert rc == 0

    # The target is persisted as available in state.yaml.
    persisted = _read_state_yaml(root)["progress"]
    assert persisted["math.algebra.variables_expressions_01"]["state"] == "available"
    # The passed source is untouched (asserted progress preserved).
    assert persisted["math.arithmetic.order_operations_01"]["state"] == "passed"

    # Exactly one sync event names the flipped node.
    events = [e for e in load_events(root) if e["command"] == "sync"]
    assert len(events) == 1
    assert events[0]["records_touched"] == ["math.algebra.variables_expressions_01"]


def test_sync_reload_reflects_persisted_readiness(tmp_path):
    root = _seed_repo(tmp_path)
    store = load_state(root)
    store.write_asserted("math.arithmetic.order_operations_01", "passed")
    from skilltrace.graph.state import save_state

    save_state(store, root)

    cli.run(["sync"], root=root)

    reloaded = load_state(root)
    assert reloaded.state_of("math.algebra.variables_expressions_01") == "available"
