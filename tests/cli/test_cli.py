"""End-to-end CLI surface: parser, command wiring, and the audit contract."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from skilltrace import cli
from skilltrace.events import load_events


def test_help_lists_the_command_surface():
    help_text = cli.build_parser().format_help()
    for name in ("validate", "sync", "next", "evidence", "attempt", "eligibility", "pass"):
        assert name in help_text


def test_help_lists_aliases_as_alias_for_canonical():
    help_text = cli.build_parser().format_help()
    assert "Alias for `evidence submit`." in help_text
    assert "Alias for `session close`." in help_text
    assert "Alias for `serve`." in help_text


def test_registry_has_the_expected_commands():
    assert set(cli.REGISTRY.names()) == {
        "validate graph",
        "validate evidence",
        "validate execution",
        "validate policy",
        "validate resources",
        "health",
        "node",
        "check-automation",
        "master",
        "sync",
        "next",
        "today",
        "evidence submit",
        "attempt record",
        "eligibility",
        "pass",
        "start",
        "work",
        "session close",
        "blocker create",
        "blocker resolve",
        "remediation create",
        "remediation complete",
        "review schedule",
        "review complete",
        "review cancel",
        "blockers",
        "reviews",
        "resources",
        "verify-resource",
        "resource-report",
        "report progress",
        "report blockers",
        "report reviews",
        "report evidence",
        "report resources",
        "suggest remediation",
        "suggest reviews",
        "retention status",
        "export markdown",
        "export sqlite",
        "export html",
        "backup",
        "serve",
    }


def test_main_is_callable_entry_point():
    assert callable(cli.main)


def test_sync_is_mutating_and_logs_one_event(tmp_path):
    rc = cli.run(["sync"], root=tmp_path)
    assert rc == 0
    events = load_events(tmp_path)
    assert len(events) == 1
    assert events[0]["command"] == "sync"
    # Argparse routing dests must not leak into the audit args.
    assert events[0]["args"] == {}


def test_next_is_read_only_and_logs_nothing(tmp_path):
    rc = cli.run(["next", "--minutes", "30", "--limit", "3", "--show-locked"], root=tmp_path)
    assert rc == 0
    assert load_events(tmp_path) == []


def test_validate_graph_is_read_only_and_logs_nothing(tmp_path):
    rc = cli.run(["validate", "graph"], root=tmp_path)
    assert rc == 0
    assert load_events(tmp_path) == []


def test_root_flag_overrides_detection(tmp_path):
    rc = cli.run(["--root", str(tmp_path), "sync"])
    assert rc == 0
    assert len(load_events(tmp_path)) == 1


# --- Entry-point smoke tests ---------------------------------------------------
#
# The console-script wiring in `pyproject.toml` and the `-m skilltrace` shim in
# `src/skilltrace/__main__.py` both reach `cli.main`; a `pyproject.toml` typo
# would silently ship a broken install. These two subprocess tests pin the
# contract from outside the in-process seam.

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_python_m_skilltrace_reaches_cli_main():
    result = subprocess.run(
        [sys.executable, "-m", "skilltrace", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    # The help text comes from the same parser the in-process tests use, so a
    # shared command name proves the shim reached `cli.main`.
    assert "validate" in result.stdout


def test_pyproject_declares_skilltrace_console_script_pointing_at_cli_main():
    # Read-only: the wiring must point at the module that defines `main`.
    text = PYPROJECT.read_text(encoding="utf-8")
    assert 'skilltrace = "skilltrace.cli:main"' in text
    assert 'st = "skilltrace.cli:main"' in text


# --- Cwd auto-detect ----------------------------------------------------------
#
# The CLI's `--root` override is the test-only path; the in-the-wild path is
# `cli.run(argv)` with no `root` argument, which calls `find_root()` walking
# up from cwd. This test seeds a real `graph/` under a subdir of a tmp repo
# and chdirs into that subdir to prove the walker picks it up.

def test_cwd_auto_detect_finds_the_repo_root_from_a_subdir(tmp_path, monkeypatch):
    sub = tmp_path / "src" / "skilltrace_pkg"
    sub.mkdir(parents=True)
    (sub / "graph").mkdir()
    (sub / "graph" / "edges.yaml").write_text("edges: []\n", encoding="utf-8")

    monkeypatch.chdir(sub)
    rc = cli.run(["validate", "graph"], root=None)
    assert rc == 0
