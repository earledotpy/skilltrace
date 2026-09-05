"""v1.8 release doc gates (spec §7 E3).

- DG1 — the spec carries all required sections (§§0–10), every E1 command,
  and every assertion label SA1–SA7 as substrings.
- DG2 — CONTEXT.md carries the §8 term touch (the `Broken marker` line
  names the optional `status_code` and `final_url` fields).

Substring matches (not byte-identical diffs) so formatting drift does not
fail the gate; only a missing section, command, label, or term does.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_SPEC = REPO_ROOT / "docs" / "spec-v1.8-phase2-ml-seed-graph.md"

# E1 functional gates (spec §7.1): the full command list.
_E1_COMMANDS = (
    "pytest tests/resources tests/policy tests/cli",
    "skilltrace validate policy",
    "skilltrace validate graph",
    "skilltrace validate resources",
    "skilltrace check-resource mlcc-crash-course",
    "skilltrace check-resources --all",
    "skilltrace check-resources --stale-only",
    "skilltrace verify-resource mlcc-crash-course --check-url",
    "skilltrace resource-report",
    "skilltrace health",
)

_E2_LABELS = ("SA1", "SA2", "SA3", "SA4", "SA5", "SA6", "SA7")


def test_dg1_spec_has_all_required_sections():
    """The spec carries §§0–10."""
    text = _SPEC.read_text(encoding="utf-8")
    missing = [f"## {n}" for n in range(11) if f"## {n}" not in text]
    assert not missing, f"spec is missing sections: {missing}"


def test_dg1_spec_exit_gates_section_lists_every_gate():
    """Spec §7 names all E1 commands and all seven E2 assertion labels."""
    text = _SPEC.read_text(encoding="utf-8")
    assert "## 7" in text, "spec is missing its §7 exit-gates section"
    missing_commands = [cmd for cmd in _E1_COMMANDS if cmd not in text]
    assert not missing_commands, (
        "spec §7 is missing gate commands: " f"{missing_commands}"
    )
    missing_labels = [label for label in _E2_LABELS if label not in text]
    assert not missing_labels, (
        "spec §7 is missing safety-assertion labels: " f"{missing_labels}"
    )


def test_dg2_context_names_broken_marker_enrichment_fields():
    """CONTEXT.md's Broken marker line names status_code and final_url."""
    text = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
    assert "Broken marker" in text, "CONTEXT.md is missing the Broken marker term"
    assert "status_code" in text, (
        "CONTEXT.md Broken marker line must name the optional status_code field"
    )
    assert "final_url" in text, (
        "CONTEXT.md Broken marker line must name the optional final_url field"
    )
