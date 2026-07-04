"""`skilltrace pass <node_id>`: the wired assert-progress + audit path.

The decision logic is unit-tested in test_passing.py. Here we drive the real
command through the CLI on a temp copy of the seed repo, pinning what only the
wired path can show: eligibility gates the pass; a locked node refuses regardless
of evidence; a pass succeeds from `available` (skipping `active`) and from
`active`; an already-passed/mastered node refuses; a successful pass appends
exactly one audit event and touches *only* the progress store (no evidence,
attempt, or review side-effects); a refusal writes nothing; and `passed` is
written through the guarded store API. A safety test pins that the pass command
is the sole caller of the asserted writer with `passed`.
"""

from __future__ import annotations

import ast
import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events
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


def _state_of(root: Path, node_id: str) -> str:
    return load_state(root).state_of(node_id)


def _calls_write_asserted_passed(path: Path) -> bool:
    """True iff `path` has a real `<x>.write_asserted(..., "passed")` call site.

    AST-based so docstrings/comments that merely mention the call do not count.
    Matches a `passed` string in any argument position (positional or keyword).
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_asserted"
        ):
            args = list(node.args) + [kw.value for kw in node.keywords]
            if any(isinstance(a, ast.Constant) and a.value == "passed" for a in args):
                return True
    return False


# --- Eligibility gates the pass --------------------------------------------


def test_pass_refuses_without_eligibility(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "available")
    _submit_accepted(root, 2)  # below the minimum of 3
    events_before = len(load_events(root))

    rc, out = _run(root, "pass", NODE)

    assert rc == 2
    assert "not pass-eligible" in out
    assert "nothing passed" in out
    assert _state_of(root, NODE) == "available"  # state unchanged
    assert len(load_events(root)) == events_before  # no event on refusal


def test_pass_succeeds_with_eligibility_from_available(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "available")
    _submit_accepted(root, 3)

    rc, out = _run(root, "pass", NODE)

    assert rc == 0
    assert "is now passed" in out
    assert _state_of(root, NODE) == "passed"


def test_pass_succeeds_from_active_skipping_no_step(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "active")
    _submit_accepted(root, 3)

    rc, _ = _run(root, "pass", NODE)

    assert rc == 0
    assert _state_of(root, NODE) == "passed"


# --- Locked refuses regardless of evidence (no hard-prereq override) --------


def test_pass_refuses_on_locked_even_when_eligible(tmp_path):
    root = _seed_repo(tmp_path)
    _submit_accepted(root, 3)  # fully eligible…
    _set_state(root, NODE, "locked")  # …but locked
    events_before = len(load_events(root))

    rc, out = _run(root, "pass", NODE)

    assert rc == 2
    assert "locked" in out
    assert _state_of(root, NODE) == "locked"
    assert len(load_events(root)) == events_before


# --- Already passed / mastered refuses --------------------------------------


def test_pass_refuses_when_already_passed(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "passed")
    _submit_accepted(root, 3)
    events_before = len(load_events(root))

    rc, out = _run(root, "pass", NODE)

    assert rc == 2
    assert "already passed" in out
    assert len(load_events(root)) == events_before


def test_pass_refuses_when_already_mastered(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "mastered")
    _submit_accepted(root, 3)

    rc, out = _run(root, "pass", NODE)

    assert rc == 2
    assert "already mastered" in out
    assert _state_of(root, NODE) == "mastered"  # never demoted


# --- Unknown node is an operational failure ---------------------------------


def test_pass_unknown_node_exits_one(tmp_path):
    root = _seed_repo(tmp_path)
    rc, out = _run(root, "pass", "no.such.node_99")
    assert rc == 1
    assert "unknown node" in out.lower()


# --- Audit: exactly one event on success ------------------------------------


def test_successful_pass_appends_exactly_one_event(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "available")
    _submit_accepted(root, 3)
    events_before = len(load_events(root))

    rc, _ = _run(root, "pass", NODE)

    assert rc == 0
    events_after = load_events(root)
    assert len(events_after) == events_before + 1
    assert events_after[-1]["command"] == "pass"
    assert NODE in events_after[-1]["records_touched"]


# --- "No other file touched" ------------------------------------------------


def test_successful_pass_touches_only_the_progress_store(tmp_path):
    root = _seed_repo(tmp_path)
    _set_state(root, NODE, "available")
    _submit_accepted(root, 3)

    records_path = root / "evidence" / "evidence_records.yaml"
    attempts_path = root / "evidence" / "attempts.yaml"
    records_before = records_path.read_bytes()
    attempts_before = attempts_path.read_bytes() if attempts_path.exists() else None

    rc, _ = _run(root, "pass", NODE)
    assert rc == 0

    # The pass writes progress + the event log only — no review scheduling, no
    # sync side-effects, no touched evidence or attempts.
    assert records_path.read_bytes() == records_before
    after = attempts_path.read_bytes() if attempts_path.exists() else None
    assert after == attempts_before


# --- Safety: sole caller of the asserted writer with `passed` ---------------


def test_pass_command_is_sole_asserted_passed_writer():
    """Invariant: nothing but the pass command asserts `passed`.

    The issue's safety check, made precise with the AST so a docstring or comment
    that merely *names* the call does not register — only a real
    `<x>.write_asserted(..., "passed")` call site does. Scoped to the `passed`
    literal on purpose: `start`/`master` will legitimately call the same writer
    with `active`/`mastered` in later RCs, so a check on `write_asserted` alone
    would become a false tripwire. `state.py` (the writer definition) never calls
    it; tests are out of scope.
    """
    src = REPO_ROOT / "src" / "skilltrace"
    hits = sorted(
        path.relative_to(src).as_posix()
        for path in src.rglob("*.py")
        if _calls_write_asserted_passed(path)
    )
    assert hits == ["commands/pass_.py"], hits
