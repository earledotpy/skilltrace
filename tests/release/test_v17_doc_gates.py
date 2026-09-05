"""v1.7 release doc gates (spec §9.3).

- DG1 — the spec's exit-gates section lists every gate command and assertion.
- DG2 — CONTEXT.md carries the six v1.7 glossary terms (§10).

Substring matches (not byte-identical diffs) so formatting drift does not
fail the gate; only a missing command or term does.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# E1 functional gates (§9.1): eight commands, run against the seed repo.
_E1_COMMANDS = (
    "pytest tests/resources tests/policy tests/cli tests/release",
    "skilltrace validate policy",
    "skilltrace validate resources",
    "skilltrace check-resource <seed-resource-id>",
    "skilltrace verify-resource <seed-resource-id> --check-url",
    "skilltrace replace-resource <broken-resource-id> <candidate-resource-id> --dry-run",
    "skilltrace replace-resource <broken-resource-id> <candidate-resource-id>",
    "skilltrace resource-report",
    "skilltrace health",
)

_E2_LABELS = ("SA1", "SA2", "SA3", "SA4", "SA5", "SA6")

# §10 glossary additions.
_V17_TERMS = (
    "Resource verification",
    "Web check",
    "Retired resource",
    "Replacement candidate",
    "Replacement",
    "broken marker",
)


def test_dg1_spec_exit_gates_section_lists_every_gate():
    """Spec §9 names all E1 commands and all six E2 assertion labels."""
    text = (REPO_ROOT / "docs" / "spec-v1.7-resource-web-verification.md").read_text(
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


def test_dg2_context_contains_all_six_v17_terms():
    """CONTEXT.md defines every §10 term introduced by v1.7."""
    text = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
    missing = [term for term in _V17_TERMS if term not in text]
    assert not missing, f"CONTEXT.md is missing v1.7 terms: {missing}"