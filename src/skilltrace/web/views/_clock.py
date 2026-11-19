"""The one wall-clock read for the read-only web surfaces.

The web has no ``Context.clock`` (ARC-4: no server-side view state), but the
Study cockpit still has to show elapsed time and decide whether an open
Session is stale. Both facts are derived from *now*, so the read lives in
one place and the snapshot/axe harnesses can pin it the same way they pin
the date funnel (:func:`skilltrace.execution.overdue.utc_today`).

Nothing here writes. A page load, a navigation, an inspection or an elapsed
timer never records work (IC-3, R6): the figure is presentation only.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    """The current UTC moment — the web's only wall-clock read."""
    return datetime.now(timezone.utc)
