"""Tier 1 web surface — package scaffold (slice T1).

Deliberately named ``web``, never ``interface`` or ``views``: ADR 0002 cut the
interface layer from v1 and ADR 0005 retired the scaffold that carried one.
The serve shell (T2), daily views (T3), safety modals + daily writes (T4), and
export html (T5) live here. Two seams fix this slice:

* reads go through the ``JoinedView`` deep module (``skilltrace.context``) —
  lenient per request for live pages, strict only for the export snapshot;
* writes never touch the progress store directly — a confirmed action builds a
  ``Context(root, args, source="web")`` and nest-dispatches through the same
  registry and handlers as the CLI, so there is exactly one write path.

Importing this package has no side effects and registers no routes yet.
"""

from __future__ import annotations
