"""`skilltrace export markdown` and `skilltrace export sqlite`.

Both are mutating (the #33 resolution): a learner's explicit call to
regenerate a disposable snapshot still appends one audit event, overriding the
read-only default. Neither accepts arguments beyond the subcommand itself.

Loader failures refuse the write rather than producing a partial or
misleading snapshot/mirror (`export_data.load_export_data` folds every
layer's load errors into `ExportData.errors`; a non-empty set fails the
command before anything touches disk).
"""

from __future__ import annotations

import argparse

from ..context import load_context_strict
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..export_data import ExportData, load_export_data
from ..html_export import HTML_EXPORT_RELPATH, render_html
from ..markdown_export import MARKDOWN_EXPORT_RELPATH, render_markdown
from ..sqlite_export import SQLITE_EXPORT_RELPATH, write_sqlite_export
from ._common import now_iso


def _load_or_fail(ctx: Context, command_name: str) -> ExportData | None:
    data = load_export_data(ctx.root)
    if not data.ok:
        print(f"{command_name}: FAILED — could not load export data:")
        for error in data.errors:
            print(f"  [error] {error}")
        return None
    return data


def export_markdown(ctx: Context) -> CommandResult:
    data = _load_or_fail(ctx, "export markdown")
    if data is None:
        return CommandResult(exit_code=1)

    path = ctx.root / MARKDOWN_EXPORT_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(data, now=now_iso()), encoding="utf-8")
    print(f"export markdown: wrote {MARKDOWN_EXPORT_RELPATH.as_posix()}")
    return CommandResult()


def export_sqlite(ctx: Context) -> CommandResult:
    data = _load_or_fail(ctx, "export sqlite")
    if data is None:
        return CommandResult(exit_code=1)

    path = ctx.root / SQLITE_EXPORT_RELPATH
    write_sqlite_export(data, path)
    print(f"export sqlite: wrote {SQLITE_EXPORT_RELPATH.as_posix()}")
    return CommandResult()


def export_html(ctx: Context) -> CommandResult:
    """Write the self-contained HTML snapshot, refusing on any load error."""
    view = load_context_strict(ctx.root)
    if not view.ok:
        print("export html: FAILED — could not load export data:")
        for error in view.errors:
            print(f"  [error] {error}")
        return CommandResult(exit_code=1)

    path = ctx.root / HTML_EXPORT_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(ctx), encoding="utf-8")
    print(f"export html: wrote {HTML_EXPORT_RELPATH.as_posix()}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="export markdown",
            kind=Kind.MUTATING,
            handler=export_markdown,
            help="Write a compact Markdown snapshot to data/export.md.",
            add_parser=add_parser,
        )
    )
    registry.register(
        Command(
            name="export sqlite",
            kind=Kind.MUTATING,
            handler=export_sqlite,
            help="Rebuild the SQLite mirror at data/skilltrace.db.",
            add_parser=add_parser,
        )
    )
    registry.register(
        Command(
            name="export html",
            kind=Kind.MUTATING,
            handler=export_html,
            help="Write a self-contained HTML snapshot to data/export.html.",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `export` parser (issue #206, expand–contract).

    Co-located owner of the `export` argparse surface; `cli.build_parser`
    calls this for the new path and skips its legacy `export` block.
    """
    export_parser = subparsers.add_parser(
        "export", help="Export a disposable data snapshot (markdown, sqlite, html)."
    )
    export_targets = export_parser.add_subparsers(dest="_export_target", metavar="<target>")
    export_targets.required = True
    export_markdown_parser = export_targets.add_parser(
        "markdown", help="Write a compact Markdown snapshot to data/export.md."
    )
    export_markdown_parser.set_defaults(_command_name="export markdown")
    export_sqlite_parser = export_targets.add_parser(
        "sqlite", help="Rebuild the SQLite mirror at data/skilltrace.db."
    )
    export_sqlite_parser.set_defaults(_command_name="export sqlite")
    export_html_parser = export_targets.add_parser(
        "html", help="Write a self-contained HTML snapshot to data/export.html."
    )
    export_html_parser.set_defaults(_command_name="export html")
