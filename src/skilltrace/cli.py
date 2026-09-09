"""`skilltrace` command-line entry point.

Builds the argparse surface, resolves the repo root, and hands the parsed
command to the dispatcher (which owns audit logging and the automation
boundary). The full surface is pinned by tests/cli — graph (`validate`,
`sync`, `next`), evidence (`evidence submit`, `attempt record`,
`eligibility`, `pass`, `master`), execution (`start`, `work`, `session
close`, blockers/remediation/reviews), policy (`validate policy`,
`check-automation`, `suggest`), data-out (`export markdown`,
`export sqlite`, `backup`), and the cross-layer roll-up (`health`). Top-level
aliases `submit` and `close` wrap `evidence submit` and `session close`
respectively, sharing the same handler and `_command_name`, as does `ui` for
`serve` (the Tier 1 local web UI, ADR 0006); the `st`
console-script entry point (see `pyproject.toml`) is a second name for this
same `main`.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Callable

from .commands import register_all
from .dispatch import Context, Registry, dispatch
from .paths import find_root
from .web.server import DEFAULT_PORT

# The process-wide command registry. Handlers are placeholders in this issue;
# the dispatcher contract they exercise is final.
REGISTRY: Registry = register_all(Registry())


def _add_evidence_submit_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach `evidence submit`'s arguments to `parser`.

    Shared by the canonical `evidence submit` parser and the top-level
    `submit` alias so the two stay in lockstep.
    """
    parser.add_argument("node_id", help="Node the evidence is submitted against.")
    parser.add_argument(
        "--spec", default=None, help="Artifact spec id (optional when the node has exactly one)."
    )
    parser.add_argument(
        "--location", required=True, help="Repo-relative path or URL of the artifact."
    )
    parser.add_argument("--note", default=None, help="Optional note attached to the record.")
    verdict = parser.add_mutually_exclusive_group()
    verdict.add_argument(
        "--accept", action="store_true", help="Manual-gate verdict: accept (refused on objective nodes)."
    )
    verdict.add_argument(
        "--reject", action="store_true", help="Manual-gate verdict: reject (refused on objective nodes)."
    )
    parser.add_argument(
        "--supersedes", default=None, help="Evidence record id this submission corrects."
    )
    parser.add_argument(
        "--reason", default=None, help="Why the correction supersedes (required with --supersedes)."
    )


def _add_session_close_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach `session close`'s arguments to `parser` (canonical + `close` alias)."""
    parser.add_argument(
        "--end",
        default=None,
        help="Honest end timestamp for a forgotten session (after start, not in the future).",
    )


def _add_serve_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach `serve`'s arguments to `parser` (canonical + `ui` alias)."""
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Loopback port to serve on (fails fast if already in use).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser at the served URL.",
    )


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
        help="Validate the policy seed files (boundary agreement, structural shape).",
    )
    policy_parser.set_defaults(_command_name="validate policy")
    resources_parser = validate_targets.add_parser(
        "resources",
        help="Validate the resource registry (slug IDs, URL-or-path, node links).",
    )
    resources_parser.set_defaults(_command_name="validate resources")

    # health
    health_parser = subcommands.add_parser(
        "health",
        help="Roll up the five validate targets plus liveness facts (read-only).",
    )
    health_parser.set_defaults(_command_name="health")

    # node <node_id>
    node_parser = subcommands.add_parser(
        "node", help="Show the Mentor-voice detail view for one node."
    )
    node_parser.add_argument("node_id", help="Node to show the detail view for.")
    node_parser.set_defaults(_command_name="node")

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
    _add_evidence_submit_arguments(submit_parser)
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
    _add_session_close_arguments(close_parser)
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

    # verify-resource <resource_id> [--broken --reason ...]
    verify_resource_parser = subcommands.add_parser(
        "verify-resource",
        help="Record a resource verification (success by default; --broken with --reason for a failed check).",
    )
    verify_resource_parser.add_argument(
        "resource_id", help="Resource whose URL and claims were checked."
    )
    verify_resource_parser.add_argument(
        "--broken",
        action="store_true",
        help="Record a failed check (the dated broken marker) instead of a verification; requires --reason.",
    )
    verify_resource_parser.add_argument(
        "--reason",
        default=None,
        help="Why the resource is broken (required with --broken).",
    )
    verify_resource_parser.add_argument(
        "--check-url",
        action="store_true",
        help="Run automated URL preflight check before recording (records broken on failure; never sets last_verified).",
    )
    verify_resource_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string for --check-url.",
    )
    verify_resource_parser.set_defaults(_command_name="verify-resource")

    # check-resource <resource_id> [--timeout N] [--method HEAD|GET] [--follow-redirects] [--user-agent UA]
    check_resource_parser = subcommands.add_parser(
        "check-resource",
        help="Check reachability of a single resource's URL (read-only, exits 0 on answered check).",
    )
    check_resource_parser.add_argument(
        "resource_id", help="Resource whose URL to check."
    )
    check_resource_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method to use (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string.",
    )
    check_resource_parser.set_defaults(_command_name="check-resource")

    # check-resources [--all | --stale-only] [--timeout N] [--method HEAD|GET] [--follow-redirects] [--user-agent UA]
    check_resources_parser = subcommands.add_parser(
        "check-resources",
        help="Check reachability of all (or stale-only) resource URLs (read-only, exits 0 on answered sweep).",
    )
    selector = check_resources_parser.add_mutually_exclusive_group()
    selector.add_argument(
        "--all",
        action="store_true",
        help="Check every resource (the default when no selector is given).",
    )
    selector.add_argument(
        "--stale-only",
        action="store_true",
        help="Check only resources whose derived status is stale under the policy window.",
    )
    check_resources_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method to use (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string.",
    )
    check_resources_parser.set_defaults(_command_name="check-resources")

    # replace-resource <broken_id> <candidate_id> [--dry-run]
    replace_resource_parser = subcommands.add_parser(
        "replace-resource",
        help="Retire an ailing resource and transfer its coverage to an active verified candidate.",
    )
    replace_resource_parser.add_argument(
        "broken_id", help="Resource ID of the broken or stale resource to retire."
    )
    replace_resource_parser.add_argument(
        "candidate_id", help="Resource ID of the verified replacement candidate."
    )
    replace_resource_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and output planned changes as JSON without writing.",
    )
    replace_resource_parser.set_defaults(_command_name="replace-resource")

    # resource-report (whole-registry verification status snapshot)
    resource_report_parser = subcommands.add_parser(
        "resource-report",
        help="Report every resource's derived verification status (always exit 0, read-only).",
    )
    resource_report_parser.set_defaults(_command_name="resource-report")

    # report <target>
    report_parser = subcommands.add_parser(
        "report", help="Generate learning and diagnostic reports."
    )
    report_targets = report_parser.add_subparsers(dest="_report_target", metavar="<target>")
    report_targets.required = True

    report_progress_parser = report_targets.add_parser(
        "progress", help="Curriculum progress and track completion roll-up."
    )
    report_progress_parser.set_defaults(_command_name="report progress")

    report_blockers_parser = report_targets.add_parser(
        "blockers", help="Obstacles, open remediation, and rescue nodes."
    )
    report_blockers_parser.set_defaults(_command_name="report blockers")

    report_reviews_parser = report_targets.add_parser(
        "reviews", help="Retention checks, overdue reviews, and mastery candidates."
    )
    report_reviews_parser.set_defaults(_command_name="report reviews")

    report_evidence_parser = report_targets.add_parser(
        "evidence", help="Proof trail audit, gates, specs, and supersession chains."
    )
    report_evidence_parser.add_argument(
        "--node-id",
        default=None,
        help="Optional node ID to filter evidence trail.",
    )
    report_evidence_parser.set_defaults(_command_name="report evidence")

    report_resources_parser = report_targets.add_parser(
        "resources", help="Resource verification status snapshot."
    )
    report_resources_parser.set_defaults(_command_name="report resources")

    # export <target>
    export_parser = subcommands.add_parser(
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

    # backup
    backup_parser = subcommands.add_parser(
        "backup",
        help="Zip graph/evidence/execution/policy/release into a timestamped archive under backups/.",
    )
    backup_parser.set_defaults(_command_name="backup")

    # serve / ui — Tier 1 local web UI (ADR 0006). Loopback-only, foreground;
    # READ_ONLY in the registry, so it appends no audit event itself. The `ui`
    # alias shares the canonical registration via `_command_name`, like
    # `close` -> `session close`.
    serve_parser = subcommands.add_parser(
        "serve", help="Run the local web UI on loopback (foreground; read-only)."
    )
    _add_serve_arguments(serve_parser)
    serve_parser.set_defaults(_command_name="serve")

    ui_alias_parser = subcommands.add_parser("ui", help="Alias for `serve`.")
    _add_serve_arguments(ui_alias_parser)
    ui_alias_parser.set_defaults(_command_name="serve")

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

    # today
    today_parser = subcommands.add_parser(
        "today", help="Show the Mentor-voice daily study view (read-only)."
    )
    today_parser.add_argument(
        "--minutes",
        type=int,
        default=30,
        help="Minutes available this session, used to size the top recommendation.",
    )
    today_parser.set_defaults(_command_name="today")

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

    # analytics <command> — v1.6 event-log analytics (issue #128).
    # `analytics` with no subcommand renders the umbrella (all four themes);
    # per-theme subcommands share the same shared flags.
    analytics_parser = subcommands.add_parser(
        "analytics", help="Event-log analytics (velocity, blockers, reviews, evidence)."
    )
    analytics_parser.set_defaults(_command_name="analytics")
    analytics_commands = analytics_parser.add_subparsers(
        dest="_analytics_cmd", metavar="<command>"
    )
    analytics_commands.required = False  # bare `analytics` is the umbrella

    def _add_analytics_shared_arguments(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--days",
            type=int,
            default=None,
            metavar="N",
            help="Rolling window in days (default from policy/analytics.yaml).",
        )
        p.add_argument(
            "--group-by",
            default=None,
            choices=["prefix", "track"],
            metavar="<prefix|track>",
            help="Grouping dimension (default from policy/analytics.yaml).",
        )
        p.add_argument(
            "--state",
            action="append",
            default=None,
            metavar="STATE",
            help="Filter by node state (repeatable; OR semantics): active, passed, mastered, locked, available.",
        )

    _add_analytics_shared_arguments(analytics_parser)

    analytics_velocity_parser = analytics_commands.add_parser(
        "velocity", help="Study-velocity analytics: session cadence and node progress."
    )
    _add_analytics_shared_arguments(analytics_velocity_parser)
    analytics_velocity_parser.set_defaults(_command_name="analytics velocity")

    analytics_blockers_parser = analytics_commands.add_parser(
        "blockers", help="Blocker analytics: active stuckness grouped by domain or track."
    )
    _add_analytics_shared_arguments(analytics_blockers_parser)
    analytics_blockers_parser.set_defaults(_command_name="analytics blockers")

    analytics_reviews_parser = analytics_commands.add_parser(
        "reviews", help="Review analytics: completion rate and overdue highlighting."
    )
    _add_analytics_shared_arguments(analytics_reviews_parser)
    analytics_reviews_parser.set_defaults(_command_name="analytics reviews")

    analytics_evidence_parser = analytics_commands.add_parser(
        "evidence", help="Evidence-coverage analytics: per-node gap analysis."
    )
    _add_analytics_shared_arguments(analytics_evidence_parser)
    analytics_evidence_parser.set_defaults(_command_name="analytics evidence")

    analytics_export_parser = analytics_commands.add_parser(
        "export",
        help="Export analytics as Markdown, HTML, or JSON.",
    )
    _add_analytics_shared_arguments(analytics_export_parser)
    analytics_export_parser.add_argument(
        "--theme",
        default=None,
        choices=["all", "velocity", "blockers", "reviews", "evidence"],
        metavar="<all|velocity|blockers|reviews|evidence>",
        help="Theme to export (default: all).",
    )
    analytics_export_parser.add_argument(
        "--format",
        default=None,
        choices=["md", "html", "json"],
        metavar="<md|html|json>",
        help="Output format (default: md).",
    )
    analytics_export_parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Output path override (use - for stdout; default: data/analytics-report-<theme>.<ext>).",
    )
    analytics_export_parser.set_defaults(_command_name="analytics export")

    # retention <command> — Tier 2 retention overlay (read-only).
    retention_parser = subcommands.add_parser(
        "retention", help="Retention model commands (status)."
    )
    retention_commands = retention_parser.add_subparsers(
        dest="_retention_cmd", metavar="<command>"
    )
    retention_commands.required = True
    retention_status_parser = retention_commands.add_parser(
        "status",
        help="Show the retention model's memory state for passed/mastered nodes (or one).",
    )
    retention_status_parser.add_argument(
        "--node-id",
        default=None,
        help="Optional single node id to show retention state for.",
    )
    # graph <command> — v2.2 read-only curriculum-edit advisory. The `impact`
    # subcommand compares the working tree against a git-ref (or path) baseline;
    # it is READ_ONLY and appends no audit event.
    graph_parser = subcommands.add_parser(
        "graph", help="Graph diagnostics (impact)."
    )
    graph_commands = graph_parser.add_subparsers(
        dest="_graph_cmd", metavar="<command>"
    )
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
    retention_status_parser.set_defaults(_command_name="retention status")

    # portfolio <preview|export> — v2.0 portfolio builder (map #174).
    # `preview` renders to stdout (READ_ONLY); `export` writes the
    # disposable bundle to data/portfolio-<date>/ (MUTATING, one audit event).
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

    portfolio_parser = subcommands.add_parser(
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

    # top-level aliases (resolution of #32: cheap keystroke wins for the
    # most-typed multi-word commands, wired to the same handler and
    # `_command_name` as their canonical form so the audit log records
    # only canonical command names)
    submit_alias_parser = subcommands.add_parser(
        "submit", help="Alias for `evidence submit`."
    )
    _add_evidence_submit_arguments(submit_alias_parser)
    submit_alias_parser.set_defaults(_command_name="evidence submit")

    close_alias_parser = subcommands.add_parser(
        "close", help="Alias for `session close`."
    )
    _add_session_close_arguments(close_alias_parser)
    close_alias_parser.set_defaults(_command_name="session close")

    return parser


def run(
    argv: list[str] | None = None,
    root: Path | str | None = None,
    *,
    clock: Callable[[], datetime] | None = None,
) -> int:
    """Parse `argv`, resolve the root, and dispatch. Returns an exit code.

    `root` (or `--root`) overrides auto-detection; tests pass a temp copy.
    `clock` is an optional wall-clock override threaded through to handlers
    via `Context`; production callers leave it at the default.
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

    return dispatch(command, Context(root=resolved_root, args=args, clock=clock))


def main() -> None:
    """Console-script entry point."""
    import io
    import sys

    # Ensure UTF-8 output on Windows consoles (cp1252 default) so em dashes
    # and other Unicode characters render correctly.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(run())
