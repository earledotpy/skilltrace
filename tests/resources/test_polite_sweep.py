"""Unit tests for the deep resource-check interface (issue #200).

`check_urls()` merges policy seeds with explicit overrides and runs the
polite sweep end-to-end. All tests exercise the sweep through the single
`check_urls` seam with an injected fake `opener` (plus an injected
`sleep` recorder) — never by poking internal robots/bucket machinery and
never by patching urllib.

Safety seam: performs zero writes and emits no event. Order is
preserved; empty input yields an empty list.
"""

from __future__ import annotations

import io
import urllib.error
import urllib.parse

from skilltrace.resources.polite_sweep import WebCheckResult, check_urls


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


def _opener_for(
    *,
    robots_bodies: dict | None = None,
    targets: dict | None = None,
    calls: list | None = None,
):
    """Build a fake opener routing robots fetches and target fetches.

    `robots_bodies` maps lowercase host -> body bytes (default: empty
    allow-all) or an exception to raise for that host's robots fetch.
    `targets` maps full URL -> response/exception or a list (queue) of
    them, consumed in order. `calls` records `(url, timeout, method,
    user_agent)` per invocation.
    """
    robots_bodies = robots_bodies or {}
    targets = targets or {}

    def opener(req, timeout=None, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else req.get_full_url()
        if calls is not None:
            calls.append((url, timeout, req.get_method(), req.headers.get("User-agent")))
        if url.endswith("/robots.txt"):
            host = (urllib.parse.urlparse(url).hostname or "").lower()
            spec = robots_bodies.get(host, b"")
            if isinstance(spec, BaseException):
                raise spec
            return _MockResponse(code=200, url=url, body=bytes(spec))
        spec = targets.get(url)
        if spec is None:
            return _MockResponse(code=200, url=url)
        if isinstance(spec, list):
            assert spec, f"fake opener queue exhausted for {url}"
            outcome = spec.pop(0)
        else:
            outcome = spec
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return opener


def _plain_kwargs(**overrides):
    base = {
        "timeout_seconds": 10,
        "follow_redirects": True,
        "method": "HEAD",
        "user_agent": "skilltrace/2.3 check-resources",
        "per_host_delay_seconds": 0.0,
        "respect_robots": False,
        "backoff_max_attempts": 1,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Robots layer through the check_urls seam
# ---------------------------------------------------------------------------


def test_robots_disallow_blocks_disallowed_path_without_fetching():
    calls: list = []
    opener = _opener_for(
        robots_bodies={"example.com": b"User-agent: *\nDisallow: /private/\n"},
        targets={"https://example.com/open": _MockResponse(code=200, url="https://example.com/open")},
        calls=calls,
    )
    pairs = check_urls(
        ["https://example.com/private/x", "https://example.com/open"],
        opener=opener,
        **_plain_kwargs(respect_robots=True),
    )
    fetched = [url for url, _, _, _ in calls if not url.endswith("/robots.txt")]
    assert fetched == ["https://example.com/open"]
    skipped_entry, skipped_result = pairs[0]
    assert skipped_entry == "https://example.com/private/x"
    assert skipped_result.ok is False
    assert skipped_result.status_code is None
    assert "robots" in (skipped_result.reason or "").lower()
    assert pairs[1][1].ok is True


def test_robots_fails_open_on_fetch_error():
    opener = _opener_for(
        robots_bodies={"example.com": urllib.error.URLError("Connection refused")},
        targets={"https://example.com/anything": _MockResponse(code=200, url="https://example.com/anything")},
    )
    pairs = check_urls(
        ["https://example.com/anything"], opener=opener, **_plain_kwargs(respect_robots=True)
    )
    assert pairs[0][1].ok is True


def test_robots_fails_open_on_404():
    opener = _opener_for(
        robots_bodies={
            "example.com": _http_error("https://example.com/robots.txt", 404, "Not Found")
        },
        targets={"https://example.com/anything": _MockResponse(code=200, url="https://example.com/anything")},
    )
    pairs = check_urls(
        ["https://example.com/anything"], opener=opener, **_plain_kwargs(respect_robots=True)
    )
    assert pairs[0][1].ok is True


def test_robots_one_fetch_per_host_not_per_url():
    calls: list = []
    opener = _opener_for(
        robots_bodies={"example.com": b"User-agent: *\nDisallow: /\n"},
        calls=calls,
    )
    pairs = check_urls(
        ["https://example.com/a", "https://example.com/b", "https://example.com/c"],
        opener=opener,
        **_plain_kwargs(respect_robots=True),
    )
    robots_calls = [url for url, _, _, _ in calls if url.endswith("/robots.txt")]
    assert robots_calls == ["https://example.com/robots.txt"]
    assert all(r.ok is False and "robots" in (r.reason or "").lower() for _, r in pairs)


def test_no_robots_skips_robots_layer():
    calls: list = []
    opener = _opener_for(
        targets={"https://example.com/a": _MockResponse(code=200, url="https://example.com/a")},
        calls=calls,
    )
    pairs = check_urls(["https://example.com/a"], opener=opener, **_plain_kwargs())
    assert calls == [
        ("https://example.com/a", 10, "HEAD", "skilltrace/2.3 check-resources")
    ]
    assert pairs[0][1].ok is True


# ---------------------------------------------------------------------------
# Rate limiting through the check_urls seam
# ---------------------------------------------------------------------------


def test_sleeps_per_host_delay_between_same_host_requests():
    sleeps: list[float] = []
    opener = _opener_for()
    check_urls(
        ["https://example.com/a", "https://example.com/b", "https://other.org/c"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(respect_robots=False, per_host_delay_seconds=1.5),
    )
    assert sleeps == [0.0, 1.5, 0.0]


def test_zero_delay_never_sleeps():
    sleeps: list[float] = []
    opener = _opener_for()
    check_urls(
        ["https://example.com/a", "https://example.com/b"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(),
    )
    assert sleeps == []


# ---------------------------------------------------------------------------
# 429 backoff through the check_urls seam
# ---------------------------------------------------------------------------


def test_429_backs_off_and_retries_then_reports_result():
    sleeps: list[float] = []
    opener = _opener_for(
        targets={
            "https://example.com/rate": [
                _http_error("https://example.com/rate", 429, "Too Many Requests"),
                _http_error("https://example.com/rate", 429, "Too Many Requests"),
                _http_error("https://example.com/rate", 429, "Too Many Requests"),
            ]
        },
    )
    pairs = check_urls(
        ["https://example.com/rate"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(backoff_max_attempts=3),
    )
    entry, result = pairs[0]
    assert entry == "https://example.com/rate"
    assert result.ok is False
    assert result.status_code == 429
    assert "too many requests" in (result.reason or "").lower()
    assert sleeps == [1.0, 2.0]


def test_429_retry_after_header_honored():
    sleeps: list[float] = []
    opener = _opener_for(
        targets={
            "https://example.com/rate": [
                _http_error(
                    "https://example.com/rate", 429, "Too Many Requests", {"Retry-After": "7"}
                ),
                _MockResponse(code=200, url="https://example.com/rate"),
            ]
        },
    )
    pairs = check_urls(
        ["https://example.com/rate"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(backoff_max_attempts=3),
    )
    assert pairs[0][1].ok is True
    assert sleeps == [7.0]


def test_explicit_single_attempt_never_retries_429():
    sleeps: list[float] = []
    calls: list = []
    opener = _opener_for(
        targets={
            "https://example.com/rate": [
                _http_error("https://example.com/rate", 429, "Too Many Requests"),
                _MockResponse(code=200, url="https://example.com/rate"),
            ]
        },
        calls=calls,
    )
    pairs = check_urls(
        ["https://example.com/rate"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(backoff_max_attempts=1),
    )
    assert pairs[0][1].status_code == 429
    assert sleeps == []
    assert len(calls) == 1


def test_404_is_never_retried_even_with_backoff_enabled():
    sleeps: list[float] = []
    calls: list = []
    opener = _opener_for(
        targets={
            "https://example.com/gone": [
                _http_error("https://example.com/gone", 404, "Not Found"),
                _MockResponse(code=200, url="https://example.com/gone"),
            ]
        },
        calls=calls,
    )
    pairs = check_urls(
        ["https://example.com/gone"],
        opener=opener,
        sleep=sleeps.append,
        **_plain_kwargs(backoff_max_attempts=3),
    )
    assert pairs[0][1].status_code == 404
    assert sleeps == []
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# Result shape, validation, and safety through the check_urls seam
# ---------------------------------------------------------------------------


def test_ok_sweep_checks_exact_fields_in_order():
    opener = _opener_for(
        targets={
            "https://example.com/a": _MockResponse(code=200, url="https://example.com/a"),
            "https://docs.example.org/b": _MockResponse(code=200, url="https://docs.example.org/b"),
        }
    )
    pairs = check_urls(
        ["https://example.com/a", "https://docs.example.org/b"],
        opener=opener,
        **_plain_kwargs(),
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


def test_mixed_ok_and_failed_preserves_order():
    opener = _opener_for(
        targets={
            "https://example.com/good": _MockResponse(code=200, url="https://example.com/good"),
            "https://example.com/missing": _http_error(
                "https://example.com/missing", 404, "Not Found"
            ),
            "https://example.com/down": urllib.error.URLError("Connection refused"),
            "https://example.com/slow": TimeoutError("timed out"),
        }
    )
    pairs = check_urls(
        [
            "https://example.com/good",
            "https://example.com/missing",
            "https://example.com/down",
            "https://example.com/slow",
        ],
        opener=opener,
        **_plain_kwargs(),
    )
    assert pairs == [
        (
            "https://example.com/good",
            WebCheckResult(
                ok=True, status_code=200, final_url="https://example.com/good", reason=None
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
                ok=False, status_code=None, final_url=None, reason="Connection refused"
            ),
        ),
        (
            "https://example.com/slow",
            WebCheckResult(
                ok=False, status_code=None, final_url=None, reason="timeout after 10s"
            ),
        ),
    ]


def test_forwards_method_user_agent_and_timeout_per_entry():
    calls: list = []
    opener = _opener_for(calls=calls)
    pairs = check_urls(
        ["http://example.com/source"],
        opener=opener,
        **_plain_kwargs(timeout_seconds=7, method="GET", user_agent="CustomAgent/2.0"),
    )
    assert pairs[0][1].ok is True
    assert calls[0] == ("http://example.com/source", 7, "GET", "CustomAgent/2.0")


def test_invalid_arguments_raise_before_any_fetch():
    calls: list = []
    opener = _opener_for(calls=calls)
    import pytest

    with pytest.raises(ValueError, match="timeout_seconds"):
        check_urls(["https://example.com"], opener=opener, **_plain_kwargs(timeout_seconds=0))
    with pytest.raises(ValueError, match="backoff-attempts"):
        check_urls(
            ["https://example.com"], opener=opener, **_plain_kwargs(backoff_max_attempts=11)
        )
    with pytest.raises(ValueError, match="per-host-delay"):
        check_urls(
            ["https://example.com"], opener=opener, **_plain_kwargs(per_host_delay_seconds=-1)
        )
    assert calls == []


def test_empty_input_yields_empty_list():
    calls: list = []
    opener = _opener_for(calls=calls)
    assert check_urls([], opener=opener, **_plain_kwargs()) == []
    assert calls == []


def test_performs_zero_writes(tmp_path):
    """The sweep never writes: no stored verification state touched."""
    sentinel = tmp_path / "resources.yaml"
    sentinel.write_text("resources: []", encoding="utf-8")
    before = sentinel.stat().st_mtime_ns
    opener = _opener_for(
        targets={"https://example.com": _MockResponse(code=200, url="https://example.com")}
    )
    pairs = check_urls(["https://example.com"], opener=opener, **_plain_kwargs())
    assert pairs[0][1].ok is True
    assert sentinel.stat().st_mtime_ns == before
    assert sentinel.read_text(encoding="utf-8") == "resources: []"
