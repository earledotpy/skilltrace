"""The v0.3 command surface.

Handlers here are placeholders: this issue (#1) builds the dispatcher, package,
and cross-cutting chokepoints. The real behavior lands in later v0.3 issues —
`validate graph` (#5), `sync` (#6), `next`/recommendation (#7). Each command is
registered now with its final name and classification so the dispatcher contract
(audit event on mutation, read-only appends nothing) is exercised from day one.
"""

from __future__ import annotations

from ..dispatch import Registry
from . import recommend, sync, validate


def register_all(registry: Registry) -> Registry:
    """Register every v0.3 command onto `registry` and return it."""
    validate.register(registry)
    sync.register(registry)
    recommend.register(registry)
    return registry
