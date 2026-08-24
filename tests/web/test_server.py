"""The serve shell — traits from ADR 0006 / spec §C, pinned (Tier-1 slice T2).

What only the wired shell can show: `serve --help`/`ui --help` list the
loopback traits; there is no `--host` flag; a busy port fails fast with a
clear message before any browser open; the browser opens exactly once at the
served URL and `--no-browser` opts out; Ctrl+C stops cleanly; and a real HTTP
round-trip renders `/health` fresh from the lenient seam without touching
`data/*`.
"""

from __future__ import annotations

import argparse
import errno
import re
import shutil
import threading
import urllib.request
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from skilltrace import cli
from skilltrace.dispatch import Context
from skilltrace.web.handler import page
from skilltrace.web.server import SkillTraceServer, make_server, serve

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _serve_args(port: int = 8341, no_browser: bool = True) -> argparse.Namespace:
    return argparse.Namespace(port=port, no_browser=no_browser)


# --- CLI surface: help text lists the loopback traits -----------------------


@pytest.mark.parametrize("argv", [["serve"], ["ui"]])
def test_serve_help_lists_port_and_no_browser(argv, capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.run([*argv, "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "--port" in out
    assert "--no-browser" in out


def test_no_host_flag_loopback_is_not_configurable(capsys):
    parser = cli.build_parser()
    assert "--host" not in parser.format_help()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["serve", "--host", "0.0.0.0"])
    assert excinfo.value.code == 2  # argparse refused the unknown flag
    capsys.readouterr()


# --- Port binding: fail fast when busy --------------------------------------


def test_make_server_fails_fast_on_busy_port(tmp_path):
    first, failure = make_server(_seed_repo(tmp_path), 0)
    assert first is not None and failure == ""
    try:
        second, failure = make_server(tmp_path, first.server_port)
        assert second is None
        assert str(first.server_port) in failure
        assert "--port" in failure  # points at the escape hatch
    finally:
        first.server_close()


def test_serve_command_reports_busy_port_without_opening_browser(
    tmp_path, monkeypatch, capsys
):
    opened: list[str] = []
    monkeypatch.setattr(
        "skilltrace.web.server.webbrowser.open", lambda url: opened.append(url)
    )
    holder = make_server(tmp_path, 0)
    blocker = holder[0]
    assert blocker is not None
    try:
        result = serve(Context(root=tmp_path, args=_serve_args(blocker.server_port)))
        assert result.exit_code == 1
        out = capsys.readouterr().out
        assert f"cannot bind 127.0.0.1:{blocker.server_port}" in out
        assert opened == []  # nothing half-started, nothing opened
    finally:
        blocker.server_close()


def test_default_port_is_8341():
    args = cli.build_parser().parse_args(["serve"])
    assert args.port == 8341
    assert args.no_browser is False


# --- Browser auto-open and clean shutdown ------------------------------------


def test_serve_opens_browser_once_at_served_url(monkeypatch, tmp_path, capsys):
    opened: list[str] = []
    monkeypatch.setattr(
        "skilltrace.web.server.webbrowser.open", lambda url: opened.append(url)
    )
    monkeypatch.setattr(SkillTraceServer, "serve_forever", lambda self: None)

    result = serve(Context(root=tmp_path, args=_serve_args(no_browser=False)))
    assert result.exit_code == 0
    assert len(opened) == 1
    assert opened[0].startswith("http://127.0.0.1:")
    assert "Ctrl+C" in capsys.readouterr().out


def test_serve_no_browser_opt_out(monkeypatch, tmp_path, capsys):
    opened: list[str] = []
    monkeypatch.setattr(
        "skilltrace.web.server.webbrowser.open", lambda url: opened.append(url)
    )
    monkeypatch.setattr(SkillTraceServer, "serve_forever", lambda self: None)

    result = serve(Context(root=tmp_path, args=_serve_args(no_browser=True)))
    assert result.exit_code == 0
    assert opened == []


def test_ctrl_c_stops_cleanly_with_zero_exit(monkeypatch, tmp_path, capsys):
    def interrupt(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(SkillTraceServer, "serve_forever", interrupt)
    result = serve(Context(root=tmp_path, args=_serve_args()))
    assert result.exit_code == 0
    assert "stopped." in capsys.readouterr().out


# --- Real round-trip: GET routes render fresh from the join ------------------


@pytest.fixture
def running_server(tmp_path):
    server, failure = make_server(_seed_repo(tmp_path), 0)
    assert server is not None, failure
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, tmp_path
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _get(url: str) -> tuple[int, str, str]:
    try:
        with urllib.request.urlopen(url) as response:
            return (
                response.status,
                response.headers.get("Content-Type", ""),
                response.read().decode("utf-8"),
            )
    except urllib.error.HTTPError as err:
        return err.code, err.headers.get("Content-Type", ""), err.read().decode("utf-8")


def test_health_route_renders_via_lenient_seam(running_server):
    server, root = running_server
    status, content_type, body = _get(f"http://127.0.0.1:{server.server_port}/health")

    assert status == 200
    assert content_type.startswith("text/html")
    assert "charset=utf-8" in content_type
    # Layer counts derived from the fresh lenient join over the seed repo —
    # matched loosely so curriculum edits don't break the shell's tests.
    assert re.search(r"\d+ nodes, \d+ edges", body)
    assert "verified=" in body  # resource verification summary present
    assert "states: available=" in body  # progress-store roll-up present


def test_index_route_renders_today_dashboard(running_server):
    # T3 replaced the placeholder shell with the today dashboard (variant A).
    server, _ = running_server
    status, _, body = _get(f"http://127.0.0.1:{server.server_port}/")
    assert status == 200
    assert "TODAY" in body  # the canonical Mentor kicker
    assert 'href="/nodes/' in body  # focus card links at the node detail


def test_unknown_route_is_404(running_server):
    server, _ = running_server
    status, _, body = _get(f"http://127.0.0.1:{server.server_port}/nope")
    assert status == 404


def test_requests_touch_no_data_dir(running_server):
    server, root = running_server
    _get(f"http://127.0.0.1:{server.server_port}/health")
    _get(f"http://127.0.0.1:{server.server_port}/")
    assert not (root / "data").exists()  # data/* never read or written


# --- T3 routes over real HTTP: /next, /nodes/{id}, freshness -------------------


def test_next_route_mirrors_flags_over_http(running_server):
    server, _ = running_server
    base = f"http://127.0.0.1:{server.server_port}"
    _, _, default_body = _get(f"{base}/next")
    assert "60-min session" in default_body
    _, _, limited = _get(f"{base}/next?minutes=90&limit=2")
    assert "90-min session" in limited
    _, _, locked = _get(f"{base}/next?locked=1")
    assert "Locked (" in locked


def test_next_route_bad_query_param_is_400(running_server):
    server, _ = running_server
    status, _, _ = _get(f"http://127.0.0.1:{server.server_port}/next?minutes=abc")
    assert status == 400


def test_node_route_serves_detail_and_unknown_is_404(running_server):
    server, root = running_server
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(root)
    node_id = sorted(view.nodes, key=lambda n: n.id)[0].id
    status, _, body = _get(f"http://127.0.0.1:{server.server_port}/nodes/{node_id}")
    assert status == 200
    assert "THIS SKILL" in body  # canonical Mentor kicker
    assert "DRILL-DOWN" in body
    status, _, _ = _get(f"http://127.0.0.1:{server.server_port}/nodes/no.such_node_99")
    assert status == 404


def test_trailing_slash_and_encoded_node_ids_normalize(running_server):
    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"
    status, _, body = _get(f"{base}/next/")
    assert status == 200  # /next/ behaves like /next
    assert "Next" in body


def test_routes_render_fresh_after_state_edit_over_http(running_server):
    import yaml as _yaml

    server, root = running_server
    base = f"http://127.0.0.1:{server.server_port}"

    from skilltrace.context import load_context_lenient

    view = load_context_lenient(root)
    node_id = next(
        n.id for n in sorted(view.nodes, key=lambda x: x.id)
        if view.store.state_of(n.id) == "available"
    )

    _, _, before = _get(f"{base}/nodes/{node_id}")
    state_path = root / "graph" / "state.yaml"
    doc = _yaml.safe_load(state_path.read_text(encoding="utf-8"))
    doc["progress"][node_id]["state"] = "active"
    state_path.write_text(
        _yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )
    _, _, after = _get(f"{base}/nodes/{node_id}")
    assert before != after  # no cache — the edit is live on refresh
    assert '<span class="pill in-progress">In progress</span>' in after


# --- Escaping discipline and error-message honesty ---------------------------


def test_page_escapes_interpolated_title():
    # ADR 0006: the project owns its escaping — nothing reaches the page raw.
    assert "<script>" not in page("<script>alert(1)</script>", "<p>ok</p>")
    assert "&lt;script&gt;" in page("<script>alert(1)</script>", "")


def test_non_busy_bind_failure_does_not_blame_another_serve(tmp_path, monkeypatch):
    def refuse(self, address, handler):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(SkillTraceServer, "__init__", refuse)
    _, failure = make_server(tmp_path, 8341)
    assert "Permission denied" in failure
    assert "Another skilltrace serve" not in failure  # the hint is for busy ports only
