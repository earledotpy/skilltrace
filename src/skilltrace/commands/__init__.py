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
    listings,
    master,
    pass_,
    recommend,
    remediation,
    resource_listing,
    resource_report,
    review,
    session,
    submit,
    suggest,
    sync,
    validate,
    verify_resource,
)


def register_all(registry: Registry) -> Registry:
    """Register every command onto `registry` and return it."""
    validate.register(registry)
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
    listings.register(registry)
    resource_listing.register(registry)
    resource_report.register(registry)
    verify_resource.register(registry)
    check_automation.register(registry)
    suggest.register(registry)
    export.register(registry)
    backup.register(registry)
    return registry
