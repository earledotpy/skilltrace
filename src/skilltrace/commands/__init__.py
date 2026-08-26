"""The v0.3 command surface.

Handlers here are placeholders: this issue (#1) builds the dispatcher, package,
and cross-cutting chokepoints. The real behavior lands in later v0.3 issues —
`validate graph` (#5), `sync` (#6), `next`/recommendation (#7). Each command is
registered now with its final name and classification so the dispatcher contract
(audit event on mutation, read-only appends nothing) is exercised from day one.
"""

from __future__ import annotations

from ..dispatch import Registry
from . import (
    attempt,
    backup,
    blocker,
    check_automation,
    eligibility,
    export,
    health,
    listings,
    master,
    node_detail,
    pass_,
    recommend,
    remediation,
    report,
    resource_listing,
    resource_report,
    retention,
    review,
    session,
    submit,
    suggest,
    sync,
    today,
    validate,
    verify_resource,
)


def register_all(registry: Registry) -> Registry:
    """Register every command onto `registry` and return it."""
    # Imported here, not at module level: the command package must not load the
    # presentation layer on import (the web views read back through these very
    # command modules — a module-level import would be a cycle).
    from ..web import server as web_server

    validate.register(registry)
    health.register(registry)
    node_detail.register(registry)
    sync.register(registry)
    recommend.register(registry)
    submit.register(registry)
    attempt.register(registry)
    eligibility.register(registry)
    pass_.register(registry)
    master.register(registry)
    session.register(registry)
    blocker.register(registry)
    remediation.register(registry)
    review.register(registry)
    report.register(registry)
    listings.register(registry)
    resource_listing.register(registry)
    resource_report.register(registry)
    verify_resource.register(registry)
    check_automation.register(registry)
    suggest.register(registry)
    today.register(registry)
    export.register(registry)
    backup.register(registry)
    retention.register(registry)
    # Tier 1 local web UI (ADR 0006): READ_ONLY — serve appends no event; the
    # `ui` alias shares this registration via its `_command_name`.
    web_server.register(registry)
    return registry
