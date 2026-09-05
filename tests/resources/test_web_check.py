"""Unit tests for the standard-library URL reachability checker (v1.7 spec §2, §8).

Asserts exact result fields for:
- HEAD and GET methods
- Redirects (followed vs disabled)
- HTTP failures (e.g. 404, 500)
- Transport and timeout failures
- User-Agent transmission
- Invalid arguments raising ValueError
- Read-only behavior (no files modified, no registry writes)
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from skilltrace.resources.web_check import WebCheckResult, check_url


class _MockResponse:
    """Mock HTTP response returned by urllib.request."""

    def __init__(self, code: int = 200, url: str = "https://example.com", headers: dict | None = None) -> None:
        self.code = code
        self.status = code
        self.url = url
        self.headers = headers or {}

    def getcode(self) -> int:
        return self.code

    def geturl(self) -> str:
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestWebCheckUnit:
    def test_successful_head_request(self):
        mock_resp = _MockResponse(code=200, url="https://example.com/page")
        with patch("urllib.request.OpenerDirector.open", return_value=mock_resp) as mock_open:
            result = check_url(
                "https://example.com/page",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result == WebCheckResult(
                ok=True,
                status_code=200,
                final_url="https://example.com/page",
                reason=None,
            )
            assert mock_open.called
            req = mock_open.call_args[0][0]
            assert req.get_method() == "HEAD"
            assert req.headers["User-agent"] == "SkillTrace/1.7"

    def test_successful_get_request(self):
        mock_resp = _MockResponse(code=200, url="https://example.com/page")
        with patch("urllib.request.OpenerDirector.open", return_value=mock_resp) as mock_open:
            result = check_url(
                "https://example.com/page",
                timeout_seconds=5,
                follow_redirects=True,
                method="GET",
                user_agent="CustomAgent/1.0",
            )
            assert result == WebCheckResult(
                ok=True,
                status_code=200,
                final_url="https://example.com/page",
                reason=None,
            )
            req = mock_open.call_args[0][0]
            assert req.get_method() == "GET"
            assert req.headers["User-agent"] == "CustomAgent/1.0"

    def test_redirect_followed(self):
        mock_resp = _MockResponse(code=200, url="https://example.com/destination")
        with patch("urllib.request.OpenerDirector.open", return_value=mock_resp):
            result = check_url(
                "http://example.com/source",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result == WebCheckResult(
                ok=True,
                status_code=200,
                final_url="https://example.com/destination",
                reason=None,
            )

    def test_redirect_not_followed(self):
        # When follow_redirects=False, an HTTP redirect raises HTTPError from urllib
        http_err = urllib.error.HTTPError(
            url="http://example.com/source",
            code=301,
            msg="Moved Permanently",
            hdrs={},
            fp=io.BytesIO(),
        )
        with patch("urllib.request.OpenerDirector.open", side_effect=http_err):
            result = check_url(
                "http://example.com/source",
                timeout_seconds=10,
                follow_redirects=False,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result.ok is False
            assert result.status_code == 301
            assert result.final_url == "http://example.com/source"
            assert "moved permanently" in (result.reason or "").lower()

    def test_http_404_failure(self):
        http_err = urllib.error.HTTPError(
            url="https://example.com/missing",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(),
        )
        with patch("urllib.request.OpenerDirector.open", side_effect=http_err):
            result = check_url(
                "https://example.com/missing",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result == WebCheckResult(
                ok=False,
                status_code=404,
                final_url="https://example.com/missing",
                reason="not found",
            )

    def test_http_500_failure(self):
        http_err = urllib.error.HTTPError(
            url="https://example.com/error",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=io.BytesIO(),
        )
        with patch("urllib.request.OpenerDirector.open", side_effect=http_err):
            result = check_url(
                "https://example.com/error",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result.ok is False
            assert result.status_code == 500
            assert "internal server error" in (result.reason or "").lower()

    def test_timeout_failure(self):
        timeout_err = TimeoutError("timed out")
        with patch("urllib.request.OpenerDirector.open", side_effect=timeout_err):
            result = check_url(
                "https://example.com/slow",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result == WebCheckResult(
                ok=False,
                status_code=None,
                final_url=None,
                reason="timeout after 10s",
            )

    def test_transport_failure(self):
        url_err = urllib.error.URLError("Connection refused")
        with patch("urllib.request.OpenerDirector.open", side_effect=url_err):
            result = check_url(
                "https://example.com/down",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )
            assert result.ok is False
            assert result.status_code is None
            assert result.final_url is None
            assert "connection refused" in (result.reason or "").lower()

    @pytest.mark.parametrize(
        "kwargs,match",
        [
            ({"url": ""}, "URL"),
            ({"url": "ftp://example.com"}, "scheme"),
            ({"timeout_seconds": 0}, "timeout_seconds"),
            ({"timeout_seconds": 121}, "timeout_seconds"),
            ({"timeout_seconds": True}, "timeout_seconds"),
            ({"follow_redirects": "true"}, "follow_redirects"),
            ({"method": "POST"}, "method"),
            ({"user_agent": ""}, "user_agent"),
            ({"user_agent": "   "}, "user_agent"),
        ],
    )
    def test_invalid_arguments_raise_value_error(self, kwargs, match):
        base_args = {
            "url": "https://example.com",
            "timeout_seconds": 10,
            "follow_redirects": True,
            "method": "HEAD",
            "user_agent": "SkillTrace/1.7",
        }
        base_args.update(kwargs)
        with pytest.raises(ValueError, match=match):
            check_url(**base_args)

    def test_web_checker_performs_no_writes(self, tmp_path):
        """Web checker performs no filesystem writes or registry modifications."""
        dummy_file = tmp_path / "resources.yaml"
        dummy_file.write_text("resources: []", encoding="utf-8")
        before_mtime = dummy_file.stat().st_mtime_ns

        mock_resp = _MockResponse(code=200, url="https://example.com")
        with patch("urllib.request.OpenerDirector.open", return_value=mock_resp):
            check_url(
                "https://example.com",
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="SkillTrace/1.7",
            )

        assert dummy_file.stat().st_mtime_ns == before_mtime
        assert dummy_file.read_text(encoding="utf-8") == "resources: []"
