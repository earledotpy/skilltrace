"""Pipeline-seam tests for the deep portfolio interface (issue #203).

Exercises ``build_portfolio(joined, options)`` as the production pipeline:
selection + share-profile redaction inside, renderers format-only after.
"""

from __future__ import annotations

import datetime

from skilltrace.context import JoinedView, _build_derived
from skilltrace.evidence.evidence import ArtifactSpec, EvidenceRecord
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.state import ProgressEntry, ProgressStore
from skilltrace.portfolio.export import render_json, render_markdown
from skilltrace.portfolio.models import SelectionOptions
from skilltrace.portfolio.pipeline import build_portfolio
from skilltrace.portfolio.redaction import REDACTED

NODE_A = "portfolio.project.slope_calculator_01"
TODAY = datetime.date(2026, 9, 6)


def _node(node_id: str = NODE_A) -> SkillNode:
    return SkillNode(
        id=node_id,
        title=f"Title for {node_id}",
        summary="Summary.",
        domain="testing",
        track="portfolio",
    )


def _spec(spec_id: str, node_id: str) -> ArtifactSpec:
    return ArtifactSpec(
        id=spec_id,
        node_id=node_id,
        title=f"Spec {spec_id}",
        artifact_kind="project",
        required=True,
        minimum_count=1,
    )


def _view() -> JoinedView:
    node = _node()
    spec = _spec("spec.portfolio.project.slope_calculator", node.id)
    record = EvidenceRecord(
        id="ev.001",
        artifact_spec_id=spec.id,
        location="evidence/a.md",
        accepted=True,
        accepted_by="learner_manual",
        artifact_hash="sha256:aaa",
        created_at="2026-08-01",
        note="learner note",
        gate_run={
            "command_argv": ["python", "evidence/check.py"],
            "inputs": ["evidence/a.md"],
            "exit_class": "passed",
        },
    )
    view = JoinedView(
        nodes=[node],
        store=ProgressStore(entries={node.id: ProgressEntry(state="passed")}),
        specs=[spec],
        records=[record],
    )
    _build_derived(view)
    return view


def test_build_portfolio_default_deny_all_dimensions():
    view = build_portfolio(_view(), SelectionOptions(), today=TODAY)
    (block,) = view.nodes
    (item,) = block["evidence"]
    assert item["location"] == REDACTED
    assert item["note"] == REDACTED
    assert item["gate_run"] is None
    assert block["artifacts"] == [REDACTED]
    assert block["notes"] == [REDACTED]


def test_build_portfolio_overrides_reveal_paths_and_notes():
    view = build_portfolio(
        _view(),
        SelectionOptions(include_paths=True, include_notes=True),
        today=TODAY,
    )
    (block,) = view.nodes
    (item,) = block["evidence"]
    assert item["location"] == "evidence/a.md"
    assert item["note"] == "learner note"
    assert item["gate_run"] == {
        "command_argv": ["python", "evidence/check.py"],
        "inputs": ["evidence/a.md"],
        "exit_class": "passed",
    }


def test_renderers_do_not_double_redact_receipt():
    view = build_portfolio(
        _view(), SelectionOptions(include_paths=True), today=TODAY
    )
    md = render_markdown(view, view.selection)
    assert "evidence/a.md" in md
    payload_item = __import__("json").loads(
        render_json(view, view.selection)
    )["nodes"][0]["evidence"][0]
    assert payload_item["gate_run"] == {
        "command_argv": ["python", "evidence/check.py"],
        "inputs": ["evidence/a.md"],
        "exit_class": "passed",
    }
