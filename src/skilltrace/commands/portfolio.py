"""`skilltrace portfolio preview|export` — v2.0 portfolio builder (map #174).

- ``portfolio preview --track <T> --format <md|html|json>`` renders to stdout
  (or ``--output``); READ_ONLY, no audit event.
- ``portfolio export ...`` writes the disposable bundle to
  ``data/portfolio-<date>/``; MUTATING, exactly one ``portfolio_export``
  audit event via the dispatcher.

The wall clock is read once per handler via ``utc_today`` and injected as
``today`` — portfolio internals never call the clock (§8.1). Any data load
error refuses with a non-zero exit and no partial output. This module emits
no audit event itself (SA6); the dispatcher owns the single export event.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from ..context import JoinedView, load_context_strict
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import utc_today
from ..portfolio.bundle import bundle_portfolio
from ..portfolio.export import (
    PortfolioExportError,
    normalize_format,
    render_preview,
)
from ..portfolio.models import SelectionOptions
from ..portfolio.pipeline import build_portfolio


def _resolve_track(args: object, policy_track: str) -> str | None:
    """Resolve the track filter: explicit ``--track`` wins; ``--node`` without
    ``--track`` drops the restriction; otherwise the policy default applies."""
    nodes = list(getattr(args, "node", None) or [])
    track = getattr(args, "track", None)
    if track is not None:
        return str(track)
    if nodes:
        return None
    return policy_track


def _resolve_format(args: object, policy_format: str) -> str:
    """Resolve the output format: explicit ``--format`` wins; otherwise the
    policy default applies (spec §6.2/§7 — policy values, not constants)."""
    fmt = getattr(args, "format", None)
    if fmt:
        return str(fmt)
    return policy_format


def _resolve_options(args: object, *, track: str | None) -> SelectionOptions:
    return SelectionOptions(
        nodes=tuple(getattr(args, "node", None) or []),
        track=track,
        include_active=bool(getattr(args, "include_active", False)),
        include_rejected=bool(getattr(args, "include_rejected", False)),
        include_superseded=bool(getattr(args, "include_superseded", False)),
        include_paths=bool(getattr(args, "include_paths", False)),
        include_notes=bool(getattr(args, "include_notes", False)),
        include_blockers=bool(getattr(args, "include_blockers", False)),
        include_reviews=bool(getattr(args, "include_reviews", False)),
        include_free_text=bool(getattr(args, "include_free_text", False)),
        include_urls=bool(getattr(args, "include_urls", False)),
    )


def _today(ctx: Context) -> date:
    return utc_today(clock=ctx.clock)


def _shared_portfolio_load(
    ctx: Context, command: str
) -> tuple[object | None, SelectionOptions | None, str | None, date | None, CommandResult | None]:
    """Single shared view-loading path for preview and export (T6).

    One ``JoinedView`` load serves policy defaults, selection, and
    redaction together — no second load solely for portfolio policy
    values. Returns ``(view, options, fmt, today, None)`` on success or
    ``(None, None, None, None, error)`` on failure. Identical refusal
    semantics for both surfaces: non-zero exit, ``portfolio <command>: FAILED``
    message, no partial bundle or output.

    Every portfolio surface must go through this function so the preview
    pipeline cannot drift from the export pipeline (spec §4 — preview uses
    the same selection, redaction, and rendering pipeline as export).
    """
    today = _today(ctx)
    try:
        joined: JoinedView = load_context_strict(ctx.root)
    except Exception as exc:  # noqa: BLE001 - strict loaders fail open to refusal
        print(f"portfolio {command}: FAILED — {exc}")
        return None, None, None, None, CommandResult(exit_code=1)
    if not joined.ok:
        print(
            "portfolio "
            + command
            + ": FAILED — Cannot build portfolio — data load failed:\n"
            + "\n".join(f"  {e}" for e in joined.errors)
        )
        return None, None, None, None, CommandResult(exit_code=1)
    policy = joined.policy.portfolio
    options = _resolve_options(ctx.args, track=_resolve_track(ctx.args, policy.default_track))
    try:
        fmt = normalize_format(_resolve_format(ctx.args, policy.default_format))
    except PortfolioExportError as exc:
        print(f"portfolio {command}: FAILED — {exc}")
        return None, None, None, None, CommandResult(exit_code=1)
    view = build_portfolio(joined, options, today=today)
    return view, options, fmt, today, None


def portfolio_preview(ctx: Context) -> CommandResult:
    """Render the portfolio to stdout (or ``--output``); never writes a bundle."""
    args = ctx.args
    view, options, fmt, today, err = _shared_portfolio_load(ctx, "preview")
    if err is not None:
        return err
    assert view is not None and options is not None and fmt is not None and today is not None
    output_raw = getattr(args, "output", None)
    content = render_preview(view, options, fmt=fmt)
    if output_raw is not None and str(output_raw) != "-":
        dest = Path(str(output_raw))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        rel = dest.relative_to(ctx.root) if dest.is_relative_to(ctx.root) else dest
        print(f"portfolio preview: wrote {rel.as_posix()}")
    else:
        sys.stdout.write(content)
    return CommandResult(exit_code=0)


def portfolio_export(ctx: Context) -> CommandResult:
    """Write the disposable bundle to ``data/portfolio-<date>/`` (MUTATING)."""
    args = ctx.args
    # Same single view-loading path as preview — identical refusal semantics (T6).
    view, options, _fmt, today, err = _shared_portfolio_load(ctx, "export")
    if err is not None:
        return err
    assert view is not None and options is not None and today is not None
    output_raw = getattr(args, "output", None)
    dest_override = (
        Path(str(output_raw))
        if output_raw is not None and str(output_raw) != "-"
        else None
    )
    try:
        dest = bundle_portfolio(ctx.root, options, today=today, dest=dest_override, view=view)
    except PortfolioExportError as exc:
        print(f"portfolio export: FAILED — {exc}")
        return CommandResult(exit_code=1)
    except OSError as exc:
        print(f"portfolio export: FAILED — {exc}")
        return CommandResult(exit_code=1)
    rel = dest.relative_to(ctx.root) if dest.is_relative_to(ctx.root) else dest
    print(f"portfolio export: wrote {rel.as_posix()}/")
    return CommandResult(records_touched=[n for n in options.nodes])


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="portfolio preview",
            kind=Kind.READ_ONLY,
            handler=portfolio_preview,
            help="Render the portfolio to stdout (read-only; same pipeline as export).",
            add_parser=add_parser,
        )
    )
    registry.register(
        Command(
            name="portfolio export",
            kind=Kind.MUTATING,
            handler=portfolio_export,
            help="Write the disposable portfolio bundle to data/portfolio-<date>/.",
            add_parser=add_parser,
        )
    )


def _add_portfolio_shared_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--node",
        action="append",
        default=None,
        metavar="ID",
        help="Restrict to named node(s) (repeatable).",
    )
    p.add_argument(
        "--track",
        default=None,
        metavar="NAME",
        help="Restrict to track (default from policy/portfolio.yaml; "
        "omitted when --node is given without --track).",
    )
    p.add_argument("--include-active", action="store_true")
    p.add_argument("--include-rejected", action="store_true")
    p.add_argument("--include-superseded", action="store_true")
    p.add_argument("--include-paths", action="store_true")
    p.add_argument("--include-notes", action="store_true")
    p.add_argument("--include-blockers", action="store_true")
    p.add_argument("--include-reviews", action="store_true")
    p.add_argument("--include-free-text", action="store_true")
    p.add_argument("--include-urls", action="store_true")
    p.add_argument(
        "--format",
        default=None,
        metavar="<md|html|json>",
        help="Output format (default from policy/portfolio.yaml).",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Destination (use - for stdout).",
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `portfolio` parser (issue #206, expand–contract).

    Co-located owner of the `portfolio` argparse surface; `cli.build_parser`
    calls this for the new path and skips its legacy `portfolio` block.
    """
    portfolio_parser = subparsers.add_parser(
        "portfolio", help="Portfolio builder (preview, export)."
    )
    portfolio_commands = portfolio_parser.add_subparsers(
        dest="_portfolio_cmd", metavar="<command>"
    )
    portfolio_commands.required = True
    portfolio_preview_parser = portfolio_commands.add_parser(
        "preview", help="Render the portfolio to stdout (read-only)."
    )
    _add_portfolio_shared_arguments(portfolio_preview_parser)
    portfolio_preview_parser.set_defaults(_command_name="portfolio preview")
    portfolio_export_parser = portfolio_commands.add_parser(
        "export", help="Write the disposable portfolio bundle (mutating)."
    )
    _add_portfolio_shared_arguments(portfolio_export_parser)
    portfolio_export_parser.set_defaults(_command_name="portfolio export")
