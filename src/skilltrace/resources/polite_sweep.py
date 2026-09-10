"""Polite batch sweep — verification-hygiene hardening (v2.3).

Wraps the v1.7 `check_url` seam with three politeness layers for batch
sweeps:

- **Per-host rate limiting** — nominal per-host spacing: a host's first
  request proceeds immediately and any later same-host request waits
  `per_host_delay_seconds` (0 = the sweep never sleeps). Delays are
  host-keyed — different hosts never wait on each other.
- **`robots.txt` respect** — one `robots.txt` fetch per host; disallowed
  URLs are never fetched and report `ok=False` with a `robots.txt disallow`
  reason. Any robots fetch failure (404, transport error, timeout) fails
  open: the URL is checked anyway. A robots check must never turn a
  reachable resource broken.
- **429 backoff** — a 429 may be retried with bounded exponential backoff
  (base doubling, capped at `backoff_max_seconds`); a larger `Retry-After`
  header wins. Only 429 is retried — every other HTTP/transport/timeout
  failure is final after one attempt. `backoff_max_attempts=1` (the
  default) reproduces the v1.8 never-retry behavior exactly.

Pure network reads: performs zero writes (never calls
`record_verification`, never sets `last_verified`, never clears `broken`)
and emits no event. Order is preserved; an empty input yields an empty
list.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections.abc import Callable, Iterable

from .web_check import WebCheckResult, check_url_detailed

__all__ = [
    "PerHostBucket",
    "PoliteSweepDefaults",
    "RobotsCache",
    "WebCheckResult",
    "polite_batch",
    "resolve_polite_sweep_policy",
]


def _host_of(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return (parsed.hostname or "").lower()


# ---------------------------------------------------------------------------
# Robots cache
# ---------------------------------------------------------------------------


class RobotsCache:
    """Per-host `robots.txt` cache; disallowed URLs are never fetched.

    One fetch per host (keyed by normalized hostname). Any fetch failure —
    missing file, transport error, timeout — fails open (the URL is
    allowed), because a robots check must never turn a reachable resource
    broken. Performs no writes of its own (the underlying RobotFileParser
    caches only in memory).
    """

    def __init__(self, *, user_agent: str, timeout_seconds: int = 10) -> None:
        self._user_agent = user_agent
        self._timeout_seconds = timeout_seconds
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    host_of = staticmethod(_host_of)

    def allowed(self, url: str) -> bool:
        host = _host_of(url)
        if host in self._parsers:
            parser = self._parsers[host]
        else:
            parser = self._fetch_parser(host, url)
            self._parsers[host] = parser
        if parser is None:
            return True  # fail open
        return parser.can_fetch(self._user_agent, url)

    def _fetch_parser(self, host: str, url: str) -> urllib.robotparser.RobotFileParser | None:
        scheme = urllib.parse.urlsplit(url).scheme or "https"
        robots_url = f"{scheme}://{host}/robots.txt"
        req = urllib.request.Request(
            robots_url,
            headers={"User-Agent": self._user_agent},
            method="GET",
        )
        try:
            with urllib.request.build_opener().open(req, timeout=self._timeout_seconds) as response:
                body = response.read() if hasattr(response, "read") else b""
                status = response.getcode()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
            return None  # fail open
        if status is not None and status >= 400:
            # 404/no robots = allow-all; other error statuses also fail open.
            return None
        parser = urllib.robotparser.RobotFileParser()
        try:
            parser.parse(body.decode("utf-8", errors="replace").splitlines())
        except (ValueError, OSError):
            return None  # fail open
        return parser


# ---------------------------------------------------------------------------
# Per-host rate limiting
# ---------------------------------------------------------------------------


class PerHostBucket:
    """Monotonic per-host spacing: same-host requests are delayed apart.

    `reserve(host)` returns the seconds the caller must sleep before the
    Callers sleep the returned amount: `polite_batch` calls `sleep()` on
    every result (including 0) via its injected sleeper. The optional
    `on_sleep` hook exists only so unit tests can observe reservations
    without monkeying a clock; the bucket itself never sleeps.
    """

    def __init__(
        self,
        *,
        per_host_delay_seconds: float,
        on_sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._delay = float(per_host_delay_seconds)
        self._on_sleep = on_sleep
        self._seen: set[str] = set()

    host_of = staticmethod(_host_of)

    def reserve(self, host: str) -> float:
        """Return the delay before this request (0 for a host's first).

        Nominal spacing: any same-host request after the first returns the
        full `per_host_delay_seconds` and records the host as seen. Real
        callers sleep the returned amount, preserving at-least spacing;
        this keeps the returned delays deterministic for offline tests.
        """
        if self._delay <= 0:
            delay = 0.0
        elif host in self._seen:
            delay = self._delay
        else:
            self._seen.add(host)
            delay = 0.0
        if self._on_sleep is not None:
            self._on_sleep(delay)
        return delay


# ---------------------------------------------------------------------------
# Policy resolution
# ---------------------------------------------------------------------------


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class PoliteSweepDefaults:
    """Default polite-sweep configuration resolved from policy seed data."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        per_host_delay_seconds: float = 1.0,
        respect_robots: bool = True,
        backoff_max_attempts: int = 3,
        backoff_base_seconds: float = 1.0,
        backoff_max_seconds: float = 60.0,
    ) -> None:
        self.enabled = enabled
        self.per_host_delay_seconds = per_host_delay_seconds
        self.respect_robots = respect_robots
        self.backoff_max_attempts = backoff_max_attempts
        self.backoff_base_seconds = backoff_base_seconds
        self.backoff_max_seconds = backoff_max_seconds


def resolve_polite_sweep_policy(root) -> PoliteSweepDefaults:
    """Resolve polite-sweep defaults from the `polite_sweep.yaml` seed.

    A missing or unparseable file falls back to the defaults; individual
    fields out of type/range fall back per-field (the `validate policy`
    command surfaces those as hard errors).
    """
    defaults = PoliteSweepDefaults()
    if root is None:
        return defaults
    from ..policy.loading import PolicyLoadError, load_policy_doc

    try:
        doc = load_policy_doc(root, "polite_sweep.yaml")
    except PolicyLoadError:
        return defaults

    enabled = doc.get("enabled")
    if isinstance(enabled, bool):
        defaults.enabled = enabled

    delay = doc.get("per_host_delay_seconds")
    if _is_number(delay) and 0 <= float(delay) <= 600:
        defaults.per_host_delay_seconds = float(delay)

    respect = doc.get("respect_robots")
    if isinstance(respect, bool):
        defaults.respect_robots = respect

    attempts = doc.get("backoff_max_attempts")
    if isinstance(attempts, int) and not isinstance(attempts, bool) and 1 <= attempts <= 10:
        defaults.backoff_max_attempts = attempts

    base = doc.get("backoff_base_seconds")
    if _is_number(base) and 0 < float(base) <= 60:
        defaults.backoff_base_seconds = float(base)

    ceiling = doc.get("backoff_max_seconds")
    if _is_number(ceiling) and 0 < float(ceiling) <= 600:
        defaults.backoff_max_seconds = float(ceiling)

    return defaults


# ---------------------------------------------------------------------------
# The polite batch sweep
# ---------------------------------------------------------------------------


def _retry_after_seconds(headers: dict[str, str]) -> float | None:
    raw = headers.get("Retry-After")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def polite_batch(
    entries: Iterable[str],
    *,
    timeout_seconds: int,
    follow_redirects: bool,
    method: str,
    user_agent: str,
    per_host_delay_seconds: float = 0.0,
    respect_robots: bool = True,
    backoff_max_attempts: int = 1,
    backoff_base_seconds: float = 1.0,
    backoff_max_seconds: float = 60.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[tuple[str, WebCheckResult]]:
    """Check URLs sequentially with per-host spacing, robots, and 429 backoff.

    A polite loop over `check_url_detailed` (same result shape as the v1.8
    `batch()` plus the v2.3 hygiene layers). A 429 is retried until
    `backoff_max_attempts` total attempts with exponential backoff
    (`Retry-After` honored when larger); every other failure is final after
    one attempt. Pure network reads: performs zero writes and emits no
    event. An empty input yields an empty list; input order is preserved.
    """
    robots = (
        RobotsCache(user_agent=user_agent, timeout_seconds=timeout_seconds)
        if respect_robots
        else None
    )
    bucket = PerHostBucket(per_host_delay_seconds=per_host_delay_seconds)

    pairs: list[tuple[str, WebCheckResult]] = []
    for entry in entries:
        if robots is not None and not robots.allowed(entry):
            pairs.append(
                (
                    entry,
                    WebCheckResult(
                        ok=False,
                        status_code=None,
                        final_url=None,
                        reason="robots.txt disallow",
                    ),
                )
            )
            continue

        if per_host_delay_seconds > 0:
            sleep(bucket.reserve(_host_of(entry)))

        result, headers = check_url_detailed(
            entry,
            timeout_seconds=timeout_seconds,
            follow_redirects=follow_redirects,
            method=method,
            user_agent=user_agent,
        )

        attempts = max(1, int(backoff_max_attempts))
        attempt = 1
        while not result.ok and result.status_code == 429 and attempt < attempts:
            wait = backoff_base_seconds * (2 ** (attempt - 1))
            retry_after = _retry_after_seconds(headers)
            if retry_after is not None and retry_after > wait:
                wait = retry_after
            wait = min(wait, backoff_max_seconds)
            sleep(wait)
            attempt += 1
            result, headers = check_url_detailed(
                entry,
                timeout_seconds=timeout_seconds,
                follow_redirects=follow_redirects,
                method=method,
                user_agent=user_agent,
            )

        pairs.append((entry, result))
    return pairs

