"""Unit tests for portfolio selection (v2.0 spec §2, T-TestArch #180).

Calls ``selection.select`` directly with hand-built joined views; pins exact
node sets and evidence sets computed from the spec defaults and flag
combinations.
"""

from __future__ import annotations

from skilltrace.context import JoinedView, _build_derived
from skilltrace.evidence.evidence import ArtifactSpec, EvidenceRecord
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.state import ProgressEntry, ProgressStore
from skilltrace.portfolio.models import SelectionOptions
from skilltrace.portfolio.selection import select

NODE_A = "portfolio.project.slope_calculator_01"
NODE_B = "portfolio.project.data_cleaning_tool_01"
NODE_OTHER = "foundations.python.basics_01"


def _node(node_id: str, track: str = "portfolio") -> SkillNode:
    return SkillNode(
        id=node_id,
        title=f"Title for {node_id}",
        summary="Summary.",
        domain="testing",
        track=track,
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


def _record(
    record_id: str,
    spec_id: str,
    *,
    accepted: bool = True,
    location: str = "evidence/a.md",
    supersedes: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=record_id,
        artifact_spec_id=spec_id,
        location=location,
        accepted=accepted,
        accepted_by="learner_manual",
        artifact_hash="sha256:aaa",
        supersedes=supersedes,
        supersede_reason="fix" if supersedes is not None else None,
        created_at="2026-08-01",
    )


def _view(
    *,
    states: dict[str, str],
    records: list[EvidenceRecord] | None = None,
    tracks: dict[str, str] | None = None,
) -> JoinedView:
    tracks = tracks or {}
    nodes = [
        _node(node_id, tracks.get(node_id, "portfolio")) for node_id in states
    ]
    specs = [_spec(f"spec.{node_id}.main", node_id) for node_id in states]
    view = JoinedView(
        nodes=nodes,
        store=ProgressStore(
            entries={
                node_id: ProgressEntry(state=state)
                for node_id, state in states.items()
            }
        ),
        specs=specs,
        records=list(records or []),
    )
    _build_derived(view)
    return view


def _ids(selected) -> list[str]:
    return [n.node_id for n in selected]


# --- Default selection -----------------------------------------------------


def test_default_selects_passed_and_mastered_portfolio_nodes_only():
    view = _view(
        states={NODE_A: "passed", NODE_B: "mastered", NODE_OTHER: "passed"},
        tracks={NODE_OTHER: "foundational"},
        records=[
            _record(f"ev.{NODE_A}.001", f"spec.{NODE_A}.main"),
            _record(f"ev.{NODE_B}.001", f"spec.{NODE_B}.main"),
            _record(f"ev.{NODE_OTHER}.001", f"spec.{NODE_OTHER}.main"),
        ],
    )
    selected = select(view, SelectionOptions())
    assert _ids(selected) == [NODE_B, NODE_A]
    assert all(n.state in ("passed", "mastered") for n in selected)
    assert all(n.track == "portfolio" for n in selected)


def test_default_excludes_active_locked_and_available():
    view = _view(
        states={
            NODE_A: "active",
            NODE_B: "available",
            "portfolio.project.extra_node_01": "locked",
        }
    )
    assert select(view, SelectionOptions()) == []


def test_default_evidence_is_accepted_live_head_only():
    live = f"ev.{NODE_A}.001"
    old = f"ev.{NODE_A}.002"
    new = f"ev.{NODE_A}.003"
    rejected = f"ev.{NODE_A}.004"
    view = _view(
        states={NODE_A: "passed"},
        records=[
            _record(live, f"spec.{NODE_A}.main"),
            _record(old, f"spec.{NODE_A}.main"),
            _record(
                new, f"spec.{NODE_A}.main", supersedes=old,
            ),
            _record(rejected, f"spec.{NODE_A}.main", accepted=False),
        ],
    )
    (node,) = select(view, SelectionOptions())
    assert [e.record_id for e in node.evidence] == [live, new]
    # The supersession mismatch is surfaced, not silently dropped.
    assert node.has_superseded is True


def test_node_without_evidence_is_selected_with_unverified_claim():
    view = _view(states={NODE_A: "passed"})
    (node,) = select(view, SelectionOptions())
    assert node.evidence == []
    assert node.has_unverified_claim is True


# --- Flag set --------------------------------------------------------------


def test_include_active_adds_active_nodes():
    view = _view(states={NODE_A: "active", NODE_B: "passed"})
    assert _ids(select(view, SelectionOptions())) == [NODE_B]
    assert _ids(select(view, SelectionOptions(include_active=True))) == [
        NODE_B,
        NODE_A,
    ]


def test_track_filter_restricts_and_node_without_track_drops_it():
    view = _view(
        states={NODE_A: "passed", NODE_OTHER: "passed"},
        tracks={NODE_OTHER: "consolidation"},
        records=[
            _record(f"ev.{NODE_A}.001", f"spec.{NODE_A}.main"),
            _record(f"ev.{NODE_OTHER}.001", f"spec.{NODE_OTHER}.main"),
        ],
    )
    assert _ids(select(view, SelectionOptions(track="consolidation"))) == [
        NODE_OTHER
    ]
    # --node without --track: no implicit track restriction.
    selected = select(
        view, SelectionOptions(nodes=(NODE_OTHER,), track=None)
    )
    assert _ids(selected) == [NODE_OTHER]


def test_node_filter_restricts_to_named_nodes():
    view = _view(states={NODE_A: "passed", NODE_B: "passed"})
    selected = select(view, SelectionOptions(nodes=(NODE_B,)))
    assert _ids(selected) == [NODE_B]


def test_include_rejected_and_superseded_add_records_with_banner():
    old = f"ev.{NODE_A}.001"
    new = f"ev.{NODE_A}.002"
    rejected = f"ev.{NODE_A}.003"
    view = _view(
        states={NODE_A: "passed"},
        records=[
            _record(old, f"spec.{NODE_A}.main"),
            _record(new, f"spec.{NODE_A}.main", supersedes=old),
            _record(rejected, f"spec.{NODE_A}.main", accepted=False),
        ],
    )
    (node,) = select(
        view,
        SelectionOptions(include_rejected=True, include_superseded=True),
    )
    assert [e.record_id for e in node.evidence] == [old, new, rejected]
    assert any(e.superseded for e in node.evidence)
    assert any(not e.accepted for e in node.evidence)
