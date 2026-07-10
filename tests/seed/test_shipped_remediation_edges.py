"""Shipped remediation edges activate against the shipped policy (v0.8 slice 5).

The policy-layer suite (`tests/policy/test_remediation_edges.py`) proves the
activation *mechanism* on synthetic edges. This suite proves the *shipped* edges
authored in this slice actually fire: it drives the real CLI against a disposable
copy of the shipped repo with one injected trigger and asserts that
`suggest remediation` and `next` surface the right rescue — exercising acceptance
criterion 4 (activate on a blocker or the attempt threshold; never lock the
target) through the existing commands, not a re-derivation of the six-case matrix.

The copy is disposable by design: a real `submit`/`blocker` on the shipped repo
would write an evidence record and an audit event, so the injection happens only
in a `copytree` under tmp.
"""

from __future__ import annotations

import shutil

import yaml

from skilltrace import cli

from .conftest import REPO_ROOT

# A remediation edge shipped in this slice: the fraction-fluency rescue supports
# solving linear equations. Chosen because both endpoints are stable node ids.
REMEDIATION_NODE = "math.arithmetic.fractions_01"
RESCUE_TARGET = "math.algebra.linear_equations_01"
# A second shipped target of the same rescue that is `available` in the shipped
# store (no unmet hard prereq) — used to show activation leaves readiness intact.
AVAILABLE_TARGET = "math.algebra.variables_expressions_01"


def _disposable_repo(tmp_path):
    """A throwaway copy of the shipped repo (no .git / caches) to mutate freely."""
    dst = tmp_path / "repo"
    shutil.copytree(
        REPO_ROOT,
        dst,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache"),
    )
    return dst


def _write_yaml(root, relpath, doc):
    (root / relpath).write_text(yaml.safe_dump(doc), encoding="utf-8")


def test_shipped_edge_exists_for_the_fixture():
    # Guard the fixture: if the authored edge is ever renamed, fail loudly here
    # rather than silently passing a test that no longer exercises anything.
    edges = yaml.safe_load((REPO_ROOT / "graph" / "edges.yaml").read_text("utf-8"))
    match = [
        e
        for e in edges["edges"]
        if e["edge_type"] == "remediation"
        and e["source"] == REMEDIATION_NODE
        and e["target"] == RESCUE_TARGET
    ]
    assert match, f"expected a shipped remediation edge {REMEDIATION_NODE} -> {RESCUE_TARGET}"
    assert match[0]["active"] is True


def test_open_blocker_on_target_activates_the_shipped_edge(tmp_path, capsys):
    root = _disposable_repo(tmp_path)
    _write_yaml(
        root,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.{RESCUE_TARGET}.001",
                    "node_id": RESCUE_TARGET,
                    "status": "open",
                    "description": "stuck manipulating fractional coefficients",
                    "created_at": "2026-07-07T10:00:00+00:00",
                }
            ]
        },
    )

    rc = cli.run(["suggest", "remediation"], root=root)
    out = capsys.readouterr().out
    assert rc == 0, out
    # The shipped rescue is named, pointed at the blocked target, with the trigger.
    assert REMEDIATION_NODE in out and RESCUE_TARGET in out, out
    assert "open blocker" in out, out


def test_attempt_threshold_on_target_activates_the_shipped_edge(tmp_path, capsys):
    root = _disposable_repo(tmp_path)
    # Three failed attempts without a pass — the shipped policy threshold.
    _write_yaml(
        root,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{RESCUE_TARGET}.{n:03d}",
                    "node_id": RESCUE_TARGET,
                    "outcome": "failed",
                    "created_at": "2026-07-07",
                }
                for n in range(1, 4)
            ]
        },
    )

    rc = cli.run(["suggest", "remediation"], root=root)
    out = capsys.readouterr().out
    assert rc == 0, out
    assert REMEDIATION_NODE in out and RESCUE_TARGET in out, out
    assert "failed attempt" in out, out


def test_activation_never_locks_the_target(tmp_path, capsys):
    # Criterion 4's "never locking the target": an active remediation edge raises
    # the rescue's priority but leaves the target's derived readiness untouched.
    # AVAILABLE_TARGET has no unmet hard prereq, so with an open blocker on it the
    # edge activates yet the target stays an `available`, rankable candidate rather
    # than being demoted to locked.
    root = _disposable_repo(tmp_path)
    _write_yaml(
        root,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.{AVAILABLE_TARGET}.001",
                    "node_id": AVAILABLE_TARGET,
                    "status": "open",
                    "description": "stuck on fractional coefficients",
                    "created_at": "2026-07-07T10:00:00+00:00",
                }
            ]
        },
    )

    rc = cli.run(["next", "--minutes", "30", "--limit", "40", "--show-locked"], root=root)
    out = capsys.readouterr().out
    assert rc == 0, out
    # The advisory names the active edge for this target...
    assert f"{REMEDIATION_NODE} supports {AVAILABLE_TARGET}" in out, out
    # ...and the target still ranks as a candidate (has a score line), never
    # appearing in the locked section the `--show-locked` tail would print.
    lines = out.splitlines()
    split = next((i for i, l in enumerate(lines) if l.startswith("locked (")), len(lines))
    ranked, locked_lines = "\n".join(lines[:split]), lines[split:]
    assert AVAILABLE_TARGET in ranked and "score" in ranked, out
    # The target must not be a *locked entry* itself. It may still appear in the
    # locked tail as another node's unmet-prerequisite reason ("blocked by: ..."),
    # so match the entry form (`  <node> - `) rather than a bare substring.
    locked_entry = f"  {AVAILABLE_TARGET} - "
    assert not any(l.startswith(locked_entry) for l in locked_lines), (
        "an active remediation edge must not lock its target"
    )
