"""Tier 1 web surface — serve shell, views, and export html.

Deliberately named ``web``, never ``interface`` or ``views``: ADR 0002 cut the
interface layer from v1 and ADR 0005 retired the scaffold that carried one.
The serve shell lives here (T2: ``server.py`` + ``handler.py``, registered as
the READ_ONLY ``serve`` command with the ``ui`` alias); daily views (T3),
safety modals + daily writes (T4), and export html (T5) land here next. Two
seams fix the surface:

* reads go through the ``JoinedView`` deep module (``skilltrace.context``) —
  lenient per request for live pages, strict only for the export snapshot;
* writes never touch the progress store directly — a confirmed action builds a
  ``Context(root, args, source="web")`` and nest-dispatches through the same
  registry and handlers as the CLI, so there is exactly one write path.

Importing this package has no side effects; only ``serve`` starts a server.
"""

from __future__ import annotations
