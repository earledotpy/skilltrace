"""v2.1 release safety gates (spec §7, T-Storage-guard).

Static scans (no threading, no seed mutation) that fail with the offending
path or diff as the message.

- SA1 — Schema frozen: `execution/reviews.yaml` (seed matches the snapshot).
- SA2 — Schema frozen: `graph/state.yaml` (seed matches the snapshot).
- SA3 — Engine never reads `data/skilltrace.db` (disposable writer only).
- SA4 — No automated pass/master/undo path (hard-boundary tokens stay in
  explicit paths only).
- SA5 — `suggest reviews` calendar-due block is never reordered (sequencing
  re-ranks `next`/`today` only).
- SA6 — `Review.outcome` stays binary and the advisory v2.1 surfaces never
  write an outcome (advisory-only, no new grade boundary).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"

_HARD_BOUNDARY_TOKENS = ("pass_node", "master_node", "delete_record")

# Mirrors test_v18_safety_gates.py: the only src/ files allowed to name the
# hard-boundary tokens are the execution engine and the two explicit commands.
_SA4_TOKEN_ALLOWLIST = {
    "src/skilltrace/automation.py",
    "src/skilltrace/commands/pass_.py",
    "src/skilltrace/commands/master.py",
    "src/skilltrace/cli.py",
}

# The v2.1 advisory-only surfaces (relative to SRC) must never write outcome.
_V21_ADVISORY_FILES = (
    "commands/retention.py",
    "commands/suggest.py",
    "commands/recommend.py",
    "commands/today.py",
    "policy/agent_input.py",
    "policy/sequencing.py",
    "policy/retention_model.py",
)


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "", text, flags=re.DOTALL)
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines)


# --- SA1 — reviews schema frozen ---------------------------------------------------


def test_sa1_reviews_yaml_schema_frozen():
    """Seed `execution/reviews.yaml` matches the v2.1 key snapshot exactly."""
    snapshot = yaml.safe_load(
        (
            REPO_ROOT / "tests" / "release" / "snapshots" / "reviews_v2_1.yaml"
        ).read_text(encoding="utf-8")
    )
    doc = yaml.safe_load(
        (REPO_ROOT / "execution" / "reviews.yaml").read_text(encoding="utf-8")
    ) or {}
    assert sorted(doc.keys()) == sorted(snapshot["top_level_keys"]), (
        "execution/reviews.yaml top-level drift: " f"{sorted(doc.keys())}"
    )
    for index, record in enumerate(doc.get("reviews") or []):
        record_keys = sorted(k for k in record if record[k] is not None)
        if record_keys != sorted(snapshot["record_keys"]):
            raise AssertionError(
                f"execution/reviews.yaml record[{index}] drift: "
                f"{record_keys} != {sorted(snapshot['record_keys'])}"
            )


# --- SA2 — state schema frozen ------------------------------------------------------------


def test_state_yaml_schema_frozen():
    """Seed `graph/state.yaml` matches the v2.1 key snapshot exactly."""
    snapshot = yaml.safe_load(
        (REPO_ROOT / "tests" / "release" / "snapshots" / "state_v2_1.yaml").read_text(
            encoding="utf-8"
        )
    )
    doc = yaml.safe_load(
        (REPO_ROOT / "graph" / "state.yaml").read_text(encoding="utf-8")
    ) or {}
    assert sorted(doc.keys()) == sorted(snapshot["top_level_keys"]), (
        "graph/state.yaml top-level drift: " f"{sorted(doc.keys())}"
    )
    for node_id, record in (doc.get("progress") or {}).items():
        # `transitions` is optional (only asserted writes record it), so the
        # frozen check is: required keys present, everything within the set.
        allowed = set(snapshot["record_keys"])
        if not {"changed_at", "state"} <= set(record.keys()) <= allowed:
            raise AssertionError(
                f"graph/state.yaml entry {node_id!r} drift: "
                f"{sorted(record.keys())} not within {sorted(allowed)}"
            )


# --- SA3 — engine never reads the disposable SQLite mirror ---------------------------


def test_engine_never_reads_skilltrace_db():
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


# --- SA4 — no automated pass/master/undo path ----------------------------------------


def test_hard_boundary_tokens_only_in_explicit_paths():
    """No new src/ file re-names the hard-boundary actions."""
    hits = [
        str(path.relative_to(REPO_ROOT))
        for path in SRC.rglob("*.py")
        if path.relative_to(REPO_ROOT).as_posix() not in _SA4_TOKEN_ALLOWLIST
        and any(token in path.read_text(encoding="utf-8") for token in _HARD_BOUNDARY_TOKENS)
    ]
    assert hits == [], "hard-boundary tokens in an unexpected path: " f"{hits}"


# --- SA5: calendar-due block ordering preserved ---------------------------------------


def test_suggest_reviews_keeps_calendar_before_retention():
    """Sequencing re-ranks `next`/`today` only; the due list order is frozen."""
    code = (SRC / "commands" / "suggest.py").read_text(encoding="utf-8")
    cal = code.find("suggest reviews: Calendar-due reviews")
    ret = code.find("suggest reviews: Retention suggestions")
    assert -1 not in (cal, ret), "suggest reviews must keep both section headers"
    assert cal < ret, (
        "calendar-due must render before the retention section "
        "(G-Authority / T-Exit §5)"
    )


# --- SA-6: binary outcome closed; advisory surfaces never write it ---------------------


def test_advisory_surfaces_never_write_a_review_outcome():
    """The v2.1 advisory code derives/warns; it never assigns ``Review.outcome``."""
    mutations: list[str] = []
    _outcome_assign = re.compile(r'\[\s*"outcome"\s*\]\s*=(?!=)|\.outcome\s*=(?!=)')
    for rel in _V21_ADVISORY_FILES:
        path = (SRC / rel).resolve()
        for lineno, line in enumerate(_code_text(path).splitlines(), start=1):
            if _outcome_assign.search(line):
                mutations.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}")
    assert mutations == [], (
        "advisory-only v2.1 surface writes a Review outcome:\n"
        + "\n".join(mutations)
    )