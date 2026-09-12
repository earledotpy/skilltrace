"""Deep resource URL-check interface — policy merge plus polite sweep.

One production call path for URL sweeps (`check_urls`): it merges the
`resource_web_verification` and `polite_sweep` policy seeds with explicit
caller overrides, then checks URLs sequentially with three politeness
layers:

- **Per-host rate limiting** — nominal per-host spacing: a host's first
  request proceeds immediately and any later same-host request waits
  `per_host_delay_seconds` (0 = the sweep never sleeps). Delays are
  host-keyed — different hosts never wait on each other.
- **`robots.txt` respect** — one `robots.txt` fetch per host; disallowed
  URLs are never fetched and report `ok=False` with a `robots.txt disallow`
  reason. Any robots fetch failure (404, transport error, timeout) fails
  open: the URL is checked anyway. A robots check must never turn a
  reachable resource into a failure verdict.
- **429 backoff** — a 429 may be retried with bounded exponential backoff
  (base doubling, capped at `backoff_max_seconds`); a larger `Retry-After`
  header wins. Only 429 is retried — every other HTTP/transport/timeout
  failure is final after one attempt. `backoff_max_attempts=1`
  reproduces the never-retry behavior exactly.

Pure network reads: performs zero writes (never touches stored
verification state) and emits no event. Order is preserved; an empty input
yields an empty list.

The robots cache and per-host spacing machinery are internal to this
module (underscore names, not exported). Tests exercise the sweep through
`check_urls` with an injected `opener` (plus an injected `sleep`), never
by poking internals.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections.abc import Callable, Iterable
from typing import Any

from .web_check import WebCheckResult, check_url_detailed, resolve_web_verification_policy

__all__ = [
    "PoliteSweepDefaults",
    "WebCheckResult",
    "check_urls",
    "resolve_polite_sweep_policy",
]


def _host_of(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return (parsed.hostname or "").lower()


# ---------------------------------------------------------------------------
# Internal robots cache (not part of the public interface)
# ---------------------------------------------------------------------------


class _RobotsCache:
    """Per-host `robots.txt` cache; disallowed URLs are never fetched."""

    def __init__(
        self,
        *,
        user_agent: str,
        timeout_seconds: int = 10,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._timeout_seconds = timeout_seconds
        self._opener = opener
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}

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
            if self._opener is None:
                with urllib.request.build_opener().open(
                    req, timeout=self._timeout_seconds
                ) as response:
                    body = response.read() if hasattr(response, "read") else b""
                    status = response.getcode()
            else:
                with self._opener(req, timeout=self._timeout_seconds) as response:
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
# Internal per-host spacing (not part of the public interface)
# ---------------------------------------------------------------------------


class _PerHostBucket:
    """Monotonic per-host spacing: same-host requests are delayed apart."""

    def __init__(
        self,
        *,
        per_host_delay_seconds: float,
        on_sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._delay = float(per_host_delay_seconds)
        self._on_sleep = on_sleep
        self._seen: set[str] = set()

    def reserve(self, host: str) -> float:
        """Return the delay before this request (0 for a host's first)."""
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
# The deep sweep interface
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


def check_urls(
    entries: Iterable[str],
    *,
    root=None,
    timeout_seconds: int | None = None,
    follow_redirects: bool | None = None,
    method: str | None = None,
    user_agent: str | None = None,
    per_host_delay_seconds: float | None = None,
    respect_robots: bool | None = None,
    backoff_max_attempts: int | None = None,
    backoff_base_seconds: float | None = None,
    backoff_max_seconds: float | None = None,
    opener: Callable[..., Any] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[tuple[str, WebCheckResult]]:
    """Check URLs end-to-end: policy merge plus polite sweep.

    `None` parameters resolve from the policy seeds under `root`
    (`resource_web_verification.yaml` for timeout/method/redirects/agent;
    `polite_sweep.yaml` for delay/robots/backoff). Explicit values win.
    A disabled sweep policy degrades to a plain sequential sweep
    (robots skipped, no extra delay, no 429 retries).

    `opener`, when given, replaces the default urllib open call for both
    the `robots.txt` fetch and each URL fetch — tests inject a fake here.
    `sleep` receives every spacing/backoff wait (tests inject a recorder).

    Raises ValueError on invalid merged arguments before any fetch.
    Pure network reads: performs zero writes and emits no event. An empty
    input yields an empty list; input order is preserved.
    """
    web_policy = resolve_web_verification_policy(root)
    sweep_policy = resolve_polite_sweep_policy(root)

    timeout = web_policy.timeout_seconds if timeout_seconds is None else timeout_seconds
    follow = web_policy.follow_redirects if follow_redirects is None else follow_redirects
    meth = web_policy.check_method if method is None else method
    agent = web_policy.user_agent if user_agent is None else user_agent

    delay = (
        sweep_policy.per_host_delay_seconds
        if per_host_delay_seconds is None
        else per_host_delay_seconds
    )
    respect = sweep_policy.respect_robots if respect_robots is None else respect_robots
    attempts_opt = (
        sweep_policy.backoff_max_attempts
        if backoff_max_attempts is None
        else backoff_max_attempts
    )
    base = (
        sweep_policy.backoff_base_seconds
        if backoff_base_seconds is None
        else backoff_base_seconds
    )
    ceiling = (
        sweep_policy.backoff_max_seconds
        if backoff_max_seconds is None
        else backoff_max_seconds
    )

    if root is not None and not sweep_policy.enabled:
        respect = False
        delay = 0.0
        attempts_opt = 1

    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or not (1 <= timeout <= 120)
    ):
        raise ValueError(
            "Invalid timeout_seconds: expected integer in [1, 120], "
            f"got {timeout!r}."
        )
    if not isinstance(follow, bool):
        raise ValueError(
            f"Invalid follow_redirects: expected bool, got {follow!r}."
        )
    if meth not in ("HEAD", "GET"):
        raise ValueError(f"Invalid method: expected 'HEAD' or 'GET', got {meth!r}.")
    if not isinstance(agent, str) or not agent.strip():
        raise ValueError(
            f"Invalid user_agent: expected non-empty string, got {agent!r}."
        )
    if (
        isinstance(delay, bool)
        or not isinstance(delay, (int, float))
        or not (0 <= float(delay) <= 600)
    ):
        raise ValueError(
            "check-resources: FAILED — --per-host-delay must be a number "
            f"in [0, 600]; got {per_host_delay_seconds!r}."
            if per_host_delay_seconds is not None
            else f"Invalid per_host_delay_seconds: expected number in [0, 600], got {delay!r}."
        )
    if not isinstance(respect, bool):
        raise ValueError(
            f"Invalid respect_robots: expected bool, got {respect!r}."
        )
    if (
        isinstance(attempts_opt, bool)
        or not isinstance(attempts_opt, int)
        or not (1 <= attempts_opt <= 10)
    ):
        raise ValueError(
            "check-resources: FAILED — --backoff-attempts must be an "
            f"integer in [1, 10]; got {backoff_max_attempts!r}."
            if backoff_max_attempts is not None
            else f"Invalid backoff_max_attempts: expected integer in [1, 10], got {attempts_opt!r}."
        )
    if not _is_number(base) or not (0 < float(base) <= 60):
        raise ValueError(
            f"Invalid backoff_base_seconds: expected number in (0, 60], got {base!r}."
        )
    if not _is_number(ceiling) or not (0 < float(ceiling) <= 600):
        raise ValueError(
            f"Invalid backoff_max_seconds: expected number in (0, 600], got {ceiling!r}."
        )

    delay = float(delay)
    base = float(base)
    ceiling = float(ceiling)
    attempts = max(1, int(attempts_opt))

    robots = (
        _RobotsCache(user_agent=agent, timeout_seconds=timeout, opener=opener)
        if respect
        else None
    )
    bucket = _PerHostBucket(per_host_delay_seconds=delay)

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

        if delay > 0:
            sleep(bucket.reserve(_host_of(entry)))

        result, headers = check_url_detailed(
            entry,
            timeout_seconds=timeout,
            follow_redirects=follow,
            method=meth,  # type: ignore[arg-type]
            user_agent=agent,
            opener=opener,
        )

        attempt = 1
        while not result.ok and result.status_code == 429 and attempt < attempts:
            wait = base * (2 ** (attempt - 1))
            retry_after = _retry_after_seconds(headers)
            if retry_after is not None and retry_after > wait:
                wait = retry_after
            wait = min(wait, ceiling)
            sleep(wait)
            attempt += 1
            result, headers = check_url_detailed(
                entry,
                timeout_seconds=timeout,
                follow_redirects=follow,
                method=meth,  # type: ignore[arg-type]
                user_agent=agent,
                opener=opener,
            )

        pairs.append((entry, result))
    return pairs


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
    opener: Callable[..., Any] | None = None,
) -> list[tuple[str, WebCheckResult]]:
    """Legacy alias over `check_urls` (kept out of the public interface).

    Existing callers pass fully-resolved values with no policy root, so
    this forwards verbatim with `root=None`.
    """
    return check_urls(
        entries,
        root=None,
        timeout_seconds=timeout_seconds,
        follow_redirects=follow_redirects,
        method=method,
        user_agent=user_agent,
        per_host_delay_seconds=per_host_delay_seconds,
        respect_robots=respect_robots,
        backoff_max_attempts=backoff_max_attempts,
        backoff_base_seconds=backoff_base_seconds,
        backoff_max_seconds=backoff_max_seconds,
        opener=opener,
        sleep=sleep,
    )
