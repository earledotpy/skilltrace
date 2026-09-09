"""Release gates pinning v2.2's documentation obligations.

Spec-v2.2 §6: the four new terms land in `CONTEXT.md` in the same change as
the receipts + diagnostic (Working convention: when a domain term is added,
update `CONTEXT.md` in the same change); the roadmap's Shipped section gains
an append-only v2.2.0 line. The safety gates in test_v22_safety_gates.py
cover the engine rules; this file only proves the docs moved with them.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CONTEXT_MD = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
ROADMAP_MD = (REPO_ROOT / "docs" / "POST_V2_ROADMAP.md").read_text(encoding="utf-8")


def test_context_md_defines_gate_run_receipt():
    assert "**Gate-run receipt**" in CONTEXT_MD


def test_context_md_defines_exit_class():
    assert "**Exit class**" in CONTEXT_MD


def test_context_md_defines_graph_impact_diagnostic():
    assert "**Graph-impact diagnostic**" in CONTEXT_MD


def test_context_md_defines_no_op_edge():
    assert "**No-op edge**" in CONTEXT_MD


def test_receipt_glossary_entries_stay_definition_only():
    # Glossary rule: CONTEXT.md carries definitions, not implementation
    # details. The provenance entries must not name modules, commands, or
    # file paths.
    for term in ("Gate-run receipt", "Exit class", "Graph-impact diagnostic", "No-op edge"):
        start = CONTEXT_MD.index(f"**{term}**")
        end = CONTEXT_MD.find("\n**", start + 1)
        if end == -1:
            end = len(CONTEXT_MD)
        body = CONTEXT_MD[start:end]
        forbidden = ("src/", ".py", "compute_impact", "gate_run", "--from")
        assert not any(bad in body for bad in forbidden), term


def test_roadmap_shipped_gains_v2_2_0_line():
    assert "- **v2.2.0**" in ROADMAP_MD
