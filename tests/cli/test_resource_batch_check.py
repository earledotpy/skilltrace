"""CLI integration tests for check-resources (v1.8 spec §4.1, §6).

Drives the in-process CLI against disposable repos with mocked HTTP:

- exit 0 for answered sweeps (including all-BROKEN — a failure verdict is
  the resource's, not the command's)
- non-zero exit for usage/load failures (unknown id is N/A — the sweep has
  no id argument; unreadable registry and url-less entries fail)
- per-line OK/BROKEN presence plus the `N checked, …` summary
- --stale-only selection against the existing staleness window
- registry byte-identical after the run (zero writes), no event appended
- 429 reported as BROKEN via `reason`, no retry
"""

from __future__ import annotations

import io
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from skilltrace import cli
from skilltrace.events import load_events


class _MockResponse:
    def __init__(self, code: int = 200, url: str = "https://example.com/page") -> None:
        self.code = code
        self.status = code
        self.url = url

    def getcode(self) -> int:
        return self.code

    def geturl(self) -> str:
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def _write_res(root: Path, resources: list[dict]):
    path = root / "graph" / "resources.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"resources": resources}, sort_keys=False), encoding="utf-8"
    )


def _registry_bytes(root: Path) -> bytes:
    return (root / "graph" / "resources.yaml").read_bytes()


def _ok(url: str) -> _MockResponse:
    return _MockResponse(code=200, url=url)


def _http_error(url: str, code: int, msg: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url=url, code=code, msg=msg, hdrs={}, fp=io.BytesIO()
    )


# ---------------------------------------------------------------------------
# Answered sweeps exit 0
# ---------------------------------------------------------------------------


def test_check_resources_all_ok(resources_repo, capsys):
    _write_res(
        resources_repo,
        [
            {"id": "res-a", "url": "https://example.com/a", "cost": "free"},
            {"id": "res-b", "url": "https://example.com/b", "cost": "free"},
        ],
    )
    before = _registry_bytes(resources_repo)
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _ok("https://example.com/a"),
            _ok("https://example.com/b"),
        ],
    ):
        rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: OK res-a — status 200" in out
    assert "check-resources: OK res-b — status 200" in out
    assert "check-resources: 2 checked, 2 OK, 0 BROKEN" in out
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


def test_check_resources_default_selector_is_all(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "res-a", "url": "https://example.com/a", "cost": "free"}],
    )
    before = _registry_bytes(resources_repo)
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _ok("https://example.com/a"),
        ],
    ):
        rc = cli.run(["check-resources"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: OK res-a — status 200" in out
    assert "check-resources: 1 checked, 1 OK, 0 BROKEN" in out
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


def test_check_resources_mixed_ok_and_broken_still_exit_0(resources_repo, capsys):
    _write_res(
        resources_repo,
        [
            {"id": "good-res", "url": "https://example.com/good", "cost": "free"},
            {"id": "gone-res", "url": "https://example.com/gone", "cost": "free"},
            {"id": "down-res", "url": "https://example.com/down", "cost": "free"},
        ],
    )
    before = _registry_bytes(resources_repo)
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _ok("https://example.com/good"),
            _http_error("https://example.com/gone", 404, "Not Found"),
            urllib.error.URLError("Connection refused"),
        ],
    ):
        rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: OK good-res — status 200" in out
    assert "check-resources: BROKEN gone-res — status 404" in out
    assert "check-resources: BROKEN down-res — Connection refused" in out
    assert "check-resources: 3 checked, 1 OK, 2 BROKEN" in out
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


def test_check_resources_all_broken_still_exit_0(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "gone-res", "url": "https://example.com/gone", "cost": "free"}],
    )
    before = _registry_bytes(resources_repo)
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _http_error("https://example.com/gone", 500, "Server Error"),
        ],
    ):
        rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: BROKEN gone-res — status 500" in out
    assert "check-resources: 1 checked, 0 OK, 1 BROKEN" in out
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


def test_check_resources_429_backs_off_bounded_then_reports_broken(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "rate-res", "url": "https://example.com/rate", "cost": "free"}],
    )
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
        ],
    ) as mock_open:
        rc = cli.run(
            ["check-resources", "--all", "--backoff-attempts", "2", "--per-host-delay", "0"],
            root=resources_repo,
        )
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: BROKEN rate-res — status 429" in out
    assert "check-resources: 1 checked, 0 OK, 1 BROKEN" in out
    # Bounded backoff: exactly two total attempts (initial + one retry), then
    # the 429 is the resource's BROKEN verdict.
    assert mock_open.call_count == 3  # robots + two 429 attempts
    assert load_events(resources_repo) == []


def test_check_resources_429_default_attempts_is_policy_three(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "rate-res", "url": "https://example.com/rate", "cost": "free"}],
    )
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
        ],
    ) as mock_open:
        rc = cli.run(
            ["check-resources", "--all", "--per-host-delay", "0"],
            root=resources_repo,
        )
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: BROKEN rate-res — status 429" in out
    # Policy default: three bounded attempts, then BROKEN.
    assert mock_open.call_count == 4  # robots + three 429 attempts
    assert load_events(resources_repo) == []


def test_check_resources_no_robots_flag_skips_robots_fetch(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "res-a", "url": "https://example.com/a", "cost": "free"}],
    )
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[_ok("https://example.com/a")],
    ) as mock_open:
        rc = cli.run(["check-resources", "--all", "--no-robots"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: OK res-a — status 200" in out
    assert mock_open.call_count == 1  # only the target URL, no robots fetch


def test_check_resources_disabled_sweep_policy_degrades_to_plain_batch(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "rate-res", "url": "https://example.com/rate", "cost": "free"}],
    )
    sweep_path = resources_repo / "policy" / "polite_sweep.yaml"
    doc = yaml.safe_load(sweep_path.read_text(encoding="utf-8"))
    doc["polite_sweep_policy"]["enabled"] = False
    sweep_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _http_error("https://example.com/rate", 429, "Too Many Requests"),
        ],
    ) as mock_open:
        rc = cli.run(["check-resources", "--all", "--per-host-delay", "5"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: BROKEN rate-res — status 429" in out
    # Disabled: explicit delay ignored, robots skipped, no 429 retry.
    assert mock_open.call_count == 1


@pytest.mark.parametrize(
    "argv",
    [
        ["check-resources", "--all", "--backoff-attempts", "0"],
        ["check-resources", "--all", "--backoff-attempts", "11"],
        ["check-resources", "--all", "--per-host-delay", "-1"],
        ["check-resources", "--all", "--per-host-delay", "601"],
    ],
)
def test_check_resources_rejects_out_of_range_sweep_flags(resources_repo, capsys, argv):
    _write_res(
        resources_repo,
        [{"id": "res-a", "url": "https://example.com/a", "cost": "free"}],
    )
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        rc = cli.run(argv, root=resources_repo)
    assert rc == 1
    assert "check-resources: FAILED" in capsys.readouterr().out
    assert mock_open.call_count == 0


def test_check_resources_empty_registry(resources_repo, capsys):
    _write_res(resources_repo, [])
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resources: 0 checked, 0 OK, 0 BROKEN" in out
    assert mock_open.call_count == 0
    assert load_events(resources_repo) == []


# ---------------------------------------------------------------------------
# --stale-only selection
# ---------------------------------------------------------------------------


def test_check_resources_stale_only_selects_stale(resources_repo, capsys):
    fresh = date.today().isoformat()
    ancient = (date.today() - timedelta(days=400)).isoformat()
    _write_res(
        resources_repo,
        [
            {
                "id": "fresh-res",
                "url": "https://example.com/fresh",
                "cost": "free",
                "last_verified": fresh,
            },
            {
                "id": "stale-res",
                "url": "https://example.com/stale",
                "cost": "free",
                "last_verified": ancient,
            },
            {
                "id": "never-res",
                "url": "https://example.com/never",
                "cost": "free",
            },
        ],
    )
    before = _registry_bytes(resources_repo)
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=[
            _ok("https://example.com/robots.txt"),
            _ok("https://example.com/stale"),
        ],
    ) as mock_open:
        rc = cli.run(["check-resources", "--stale-only"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out
    # Only the stale entry is swept: verified-within-window and unverified
    # entries are not stale under the existing window.
    assert "check-resources: OK stale-res — status 200" in out
    assert "fresh-res" not in out
    assert "never-res" not in out
    assert "check-resources: 1 checked, 1 OK, 0 BROKEN" in out
    assert mock_open.call_count == 2  # robots + the one stale entry
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


# ---------------------------------------------------------------------------
# Failures exit non-zero, write nothing
# ---------------------------------------------------------------------------


def test_check_resources_url_less_entry_fails(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "local-doc", "local_path": "resources/doc.pdf", "cost": "free"}],
    )
    before = _registry_bytes(resources_repo)
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "resource local-doc has no url" in out
    assert mock_open.call_count == 0
    assert _registry_bytes(resources_repo) == before
    assert load_events(resources_repo) == []


def test_check_resources_unreadable_registry_fails(resources_repo, capsys):
    (resources_repo / "graph" / "resources.yaml").write_text(
        "resources: [unclosed", encoding="utf-8"
    )
    rc = cli.run(["check-resources", "--all"], root=resources_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "check-resources: FAILED" in out
    assert load_events(resources_repo) == []
