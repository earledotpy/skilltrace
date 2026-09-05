"""v1.6 release doc gates (spec §9.3, T-Exit #132).

- DG1 — the spec's exit-gates section lists every gate command and assertion.
- DG2 — CONTEXT.md carries the six v1.6 glossary terms (§10).

Substring matches (not byte-identical diffs) so formatting drift does not
fail the gate; only a missing command or term does.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# E1 functional gates (§9.1): eleven commands, run against the seed repo.
_E1_COMMANDS = (
    "pytest tests/analytics tests/policy tests/cli tests/web",
    "skilltrace validate policy",
    "skilltrace analytics",
    "skilltrace analytics velocity",
    "skilltrace analytics blockers",
    "skilltrace analytics reviews",
    "skilltrace analytics evidence",
    "skilltrace analytics export --theme velocity --format md",
    "skilltrace analytics export --theme velocity --format html",
    "skilltrace analytics export --theme velocity --format json",
    "skilltrace today",
)

_E2_LABELS = ("SA1", "SA2", "SA3", "SA4")

# §10 glossary additions.
_V16_TERMS = (
    "Study velocity",
    "Blockers by domain",
    "Review completion",
    "Evidence coverage",
    "Rolling window",
    "Soft data threshold",
)


def test_dg1_spec_exit_gates_section_lists_every_gate():
    """Spec §9 names all eleven E1 commands and all four E2 assertion labels."""
    text = (REPO_ROOT / "docs" / "spec-v1.6-event-log-analytics.md").read_text(
        encoding="utf-8"
    )
    assert "## 9" in text, "spec is missing its §9 exit-gates section"
    missing_commands = [cmd for cmd in _E1_COMMANDS if cmd not in text]
    assert not missing_commands, (
        "spec §9 is missing gate commands: " f"{missing_commands}"
    )
    missing_labels = [label for label in _E2_LABELS if label not in text]
    assert not missing_labels, (
        "spec §9 is missing safety-assertion labels: " f"{missing_labels}"
    )


def test_dg2_context_contains_all_six_v16_terms():
    """CONTEXT.md defines every §10 term introduced by v1.6."""
    text = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
    missing = [term for term in _V16_TERMS if term not in text]
    assert not missing, f"CONTEXT.md is missing v1.6 terms: {missing}"
