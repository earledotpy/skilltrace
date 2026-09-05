"""Unit tests for the batch sweep helper (v1.8 spec §4.1, §6).

`batch()` is a sequential loop over `check_url` (no token bucket, no
`robots.txt`, no retry loop) in the existing `web_check.py` seam. Exact
structured assertions with mocked urllib:

- per-entry `(entry, WebCheckResult)` fields for HEAD/GET, redirects,
  HTTP/transport/timeout failures
- 429 reported as BROKEN via `reason`, never retried (exactly one call)
- User-Agent / method / timeout / follow_redirects forwarded per entry
- sequential order preserved over N entries
- empty input yields an empty list
- the no-write seam: never calls `record_verification`, never touches
  `last_verified`/`broken` state
"""

from __future__ import annotations

import io
import urllib.error
from unittest.mock import patch

from skilltrace.resources.web_check import WebCheckResult, batch


class _MockResponse:
    """Mock HTTP response returned by urllib.request."""

    def __init__(self, code: int = 200, url: str = "https://example.com") -> None:
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


def _http_error(url: str, code: int, msg: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url=url, code=code, msg=msg, hdrs={}, fp=io.BytesIO()
    )


def test_batch_head_ok_pins_exact_fields_in_order():
    responses = [
        _MockResponse(code=200, url="https://example.com/a"),
        _MockResponse(code=200, url="https://example.com/b"),
    ]
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=responses
    ) as mock_open:
        pairs = batch(
            ["https://example.com/a", "https://example.com/b"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/1.8 check-resources",
        )
    assert pairs == [
        (
            "https://example.com/a",
            WebCheckResult(
                ok=True, status_code=200, final_url="https://example.com/a", reason=None
            ),
        ),
        (
            "https://example.com/b",
            WebCheckResult(
                ok=True, status_code=200, final_url="https://example.com/b", reason=None
            ),
        ),
    ]
    assert mock_open.call_count == 2
    methods = [call[0][0].get_method() for call in mock_open.call_args_list]
    assert methods == ["HEAD", "HEAD"]
    agents = [call[0][0].headers["User-agent"] for call in mock_open.call_args_list]
    assert agents == [
        "skilltrace/1.8 check-resources",
        "skilltrace/1.8 check-resources",
    ]


def test_batch_get_forwards_method_and_redirect_target():
    responses = [_MockResponse(code=200, url="https://example.com/destination")]
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=responses
    ) as mock_open:
        pairs = batch(
            ["http://example.com/source"],
            timeout_seconds=7,
            follow_redirects=True,
            method="GET",
            user_agent="CustomAgent/2.0",
        )
    assert pairs == [
        (
            "http://example.com/source",
            WebCheckResult(
                ok=True,
                status_code=200,
                final_url="https://example.com/destination",
                reason=None,
            ),
        )
    ]
    req = mock_open.call_args[0][0]
    assert req.get_method() == "GET"
    assert req.headers["User-agent"] == "CustomAgent/2.0"
    assert mock_open.call_args[1]["timeout"] == 7


def test_batch_mixed_ok_and_broken_preserves_order():
    side_effects = [
        _MockResponse(code=200, url="https://example.com/good"),
        _http_error("https://example.com/missing", 404, "Not Found"),
        urllib.error.URLError("Connection refused"),
        TimeoutError("timed out"),
    ]
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=side_effects
    ) as mock_open:
        pairs = batch(
            [
                "https://example.com/good",
                "https://example.com/missing",
                "https://example.com/down",
                "https://example.com/slow",
            ],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/1.8 check-resources",
        )
    assert pairs == [
        (
            "https://example.com/good",
            WebCheckResult(
                ok=True,
                status_code=200,
                final_url="https://example.com/good",
                reason=None,
            ),
        ),
        (
            "https://example.com/missing",
            WebCheckResult(
                ok=False,
                status_code=404,
                final_url="https://example.com/missing",
                reason="not found",
            ),
        ),
        (
            "https://example.com/down",
            WebCheckResult(
                ok=False,
                status_code=None,
                final_url=None,
                reason="Connection refused",
            ),
        ),
        (
            "https://example.com/slow",
            WebCheckResult(
                ok=False, status_code=None, final_url=None, reason="timeout after 10s"
            ),
        ),
    ]
    # Sequential: one opener call per entry, in input order.
    assert mock_open.call_count == 4
    requested = [call[0][0].full_url for call in mock_open.call_args_list]
    assert requested == [
        "https://example.com/good",
        "https://example.com/missing",
        "https://example.com/down",
        "https://example.com/slow",
    ]


def test_batch_429_reported_as_broken_with_no_retry():
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=_http_error("https://example.com/rate", 429, "Too Many Requests"),
    ) as mock_open:
        pairs = batch(
            ["https://example.com/rate"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/1.8 check-resources",
        )
    assert len(pairs) == 1
    entry, result = pairs[0]
    assert entry == "https://example.com/rate"
    assert result.ok is False
    assert result.status_code == 429
    assert "too many requests" in (result.reason or "").lower()
    # No retry loop, no backoff: exactly one attempt.
    assert mock_open.call_count == 1


def test_batch_empty_input_yields_empty_list():
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        assert (
            batch(
                [],
                timeout_seconds=10,
                follow_redirects=True,
                method="HEAD",
                user_agent="skilltrace/1.8 check-resources",
            )
            == []
        )
    assert mock_open.call_count == 0


def test_batch_performs_zero_writes(tmp_path):
    """The batch sweep never writes: no record_verification call, no file change."""
    sentinel = tmp_path / "resources.yaml"
    sentinel.write_text("resources: []", encoding="utf-8")
    before = sentinel.stat().st_mtime_ns

    mock_resp = _MockResponse(code=200, url="https://example.com")
    with (
        patch("urllib.request.OpenerDirector.open", return_value=mock_resp),
        patch(
            "skilltrace.resources.verification.record_verification"
        ) as mock_record,
    ):
        pairs = batch(
            ["https://example.com"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/1.8 check-resources",
        )

    assert pairs[0][1].ok is True
    assert mock_record.call_count == 0
    assert sentinel.stat().st_mtime_ns == before
    assert sentinel.read_text(encoding="utf-8") == "resources: []"
