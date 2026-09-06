"""v2.0 release doc gates (spec §9.3, T-Exit #181).

- DG1 — the spec's exit-gates section lists every gate command and assertion.
- DG2 — CONTEXT.md carries the six v2.0 glossary terms (§10).

Substring matches (not byte-identical diffs) so formatting drift does not
fail the gate; only a missing command or term does.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# E1 functional gates (§9.1): run against the seed repo in order.
_E1_COMMANDS = (
    "pytest tests/portfolio tests/policy tests/cli tests/release",
    "skilltrace validate policy",
    "skilltrace validate graph",
    "skilltrace validate evidence",
    "skilltrace portfolio preview --track portfolio --format markdown",
    "skilltrace portfolio preview --track portfolio --format html",
    "skilltrace portfolio preview --track portfolio --format json",
    "skilltrace portfolio export --track portfolio --format markdown",
    "skilltrace portfolio export --track portfolio --format html",
    "skilltrace portfolio export --track portfolio --format json",
    "skilltrace portfolio export --track portfolio --include-active "
    "--include-rejected --include-superseded --include-paths --include-notes "
    "--include-blockers --include-reviews --include-free-text --include-urls "
    "--format json",
    "skilltrace portfolio export --track portfolio "
    "--node portfolio.project.slope_calculator_01 --format json",
    "skilltrace today",
    "skilltrace health",
)

_E2_LABELS = ("SA1", "SA2", "SA3", "SA4", "SA5", "SA6", "SA7")

# §10 glossary additions.
_V20_TERMS = (
    "Portfolio export",
    "Share profile",
    "Redaction override",
    "Honesty banner",
    "Portfolio bundle",
    "Portfolio preview",
)


def test_dg1_spec_exit_gates_section_lists_every_gate():
    """Spec §9 names all E1 commands and all seven E2 assertion labels."""
    text = (REPO_ROOT / "docs" / "spec-v2.0-portfolio-builder.md").read_text(
        encoding="utf-8"
    )
    assert "Exit gates" in text, "spec is missing its §9 exit-gates section"
    missing_commands = [cmd for cmd in _E1_COMMANDS if cmd not in text]
    assert not missing_commands, (
        "spec §9 is missing gate commands: " f"{missing_commands}"
    )
    missing_labels = [label for label in _E2_LABELS if label not in text]
    assert not missing_labels, (
        "spec §9 is missing safety-assertion labels: " f"{missing_labels}"
    )


def test_dg2_context_contains_all_six_v20_terms():
    """CONTEXT.md defines every §10 term introduced by v2.0."""
    text = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
    missing = [term for term in _V20_TERMS if term not in text]
    assert not missing, f"CONTEXT.md is missing v2.0 terms: {missing}"
