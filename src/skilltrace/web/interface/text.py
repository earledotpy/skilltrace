"""The web text micro-utilities — one home per convention (#315).

Two conventions that used to be copied around the web tree live here once:

* :func:`esc` — the **one door** into page HTML. The interface renderer, the
  handoff copy, the page layer and the Health guidance renderer all escape
  through this function, so a fix here is a fix on every web surface. No other
  web module defines an escaper (``tests/web/test_micro_utilities.py`` is the
  gate that keeps it that way).
* :func:`plural` — the **one agreement helper**: the inflection that makes a
  noun agree with its count, instead of an inline ``'s' if n != 1 else ''``
  written out again at every call site.

Pure string plumbing: no I/O, no engine state, no markup structure. Both names
are re-exported on the sublayer's public surface (``web.interface.esc``,
``web.interface.plural``).
"""

from __future__ import annotations

import html

__all__ = ["esc", "plural"]


def esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


def plural(n: int, one: str = "", many: str = "s") -> str:
    """The inflection that makes a noun agree with its count.

    ``one`` is the form used when the count is exactly one, ``many`` the form
    for every other count. The defaults are the plain suffix pair (``''`` /
    ``'s'``); an explicit pair covers the irregular agreements too —
    ``plural(n, 'es', '')`` for *match/matches*, ``plural(n, 's', '')`` for
    *falls/fall*.
    """
    return one if n == 1 else many
