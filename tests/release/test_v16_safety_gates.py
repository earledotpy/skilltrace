"""v1.6 release safety gates (spec §9.2, T-Exit #132).

Four static scans. All fail with the offending diff or path list as the
message; none executes commands or touches the seed repo.

- SA1 — Event schema frozen (R1: events are audit-only, never read to
  compute state; analytics derives from the primary execution YAMLs).
- SA2 — No new SQLite reader (Tier 2 precedent: the engine never reads
  ``data/skilltrace.db``; only the disposable mirror writer opens it).
- SA3 — No automated pass/master/delete (Tier 2 precedent: passing,
  mastering, and deleting stay explicit learner commands).
- SA4 — Audit-only events from analytics surfaces (the single permitted
  emission is the dispatcher's event for ``analytics export``).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"

_HARD_BOUNDARY_TOKENS = ("pass_node", "master_node", "delete_record")


# --- SA1 — Event schema frozen --------------------------------------------


def test_sa1_event_schema_frozen():
    """Seed ``execution/events.yaml`` matches the v1.5 key snapshot exactly."""
    snapshot = yaml.safe_load(
        (REPO_ROOT / "tests" / "release" / "snapshots" / "events_v1_5.yaml").read_text(
            encoding="utf-8"
        )
    )
    doc = yaml.safe_load(
        (REPO_ROOT / "execution" / "events.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(doc, dict), f"events.yaml must be a mapping; got {type(doc)}"

    diffs: list[str] = []
    top_keys = sorted(doc.keys())
    if top_keys != sorted(snapshot["top_level_keys"]):
        diffs.append(
            f"top-level keys: expected {sorted(snapshot['top_level_keys'])}, "
            f"got {top_keys}"
        )
    expected_record_keys = sorted(snapshot["record_keys"])
    for index, record in enumerate(doc.get("events") or []):
        record_keys = sorted(record.keys())
        if record_keys != expected_record_keys:
            diffs.append(
                f"record[{index}] keys: expected {expected_record_keys}, "
                f"got {record_keys}"
            )
    assert not diffs, "event schema drift (R1 violation):\n" + "\n".join(diffs)


# --- SA2 — No new SQLite reader ---------------------------------------------


def test_sa2_no_new_sqlite_reader():
    """Only the disposable mirror writer opens ``data/skilltrace.db``.

    NOTE: the spec names the whitelist ``src/skilltrace/export/sqlite_export.py``,
    but the repo carries the writer at ``src/skilltrace/sqlite_export.py``
    (no ``export/`` package exists) — the scan whitelists the actual path.
    """
    whitelist = {"src/skilltrace/sqlite_export.py"}
    paired = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in SRC.rglob("*.py")
        if "sqlite3.connect" in path.read_text(encoding="utf-8")
        and "skilltrace.db" in path.read_text(encoding="utf-8")
    )
    assert paired == sorted(whitelist), (
        "new SQLite reader outside the whitelist "
        f"(engine never reads data/skilltrace.db): {paired}"
    )


# --- SA3 — No automated pass/master/delete ----------------------------------


# The only src/ files permitted to name the hard-boundary actions: the code
# floor itself, the two explicit learner-command handlers (which carry no
# automation_action by construction), and the check-automation help example
# (co-located in its command module since #206; formerly in cli.py).
_SA3_TOKEN_ALLOWLIST = {
    "src/skilltrace/automation.py",
    "src/skilltrace/commands/pass_.py",
    "src/skilltrace/commands/master.py",
    "src/skilltrace/commands/check_automation.py",
}

_CALL_RE = re.compile(r"\b(pass_node|master_node|delete_record)\s*\(")
_AUTOMATION_LABEL_RE = re.compile(
    r'automation_action\s*=\s*["\'](pass_node|master_node|delete_record)["\']'
)


def _readable_py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def test_sa3_hard_boundary_tokens_only_in_explicit_paths():
    """No new src/ code path names ``pass_node``/``master_node``/``delete_record``."""
    hits = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _readable_py_files(SRC)
        if any(token in path.read_text(encoding="utf-8") for token in _HARD_BOUNDARY_TOKENS)
    )
    assert hits == sorted(_SA3_TOKEN_ALLOWLIST), (
        "new code path naming a hard-boundary action "
        "(pass/master/delete stay explicit learner commands): "
        f"{[h for h in hits if h not in _SA3_TOKEN_ALLOWLIST]}"
    )


def test_sa3_no_automation_action_labels_for_hard_boundary():
    """No command carries a hard-boundary action as automatable (src/)."""
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}"
        for path in _readable_py_files(SRC)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _AUTOMATION_LABEL_RE.search(line)
    ]
    assert hits == [], (
        "hard-boundary action registered as automatable "
        "(refused unconditionally by the code floor): "
        f"{hits}"
    )


def test_sa3_no_direct_handler_calls():
    """Nobody calls the asserted writers except through dispatch (src/ + tests/).

    The ``pass``/``master`` commands are explicit learner commands: the CLI
    entry dispatch and the Serve confirmation modals are the only callers,
    and tests reach them through ``cli.run``/``dispatch`` — never by
    invoking the asserted writers as an automated side effect.
    """
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for base in (SRC, REPO_ROOT / "tests")
        for path in _readable_py_files(base)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _CALL_RE.search(line) and not line.strip().startswith("def ")
    ]
    assert hits == [], (
        "direct call of an asserted writer outside dispatch "
        "(no automated pass/master/delete): "
        f"{hits}"
    )


def test_sa3_pass_master_commands_carry_no_automation_action():
    """The registry's ``pass``/``master`` commands are explicit (no label)."""
    from skilltrace.cli import REGISTRY

    for name in ("pass", "master"):
        command = REGISTRY.get(name)
        assert command is not None, f"command {name!r} is not registered"
        assert command.automation_action is None, (
            f"command {name!r} carries automation_action={command.automation_action!r}; "
            "pass/master are explicit learner commands and never consult the boundary"
        )


# --- SA4 — Audit-only events from analytics surfaces -------------------------


def test_sa4_no_direct_event_writes_in_analytics_surfaces():
    """Analytics and Serve never write the event log themselves.

    The single permitted emission is the dispatcher's audit event for the
    MUTATING ``analytics export`` command (CLI export path and the Serve
    ``POST /analytics/export`` route both dispatch that command).
    """
    scopes = [SRC / "analytics", SRC / "commands" / "analytics.py", SRC / "web"]
    hits = []
    for scope in scopes:
        paths = [scope] if scope.is_file() else _readable_py_files(scope)
        hits.extend(
            path.relative_to(REPO_ROOT).as_posix()
            for path in paths
            if "append_event" in path.read_text(encoding="utf-8")
        )
    assert hits == [], (
        "direct event-log write in an analytics surface "
        "(events flow only through the dispatcher): "
        f"{sorted(hits)}"
    )


def test_sa4_analytics_registry_kinds():
    """All analytics query commands are READ_ONLY; only export is MUTATING."""
    from skilltrace.cli import REGISTRY

    for name in (
        "analytics",
        "analytics velocity",
        "analytics blockers",
        "analytics reviews",
        "analytics evidence",
    ):
        command = REGISTRY.get(name)
        assert command is not None, f"command {name!r} is not registered"
        assert command.kind.value == "read_only", (
            f"command {name!r} must be READ_ONLY (emits no event); "
            f"got {command.kind.value}"
        )
    export = REGISTRY.get("analytics export")
    assert export is not None, "command 'analytics export' is not registered"
    assert export.kind.value == "mutating", (
        "command 'analytics export' must be MUTATING "
        f"(exactly one audit event per call); got {export.kind.value}"
    )


def test_sa4_serve_export_delegates_to_the_cli_command():
    """``POST /analytics/export`` nest-dispatches ``analytics export`` (one path)."""
    text = (SRC / "web" / "views.py").read_text(encoding="utf-8")
    assert '"analytics export"' in text, (
        "Serve export route must dispatch the canonical 'analytics export' "
        "command (no second write path)"
    )
