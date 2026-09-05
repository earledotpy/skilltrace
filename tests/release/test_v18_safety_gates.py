"""v1.8 release safety gates (spec §7 E2, SA1–SA7).

Static scans (plus registry-kind assertions that import but never execute
commands and never touch the seed repo). All fail with the offending diff
or path list as the message.

- SA1 — Event schema frozen (compare with the v1.6 snapshot; only the
  established whitelisted event shape may be added).
- SA2 — No new SQLite reader (only the existing SQLite export reader may
  read `data/skilltrace.db`).
- SA3 — No automated pass/master/delete (new paths never issue
  `pass_node`, `master_node`, or `delete_record`).
- SA4 — Batch check is read-only on registry state.
- SA5 — Marker enrichment is descriptive-only.
- SA6 — Retired WARN is advisory-only.
- SA7 — Mutation and audit whitelist; no scheduler ships.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"

_HARD_BOUNDARY_TOKENS = ("pass_node", "master_node", "delete_record")


# --- SA1 — Event schema frozen -----------------------------------------------


def test_sa1_event_schema_frozen():
    """Seed execution/events.yaml matches the v1.6 key snapshot exactly."""
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
    assert not diffs, "event schema drift (SA1 violation):\n" + "\n".join(diffs)


# --- SA2 — No new SQLite reader ----------------------------------------------


def test_sa2_no_new_sqlite_reader():
    """Only the disposable mirror writer opens data/skilltrace.db."""
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


# --- SA3 — No automated pass/master/delete -----------------------------------


_SA3_TOKEN_ALLOWLIST = {
    "src/skilltrace/automation.py",
    "src/skilltrace/commands/pass_.py",
    "src/skilltrace/commands/master.py",
    "src/skilltrace/cli.py",
}

_CALL_RE = re.compile(r"\b(pass_node|master_node|delete_record)\s*\(")
_AUTOMATION_LABEL_RE = re.compile(
    r'automation_action\s*=\s*["\'](pass_node|master_node|delete_record)["\']'
)


def _readable_py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def test_sa3_hard_boundary_tokens_only_in_explicit_paths():
    """No new src/ code path names pass_node/master_node/delete_record."""
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
    """Nobody calls the asserted writers except through dispatch (src/ + tests/)."""
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
    """The registry's pass/master commands are explicit (no label)."""
    from skilltrace.cli import REGISTRY

    for name in ("pass", "master"):
        command = REGISTRY.get(name)
        assert command is not None, f"command {name!r} is not registered"
        assert command.automation_action is None, (
            f"command {name!r} carries automation_action={command.automation_action!r}; "
            "pass/master are explicit learner commands and never consult the boundary"
        )


# --- SA4 — Batch check is read-only on registry state ------------------------


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "", text, flags=re.DOTALL)
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines)


def test_sa4_batch_helper_never_writes_registry_state():
    """`batch()` never writes, calls record_verification, or touches verified/broken."""
    code = _code_text(SRC / "resources" / "web_check.py")
    forbidden = (
        "append_event",
        "record_verification",
        "last_verified",
        "broken",
    )
    hits = [token for token in forbidden if token in code]
    assert hits == [], (
        "batch/check_url must be read-only on registry state "
        f"(no writes, no record_verification, no last_verified/broken): {hits}"
    )


def test_sa4_check_resources_command_never_writes_registry_state():
    """`check-resources` never writes, sets last_verified, or clears/writes broken."""
    code = _code_text(SRC / "commands" / "check_resources.py")
    forbidden = (
        "append_event",
        "record_verification",
        "last_verified",
        "broken",
    )
    hits = [token for token in forbidden if token in code]
    assert hits == [], (
        "check-resources must be read-only on registry state: "
        f"{hits}"
    )


def test_sa4_check_resources_is_read_only_and_emits_no_event():
    """`check-resources` is registered Kind.READ_ONLY (dispatcher logs nothing)."""
    from skilltrace.cli import REGISTRY

    command = REGISTRY.get("check-resources")
    assert command is not None, "command 'check-resources' is not registered"
    assert command.kind.value == "read_only", (
        f"check-resources must be READ_ONLY; got {command.kind.value}"
    )
    assert command.automation_action is None


# --- SA5 — Marker enrichment is descriptive-only ------------------------------


def test_sa5_writer_adds_at_most_the_two_optional_fields():
    """`record_verification` gains exactly status_code/final_url, keyword-only."""
    from skilltrace.resources.verification import record_verification

    params = inspect.signature(record_verification).parameters
    assert list(params) == [
        "root",
        "resource_id",
        "date",
        "broken_reason",
        "status_code",
        "final_url",
    ], f"record_verification signature drift: {list(params)}"
    for name in ("status_code", "final_url"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert params[name].default is None


def test_sa5_success_path_writes_no_observed_detail():
    """The success branch sets last_verified/clears broken and nothing else."""
    code = _code_text(SRC / "resources" / "verification.py")
    success_branch = code.split("if broken_reason is None:")[1].split("else:")[0]
    assert "status_code" not in success_branch, (
        "success path must not write observed detail: "
        f"{success_branch!r}"
    )
    assert "final_url" not in success_branch, (
        "success path must not write observed detail: "
        f"{success_branch!r}"
    )


def test_sa5_reports_render_enrichment_as_advisory_detail():
    """resource-report names the new fields as display detail (never a verdict)."""
    code = _code_text(SRC / "commands" / "resource_report.py")
    assert "status_code" in code, "resource-report must render status_code detail"
    assert "final_url" in code, "resource-report must render final_url detail"


def test_sa5_human_verify_success_path_unchanged():
    """The human --broken/--reason path stays reason-text only (no new flags)."""
    from skilltrace.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["verify-resource", "some-res", "--broken", "--reason", "x"])
    assert not hasattr(args, "status_code")
    assert not hasattr(args, "final_url")


# --- SA6 — Retired WARN is advisory-only --------------------------------------


def test_sa6_retired_warn_line_is_locked():
    """validation.py carries exactly the locked WARN line (additive delta only)."""
    code = (SRC / "resources" / "validation.py").read_text(encoding="utf-8")
    assert (
        "WARN retired-resource {resource.id} — retired " in code
    ), "locked WARN retired-resource line missing from validation.py"
    assert "preserved as history" in code


def test_sa6_validate_graph_has_no_resources_aware_change():
    """`validate graph` never reads graph/resources.yaml (nodes/edges only)."""
    code = _code_text(SRC / "commands" / "validate.py")
    assert "resources.yaml" not in code, (
        "validate graph must stay resources-unaware"
    )
    assert "load_resources" not in code
    assert "load_and_validate_resources" not in code.split("def validate_graph")[1].split(
        "\ndef "
    )[0]


def test_sa6_retired_handling_touches_no_progress_or_evidence():
    """The retired delta never references asserted progress, edges, or evidence."""
    code = _code_text(SRC / "resources" / "validation.py")
    forbidden = ("state.yaml", "edges.yaml", "last_verified", "evidence", "passed")
    hits = [token for token in forbidden if token in code]
    assert hits == [], (
        f"retired handling must not touch progress/edges/evidence: {hits}"
    )


# --- SA7 — Mutation and audit whitelist; no scheduler -------------------------


def test_sa7_check_report_health_are_read_only():
    """check(-resource(s)), report, and health surfaces are READ_ONLY."""
    from skilltrace.cli import REGISTRY

    for name in (
        "check-resource",
        "check-resources",
        "resource-report",
        "report resources",
        "health",
    ):
        command = REGISTRY.get(name)
        assert command is not None, f"command {name!r} is not registered"
        assert command.kind.value == "read_only", (
            f"command {name!r} must be READ_ONLY; got {command.kind.value}"
        )


def test_sa7_verify_and_replace_kinds_unchanged():
    """verify-resource / replace-resource stay MUTATING (one event on success)."""
    from skilltrace.cli import REGISTRY

    for name in ("verify-resource", "replace-resource"):
        command = REGISTRY.get(name)
        assert command is not None, f"command {name!r} is not registered"
        assert command.kind.value == "mutating", (
            f"command {name!r} must be MUTATING; got {command.kind.value}"
        )


def test_sa7_no_scheduler_ships_on_new_paths():
    """No cron / serve-background / today-hook call site exists on v1.8 paths."""
    scopes = [
        SRC / "resources" / "web_check.py",
        SRC / "resources" / "registry.py",
        SRC / "resources" / "verification.py",
        SRC / "resources" / "validation.py",
        SRC / "commands" / "check_resources.py",
        SRC / "commands" / "check_resource.py",
        SRC / "commands" / "verify_resource.py",
        SRC / "commands" / "resource_report.py",
        SRC / "commands" / "validate.py",
        SRC / "cli.py",
    ]
    forbidden = ("cron", "serve-background", "today-hook", "background task")
    hits = [
        f"{scope.relative_to(REPO_ROOT).as_posix()}: contains {token!r}"
        for scope in scopes
        for token in forbidden
        if token in _code_text(scope).lower()
    ]
    assert hits == [], f"scheduling automation ships on v1.8 paths: {hits}"
