"""`skilltrace graph impact` — the read-only curriculum-edit advisory (v2.2).

Compares the working tree against a baseline and renders the pure
`..graph.impact.diagnose` findings. Advisory only: `Kind.READ_ONLY`.

The command layer is renderer/exit-code only: it picks the `BaselineSource`
(git ref by default, `--baseline` path when given), calls `diagnose()`, and
prints the formatted report. Exit 0 when computed, 1 only when the baseline
(or the current graph/state) cannot be loaded. No progress-store writes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..dispatch import Command, CommandResult, Context, Kind, Registry

# Re-exported so existing `from ...commands.impact import BaselineUnavailable`
# imports keep working; the class itself lives in the deep module.
from ..graph.impact import BaselineUnavailable


def graph_impact(ctx: Context) -> CommandResult:
    """Compare the working tree against its baseline; exit 0 when computed."""
    root = ctx.root
    baseline_opt = getattr(ctx.args, "baseline", None)
    from_ref = getattr(ctx.args, "from_ref", "HEAD")

    from ..context import load_context_lenient
    from ..graph.edges import EdgeLoadError
    from ..graph.impact import (
        GitBaselineSource,
        PathBaselineSource,
        diagnose,
        format_report,
    )
    from ..graph.nodes import NodeLoadError
    from ..graph.state import ProgressStoreError

    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"graph impact: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if baseline_opt is not None:
        source: GitBaselineSource | PathBaselineSource = PathBaselineSource(
            Path(baseline_opt)
        )
    else:
        source = GitBaselineSource(root, from_ref)

    try:
        outcome = diagnose(
            joined,
            source,
            root=root,
            minutes=getattr(ctx.args, "minutes", 60),
        )
    except BaselineUnavailable as exc:
        print(f"graph impact: FAILED — baseline unavailable: {exc}")
        return CommandResult(exit_code=1)

    for line in format_report(outcome.report, outcome.baseline_label):
        print(line)
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="graph impact",
            kind=Kind.READ_ONLY,
            handler=graph_impact,
            help="Advisory: what a curriculum edit would change (flips, rec diffs, dangling refs, no-op edges).",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `graph impact` parser (issue #207 contract).

    Co-located owner of the `graph impact` argparse surface (issue #207
    contract: sole source of CLI flags and help text). The builder creates
    the `graph` parent itself, so any other command under `graph` must reuse
    it.
    """
    graph_parser = subparsers.add_parser(
        "graph", help="Graph diagnostics (impact)."
    )
    graph_commands = graph_parser.add_subparsers(dest="_graph_cmd", metavar="<command>")
    graph_commands.required = True
    impact_parser = graph_commands.add_parser(
        "impact",
        help="Advisory: what a curriculum edit would change (flips, rec diffs, dangling refs, no-op edges).",
    )
    impact_parser.add_argument(
        "--from",
        dest="from_ref",
        default="HEAD",
        help="Git ref to use as the baseline (default: HEAD).",
    )
    impact_parser.add_argument(
        "--baseline",
        default=None,
        metavar="PATH",
        help="Path to a second checkout to use as the baseline instead of a git ref.",
    )
    impact_parser.add_argument(
        "--minutes",
        type=int,
        default=60,
        help="Minutes available this session, used by the recommendation diff (default: 60).",
    )
    impact_parser.set_defaults(_command_name="graph impact")
