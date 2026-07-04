"""`skilltrace` command-line entry point.

Builds the argparse surface, resolves the repo root, and hands the parsed
command to the dispatcher (which owns audit logging and the automation
boundary). The surface is `validate graph`, `validate evidence`, `sync`,
`evidence submit`, `attempt record`, `eligibility`, and `next`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .commands import register_all
from .dispatch import Context, Registry, dispatch
from .paths import find_root

# The process-wide command registry. Handlers are placeholders in this issue;
# the dispatcher contract they exercise is final.
REGISTRY: Registry = register_all(Registry())


def build_parser() -> argparse.ArgumentParser:
    """Construct the full `skilltrace` argument parser.

    Command names are attached as `_command_name` defaults matching the registry
    keys, so `run` can look the command up without re-deriving it from argparse
    internals.
    """
    parser = argparse.ArgumentParser(
        prog="skilltrace",
        description="Local-first, CLI-first, single-learner learning engine.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="SkillTrace repo root (default: auto-detect from the working directory).",
    )

    # Routing dests are underscore-prefixed so they are treated as plumbing and
    # excluded from audit-event args (see dispatch._event_args).
    subcommands = parser.add_subparsers(dest="_command", metavar="<command>")
    subcommands.required = True

    # validate <target>
    validate_parser = subcommands.add_parser(
        "validate", help="Validate a layer of the repository."
    )
    validate_targets = validate_parser.add_subparsers(dest="_target", metavar="<target>")
    validate_targets.required = True
    graph_parser = validate_targets.add_parser(
        "graph", help="Validate the skill graph (nodes, edges, cycles)."
    )
    graph_parser.set_defaults(_command_name="validate graph")
    evidence_parser = validate_targets.add_parser(
        "evidence",
        help="Validate the evidence trail (specs, gates, records, attempts).",
    )
    evidence_parser.set_defaults(_command_name="validate evidence")

    # sync
    sync_parser = subcommands.add_parser(
        "sync", help="Recompute derived readiness (locked/available) for every node."
    )
    sync_parser.set_defaults(_command_name="sync")

    # evidence <command>
    evidence_parser = subcommands.add_parser(
        "evidence", help="Evidence-trail commands (submit)."
    )
    evidence_commands = evidence_parser.add_subparsers(dest="_evidence_cmd", metavar="<command>")
    evidence_commands.required = True
    submit_parser = evidence_commands.add_parser(
        "submit", help="Submit one item of evidence against a node (judged at submission)."
    )
    submit_parser.add_argument("node_id", help="Node the evidence is submitted against.")
    submit_parser.add_argument(
        "--spec", default=None, help="Artifact spec id (optional when the node has exactly one)."
    )
    submit_parser.add_argument(
        "--location", required=True, help="Repo-relative path or URL of the artifact."
    )
    submit_parser.add_argument("--note", default=None, help="Optional note attached to the record.")
    verdict = submit_parser.add_mutually_exclusive_group()
    verdict.add_argument(
        "--accept", action="store_true", help="Manual-gate verdict: accept (refused on objective nodes)."
    )
    verdict.add_argument(
        "--reject", action="store_true", help="Manual-gate verdict: reject (refused on objective nodes)."
    )
    submit_parser.add_argument(
        "--supersedes", default=None, help="Evidence record id this submission corrects."
    )
    submit_parser.add_argument(
        "--reason", default=None, help="Why the correction supersedes (required with --supersedes)."
    )
    submit_parser.set_defaults(_command_name="evidence submit")

    # attempt <command>
    attempt_parser = subcommands.add_parser(
        "attempt", help="Assessment-attempt commands (record)."
    )
    attempt_commands = attempt_parser.add_subparsers(dest="_attempt_cmd", metavar="<command>")
    attempt_commands.required = True
    record_parser = attempt_commands.add_parser(
        "record", help="Record one assessment attempt (passed/failed) as an immutable fact."
    )
    record_parser.add_argument("node_id", help="Node the attempt was against.")
    record_parser.add_argument(
        "--outcome", required=True, help="Attempt outcome: passed or failed."
    )
    record_parser.add_argument("--note", default=None, help="Optional note attached to the attempt.")
    record_parser.set_defaults(_command_name="attempt record")

    # eligibility <node_id>
    eligibility_parser = subcommands.add_parser(
        "eligibility",
        help="Report whether a node is pass-eligible, with per-spec counts.",
    )
    eligibility_parser.add_argument("node_id", help="Node to compute pass-eligibility for.")
    eligibility_parser.set_defaults(_command_name="eligibility")

    # next
    next_parser = subcommands.add_parser(
        "next", help="Recommend prerequisite-safe nodes sized to available minutes."
    )
    next_parser.add_argument(
        "--minutes", type=int, default=60, help="Minutes available this session."
    )
    next_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of recommendations."
    )
    next_parser.add_argument(
        "--show-locked",
        action="store_true",
        help="Also show locked nodes (never recommended as available).",
    )
    next_parser.set_defaults(_command_name="next")

    return parser


def run(argv: list[str] | None = None, root: Path | str | None = None) -> int:
    """Parse `argv`, resolve the root, and dispatch. Returns an exit code.

    `root` (or `--root`) overrides auto-detection; tests pass a temp copy.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if root is not None:
        resolved_root = Path(root)
    elif args.root is not None:
        resolved_root = Path(args.root)
    else:
        resolved_root = find_root()

    command = REGISTRY.get(getattr(args, "_command_name", ""))
    if command is None:  # pragma: no cover - guarded by required subparsers
        parser.error("no command selected")

    return dispatch(command, Context(root=resolved_root, args=args))


def main() -> None:
    """Console-script entry point."""
    raise SystemExit(run())
