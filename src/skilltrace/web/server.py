"""Serve shell placeholder (Tier-1 slice T2 lands it here).

Slice T1 scaffolds this module empty by design — importing it must have no
side effects. T2 will own the stdlib-only `http.server.ThreadingHTTPServer`
shell: port 8341 fail-fast, loopback-only, browser auto-open, foreground
until Ctrl+C (G3#67 / ADR 0006). It registers no CLI command from here;
`serve` (+ `ui` alias) is registered READ_ONLY in T2.
"""

from __future__ import annotations
