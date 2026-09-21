"""
GET ``/health`` — the study-guidance roll-up (ADR 0009).

"""

from __future__ import annotations

from ...execution.overdue import utc_today
from ..health import (
    derive_study_guidance,
    render_guidance_html,
)
from .shell import (
    _chrome,
    _fresh_join,
)


def health_body(root) -> tuple[str, str, int]:
    """GET `/health` — the study-guidance roll-up (§C-ter, build #311).

    Five cards in the locked hierarchy (Stuck right now → Due for review →
    Evidence gaps → Study rhythm → Study resources), each carrying counts +
    one-line why + links. Repository diagnostics are CLI-only with zero web-UI
    presence — the per-layer validator table and liveness lines live only in
    `skilltrace health`. Not a nav stop: health reaches only through the
    header pill strip + ``Health`` pointer.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    guidance = derive_study_guidance(view, utc_today())
    header_html = _chrome(root)
    body = (
        header_html
        + '<div class="card guidance">\n'
        + '<div class="kicker">Health roll-up</div>\n'
        + '<p class="big">Your study guidance for today.</p>\n'
        + '<p class="mut">Daily study guidance only — repository checks live '
        "on the command line, and nothing here blocks your next move.</p>\n"
        + "</div>\n"
        + render_guidance_html(guidance)
    )
    return "Health", body, 200

