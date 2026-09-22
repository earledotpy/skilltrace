"""Honest CLI handoffs — the one shared handoff helper (map #258).

Locked in G-StudyDayHandoffs #263, applied in T-HandoffCopy #266, deduped in
#271: one slotted sentence, muted plain copy, omittable by the caller. The
views layer (``web.views``) and the interface render layer
(``interface.render``) both call :func:`handoff_html` — the sentence lives
here once so the two layers can never drift apart.

P3.1-clean by construction: no command names, flags, ids, or paths; the far
side is always "your terminal", never the bare word "CLI".
"""

from __future__ import annotations

from .text import esc as _esc  # the one door — never a local escaper (#315)


def handoff_html(verb: str, title: str | None = None) -> str:
    """One slotted handoff sentence as muted plain copy.

    Rendered only where the caller places it — targeted dead-ends, never
    ambient — and omitted entirely when the triggering fact is absent (the
    P4.1 absent-fact rule lives with the caller).
    """
    if title:
        sentence = (
            f"{verb} for {title} continues in your terminal "
            "\u2014 ask there for the exact form."
        )
    else:
        sentence = (
            f"{verb} continues in your terminal \u2014 ask there for the exact form."
        )
    return f'<p class="mut">{_esc(sentence)}</p>\n'
