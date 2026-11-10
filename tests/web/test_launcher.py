"""The `./start.sh` launcher — issue #366, pinned.

What only a launcher can show: the root is pinned to the directory the shim
lives in (never the cwd, never an ancestor walk); a running instance that
serves the same root is reused instead of collided with; anything else in the
port range is walked past; an explicit `--port` keeps `serve`'s
fail-fast-if-busy trait; a directory that is not a repository is refused in one
sentence; and the launcher is not a CLI command at all (it never appears in
`st --help`).

The shim itself is covered too, because "double-clickable" is the whole point
of the ticket and no unit test can fake it.
"""

from __future__ import annotations

import os
import socket
import subprocess
import threading
from pathlib import Path

import pytest

from skilltrace import cli
from skilltrace.web import launch
from skilltrace.web.server import DEFAULT_PORT, make_server

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    """A throwaway repository: the real curriculum, evidence gates and policy."""
    import shutil

    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _other_root(tmp_path: Path) -> Path:
    """A second repository whose curriculum differs in one node title.

    Two roots that differ only in a YAML comment render identically, so the
    difference has to be something a learner can actually see.
    """
    alt = _seed_repo(tmp_path / "alt")
    node = alt / "graph" / "nodes" / "agents.concepts.agent_fundamentals_01.md"
    text = node.read_text(encoding="utf-8")
    node.write_text(
        text.replace("title:", "title: Zen Confabulation Probe", 1), encoding="utf-8"
    )
    return alt


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _adjacent_free_ports(count: int = 2) -> int:
    """A base port with `count-1` free ports above it (retried, never assumed)."""
    for _ in range(50):
        base = _free_port()
        if all(
            launch._port_is_free(base + offset) for offset in range(1, count)
        ):
            return base
    raise AssertionError("no adjacent free ports on this machine")


@pytest.fixture
def running():
    """Start real servers and always shut them down."""
    started = []

    def _start(root: Path, port: int = 0):
        server, failure = make_server(root, port)
        assert server is not None, failure
        threading.Thread(target=server.serve_forever, daemon=True).start()
        started.append(server)
        return server

    try:
        yield _start
    finally:
        for server in started:
            server.shutdown()
            server.server_close()


# --- the launcher is not a CLI command --------------------------------------


def test_launcher_is_not_in_the_cli_surface(capsys):
    """`st --help` must not learn about `launch` (it is not a dispatcher command)."""
    with pytest.raises(SystemExit):
        cli.run(["--help"])
    out = capsys.readouterr().out.lower()
    assert "launch" not in out
    assert "serve" in out


# --- root pinning -----------------------------------------------------------


def test_a_directory_that_is_not_a_repository_is_refused(tmp_path, capsys):
    rc = launch.launch(tmp_path)
    assert rc == 2
    err = capsys.readouterr().err
    assert "is not a SkillTrace repository" in err
    assert "--root" in err


def test_the_root_is_the_given_directory_not_the_cwd(tmp_path, monkeypatch, capsys):
    """Pinning, not discovery: the launcher never reads the working directory."""
    root = _seed_repo(tmp_path / "repo")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    seen = {}

    def _fake_dispatch(resolved_root, port, no_browser):
        seen["root"] = resolved_root
        seen["port"] = port
        return 0

    monkeypatch.setattr(launch, "_dispatch_serve", _fake_dispatch)
    assert launch.launch(root, port=8399) == 0
    assert seen["root"] == root.resolve()
    assert seen["port"] == 8399


# --- reuse: the instance on the port is mine --------------------------------


def test_a_running_instance_serving_the_same_root_is_reused(
    tmp_path, running, monkeypatch, capsys
):
    root = _seed_repo(tmp_path / "repo")
    server = running(root)
    port = server.server_port

    assert launch._pick(root, first=port, span=1) == ("reuse", port)

    opened = []
    monkeypatch.setattr(launch.webbrowser, "open", opened.append)
    monkeypatch.setattr(launch, "_pick", lambda root, **_: ("reuse", port))
    monkeypatch.setattr(
        launch, "_dispatch_serve", lambda *a: pytest.fail("must not serve again")
    )

    assert launch.launch(root) == 0
    out = capsys.readouterr().out
    assert f"already serving {root.resolve()} at http://127.0.0.1:{port}" in out
    assert opened == [f"http://127.0.0.1:{port}"]


def test_an_instance_serving_another_root_is_not_mine(tmp_path, running):
    """Same pages, different curriculum: the fingerprint must tell them apart."""
    root = _seed_repo(tmp_path / "repo")
    alt = _other_root(tmp_path)
    port = running(alt).server_port

    assert launch._serves_root(port, root) is False


def test_a_port_served_by_another_root_is_walked_past(tmp_path, running):
    root = _seed_repo(tmp_path / "repo")
    alt = _other_root(tmp_path)
    base = _adjacent_free_ports(2)
    running(alt, port=base)

    outcome, chosen = launch._pick(root, first=base, span=2)
    assert (outcome, chosen) == ("serve", base + 1)


def test_a_full_range_reports_no_free_port(tmp_path, running, monkeypatch, capsys):
    root = _seed_repo(tmp_path / "repo")
    alt = _other_root(tmp_path)
    base = _adjacent_free_ports(1)
    running(alt, port=base)

    assert launch._pick(root, first=base, span=1) == ("none", None)

    monkeypatch.setattr(launch, "_pick", lambda root, **_: ("none", None))
    assert launch.launch(root) == 1
    err = capsys.readouterr().err
    assert f"no free port in {DEFAULT_PORT}-{DEFAULT_PORT + launch.PORT_RANGE - 1}" in err


def test_a_walked_port_is_announced(tmp_path, monkeypatch, capsys):
    root = _seed_repo(tmp_path / "repo")
    chosen = DEFAULT_PORT + 3
    sent = {}

    monkeypatch.setattr(launch, "_pick", lambda root, **_: ("serve", chosen))
    monkeypatch.setattr(
        launch, "_dispatch_serve", lambda r, p, b: sent.update(port=p) or 0
    )

    assert launch.launch(root) == 0
    out = capsys.readouterr().out
    assert f"port {DEFAULT_PORT} is not available; using {chosen}" in out
    assert sent["port"] == chosen


# --- the delegated run is still `serve`, and `serve` is unchanged -----------


def test_an_explicit_busy_port_keeps_serve_fail_fast(tmp_path, running, capsys):
    """No relocation and no reuse probe: `--port` means that port."""
    root = _seed_repo(tmp_path / "repo")
    alt = _other_root(tmp_path)
    busy = running(alt).server_port

    assert launch.launch(root, port=busy) == 1
    out = capsys.readouterr().out
    assert f"cannot bind 127.0.0.1:{busy}" in out
    assert "address already in use" in out


def test_the_handoff_dispatches_the_read_only_serve_command(tmp_path, monkeypatch):
    """The launch path is `serve` through the dispatcher — never a second path."""
    root = _seed_repo(tmp_path / "repo")
    calls = []

    real_dispatch = launch.dispatch if hasattr(launch, "dispatch") else None
    assert real_dispatch is None  # imported lazily, not at module level

    import skilltrace.dispatch as dispatch_module

    monkeypatch.setattr(
        dispatch_module,
        "dispatch",
        lambda command, ctx: calls.append((command.name, ctx.root, ctx.args.port)) or 0,
    )

    assert launch.launch(root, port=8399) == 0
    assert calls == [("serve", root.resolve(), 8399)]


# --- the shim: double-clickable, and honest when the environment is missing --


@pytest.mark.skipif(os.name == "nt", reason="the MVP shim is bash (issue #366)")
def test_start_sh_is_an_executable_bash_script():
    """The shipped artifact itself — no test can fake a double-click."""
    script = REPO_ROOT / "start.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)
    assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")


@pytest.mark.skipif(os.name == "nt", reason="the MVP shim is bash (issue #366)")
def test_start_sh_names_the_install_steps_when_the_environment_is_missing(tmp_path):
    """No `.venv`, no importable skilltrace: one sentence naming the fix."""
    script = tmp_path / "start.sh"
    script.write_text(
        (REPO_ROOT / "start.sh").read_text(encoding="utf-8"), encoding="utf-8"
    )
    script.chmod(0o755)
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()

    completed = subprocess.run(
        ["/bin/bash", str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={"PATH": str(empty_path), "HOME": str(tmp_path)},
    )
    assert completed.returncode == 2
    assert "no Python environment with SkillTrace installed was found" in completed.stderr
    assert "docs/INSTALL.md" in completed.stderr
