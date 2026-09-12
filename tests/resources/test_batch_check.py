"""Plain-mode coverage for the deep check interface (successor of `batch`).

The v1.8 `web_check.batch()` helper (sequential loop, no robots, no
delay, no retry) was removed in the issue #200 deepening: its behavior
is now the non-polite configuration of `check_urls()` (`respect_robots`
off, zero delay, a single attempt). These tests pin that configuration
through the `check_urls` seam with an injected fake opener.
"""

from __future__ import annotations

import urllib.error

from skilltrace.resources.polite_sweep import WebCheckResult, check_urls

from .test_polite_sweep import _MockResponse, _http_error, _opener_for, _plain_kwargs


def test_plain_mode_head_ok_pins_exact_fields_in_order():
    calls: list = []
    opener = _opener_for(
        targets={
            "https://example.com/a": _MockResponse(code=200, url="https://example.com/a"),
            "https://example.com/b": _MockResponse(code=200, url="https://example.com/b"),
        },
        calls=calls,
    )
    pairs = check_urls(
        ["https://example.com/a", "https://example.com/b"],
        opener=opener,
        **_plain_kwargs(user_agent="skilltrace/1.8 check-resources"),
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
    assert len(calls) == 2
    assert [c[2] for c in calls] == ["HEAD", "HEAD"]
    assert [c[3] for c in calls] == [
        "skilltrace/1.8 check-resources",
        "skilltrace/1.8 check-resources",
    ]


def test_plain_mode_429_reported_without_retry():
    calls: list = []
    opener = _opener_for(
        targets={
            "https://example.com/rate": _http_error(
                "https://example.com/rate", 429, "Too Many Requests"
            )
        },
        calls=calls,
    )
    pairs = check_urls(["https://example.com/rate"], opener=opener, **_plain_kwargs())
    entry, result = pairs[0]
    assert entry == "https://example.com/rate"
    assert result.ok is False
    assert result.status_code == 429
    assert "too many requests" in (result.reason or "").lower()
    assert len(calls) == 1


def test_plain_mode_empty_input_yields_empty_list():
    calls: list = []
    opener = _opener_for(calls=calls)
    assert check_urls([], opener=opener, **_plain_kwargs()) == []
    assert calls == []


def test_plain_mode_performs_zero_writes(tmp_path):
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
