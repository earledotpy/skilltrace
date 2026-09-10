"""Graph-impact `diagnose()` behind `BaselineSource` adapters (issue #205).

`diagnose()` is the production diagnostic path: baseline loading (git ref,
path, in-memory adapters), dangling-reference inputs, ranking `prepare`
reuse, and the pure `compute_impact`. The in-memory adapter keeps these
tests free of live git and temp curriculum files; the git adapter is
exercised with a stubbed fetch seam (blobs parsed from text, no temp
node files dropped on disk).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from skilltrace.context import JoinedView, PolicyAccess
from skilltrace.graph.edges import GraphEdge, load_edges_from_text
from skilltrace.graph.impact import (
    BaselineUnavailable,
    GitBaselineSource,
    InMemoryBaselineSource,
    PathBaselineSource,
    compute_impact,
    diagnose,
    format_report,
)
from skilltrace.graph.nodes import SkillNode, load_node_from_text
from skilltrace.graph.recommendation_prep import prepare
from skilltrace.graph.state import ProgressEntry, ProgressStore

A = "math.a_01"
B = "math.b_01"
C = "math.c_01"
TODAY = date(2026, 9, 10)


def _node(node_id: str) -> SkillNode:
    return SkillNode(id=node_id, title=node_id, summary="s", domain="d", track="t")


def _edge(edge_id: str, source: str, target: str) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source=source,
        target=target,
        edge_type="hard_prerequisite",
        reason="r",
        active=True,
    )


def _store(**states: str) -> ProgressStore:
    return ProgressStore(entries={nid: ProgressEntry(state=s) for nid, s in states.items()})


def _joined(current_edges, store, **kwargs) -> JoinedView:
    return JoinedView(
        nodes=[_node(A), _node(B), _node(C)],
        edges=list(current_edges),
        store=store,
        **kwargs,
    )


# --- diagnose() over the in-memory adapter: no git, no files ------------------


def test_diagnose_in_memory_detects_readiness_flip_without_git_or_files():
    store = _store(**{B: "available"})
    joined = _joined([_edge("e1", A, B)], store)
    baseline = InMemoryBaselineSource(nodes=(_node(A), _node(B), _node(C)), edges=())

    outcome = diagnose(joined, baseline, root=None, today=TODAY)

    assert outcome.baseline_label == "in-memory baseline"
    assert [(f.node_id, f.baseline_state, f.current_state) for f in outcome.report.flips] == [
        (B, "available", "locked")
    ]


def test_diagnose_quiet_when_baseline_matches_current():
    store = _store(**{B: "available"})
    edges = [_edge("e1", A, B)]
    joined = _joined(edges, store)
    baseline = InMemoryBaselineSource(
        nodes=(_node(A), _node(B), _node(C)), edges=tuple(edges)
    )

    outcome = diagnose(joined, baseline, root=None, today=TODAY)

    assert outcome.report.quiet is True


def test_diagnose_reuses_prepare_boosts_without_a_local_duplicate():
    """The rec diff matches `compute_impact` fed by `prepare()` directly."""
    store = _store(**{A: "available", B: "available", C: "available"})
    policies = {
        "recommendation.yaml": {
            "track_weights": {"t": 1.0},
            "factor_weights": {"downstream_leverage": 0.5},
        },
    }
    joined = _joined(
        [],
        store,
        policies=policies,
        policy=PolicyAccess(dict(policies)),
    )
    baseline = InMemoryBaselineSource(
        nodes=(_node(A), _node(B), _node(C)), edges=(_edge("e1", B, C),)
    )

    outcome = diagnose(joined, baseline, root=None, today=TODAY)
    inputs = prepare(joined, None, TODAY)
    expected = compute_impact(
        list(baseline.nodes),
        list(baseline.edges),
        joined.nodes,
        joined.edges,
        joined.store,
        minutes=60,
        limit=5,
        **inputs.recommend_kwargs(),
    )

    assert [
        (c.node_id, c.baseline_rank, c.current_rank)
        for c in outcome.report.recommendation_changes
    ] == [
        (c.node_id, c.baseline_rank, c.current_rank)
        for c in expected.recommendation_changes
    ]


def test_diagnose_collects_dangling_refs_from_the_joined_view():
    from skilltrace.evidence.evidence import ArtifactSpec

    store = _store()
    joined = _joined(
        [],
        store,
        specs=[ArtifactSpec(id="spec.gone", node_id="math.gone_01", title="t", artifact_kind="k", required=True, minimum_count=1)],
    )
    baseline = InMemoryBaselineSource(nodes=(_node(A), _node(B), _node(C)), edges=())

    outcome = diagnose(joined, baseline, root=None, today=TODAY)

    assert [(d.node_id, list(d.referenced_by)) for d in outcome.report.dangling] == [
        ("math.gone_01", ["spec:spec.gone"])
    ]
    assert outcome.report.quiet is False


# --- Text loaders: the no-temp-file foundation --------------------------------


def test_load_node_from_text_names_the_curriculum_path_not_a_temp_file(tmp_path):
    text = (
        "---\n"
        "id: math.text_01\n"
        "title: Text node\n"
        "summary: Parsed without touching disk.\n"
        "domain: testing\n"
        "track: t\n"
        "---\n\n# body ignored\n"
    )
    node = load_node_from_text(text, tmp_path / "graph" / "nodes" / "math.text_01.md")

    assert node.id == "math.text_01"
    assert node.source_path == tmp_path / "graph" / "nodes" / "math.text_01.md"


def test_load_node_from_text_rejects_forbidden_keys_naming_the_source():
    text = "---\nid: math.bad_01\nstate: active\n---\n"
    with pytest.raises(Exception, match="math.bad_01.md"):
        load_node_from_text(text, Path("graph/nodes/math.bad_01.md"))


def test_load_edges_from_text_round_trips_and_allows_empty_baseline():
    text = yaml.safe_dump(
        {
            "edges": [
                {
                    "id": "e1",
                    "source": A,
                    "target": B,
                    "edge_type": "hard_prerequisite",
                    "reason": "r",
                    "active": True,
                }
            ]
        }
    )
    edges = load_edges_from_text(text)

    assert [(e.id, e.source, e.target) for e in edges] == [("e1", A, B)]
    assert load_edges_from_text("  \n", allow_empty=True) == []


# --- Git adapter with a stubbed fetch seam (no live git, no temp files) -------


def _node_blob(node_id: str) -> str:
    return (
        "---\n"
        f"id: {node_id}\n"
        f"title: Title for {node_id}\n"
        f"summary: Summary for {node_id}.\n"
        "domain: testing\n"
        "track: t\n"
        "---\n\n# body\n"
    )


def _stub_git(blobs: dict[str, str], edges_text: str):
    """A `run_git` double serving fixed blobs keyed by `argv` tail."""

    def run(root: Path, *argv: str) -> str:
        if argv[:3] == ("rev-parse", "--verify", "--quiet"):
            return "abc123\n"
        if argv[:2] == ("ls-tree", "-r"):
            return "".join(f"{path}\n" for path in blobs if path != "graph/edges.yaml")
        assert argv[0] == "show"
        ref_path = argv[1]
        assert ":" in ref_path
        relpath = ref_path.split(":", 1)[1]
        if relpath == "graph/edges.yaml":
            if edges_text is None:
                raise BaselineUnavailable(
                    "fatal: path 'graph/edges.yaml' does not exist in 'HEAD'"
                )
            return edges_text
        try:
            return blobs[relpath]
        except KeyError:
            raise BaselineUnavailable(
                f"fatal: path '{relpath}' does not exist in 'HEAD'"
            ) from None

    return run


def test_git_source_parses_blobs_from_text_without_temp_files(tmp_path):
    blobs = {
        "graph/nodes/math.a_01.md": _node_blob("math.a_01"),
        "graph/nodes/math.b_01.md": _node_blob("math.b_01"),
    }
    edges_text = yaml.safe_dump(
        {
            "edges": [
                {
                    "id": "e1",
                    "source": A,
                    "target": B,
                    "edge_type": "hard_prerequisite",
                    "reason": "r",
                    "active": True,
                }
            ]
        }
    )
    source = GitBaselineSource(tmp_path, "HEAD", run_git=_stub_git(blobs, edges_text))

    baseline = source.load()

    assert baseline.label == "HEAD"
    assert [n.id for n in baseline.nodes] == ["math.a_01", "math.b_01"]
    # Errors name the curriculum file, never a temp file — because none exists.
    assert all(
        n.source_path == tmp_path / relpath for n, relpath in zip(baseline.nodes, blobs)
    )
    assert list(tmp_path.iterdir()) == []
    assert [(e.id, e.source, e.target) for e in baseline.edges] == [("e1", A, B)]


def test_git_source_missing_edges_at_ref_means_no_baseline_edges(tmp_path):
    blobs = {"graph/nodes/math.a_01.md": _node_blob("math.a_01")}
    source = GitBaselineSource(tmp_path, "HEAD", run_git=_stub_git(blobs, None))

    baseline = source.load()

    assert [n.id for n in baseline.nodes] == ["math.a_01"]
    assert baseline.edges == []


@pytest.mark.parametrize("edges_text", ["# just a comment\n", "[]\n", "{}\n", "edges:\n"])
def test_git_source_pre_edges_era_blobs_mean_no_baseline_edges(tmp_path, edges_text):
    """Legacy tolerance: empty/non-mapping/missing-edges docs are not failures."""
    blobs = {"graph/nodes/math.a_01.md": _node_blob("math.a_01")}
    source = GitBaselineSource(tmp_path, "HEAD", run_git=_stub_git(blobs, edges_text))

    assert source.load().edges == []


def test_git_source_unparseable_edges_is_unavailable(tmp_path):
    blobs = {"graph/nodes/math.a_01.md": _node_blob("math.a_01")}
    source = GitBaselineSource(
        tmp_path, "HEAD", run_git=_stub_git(blobs, "edges: [unclosed\n")
    )

    with pytest.raises(BaselineUnavailable, match="unparseable edges.yaml"):
        source.load()


def test_git_source_unknown_ref_is_unavailable(tmp_path):
    def run(root: Path, *argv: str) -> str:
        raise BaselineUnavailable("fatal: unknown revision")

    with pytest.raises(BaselineUnavailable, match="unknown revision"):
        GitBaselineSource(tmp_path, "no.such.ref", run_git=run).load()


def test_git_source_bad_node_blob_is_unavailable(tmp_path):
    blobs = {"graph/nodes/math.bad_01.md": "---\nstate: active\n---\n"}
    source = GitBaselineSource(tmp_path, "HEAD", run_git=_stub_git(blobs, ""))

    with pytest.raises(BaselineUnavailable, match="math.bad_01.md"):
        source.load()


# --- Path adapter: a second checkout, no git ----------------------------------


def _write_checkout(root: Path) -> None:
    from _builders import write_node

    write_node(root, "math.a_01")
    write_node(root, "math.b_01")
    (root / "graph" / "edges.yaml").write_text(
        yaml.safe_dump(
            {
                "edges": [
                    {
                        "id": "e1",
                        "source": "math.a_01",
                        "target": "math.b_01",
                        "edge_type": "hard_prerequisite",
                        "reason": "r",
                        "active": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_path_source_loads_a_second_checkout(tmp_path):
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    _write_checkout(baseline_dir)

    baseline = PathBaselineSource(baseline_dir).load()

    assert baseline.label == f"baseline {baseline_dir}"
    assert [n.id for n in baseline.nodes] == ["math.a_01", "math.b_01"]
    assert [(e.id, e.source, e.target) for e in baseline.edges] == [
        ("e1", "math.a_01", "math.b_01")
    ]


def test_path_source_bad_node_is_unavailable(tmp_path):
    baseline_dir = tmp_path / "baseline"
    (baseline_dir / "graph" / "nodes").mkdir(parents=True)
    (baseline_dir / "graph" / "nodes" / "bad.md").write_text(
        "---\nstate: active\n---\n", encoding="utf-8"
    )

    with pytest.raises(BaselineUnavailable, match="bad.md"):
        PathBaselineSource(baseline_dir).load()


# --- Renderer: pure lines, command prints -------------------------------------


def test_format_report_renders_flip_and_quiet_verbatim():
    store = _store(**{B: "available"})
    joined = _joined([_edge("e1", A, B)], store)
    baseline = InMemoryBaselineSource(nodes=(_node(A), _node(B), _node(C)), edges=())
    outcome = diagnose(joined, baseline, root=None, today=TODAY)

    lines = format_report(outcome.report, outcome.baseline_label)

    assert lines[0] == "graph impact vs in-memory baseline:"
    assert lines[1] == "  flip: math.b_01: available -> locked"


def test_format_report_quiet_names_no_change():
    outcome_lines = format_report(
        diagnose(
            _joined([], _store()),
            InMemoryBaselineSource(nodes=(_node(A),), edges=()),
            root=None,
            today=TODAY,
        ).report,
        "HEAD",
    )

    assert outcome_lines[0] == "graph impact vs HEAD:"
    assert any("no changes" in line for line in outcome_lines[1:])
