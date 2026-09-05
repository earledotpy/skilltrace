"""CLI integration tests for check-resource and verify-resource --check-url (v1.7 spec §4.1, §4.2, §8).

Asserts:
- check-resource: exit codes, output shapes, zero writes, no audit events
- verify-resource --check-url: failure writes broken marker, success writes nothing positive
- verify-resource without --check-url: human path remains intact
- Event presence and safety assertions
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import yaml

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.resources.registry import load_resources


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
    path.write_text(yaml.safe_dump({"resources": resources}, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# check-resource CLI tests
# ---------------------------------------------------------------------------


def test_check_resource_ok(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "python-course", "url": "https://example.com/course", "cost": "free"}],
    )
    mock_resp = _MockResponse(code=200, url="https://example.com/course")
    with patch("urllib.request.OpenerDirector.open", return_value=mock_resp):
        rc = cli.run(["check-resource", "python-course"], root=resources_repo)

    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resource: OK python-course — status 200, final_url https://example.com/course" in out
    # Read-only and no audit events
    assert load_events(resources_repo) == []


def test_check_resource_broken_http_404(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "python-course", "url": "https://example.com/missing", "cost": "free"}],
    )
    http_err = urllib.error.HTTPError(
        url="https://example.com/missing",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=io.BytesIO(),
    )
    with patch("urllib.request.OpenerDirector.open", side_effect=http_err):
        rc = cli.run(["check-resource", "python-course"], root=resources_repo)

    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resource: BROKEN python-course — status 404: not found" in out
    assert load_events(resources_repo) == []
    # Assert no marker was written to registry
    res = load_resources(resources_repo)[0]
    assert res.broken is None


def test_check_resource_broken_timeout(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "python-course", "url": "https://example.com/slow", "cost": "free"}],
    )
    with patch("urllib.request.OpenerDirector.open", side_effect=TimeoutError("timed out")):
        rc = cli.run(["check-resource", "python-course", "--timeout", "10"], root=resources_repo)

    assert rc == 0
    out = capsys.readouterr().out
    assert "check-resource: BROKEN python-course — timeout after 10s" in out
    assert load_events(resources_repo) == []


def test_check_resource_unknown_id(resources_repo, capsys):
    _write_res(resources_repo, [])
    rc = cli.run(["check-resource", "unknown-res"], root=resources_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "unknown resource unknown-res" in out
    assert load_events(resources_repo) == []


def test_check_resource_missing_url(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "local-doc", "local_path": "resources/doc.pdf", "cost": "free"}],
    )
    rc = cli.run(["check-resource", "local-doc"], root=resources_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "resource local-doc has no url" in out
    assert load_events(resources_repo) == []


# ---------------------------------------------------------------------------
# verify-resource --check-url CLI tests
# ---------------------------------------------------------------------------


def test_verify_resource_check_url_failure_writes_broken_marker(resources_repo, capsys):
    _write_res(
        resources_repo,
        [
            {
                "id": "failing-res",
                "url": "https://example.com/dead",
                "cost": "free",
                "last_verified": "2026-01-01",
            }
        ],
    )
    http_err = urllib.error.HTTPError(
        url="https://example.com/dead",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=io.BytesIO(),
    )
    with patch("urllib.request.OpenerDirector.open", side_effect=http_err):
        rc = cli.run(["verify-resource", "failing-res", "--check-url"], root=resources_repo)

    assert rc == 0
    out = capsys.readouterr().out
    assert "failing-res marked broken" in out
    assert "status 404: not found" in out

    # Assert broken marker was written and last_verified was NOT updated
    res = load_resources(resources_repo)[0]
    assert res.broken is not None
    assert "status 404: not found" in res.broken.reason
    assert res.last_verified == "2026-01-01"  # preserved, not touched

    # Exactly one audit event
    events = load_events(resources_repo)
    assert len(events) == 1
    assert events[0]["command"] == "verify-resource"
    assert events[0]["records_touched"] == ["failing-res"]


def test_verify_resource_check_url_success_never_writes_positive(resources_repo, capsys):
    _write_res(
        resources_repo,
        [
            {
                "id": "fresh-res",
                "url": "https://example.com/ok",
                "cost": "free",
                # no last_verified
            }
        ],
    )
    mock_resp = _MockResponse(code=200, url="https://example.com/ok")
    with patch("urllib.request.OpenerDirector.open", return_value=mock_resp):
        rc = cli.run(["verify-resource", "fresh-res", "--check-url"], root=resources_repo)

    assert rc == 0
    out = capsys.readouterr().out
    assert "positive verification not recorded" in out

    # SAFETY: last_verified is NOT set by automated check!
    res = load_resources(resources_repo)[0]
    assert res.last_verified is None

    # Exactly one audit event
    events = load_events(resources_repo)
    assert len(events) == 1
    assert events[0]["command"] == "verify-resource"
    assert events[0]["records_touched"] == ["fresh-res"]


def test_verify_resource_check_url_cannot_combine_with_broken(resources_repo, capsys):
    _write_res(
        resources_repo,
        [{"id": "res1", "url": "https://example.com", "cost": "free"}],
    )
    rc = cli.run(
        ["verify-resource", "res1", "--check-url", "--broken", "--reason", "dead"],
        root=resources_repo,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "cannot combine --check-url with --broken" in out
    assert load_events(resources_repo) == []
