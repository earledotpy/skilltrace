"""`skilltrace graph impact` — the read-only curriculum-edit advisory (v2.2).

Compares the working tree against a baseline and renders the pure
`..graph.impact.compute_impact` findings. Advisory only: `Kind.READ_ONLY`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..dispatch import Command, CommandResult, Context, Kind, Registry


class BaselineUnavailable(Exception):
    """The baseline side cannot be loaded at all (non-git dir, unknown ref)."""


def _run_git(root: Path, *argv: str) -> str:
    """Run one read-only git file-fetch; any failure is unavailable."""
    try:
        completed = subprocess.run(
            ["git", *argv],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BaselineUnavailable(f"not a git repository ({exc})") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise BaselineUnavailable(detail[0] if detail else "git command failed")
    return completed.stdout


def _tracked_node_paths(root: Path, ref: str) -> list[str]:
    """Repo-relative node-markdown paths tracked at `ref`.

    `git ls-tree` lists exactly the files the baseline loader must read —
    including ones deleted from the working tree (the D-Dangling case) and
    excluding untracked clutter.
    """
    out = _run_git(root, "ls-tree", "-r", "--name-only", ref, "--", "graph/nodes/")
    return [line for line in out.splitlines() if line.strip()]


def _show_file(root: Path, ref: str, relpath: str) -> str:
    """Fetch one baseline file's text; a path missing at `ref` reads empty."""
    try:
        return _run_git(root, "show", f"{ref}:{relpath}")
    except BaselineUnavailable as exc:
        message = str(exc).lower()
        if "does not exist" in message or "exists on disk, but not in" in message:
            return ""
        raise


def _load_baseline_from_ref(root: Path, ref: str):
    """Load baseline nodes/edges through the read-only git fetch seam.

    Nodes come from the tracked `graph/nodes/*.md` blobs at `ref`, parsed
    with the production `load_node` (via a temp file — the loader reads
    from disk, and the blob's `source_path` is re-pointed at its
    repo-relative path so errors name the curriculum file, not the temp
    file). `graph/edges.yaml` comes from `git show <ref>:graph/edges.yaml`
    (missing at `ref` means the pre-edges era — no baseline edges).
    """
    import dataclasses

    import yaml

    from ..graph.edges import EdgeLoadError, load_edge
    from ..graph.nodes import NodeLoadError, load_node

    _run_git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    nodes = []
    for relpath in _tracked_node_paths(root, ref):
        if not relpath.endswith(".md"):
            continue
        blob = _show_file(root, ref, relpath)
        if not blob:
            continue
        tmp = root / ".tmp_baseline_node.md"
        try:
            tmp.write_text(blob, encoding="utf-8")
            node = load_node(tmp)
        except NodeLoadError as exc:
            raise BaselineUnavailable(str(exc)) from exc
        finally:
            tmp.unlink(missing_ok=True)
        nodes.append(dataclasses.replace(node, source_path=root / relpath))
    edges_text = _show_file(root, ref, "graph/edges.yaml")
    if not edges_text.strip():
        return nodes, []
    try:
        doc = yaml.safe_load(edges_text)
    except yaml.YAMLError as exc:
        raise BaselineUnavailable(
            f"baseline {ref}: unparseable edges.yaml: {exc}"
        ) from exc
    items = (doc or {}).get("edges", []) if isinstance(doc, dict) else []
    edges = []
    for index, item in enumerate(items):
        try:
            edges.append(load_edge(item, index=index))
        except EdgeLoadError as exc:
            raise BaselineUnavailable(str(exc)) from exc
    return nodes, edges


def _load_baseline_from_path(path: Path):
    """Load baseline nodes/edges from a second checkout (no git needed)."""
    from ..graph.edges import EdgeLoadError, load_edges
    from ..graph.nodes import NodeLoadError, load_nodes

    try:
        nodes = load_nodes(path)
    except NodeLoadError as exc:
        raise BaselineUnavailable(str(exc)) from exc
    try:
        edges = load_edges(path) if (path / "graph" / "edges.yaml").exists() else []
    except EdgeLoadError as exc:
        raise BaselineUnavailable(str(exc)) from exc
    return nodes, edges


def _boost_inputs(joined, root: Path) -> dict:
    """Derive the recommendation boost inputs once, for both edge sets.

    Remediation pressure, open blockers, prerequisite-review urgency, and
    agent signals all come from files unchanged between the sides — the
    boost set is identical under baseline and current edges, so the diff
    isolates the *graph edit's* effect (spec §2, D-RecDiff).

    One shared seam: `prepare()` behind `recommend()` (issue #201).
    """
    from ..graph.recommendation_prep import prepare

    inputs = prepare(joined, root)
    return {
        "remediation_boosted": set(inputs.remediation_boosted),
        "open_blocked": set(inputs.open_blocked),
        "prereq_reviews_due": dict(inputs.prereq_reviews_due),
        "agent_boosted": set(inputs.agent_boosted),
    }


def _dangling_inputs(joined) -> dict:
    """Collect dangling-reference inputs from the current evidence trail."""
    from ..evidence.evidence import ArtifactSpec, ValidationGate, EvidenceRecord, AssessmentAttempt

    specs = [(s.id, s.node_id) for s in joined.specs]
    gates = [(g.id, g.node_id) for g in joined.gates]
    records = [(r.id, r.artifact_spec_id, r.location) for r in joined.records]
    attempts = [(a.id, a.node_id) for a in joined.attempts]
    return {
        "dangling_specs": specs,
        "dangling_gates": gates,
        "dangling_records": records,
        "dangling_attempts": attempts,
    }


def _print_report(report, baseline_label: str) -> None:
    print(f"graph impact vs {baseline_label}:")
    if report.quiet:
        print("  no changes — the edit flips no readiness, moves no recommendation,")
        print("  dangles no reference, and leaves no no-op edge.")
        return
    for flip in report.flips:
        print(f"  flip: {flip.node_id}: {flip.baseline_state} -> {flip.current_state}")
    for node_id in report.asserted_standing:
        print(f"  asserted progress stands (not revoked): {node_id}")
    for change in report.recommendation_changes:
        before = f"#{change.baseline_rank}" if change.baseline_rank is not None else "(unranked)"
        after = f"#{change.current_rank}" if change.current_rank is not None else "(unranked)"
        print(f"  recommendation: {change.node_id}: {before} -> {after}")
    for dangling in report.dangling:
        print(f"  dangling: {dangling.node_id} still named by {', '.join(sorted(dangling.referenced_by))}")
    for edge in report.no_op_edges:
        print(f"  no-op edge: {edge.edge_id} ({edge.source} -> {edge.target})")


def graph_impact(ctx: Context) -> CommandResult:
    """Compare the working tree against its baseline; exit 0 when computed."""
    root = ctx.root
    baseline_opt = getattr(ctx.args, "baseline", None)
    from_ref = getattr(ctx.args, "from_ref", "HEAD")

    from ..context import load_context_lenient
    from ..graph.edges import EdgeLoadError
    from ..graph.nodes import NodeLoadError
    from ..graph.state import ProgressStoreError
    from ..graph.impact import compute_impact

    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"graph impact: FAILED — {exc}")
        return CommandResult(exit_code=1)

    try:
        if baseline_opt is not None:
            baseline_nodes, baseline_edges = _load_baseline_from_path(Path(baseline_opt))
            baseline_label = f"baseline {baseline_opt}"
        else:
            baseline_nodes, baseline_edges = _load_baseline_from_ref(root, from_ref)
            baseline_label = f"{from_ref}"
    except BaselineUnavailable as exc:
        print(f"graph impact: FAILED — baseline unavailable: {exc}")
        return CommandResult(exit_code=1)

    boosts = _boost_inputs(joined, root)
    dangling = _dangling_inputs(joined)
    report = compute_impact(
        baseline_nodes,
        baseline_edges,
        joined.nodes,
        joined.edges,
        joined.store,
        minutes=getattr(ctx.args, "minutes", 60),
        factor_weights=joined.policy.factor_weights,
        track_weights=joined.policy.track_weights,
        remediation_boosted=boosts["remediation_boosted"],
        open_blocked=boosts["open_blocked"],
        prereq_reviews_due=boosts["prereq_reviews_due"],
        agent_boosted=boosts["agent_boosted"],
        **dangling,
    )
    _print_report(report, baseline_label)
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="graph impact",
            kind=Kind.READ_ONLY,
            handler=graph_impact,
            help="Advisory: what a curriculum edit would change (flips, rec diffs, dangling refs, no-op edges).",
        )
    )


