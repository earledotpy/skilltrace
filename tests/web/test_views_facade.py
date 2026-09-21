"""The web/views facade is the package's public surface (ADR 0009).

Two structural pins so a later module move cannot silently drop a
re-export:

* every top-level name defined (or imported) by any ``web/views/*.py``
  module resolves on the facade — the union is the surface;
* the frozen consumer surface resolves: the names ``web/handler.py``
  imports from ``views`` plus every ``views.<name>`` attribute it reads,
  and the ``cards_html`` / ``page`` that ``html_export.py`` imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

import skilltrace.web.views as views

REPO_ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = REPO_ROOT / "src" / "skilltrace" / "web" / "views"


def _top_level_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.asname or alias.name
                names.add(name.split(".")[0])
    return names


def _handler_surface() -> set[str]:
    tree = ast.parse(
        (REPO_ROOT / "src" / "skilltrace" / "web" / "handler.py").read_text(
            encoding="utf-8"
        )
    )
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "views":
            names.update(alias.asname or alias.name for alias in node.names)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "views":
            names.add(node.attr)
    return names


def _html_export_surface() -> set[str]:
    tree = ast.parse(
        (REPO_ROOT / "src" / "skilltrace" / "html_export.py").read_text(
            encoding="utf-8"
        )
    )
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "web.views":
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def test_every_package_module_name_resolves_on_the_facade():
    missing: dict[str, set[str]] = {}
    for path in sorted(VIEWS_DIR.glob("*.py")):
        gap = {n for n in _top_level_names(path) if not hasattr(views, n)}
        if gap:
            missing[path.name] = gap
    assert not missing, missing


def test_the_frozen_consumer_surface_resolves_on_the_facade():
    frozen = _handler_surface() | _html_export_surface() | {
        # private names the test suite calls directly, plus the incidental
        # utc_today re-export (imported from execution.overdue at HEAD views)
        "_STYLE",
        "_finish_write",
        "_status_page",
        "_flash_html",
        "utc_today",
        "render_cards",
        "cards_html",
        "page",
    }
    missing = sorted(n for n in frozen if not hasattr(views, n))
    assert not missing, missing
