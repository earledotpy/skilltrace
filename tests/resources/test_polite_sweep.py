"""Unit tests for the polite sweep helper (v2.3 spec §2, §6).

`polite_batch()` reuses the v1.7 `check_url` seam with three hygiene layers,
all offline-testable with mocked urllib and an injected sleeper:

- RobotsCache: one fetch per host, respect Disallow, fail-open on fetch error
- PerHostBucket: monotonic spacing of requests to the same host (host-keyed)
- 429 backoff: bounded exponential backoff with Retry-After honor

Safety seam (carried from v1.8): performs zero writes (never calls
`record_verification`, never sets `last_verified`, never clears `broken`)
and emits no event. Order is preserved; empty input yields an empty list.
"""

from __future__ import annotations

import io
import urllib.error
from unittest.mock import patch

from skilltrace.resources.polite_sweep import (
    PerHostBucket,
    RobotsCache,
    WebCheckResult,
    polite_batch,
)


class _MockResponse:
    def __init__(self, code: int = 200, url: str = "https://example.com", body: bytes = b"") -> None:
        self.code = code
        self.status = code
        self.url = url
        self._body = body

    def getcode(self) -> int:
        return self.code

    def geturl(self) -> str:
        return self.url

    def read(self, n: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def _http_error(url: str, code: int, msg: str, headers: dict | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url=url, code=code, msg=msg, hdrs=headers or {}, fp=io.BytesIO()
    )


# ---------------------------------------------------------------------------
# RobotsCache
# ---------------------------------------------------------------------------


def test_robots_cache_disallow_blocks_disallowed_path():
    robots_body = b"User-agent: *\nDisallow: /private/\n"
    with patch(
        "urllib.request.OpenerDirector.open",
        return_value=_MockResponse(code=200, url="https://example.com/robots.txt", body=robots_body),
    ) as mock_open:
        cache = RobotsCache(user_agent="SkillTrace/2.3")
        assert cache.allowed("https://example.com/private/lesson") is False
        assert cache.allowed("https://example.com/open/lesson") is True
    # One fetch per host, not per path.
    assert mock_open.call_count == 1


def test_robots_cache_allows_when_no_robots():
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=_http_error("https://example.com/robots.txt", 404, "Not Found"),
    ):
        cache = RobotsCache(user_agent="SkillTrace/2.3")
        assert cache.allowed("https://example.com/anything") is True


def test_robots_cache_fails_open_on_fetch_error():
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        cache = RobotsCache(user_agent="SkillTrace/2.3")
        assert cache.allowed("https://example.com/anything") is True


def test_robots_cache_one_fetch_per_host_not_per_url():
    robots_body = b"User-agent: *\nDisallow: /\n"
    with patch(
        "urllib.request.OpenerDirector.open",
        return_value=_MockResponse(code=200, url="https://example.com/robots.txt", body=robots_body),
    ) as mock_open:
        cache = RobotsCache(user_agent="SkillTrace/2.3")
        cache.allowed("https://example.com/a")
        cache.allowed("https://example.com/b")
        cache.allowed("https://example.com/c")
    assert mock_open.call_count == 1


def test_robots_cache_never_writes(tmp_path):
    sentinel = tmp_path / "resources.yaml"
    sentinel.write_text("resources: []", encoding="utf-8")
    before = sentinel.stat().st_mtime_ns
    with patch(
        "urllib.request.OpenerDirector.open",
        return_value=_MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
    ):
        RobotsCache(user_agent="SkillTrace/2.3").allowed("https://example.com/x")
    assert sentinel.stat().st_mtime_ns == before


# ---------------------------------------------------------------------------
# PerHostBucket
# ---------------------------------------------------------------------------


def test_bucket_first_request_no_wait_and_future_requests_spaced():
    waits: list[float] = []
    bucket = PerHostBucket(per_host_delay_seconds=2.0, on_sleep=waits.append)
    host = bucket.host_of("https://example.com/a")
    assert host == "example.com"
    assert bucket.reserve(host) == 0.0
    assert bucket.reserve(host) == 2.0
    assert bucket.reserve(host) == 2.0
    assert waits == [0.0, 2.0, 2.0]  # on_sleep observes every reservation


def test_bucket_delays_are_per_host():
    bucket = PerHostBucket(per_host_delay_seconds=1.0, on_sleep=lambda _s: None)
    assert bucket.reserve("example.com") == 0.0
    assert bucket.reserve("other.org") == 0.0
    assert bucket.reserve("example.com") == 1.0
    assert bucket.reserve("other.org") == 1.0


def test_bucket_zero_delay_is_pass_through():
    bucket = PerHostBucket(per_host_delay_seconds=0.0, on_sleep=lambda _s: None)
    assert bucket.reserve("example.com") == 0.0
    assert bucket.reserve("example.com") == 0.0


def test_bucket_host_of_normalizes_scheme_port_and_case():
    bucket = PerHostBucket(per_host_delay_seconds=1.0, on_sleep=lambda _s: None)
    assert bucket.host_of("http://EXAMPLE.com:80/x") == "example.com"
    assert bucket.host_of("https://example.com/y") == "example.com"

# ---------------------------------------------------------------------------
# polite_batch
# ---------------------------------------------------------------------------


def test_polite_batch_ok_sweep_checks_exact_fields_in_order():
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _MockResponse(code=200, url="https://example.com/a"),
        _MockResponse(code=200, url="https://docs.example.org/robots.txt", body=b""),
        _MockResponse(code=200, url="https://docs.example.org/b"),
    ]
    with patch("urllib.request.OpenerDirector.open", side_effect=responses):
        pairs = polite_batch(
            ["https://example.com/a", "https://docs.example.org/b"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
        )
    assert pairs == [
        (
            "https://example.com/a",
            WebCheckResult(ok=True, status_code=200, final_url="https://example.com/a", reason=None),
        ),
        (
            "https://docs.example.org/b",
            WebCheckResult(ok=True, status_code=200, final_url="https://docs.example.org/b", reason=None),
        ),
    ]


def test_polite_batch_respects_robots_disallow_without_fetching():
    robots_body = b"User-agent: *\nDisallow: /private/\n"
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=robots_body),
        _MockResponse(code=200, url="https://example.com/open"),
    ]
    with patch("urllib.request.OpenerDirector.open", side_effect=responses) as mock_open:
        pairs = polite_batch(
            ["https://example.com/private/x", "https://example.com/open"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
        )
    # The disallowed URL is never fetched (only robots.txt + the open URL ran).
    assert mock_open.call_count == 2
    skipped_entry, skipped_result = pairs[0]
    assert skipped_entry == "https://example.com/private/x"
    assert skipped_result.ok is False
    assert skipped_result.status_code is None
    assert "robots" in (skipped_result.reason or "").lower()
    # The allowed URL is checked normally.
    assert pairs[1][1].ok is True


def test_polite_batch_no_robots_skips_robots_layer():
    responses = [_MockResponse(code=200, url="https://example.com/a")]
    with patch("urllib.request.OpenerDirector.open", side_effect=responses) as mock_open:
        pairs = polite_batch(
            ["https://example.com/a"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
            respect_robots=False,
        )
    assert mock_open.call_count == 1  # only the target URL, no robots fetch
    assert pairs[0][1].ok is True

def test_polite_batch_sleeps_per_host_delay_between_same_host_requests():
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _MockResponse(code=200, url="https://other.org/robots.txt", body=b""),
        _MockResponse(code=200, url="https://example.com/a"),
        _MockResponse(code=200, url="https://example.com/b"),
        _MockResponse(code=200, url="https://other.org/c"),
    ]
    sleeps: list[float] = []
    with patch("urllib.request.OpenerDirector.open", side_effect=responses):
        polite_batch(
            ["https://example.com/a", "https://example.com/b", "https://other.org/c"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=1.5, sleep=sleeps.append,
            
        )
    # First same-host request waits 0 (robots fetch does not enter the bucket);
    # second same-host waits 1.5; the other-host first request waits 0.
    assert sleeps == [0.0, 1.5, 0.0]


def test_polite_batch_429_backs_off_and_retries_then_reports_broken():
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _http_error("https://example.com/rate", 429, "Too Many Requests"),
        _http_error("https://example.com/rate", 429, "Too Many Requests"),
        _http_error("https://example.com/rate", 429, "Too Many Requests"),
    ]
    sleeps: list[float] = []
    with patch("urllib.request.OpenerDirector.open", side_effect=responses) as mock_open:
        pairs = polite_batch(
            ["https://example.com/rate"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
            backoff_max_attempts=3,
            sleep=sleeps.append,
            
        )
    # Three attempts (1 initial + 2 backoff retries), then the 429 is the
    # resource's BROKEN verdict via reason — the v1.8 shape.
    target_fetches = [
        c
        for c in mock_open.call_args_list
        if getattr(c[0][0], "full_url", c[0][0] if isinstance(c[0][0], str) else "") == "https://example.com/rate"
    ]
    assert len(target_fetches) == 3
    entry, result = pairs[0]
    assert entry == "https://example.com/rate"
    assert result.ok is False
    assert result.status_code == 429
    assert "too many requests" in (result.reason or "").lower()
    # Exponential backoff sleeps after attempt 1 and 2 (not after the final attempt).
    assert sleeps == [1.0, 2.0]


def test_polite_batch_429_retry_after_header_honored():
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _http_error(
            "https://example.com/rate", 429, "Too Many Requests", {"Retry-After": "7"}
        ),
        _MockResponse(code=200, url="https://example.com/rate"),
    ]
    sleeps: list[float] = []
    with patch("urllib.request.OpenerDirector.open", side_effect=responses):
        pairs = polite_batch(
            ["https://example.com/rate"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
            backoff_max_attempts=3,
            sleep=sleeps.append,
            
        )
    assert pairs[0][1].ok is True
    assert sleeps == [7.0]  # Retry-After beats the exponential default


def test_polite_batch_default_attempts_one_never_retries():
    """With the v1.8-equivalent default (attempts=1), a 429 is never retried."""
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _http_error("https://example.com/rate", 429, "Too Many Requests"),
    ]
    sleeps: list[float] = []
    with patch("urllib.request.OpenerDirector.open", side_effect=responses) as mock_open:
        pairs = polite_batch(
            ["https://example.com/rate"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
            
        )
    target_fetches = [
        c
        for c in mock_open.call_args_list
        if getattr(c[0][0], "full_url", c[0][0] if isinstance(c[0][0], str) else "") == "https://example.com/rate"
    ]
    assert len(target_fetches) == 1
    assert pairs[0][1].status_code == 429
    assert sleeps == []


def test_polite_batch_404_is_never_retried_even_with_backoff_enabled():
    """Backoff is a 429 courtesy only — other failures are never retried."""
    responses = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _http_error("https://example.com/gone", 404, "Not Found"),
    ]
    sleeps: list[float] = []
    with patch("urllib.request.OpenerDirector.open", side_effect=responses) as mock_open:
        pairs = polite_batch(
            ["https://example.com/gone"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
            backoff_max_attempts=3,
            sleep=sleeps.append,
            
        )
    target_fetches = [
        c
        for c in mock_open.call_args_list
        if getattr(c[0][0], "full_url", c[0][0] if isinstance(c[0][0], str) else "") == "https://example.com/gone"
    ]
    assert len(target_fetches) == 1
    assert pairs[0][1].status_code == 404
    assert sleeps == []


def test_polite_batch_preserves_order_and_checks_exact_fields():
    robots = [
        _MockResponse(code=200, url="https://example.com/robots.txt", body=b""),
        _MockResponse(code=200, url="https://down.example.net/robots.txt", body=b""),
    ]
    responses = [
        _MockResponse(code=200, url="https://example.com/good"),
        _http_error("https://down.example.net/missing", 404, "Not Found"),
    ]
    with patch("urllib.request.OpenerDirector.open", side_effect=robots + responses):
        pairs = polite_batch(
            ["https://example.com/good", "https://down.example.net/missing"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
        )
    assert [entry for entry, _ in pairs] == [
        "https://example.com/good",
        "https://down.example.net/missing",
    ]
    assert pairs[0][1].ok is True
    assert pairs[1][1] == WebCheckResult(
        ok=False, status_code=404, final_url="https://down.example.net/missing", reason="not found"
    )


def test_polite_batch_empty_input_yields_empty_list():
    with patch("urllib.request.OpenerDirector.open") as mock_open:
        assert polite_batch(
            [],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
        ) == []
    assert mock_open.call_count == 0


def test_polite_batch_performs_zero_writes(tmp_path):
    """The polite sweep never writes: no record_verification call, no file change."""
    sentinel = tmp_path / "resources.yaml"
    sentinel.write_text("resources: []", encoding="utf-8")
    before = sentinel.stat().st_mtime_ns
    robots = _MockResponse(code=200, url="https://example.com/robots.txt", body=b"")
    resp = _MockResponse(code=200, url="https://example.com")
    with (
        patch("urllib.request.OpenerDirector.open", side_effect=[robots, resp]),
        patch("skilltrace.resources.verification.record_verification") as mock_record,
    ):
        pairs = polite_batch(
            ["https://example.com"],
            timeout_seconds=10,
            follow_redirects=True,
            method="HEAD",
            user_agent="skilltrace/2.3 check-resources",
            per_host_delay_seconds=0.0,
        )
    assert pairs[0][1].ok is True
    assert mock_record.call_count == 0
    assert sentinel.stat().st_mtime_ns == before
    assert sentinel.read_text(encoding="utf-8") == "resources: []"

