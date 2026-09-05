"""Pure standard-library URL reachability checker (v1.7 spec §2).

Performs advisory-only URL reachability checks using urllib.request.
Applies method, timeout, redirects, and User-Agent headers.
Performs no filesystem writes, never calls record_verification,
never writes last_verified, and never clears broken markers.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class WebVerificationPolicyDefaults:
    """Default policy configuration for resource web checks."""

    enabled: bool = True
    timeout_seconds: int = 10
    follow_redirects: bool = True
    check_method: Literal["HEAD", "GET"] = "HEAD"
    user_agent: str = "SkillTrace/1.7"


def resolve_web_verification_policy(root: str | Path | None) -> WebVerificationPolicyDefaults:
    """Resolve resource web verification defaults from policy seed data."""
    if root is None:
        return WebVerificationPolicyDefaults()
    from ..policy.loading import PolicyLoadError, load_policy_doc

    try:
        doc = load_policy_doc(root, "resource_web_verification.yaml")
    except PolicyLoadError:
        return WebVerificationPolicyDefaults()

    enabled = doc.get("enabled")
    if not isinstance(enabled, bool):
        enabled = True

    timeout = doc.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not (1 <= timeout <= 120):
        timeout = 10

    follow = doc.get("follow_redirects")
    if not isinstance(follow, bool):
        follow = True

    method = doc.get("check_method")
    if method not in ("HEAD", "GET"):
        method = "HEAD"

    ua = doc.get("user_agent")
    if not isinstance(ua, str) or not ua.strip():
        ua = "SkillTrace/1.7"

    return WebVerificationPolicyDefaults(
        enabled=enabled,
        timeout_seconds=timeout,
        follow_redirects=follow,
        check_method=method,
        user_agent=ua,
    )


@dataclass(frozen=True)
class WebCheckResult:

    """The outcome of an advisory URL reachability check.

    Frozen; carries `ok: bool`, `status_code`, `final_url`, and `reason`.
    """

    ok: bool
    status_code: int | None = None
    final_url: str | None = None
    reason: str | None = None


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that prevents automatic following of HTTP redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_url(
    url: str,
    *,
    timeout_seconds: int,
    follow_redirects: bool,
    method: Literal["HEAD", "GET"],
    user_agent: str,
) -> WebCheckResult:
    """Check reachability of a single HTTP/HTTPS URL via urllib.request.

    Raises ValueError on invalid arguments.
    Expected HTTP/transport/timeout failures return `ok=False`.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError(f"Invalid URL: expected non-empty string, got {url!r}.")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: expected http or https, got {parsed.scheme!r}.")

    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not (1 <= timeout_seconds <= 120):
        raise ValueError(
            f"Invalid timeout_seconds: expected integer in [1, 120], got {timeout_seconds!r}."
        )

    if not isinstance(follow_redirects, bool):
        raise ValueError(f"Invalid follow_redirects: expected bool, got {follow_redirects!r}.")

    if method not in ("HEAD", "GET"):
        raise ValueError(f"Invalid method: expected 'HEAD' or 'GET', got {method!r}.")

    if not isinstance(user_agent, str) or not user_agent.strip():
        raise ValueError(f"Invalid user_agent: expected non-empty string, got {user_agent!r}.")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent},
        method=method,
    )

    handlers = []
    if not follow_redirects:
        handlers.append(_NoRedirectHandler())

    opener = urllib.request.build_opener(*handlers)

    try:
        with opener.open(req, timeout=timeout_seconds) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            final_url = resp.geturl()
            ok = 200 <= code < 400
            return WebCheckResult(
                ok=ok,
                status_code=code,
                final_url=final_url,
                reason=None if ok else str(code),
            )
    except urllib.error.HTTPError as exc:
        code = exc.code
        final_url = getattr(exc, "url", url) or url
        reason_str = str(exc.reason).lower() if exc.reason else f"http {code}"
        return WebCheckResult(
            ok=False,
            status_code=code,
            final_url=final_url,
            reason=reason_str,
        )
    except (TimeoutError, socket.timeout):
        return WebCheckResult(
            ok=False,
            status_code=None,
            final_url=None,
            reason=f"timeout after {timeout_seconds}s",
        )
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)) or "timed out" in str(exc.reason).lower():
            return WebCheckResult(
                ok=False,
                status_code=None,
                final_url=None,
                reason=f"timeout after {timeout_seconds}s",
            )
        return WebCheckResult(
            ok=False,
            status_code=None,
            final_url=None,
            reason=str(exc.reason),
        )
    except OSError as exc:
        return WebCheckResult(
            ok=False,
            status_code=None,
            final_url=None,
            reason=str(exc),
        )


def batch(
    entries: Iterable[str],
    *,
    timeout_seconds: int,
    follow_redirects: bool,
    method: Literal["HEAD", "GET"],
    user_agent: str,
) -> list[tuple[str, WebCheckResult]]:
    """Check a list of URLs sequentially, preserving input order (v1.8 G-Batch).

    A thin loop over `check_url`: no token bucket, no `robots.txt`, no retry
    loop — a 429 (or any HTTP/transport/timeout failure) is reported as
    `ok=False` via the result's `reason`, never retried. Pure network reads:
    performs zero writes (never calls `record_verification`, never sets
    `last_verified`, never clears `broken`) and emits no event. An empty
    input yields an empty list.
    """
    return [
        (
            entry,
            check_url(
                entry,
                timeout_seconds=timeout_seconds,
                follow_redirects=follow_redirects,
                method=method,
                user_agent=user_agent,
            ),
        )
        for entry in entries
    ]
