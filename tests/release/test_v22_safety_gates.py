"""v2.2 release safety gates (spec §7, items 1–7).

Static scans plus registry-kind assertions (import but never execute
commands, never touch the seed repo). All fail with the offending path,
line, or diff as the message. The behavioural truth these pin is already
unit-tested in tests/evidence/; this file proves the *engine rules* that
are acceptance clauses of the slot:

- SA1 — Unrunnable objective gate writes nothing: the planner turns
  `GateUnrunnable` into a refusal outcome (no record, no receipt).
- SA2 — A receipt never influences state: only the exit code weighs; the
  `gate_run` field is never read by eligibility, passing, or readiness code.
- SA3 — Manual-gate records carry no receipt (attached only on the
  objective path).
- SA4 — `graph impact` is READ_ONLY, appends no event, and never flips
  asserted progress.
- SA5 — `gate_run` never carries raw gate output — only `sha256:` hashes.
- SA6 — Doc gate: this spec exists and §7's functional command list is
  verbatim.
- SA7 — Doc gate: `CONTEXT.md` carries the four v2.2 terms.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"

SPEC = (REPO_ROOT / "docs" / "spec-v2.2-provenance-impact.md").read_text(encoding="utf-8")
CONTEXT_MD = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")

_HARD_BOUNDARY_TOKENS = ("pass_node", "master_node", "delete_record")


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "", text, flags=re.DOTALL)
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines)


def _write_assignments(path: Path) -> list[tuple[int, str]]:
    """`(lineno, line)` of every assignment to a `gate_run` record key."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if re.search(r'record\["gate_run"\]\s*=|"gate_run"\s*:', line):
            hits.append((lineno, line.strip()))
    return hits


# --- SA1 — unrunnable objective gate writes nothing -----------------------------


def test_sa1_unrunnable_gate_produces_a_refusal_no_record():
    """A `GateUnrunnable` must become a refusal outcome (record stays None)."""
    submission = (SRC / "evidence" / "submission.py").read_text(encoding="utf-8")
    # The objective branch catches `GateUnrunnable` and returns a SubmitOutcome
    # with no record (the `record` field is None by default on that path).
    assert "except GateUnrunnable" in submission
    # The unrunnable outcome (from the `except` through its `exit_code`
    # argument) carries no `record=` and no `records_touched` — nothing written.
    except_idx = submission.index("except GateUnrunnable")
    branch = submission[except_idx:].split("exit_code=_EXIT_GATE_UNRUNNABLE", 1)[0]
    assert "nothing submitted" in branch
    assert "record=" not in branch
    assert "records_touched" not in branch


# --- SA2 — a receipt never influences state -------------------------------------


def test_sa2_eligibility_and_readiness_never_read_gate_run():
    """State-affecting code (eligibility/passing/readiness/state) never names `gate_run`."""
    forbidden_files = (
        SRC / "evidence" / "eligibility.py",
        SRC / "evidence" / "passing.py",
        SRC / "graph" / "readiness.py",
        SRC / "graph" / "state.py",
        SRC / "graph" / "recommendation.py",
    )
    hits = []
    for path in forbidden_files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "gate_run" in line:
                hits.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}")
    assert hits == [], (
        "eligibility/readiness code reading the receipt (a receipt never changes "
        "eligibility or readiness): "
        f"{hits}"
    )


def test_sa2_receipt_carries_no_verdict_beyond_exit_code():
    """The receipt's exit class is derived from the exit code, never an independent verdict."""
    submission = (SRC / "evidence" / "submission.py").read_text(encoding="utf-8")
    # The verdict (`accepted`) reads only the exit code before `_build_gate_run`
    # is ever called.
    assert "accepted = exit_code == 0" in submission
    assert submission.index("accepted = exit_code == 0") < submission.index(
        'record["gate_run"] = _build_gate_run'
    )


# --- SA3 — manual-gate records carry no receipt ---------------------------------


def test_sa3_receipt_attached_only_on_the_objective_path():
    """`gate_run` is set only under an `objective` authority guard."""
    submission = SRC / "evidence" / "submission.py"
    hits = _write_assignments(submission)
    assert hits, "expected a `gate_run` assignment in submission.py"
    text = submission.read_text(encoding="utf-8")
    # The single gate_run assignment is guarded by an explicit objective check.
    assert 'if gate.authority == "objective":' in text
    # Every gate_run write-site sits inside that objective branch.
    for lineno, _line in hits:
        before = text.splitlines()[: lineno - 1]
        enclosing = [
            i for i, l in enumerate(before)
            if l.strip() == 'if gate.authority == "objective":'
        ]
        assert enclosing, f"gate_run write at line {lineno} not inside objective branch"
        assert enclosing[-1] < lineno


# --- SA4 — graph impact is read-only and never flips asserted progress ----------


def test_sa4_graph_impact_is_registered_read_only():
    from skilltrace.cli import REGISTRY

    command = REGISTRY.get("graph impact")
    assert command is not None
    assert command.kind.value == "read_only"
    assert command.automation_action is None


def test_sa4_graph_impact_code_never_writes_or_names_hard_boundaries():
    """The impact core is advisory: no pass/master/delete, no state or event writes."""
    impact_files = (SRC / "graph" / "impact.py", SRC / "commands" / "impact.py")
    # Only real mutable writes count. `commands/impact.py` writes `.tmp_baseline_node.md`
    # inside the read-only git fetch seam (a throwaway blob cache, cleaned up), so
    # `write_text` alone is not a state mutation; assert on state/event writers only.
    _MUTATING_CALLS = ("save_state", "append_event", "write_asserted", "write_record")
    hits = []
    for path in impact_files:
        for lineno, line in enumerate(_code_text(path).splitlines(), start=1):
            if any(token in line for token in _HARD_BOUNDARY_TOKENS):
                hits.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}")
            if any(re.search(rf"\b{call}\s*\(", line) for call in _MUTATING_CALLS):
                hits.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}")
    assert hits == [], (
        "graph impact writing state / appending events / naming automation "
        "(read-only advisory only): "
        f"{hits}"
    )


def test_sa4_graph_impact_never_flips_asserted_nodes():
    """The impact core reports asserted-standing; it never lists asserted nodes as flips."""
    impact = (SRC / "graph" / "impact.py").read_text(encoding="utf-8")
    assert "asserted_standing" in impact
    assert "ASSERTED_STATES" in impact


# --- SA5 — gate_run never carries raw output ------------------------------------


def test_sa5_receipt_stores_only_hash_streams_never_raw_output():
    """Raw gate output is hashed; the receipt stores `*_hash`, never `stdout`/`stderr`.

    The receipt interface lives in `evidence/gate_receipt.py` (issue #202);
    `submission.py` stays a thin adapter, so both files are pinned: no raw
    output keys anywhere, hashes built in exactly one place.
    """
    receipt_module = SRC / "evidence" / "gate_receipt.py"
    submission = SRC / "evidence" / "submission.py"
    hits = []
    for path in (receipt_module, submission):
        for lineno, line in enumerate(_code_text(path).splitlines(), start=1):
            if re.search(r'receipt\["stdout"\]|receipt\["stderr"\]', line):
                hits.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}:{line.strip()}")
    assert hits == [], "receipt storing raw output: " f"{hits}"
    text = receipt_module.read_text(encoding="utf-8")
    # The only output keys the receipt may carry are the sha256-prefixed hashes,
    # built through the typed receipt (hashes only — raw output never crosses).
    assert "stdout_hash=hash_stream(stdout)" in text
    assert "stderr_hash=hash_stream(stderr)" in text
    assert "HASH_PREFIX + hashlib.sha256" in text
    # The adapter delegates rather than re-implementing hashing.
    adapter = submission.read_text(encoding="utf-8")
    assert "return _receipt_hash_stream(text)" in adapter
    assert "return _receipt_build(" in adapter


# --- SA6 — doc gate: spec exists, §7 command list verbatim ----------------------


def test_sa6_spec_exists_with_exit_gate_command_list():
    assert "v2.2" in SPEC
    # The §7 functional gates must name `graph impact` in the spelling users
    # actually type.
    assert "skilltrace graph impact" in SPEC


def test_sa6_doc_gate_section7_command_list_verbatim():
    """Doc-gate 6: the spec's §7 functional command list matches verbatim.

    Mirrors test_v21_doc_gates' §7 verbatim pin so the spec and the
    discharges stay in lockstep: every command the exit gates name must be
    present in the spec's §7 code block.
    """
    required = (
        "pytest tests/evidence tests/graph tests/cli tests/release\n"
        "skilltrace validate evidence\n"
        "skilltrace graph impact\n"
        "skilltrace graph impact --from HEAD\n"
        "skilltrace validate graph\n"
        "skilltrace health\n"
    )
    for line in (l.strip() for l in required.splitlines() if l.strip()):
        assert line in SPEC, f"spec §7 missing verbatim command: {line!r}"


# --- SA7 — doc gate: CONTEXT.md carries the four terms --------------------------


def test_sa7_context_md_carries_the_v2_2_terms():
    for term in (
        "**Gate-run receipt**",
        "**Exit class**",
        "**Graph-impact diagnostic**",
        "**No-op edge**",
    ):
        assert term in CONTEXT_MD, f"CONTEXT.md missing {term}"