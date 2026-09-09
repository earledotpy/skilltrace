"""`skilltrace graph impact` — CLI command-output tests (spec §2/§5/§7).

The pure `compute_impact` core (flips, asserted-standing, rec diffs, no-op
edges, dangling refs) is unit-tested in tests/graph/test_impact.py. Here we
drive the real command on a disposable git repo seeded with the shipped
`graph/`, pinning the things only the wired path can show: registration as
READ_ONLY, the one non-zero exit case (baseline unavailable / not a git
repository), `--baseline` overriding `--from`, and that a computed run
appends no audit event and exits 0 with advisory words only.

The seeded git repo is built once (module scope) and shared: `graph impact`
is READ_ONLY and never mutates the repo or the event log, so the shared
baseline is safe for every test here.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


def _copy_seed(root: Path) -> None:
    shutil.copytree(REPO_ROOT / "graph", root / "graph")
    shutil.copytree(REPO_ROOT / "execution", root / "execution")


def _git(root: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(root), *argv], check=True, capture_output=True, text=True)


@pytest.fixture(scope="module")
def git_seed_repo(tmp_path_factory):
    """A disposable git repo seeded with the shipped graph + execution."""
    root = tmp_path_factory.mktemp("impact_repo") / "repo"
    root.mkdir()
    _copy_seed(root)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "tester@example.com")
    _git(root, "config", "user.name", "Tester")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed baseline")
    return root


# --- Registration ----------------------------------------------------------


def test_graph_impact_is_registered_read_only():
    command = cli.REGISTRY.get("graph impact")
    assert command is not None
    assert command.kind.value == "read_only"
    assert command.automation_action is None


def test_graph_impact_logs_no_audit_event(git_seed_repo, capsys):
    root = git_seed_repo
    initial_events = len(load_events(root))
    rc = cli.run(["graph", "impact"], root=root)
    assert rc == 0
    assert len(load_events(root)) == initial_events


# --- Exit code contract ----------------------------------------------------


def test_graph_impact_exit_zero_on_seed_no_edits(git_seed_repo, capsys):
    """No edits since the baseline commit -> an advisory report, exit 0."""
    rc = cli.run(["graph", "impact"], root=git_seed_repo)
    assert rc == 0
    out = capsys.readouterr().out
    # Advisory words, never a gate verdict.
    assert "graph impact vs" in out


def test_graph_impact_non_git_dir_fails_cleanly(tmp_path, capsys):
    """The one non-zero case: no baseline can be loaded at all."""
    root = tmp_path / "repo"
    root.mkdir()
    _copy_seed(root)  # copied, but never `git init`'d
    rc = cli.run(["graph", "impact"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAILED" in out and "baseline" in out


# --- --baseline over --from ------------------------------------------------


def test_graph_impact_baseline_wins_over_from(git_seed_repo, tmp_path, capsys):
    """When both are given, `--baseline` wins and `--from` is ignored (spec D-Baseline)."""
    root = git_seed_repo

    # A second checkout holding the same curriculum, used as `--baseline`.
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    _copy_seed(baseline)

    # `--from` names a ref that does not exist; if `--baseline` wins the run
    # still computes (exit 0). If `--from` were honored, the unknown ref would
    # make the baseline unavailable and the command would exit 1.
    rc = cli.run(
        ["graph", "impact", "--from", "no.such.ref", "--baseline", str(baseline)],
        root=root,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "graph impact vs baseline" in out