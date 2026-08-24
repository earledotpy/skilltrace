"""The `skilltrace.web` scaffold imports clean — no routes, no side effects (T1).

The package exists so later slices (serve shell T2, views T3/T4, export html
T5) have their home, but until then importing it must register nothing in the
CLI registry and expose no runnable entry points. It is deliberately named
`web`, never `interface`/`views` (ADR 0002/0005).
"""

from __future__ import annotations

import importlib

from skilltrace import cli


def test_web_modules_import_without_side_effects():
    web = importlib.import_module("skilltrace.web")
    server = importlib.import_module("skilltrace.web.server")
    handler = importlib.import_module("skilltrace.web.handler")

    assert web.__doc__  # scaffold carries its intent
    assert server.__doc__
    assert handler.__doc__


def test_no_web_command_is_registered_yet():
    names = set(cli.REGISTRY.names())
    assert "serve" not in names
    assert "ui" not in names
