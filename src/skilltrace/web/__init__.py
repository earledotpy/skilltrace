"""Tier 1 web surface — serve shell, views, and the interface sublayer.

Deliberately named ``web`` at the package level (ADR 0006); the ADR 0007
**interface sublayer** lives inside it at ``web/interface/`` (v2.4): the
View / Card / Command / Active-view-state vocabulary, validated at import
and against the live dispatcher registry at serve boot. Two seams fix the
surface:

* reads go through the ``JoinedView`` deep module (``skilltrace.context``) —
  lenient per request for live pages, strict only for the export snapshot;
* writes never touch the progress store directly — a confirmed action builds a
  ``Context(root, args, source="web")`` and nest-dispatches through the same
  registry and handlers as the CLI, so there is exactly one write path.

Captured command output flows through the sublayer's forbidden-vocabulary
translation (P3.1) at the ``render_cards``/flash boundary; no surface
bypasses it. The sublayer emits no ``<script>`` — a release-tested gate.

Importing this package has no side effects; only ``serve`` starts a server.
"""

from __future__ import annotations
