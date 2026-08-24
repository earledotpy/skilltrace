"""The `skilltrace.web` scaffold imports clean and registers exactly `serve` (T2).

Importing any module in the package must have no side effects — only running
the `serve` command starts a server. The registry carries one READ_ONLY
`serve` entry; the `ui` alias is argparse-only, mapping to the same
`_command_name`. The package is deliberately named `web`, never
`interface`/`views` (ADR 0002/0005).
"""

from __future__ import annotations

import importlib

from skilltrace import cli
from skilltrace.dispatch import Kind


def test_web_modules_import_without_side_effects():
    web = importlib.import_module("skilltrace.web")
    server = importlib.import_module("skilltrace.web.server")
    handler = importlib.import_module("skilltrace.web.handler")

    assert web.__doc__  # modules carry their intent
    assert server.__doc__
    assert handler.__doc__
    # Import alone must not have started anything or registered routes beyond
    # the declarative registration done by commands/__init__.register_all.


def test_serve_registered_read_only_and_ui_alias_maps_to_it():
    names = set(cli.REGISTRY.names())
    assert "serve" in names

    command = cli.REGISTRY.get("serve")
    assert command is not None
    assert command.kind is Kind.READ_ONLY  # serve appends no audit event itself

    parser = cli.build_parser()
    serve_args = parser.parse_args(["serve"])
    ui_args = parser.parse_args(["ui"])
    assert serve_args._command_name == ui_args._command_name == "serve"
