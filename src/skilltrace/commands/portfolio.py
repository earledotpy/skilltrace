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

import sys
from datetime import date
from pathlib import Path

from ..context import load_context_strict
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import utc_today
from ..portfolio.bundle import bundle_portfolio
from ..portfolio.export import (
    PortfolioExportError,
    load_view_or_raise,
    normalize_format,
    render_preview,
)
from ..portfolio.models import SelectionOptions


def _resolve_track(ctx: Context) -> str | None:
    """Resolve the track filter: explicit ``--track`` wins; ``--node`` without
    ``--track`` drops the restriction; otherwise the policy default applies."""
    args = ctx.args
    nodes = list(getattr(args, "node", None) or [])
    track = getattr(args, "track", None)
    if track is not None:
        return str(track)
    if nodes:
        return None
    return _policy_default(ctx, "default_track", "portfolio")


def _resolve_format(ctx: Context) -> str:
    """Resolve the output format: explicit ``--format`` wins; otherwise the
    policy default applies (spec §6.2/§7 — policy values, not constants)."""
    fmt = getattr(ctx.args, "format", None)
    if fmt:
        return str(fmt)
    return _policy_default(ctx, "default_format", "md")


def _policy_default(ctx: Context, field: str, fallback: str) -> str:
    """Read one portfolio policy default, failing open to ``fallback``."""
    try:
        joined = load_context_strict(ctx.root)
        if joined.ok:
            return str(getattr(joined.policy.portfolio, field))
    except Exception:  # noqa: BLE001 - fail open to the spec default
        pass
    return fallback


def _resolve_options(ctx: Context) -> SelectionOptions:
    args = ctx.args
    return SelectionOptions(
        nodes=tuple(getattr(args, "node", None) or []),
        track=_resolve_track(ctx),
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

    Returns ``(view, options, fmt, today, None)`` on success or
    ``(None, None, None, None, error)`` on failure. Identical refusal
    semantics for both surfaces: non-zero exit, ``portfolio <command>: FAILED``
    message, no partial bundle or output.

    Every portfolio surface must go through this function so the preview
    pipeline cannot drift from the export pipeline (spec §4 — preview uses
    the same selection, redaction, and rendering pipeline as export).
    """
    options = _resolve_options(ctx)
    try:
        fmt = normalize_format(_resolve_format(ctx))
    except PortfolioExportError as exc:
        print(f"portfolio {command}: FAILED — {exc}")
        return None, None, None, None, CommandResult(exit_code=1)
    today = _today(ctx)
    try:
        view = load_view_or_raise(ctx.root, options, today=today)
    except PortfolioExportError as exc:
        print(f"portfolio {command}: FAILED — {exc}")
        return None, None, None, None, CommandResult(exit_code=1)
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
        )
    )
    registry.register(
        Command(
            name="portfolio export",
            kind=Kind.MUTATING,
            handler=portfolio_export,
            help="Write the disposable portfolio bundle to data/portfolio-<date>/.",
        )
    )
