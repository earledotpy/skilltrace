"""Request-handler placeholder (Tier-1 slices T3/T4 land views here).

Empty by design in T1 — importing it has no side effects and defines no
routes. Later slices render server-generated HTML from the lenient
``JoinedView`` reusing the CLI's ``render.py`` voice verbatim (G3#67) and
dispatch confirmed writes through the registry with ``source="web"``
(G2#66). No JavaScript, no static files, one inline style block.
"""

from __future__ import annotations
