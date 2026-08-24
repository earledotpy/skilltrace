"""Browser writes take the one dispatch path (G2#66 / Tier-1 slice T1).

Drives the real `pass` command through `REGISTRY.get("pass")` with a
web-sourced `Context` on a temp copy of the seed repo — the same handler, the
same guarded asserted writer (`write_asserted`, forward-only), exactly one
audit event under the canonical command name plus `source: "web"`. There is no
second write path for the browser to take; this test pins that a web-sourced
dispatch is indistinguishable from a CLI dispatch except for the provenance
field.
"""

from __future__ import annotations

import argparse
import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.cli import REGISTRY
from skilltrace.dispatch import Context, dispatch
from skilltrace.events import load_events
from skilltrace.graph.state import load_state

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"  # manual gate, one required spec, min 3


def _seed_repo(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def _submit_accepted(root: Path, n: int) -> None:
    """Submit `n` accepted records against NODE's manual gate via the real CLI."""
    for i in range(n):
        relpath = f"evidence/math/set_{i:03d}.md"
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"worked solutions {i}", encoding="utf-8")
        assert cli.run(
            ["evidence", "submit", NODE, "--location", relpath, "--accept"], root=root
        ) == 0


def _set_state(root: Path, node_id: str, state: str) -> None:
    """Write a progress entry directly (test fixture, not an engine automation)."""
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    doc = doc or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_pass_via_web_context_writes_and_audits_with_source(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "available")
    _submit_accepted(root, 3)
    events_before = len(load_events(root))

    command = REGISTRY.get("pass")
    assert command is not None  # the browser reuses the registry lookup, not its own table
    ctx = Context(root=root, args=argparse.Namespace(node_id=NODE), source="web")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = dispatch(command, ctx)

    assert rc == 0
    # The write went through the guarded asserted writer (forward-only): the
    # node is `passed`, and nothing demoted or bypassed the store.
    assert load_state(root).state_of(NODE) == "passed"

    events = load_events(root)
    assert len(events) == events_before + 1  # exactly one audit event
    event = events[-1]
    assert event["command"] == "pass"  # canonical name — no web-specific command
    assert event["args"]["node_id"] == NODE
    assert event["args"]["source"] == "web"
