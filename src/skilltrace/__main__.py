"""Enable `python -m skilltrace` as a PATH-independent entry point.

The console script (`skilltrace`) is the normal entry point, but it must be on
PATH to run. `python -m skilltrace` invokes the same CLI using only the
interpreter that imported the package, which is what the v0.3 exit-gate script
uses so it works on a fresh clone without relying on the script shim being
resolvable.
"""

from __future__ import annotations

from .cli import run

raise SystemExit(run())
