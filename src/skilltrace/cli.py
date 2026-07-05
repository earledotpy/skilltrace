"""`skilltrace` command-line entry point.

Builds the argparse surface, resolves the repo root, and hands the parsed
command to the dispatcher (which owns audit logging and the automation
boundary). The full surface is pinned by tests/cli — graph (`validate`,
`sync`, `next`), evidence (`evidence submit`, `attempt record`,
`eligibility`, `pass`, `master`), execution (`start`, `work`, `session
close`, blockers/remediation/reviews), and policy (`validate policy`,
`check-automation`, `suggest`).
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
    execution_parser = validate_targets.add_parser(
        "execution",
        help="Validate the execution history (sessions, work, blockers, actions, reviews).",
    )
    execution_parser.set_defaults(_command_name="validate execution")
    policy_parser = validate_targets.add_parser(
        "policy",
        help="Validate the policy seed files (six documents, boundary agreement).",
    )
    policy_parser.set_defaults(_command_name="validate policy")
    resources_parser = validate_targets.add_parser(
        "resources",
        help="Validate the resource registry (slug IDs, URL-or-path, node links).",
    )
    resources_parser.set_defaults(_command_name="validate resources")

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
    eligibility_parser.add_argument(
        "--mastery",
        action="store_true",
        help="Compute mastery eligibility (passed + accepted evidence + spaced satisfactory review).",
    )
    eligibility_parser.set_defaults(_command_name="eligibility")

    # pass <node_id>
    pass_parser = subcommands.add_parser(
        "pass",
        help="Assert a node passed (refuses without eligibility or on a locked node).",
    )
    pass_parser.add_argument("node_id", help="Node to assert as passed.")

    # master <node_id>
    master_parser = subcommands.add_parser(
        "master",
        help="Assert a node mastered (refuses without mastery eligibility).",
    )
    master_parser.add_argument("node_id", help="Node to assert as mastered.")
    master_parser.set_defaults(_command_name="master")
    pass_parser.set_defaults(_command_name="pass")

    # start <node_id>
    start_parser = subcommands.add_parser(
        "start",
        help="Open a new session with its first work item on a node.",
    )
    start_parser.add_argument("node_id", help="Node to start working on.")
    start_parser.add_argument(
        "--template",
        default=None,
        help="Optional session template label (e.g. micro/standard/deep).",
    )
    start_parser.set_defaults(_command_name="start")

    # work <node_id>
    work_parser = subcommands.add_parser(
        "work", help="Add a work item for a node to the open session."
    )
    work_parser.add_argument("node_id", help="Node the work item is about.")
    work_parser.add_argument(
        "--blocked",
        action="store_true",
        help="This stint ended stuck (session-scoped observation; requires --notes).",
    )
    work_parser.add_argument("--notes", default=None, help="Notes on the work item.")
    work_parser.add_argument(
        "--minutes", type=int, default=None, help="Optional minutes spent on this item."
    )
    work_parser.set_defaults(_command_name="work")

    # blocker <command>
    blocker_parser = subcommands.add_parser(
        "blocker", help="Blocker commands (create, resolve)."
    )
    blocker_commands = blocker_parser.add_subparsers(dest="_blocker_cmd", metavar="<command>")
    blocker_commands.required = True
    blocker_create = blocker_commands.add_parser(
        "create", help="Record persistent stuckness on a node."
    )
    blocker_create.add_argument("node_id", help="Node the learner is stuck on.")
    blocker_create.add_argument(
        "--description", required=True, help="The obstacle this blocker names."
    )
    blocker_create.set_defaults(_command_name="blocker create")
    blocker_resolve = blocker_commands.add_parser(
        "resolve", help="Resolve an open blocker."
    )
    blocker_resolve.add_argument("blocker_id", help="Blocker to resolve (blk.<node>.NNN).")
    blocker_resolve.add_argument(
        "--summary", required=True, help="How the blocker was resolved."
    )
    blocker_resolve.set_defaults(_command_name="blocker resolve")

    # remediation <command>
    remediation_parser = subcommands.add_parser(
        "remediation", help="Remediation-action commands (create, complete)."
    )
    remediation_commands = remediation_parser.add_subparsers(
        dest="_remediation_cmd", metavar="<command>"
    )
    remediation_commands.required = True
    remediation_create = remediation_commands.add_parser(
        "create", help="Log a deliberate corrective intervention for a node."
    )
    remediation_create.add_argument("node_id", help="Node the intervention targets.")
    remediation_create.add_argument(
        "--description", required=True, help="What the intervention is."
    )
    remediation_create.add_argument(
        "--blocker", default=None, help="Blocker id this action addresses (optional)."
    )
    remediation_create.set_defaults(_command_name="remediation create")
    remediation_complete = remediation_commands.add_parser(
        "complete", help="Complete a remediation action."
    )
    remediation_complete.add_argument("action_id", help="Action to complete (rem.<node>.NNN).")
    remediation_complete.add_argument(
        "--summary", required=True, help="What the intervention produced."
    )
    remediation_complete.set_defaults(_command_name="remediation complete")

    # review <command>
    review_parser = subcommands.add_parser(
        "review", help="Review commands (schedule, complete, cancel)."
    )
    review_commands = review_parser.add_subparsers(dest="_review_cmd", metavar="<command>")
    review_commands.required = True
    review_schedule = review_commands.add_parser(
        "schedule", help="Schedule a retention check on a passed or mastered node."
    )
    review_schedule.add_argument("node_id", help="Node to schedule a review for.")
    review_schedule.add_argument(
        "--date", required=True, help="Date the review is due (YYYY-MM-DD)."
    )
    review_schedule.set_defaults(_command_name="review schedule")
    review_complete = review_commands.add_parser(
        "complete", help="Complete a scheduled review."
    )
    review_complete.add_argument("review_id", help="Review to complete (rev.<node>.NNN).")
    review_complete.add_argument(
        "--outcome", required=True, help="satisfactory or unsatisfactory."
    )
    review_complete.add_argument(
        "--summary", required=True, help="Result summary of the retention check."
    )
    review_complete.set_defaults(_command_name="review complete")
    review_cancel = review_commands.add_parser(
        "cancel", help="Cancel a scheduled review (the record is kept)."
    )
    review_cancel.add_argument("review_id", help="Review to cancel (rev.<node>.NNN).")
    review_cancel.add_argument(
        "--reason", required=True, help="Why the review is cancelled."
    )
    review_cancel.set_defaults(_command_name="review cancel")

    # session <command>
    session_parser = subcommands.add_parser("session", help="Session commands (close).")
    session_commands = session_parser.add_subparsers(dest="_session_cmd", metavar="<command>")
    session_commands.required = True
    close_parser = session_commands.add_parser(
        "close", help="Complete the open session."
    )
    close_parser.add_argument(
        "--end",
        default=None,
        help="Honest end timestamp for a forgotten session (after start, not in the future).",
    )
    close_parser.set_defaults(_command_name="session close")

    # blockers / reviews (read-only listings)
    blockers_parser = subcommands.add_parser("blockers", help="List open blockers.")
    blockers_parser.set_defaults(_command_name="blockers")
    reviews_parser = subcommands.add_parser(
        "reviews", help="List scheduled reviews (overdue derived, never stored)."
    )
    reviews_parser.set_defaults(_command_name="reviews")

    # resources --node-id (per-node reverse index over the resource registry)
    resources_listing_parser = subcommands.add_parser(
        "resources",
        help="List the resources supporting a node (the per-node reverse index).",
    )
    resources_listing_parser.add_argument(
        "--node-id",
        required=True,
        help="Node whose supporting resources to list.",
    )
    resources_listing_parser.set_defaults(_command_name="resources")

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

    # suggest <topic>
    suggest_parser = subcommands.add_parser(
        "suggest", help="Advisory suggestions (remediation, reviews)."
    )
    suggest_topics = suggest_parser.add_subparsers(dest="_suggest_cmd", metavar="<topic>")
    suggest_topics.required = True
    suggest_remediation = suggest_topics.add_parser(
        "remediation",
        help="Suggest corrective work from derived remediation pressure.",
    )
    suggest_remediation.set_defaults(_command_name="suggest remediation")
    suggest_reviews = suggest_topics.add_parser(
        "reviews", help="Suggest the scheduled reviews now due or overdue."
    )
    suggest_reviews.set_defaults(_command_name="suggest reviews")

    # check-automation <action>
    check_parser = subcommands.add_parser(
        "check-automation",
        help="Report whether an action may run on an automated path.",
    )
    check_parser.add_argument(
        "action", help="Automation action label, e.g. pass_node or schedule_review."
    )
    check_parser.set_defaults(_command_name="check-automation")

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
