"""v2.1 release doc gates (spec §7 DG-6/DG-7, T-Spec).

- DG1 — the spec exists and §7 lists every functional gate command.
- DG2 — CONTEXT.md still carries the Memory state / Retention confidence /
  Retention suggestion terms.

Substring matches (not byte-identical diffs) so formatting drift does not
fail the gate; only a missing command or term does.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_SPEC = REPO_ROOT / "docs" / "spec-v2.1-adaptive-sequencing.md"

# §7 functional gates, verbatim from the spec.
_FUNCTIONAL_GATES = (
    "pytest tests/policy",
    "skilltrace validate policy",
    "skilltrace retention status",
    "skilltrace suggest reviews",
    "skilltrace next --minutes 60",
    "skilltrace today",
    "skilltrace export sqlite",
    "skilltrace health",
)

_GLOSSARY_TERMS = (
    "Memory state",
    "Retention confidence",
    "Retention suggestion",
)


def test_spec_exists_and_lists_every_functional_gate():
    text = _SPEC.read_text(encoding="utf-8")
    missing = [cmd for cmd in _FUNCTIONAL_GATES if cmd not in text]
    assert not missing, "spec §7 is missing functional gate commands: " f"{missing}"


def test_spec_carries_safety_assertion_labels():
    text = _SPEC.read_text(encoding="utf-8")
    for label in ("Schema frozen", "Engine never reads", "calendar block"):
        assert label in text, f"spec §7 is missing safety-gate label: {label!r}"


def test_context_still_carries_retention_glossary_terms():
    text = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
    missing = [term for term in _GLOSSARY_TERMS if term not in text]
    assert not missing, "CONTEXT.md is missing retention glossary terms: " f"{missing}"