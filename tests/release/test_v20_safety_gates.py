"""v2.0 release safety gates (spec §9.2 E2, SA1–SA7).

Static scans (plus registry-kind assertions that import but never execute
commands and never touch the seed repo). All fail with the offending diff
or path list as the message.

- SA1 — Event schema frozen (seed events match the v1.7 snapshot).
- SA2 — No new SQLite reader (only the disposable mirror writer reads it).
- SA3 — No automated pass/master/delete (hard-boundary tokens stay in
  explicit paths only).
- SA4 — No network calls in portfolio code (offline-first, ADR 0006).
- SA5 — Redaction-bypass scan (artifact paths funnel via redaction.py).
- SA6 — Audit-event allowlist (only `portfolio export` logs, via dispatch).
- SA7 — Export-never-read-back (nothing reads the disposable bundle).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"
PORTFOLIO = SRC / "portfolio"
PORTFOLIO_COMMAND = SRC / "commands" / "portfolio.py"

_HARD_BOUNDARY_TOKENS = ("pass_node", "master_node", "delete_record")

# Mirrors test_v18_safety_gates.py: the only src/ files naming the tokens.
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

_NETWORK_RES = tuple(
    re.compile(r"\b" + token + r"\b")
    for token in ("urllib", "requests", "http", "aiohttp", "httpx", "socket")
)


def _code_text_no_strings(path: Path) -> str:
    """Code text with quoted string literals removed.

    URL-scheme comparisons (``"http://"``) are data, not network calls —
    stripping literals keeps the offline-first scan import/call-aware.
    """
    code = _code_text(path)
    code = re.sub(r'"[^"\n]*"', '""', code)
    code = re.sub(r"'[^'\n]*'", "''", code)
    return code

_READ_PATTERNS = ("read_text", "read_bytes", "safe_load", "json.load", "open(")


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "", text, flags=re.DOTALL)
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines)


def _portfolio_files() -> list[Path]:
    return sorted(PORTFOLIO.rglob("*.py")) + [PORTFOLIO_COMMAND]


# --- SA1 — Event schema frozen ------------------------------------------------


def test_sa1_event_schema_frozen():
    """Seed execution/events.yaml matches the v1.7 key snapshot exactly."""
    snapshot = yaml.safe_load(
        (
            REPO_ROOT / "tests" / "release" / "snapshots" / "events_v1_7.yaml"
        ).read_text(encoding="utf-8")
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


# --- SA2 — No new SQLite reader -------------------------------------------------


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


# --- SA3 — No automated pass/master/delete --------------------------------------


def test_sa3_hard_boundary_tokens_only_in_explicit_paths():
    """No new src/ code path names pass_node/master_node/delete_record."""
    hits = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(SRC.rglob("*.py"))
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
        for path in sorted(SRC.rglob("*.py"))
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
        for path in sorted(base.rglob("*.py"))
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


# --- SA4 — No network calls in portfolio code --------------------------------------


def test_sa4_no_network_in_portfolio_code():
    """Portfolio code is offline-first: no network imports or calls."""
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for path in _portfolio_files()
        for lineno, line in enumerate(
            _code_text_no_strings(path).splitlines(), start=1
        )
        if any(pattern.search(line) for pattern in _NETWORK_RES)
    ]
    assert hits == [], (
        "network import/call in portfolio code "
        "(offline-first per ADR 0006): "
        f"{hits}"
    )


# --- SA5 — Redaction-bypass static scan ----------------------------------------------


def test_sa5_no_artifact_path_access_bypassing_redaction():
    """Only redaction.py funnels artifact paths; every surface passes through it."""
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for path in _portfolio_files()
        if path != PORTFOLIO / "redaction.py"
        for lineno, line in enumerate(
            _code_text(path).splitlines(), start=1
        )
        if re.search(r"\.location\b", line)
    ]
    assert hits == [], (
        "direct artifact-path access bypassing the redaction module "
        "(funnel via redaction.visible_location/capture_location): "
        f"{hits}"
    )


def test_sa5_redaction_module_owns_the_funnel():
    """The single enforcement module exposes the funnel every surface uses."""
    from skilltrace.portfolio import redaction

    for name in ("visible_location", "capture_location", "bundle_relative",
                 "redact_node_block", "redaction_notices", "REDACTED"):
        assert hasattr(redaction, name), f"redaction.{name} is missing"


def test_sa5_internal_path_field_never_leaves_the_pipeline():
    """``SelectedEvidence.artifact_path`` (post-funnel internal state) is read
    only by the pipeline modules — never by the command layer."""
    allowed = {
        "src/skilltrace/portfolio/models.py",
        "src/skilltrace/portfolio/selection.py",
        "src/skilltrace/portfolio/redaction.py",
        "src/skilltrace/portfolio/export.py",
        "src/skilltrace/portfolio/bundle.py",
    }
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for path in _portfolio_files()
        for lineno, line in enumerate(
            _code_text(path).splitlines(), start=1
        )
        if re.search(r"\.artifact_path\b", line)
        and path.relative_to(REPO_ROOT).as_posix() not in allowed
    ]
    assert hits == [], (
        "internal artifact-path field read outside the pipeline "
        "(command layer must use redacted render output): "
        f"{hits}"
    )


# --- SA6 — Audit-event allowlist -------------------------------------------------------


def test_sa6_portfolio_code_emits_no_events_itself():
    """Portfolio code never writes the event log; the dispatcher owns the event."""
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for path in _portfolio_files()
        for lineno, line in enumerate(
            _code_text(path).splitlines(), start=1
        )
        if "append_event" in line
    ]
    assert hits == [], (
        "portfolio code emitting audit events itself "
        "(only the dispatcher logs, for `portfolio export`): "
        f"{hits}"
    )


def test_sa6_only_portfolio_export_is_mutating():
    """`portfolio preview` is READ_ONLY; `portfolio export` is the one MUTATING kind."""
    from skilltrace.cli import REGISTRY

    preview = REGISTRY.get("portfolio preview")
    export = REGISTRY.get("portfolio export")
    assert preview is not None and preview.kind.value == "read_only"
    assert export is not None and export.kind.value == "mutating"
    assert preview.automation_action is None
    assert export.automation_action is None


# --- SA7 — Export-never-read-back ----------------------------------------------------------


def test_sa7_nothing_reads_the_disposable_bundle():
    """No src/ code reads data/portfolio-*/ or the portfolio outputs as input."""
    artifacts = (
        "portfolio.json",
        "portfolio.md",
        "portfolio.html",
        "manifest.json",
        "portfolio-",
    )
    hits = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}"
        for path in sorted(SRC.rglob("*.py"))
        for lineno, line in enumerate(
            _code_text(path).splitlines(), start=1
        )
        if any(artifact in line for artifact in artifacts)
        and any(pattern in line for pattern in _READ_PATTERNS)
    ]
    assert hits == [], (
        "engine reading the disposable bundle back "
        "(exports are never inputs): "
        f"{hits}"
    )
