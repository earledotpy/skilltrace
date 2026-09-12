"""Pure graph-impact core (v2.2): what a curriculum edit would change.

`compute_impact` is the TDD seam (spec §2): over already-loaded baseline and
current nodes/edges plus the *same* progress store, it reports readiness flips
on non-asserted nodes, asserted nodes a baseline-edge edit would "re-lock"
(reported as standing, never as flips), recommendation changes under both edge
sets with identical store/weights/boosts, and no-op edges. Reads relationships
only from the passed edge lists (plus the same derived-readiness code `sync`
uses) — never node frontmatter. Writes nothing, blocks nothing; the command
shell renders it. Mirrors `check_graph` / `recommend` / `plan_submit` in the
house pure-core style.

`diagnose` (issue #205) is the production diagnostic path: it owns baseline
loading behind `BaselineSource` adapters (git ref, path, in-memory), reuses
the ranking `prepare` seam for boost inputs, collects dangling-reference
inputs from the joined view, and calls `compute_impact`. The CLI command is
renderer/exit-code only.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol

import yaml

from .edges import EdgeLoadError, GraphEdge, load_edges, load_edges_from_text
from .nodes import NodeLoadError, SkillNode, load_node_from_text, load_nodes
from .readiness import _active_hard_prereqs_by_target, derive_readiness
from .recommendation import recommend
from .recommendation_prep import prepare
from .state import ASSERTED_STATES, ProgressStore

if TYPE_CHECKING:
    from ..context import JoinedView


@dataclass(frozen=True)
class ReadinessFlip:
    """One non-asserted node whose derived readiness differs between sides."""

    node_id: str
    baseline_state: str
    current_state: str


@dataclass(frozen=True)
class RecommendationChange:
    """One node that entered, left, or moved in the ranked list."""

    node_id: str
    baseline_rank: int | None  # None = entered
    current_rank: int | None  # None = left


@dataclass(frozen=True)
class NoOpEdge:
    """An active hard-prerequisite edge whose removal changes nothing."""

    edge_id: str
    source: str
    target: str


@dataclass(frozen=True)
class DanglingReference:
    """A working-tree node deleted while an evidence file still names it.

    `referenced_by` names the referencing file(s) compactly (`spec:<id>`,
    `gate:<id>`, `record:<id>`, `attempt:<id>`); the diagnostic *lists*
    these where `validate graph`/`validate evidence` *error* on them
    (spec §2, D-Dangling) — release impact, never a block.
    """

    node_id: str
    referenced_by: tuple[str, ...]


@dataclass
class ImpactReport:
    """The advisory finding set for one baseline -> current comparison."""

    flips: list[ReadinessFlip] = field(default_factory=list)
    asserted_standing: list[str] = field(default_factory=list)
    recommendation_changes: list[RecommendationChange] = field(default_factory=list)
    dangling: list[DanglingReference] = field(default_factory=list)
    no_op_edges: list[NoOpEdge] = field(default_factory=list)

    @property
    def quiet(self) -> bool:
        """True when nothing would change — the happy 'no impact' report."""
        return not (
            self.flips
            or self.asserted_standing
            or self.recommendation_changes
            or self.dangling
            or self.no_op_edges
        )


def _readiness_map(
    node_ids: list[str], edges: list[GraphEdge], store: ProgressStore
) -> dict[str, str]:
    """Derived readiness per node under one edge set, against the shared store."""
    prereq_sources = _active_hard_prereqs_by_target(edges)
    return {
        node_id: derive_readiness(node_id, prereq_sources, store)
        for node_id in node_ids
    }


def _ranked_ids(
    nodes: list[SkillNode],
    edges: list[GraphEdge],
    store: ProgressStore,
    *,
    minutes: int,
    limit: int,
    factor_weights,
    track_weights,
    remediation_boosted: set[str],
    open_blocked: set[str],
    prereq_reviews_due,
    agent_boosted: set[str],
) -> list[str]:
    """One `recommend()` pass, flattened to its ranked candidate ids."""
    result = recommend(
        nodes,
        edges,
        store,
        track_weights or {},
        minutes=minutes,
        limit=limit,
        show_locked=False,
        factor_weights=factor_weights or {},
        remediation_boosted=remediation_boosted,
        open_blocked=open_blocked,
        prereq_reviews_due=prereq_reviews_due,
        agent_boosted=agent_boosted,
    )
    return [rec.node_id for rec in result.recommendations]


def _rec_changes(
    baseline_ranked: list[str], current_ranked: list[str]
) -> list[RecommendationChange]:
    """Entered/left/moved nodes between two ranked lists (1-based ranks)."""
    baseline_pos = {node_id: i + 1 for i, node_id in enumerate(baseline_ranked)}
    current_pos = {node_id: i + 1 for i, node_id in enumerate(current_ranked)}
    changes: list[RecommendationChange] = []
    for node_id, rank in baseline_pos.items():
        other = current_pos.get(node_id)
        if other != rank:
            changes.append(RecommendationChange(node_id, rank, other))
    for node_id, rank in current_pos.items():
        if node_id not in baseline_pos:
            changes.append(RecommendationChange(node_id, None, rank))
    changes.sort(key=lambda c: c.node_id)
    return changes


def compute_impact(
    baseline_nodes: list[SkillNode],
    baseline_edges: list[GraphEdge],
    current_nodes: list[SkillNode],
    current_edges: list[GraphEdge],
    store: ProgressStore,
    *,
    minutes: int = 60,
    limit: int = 5,
    factor_weights=None,
    track_weights=None,
    remediation_boosted: set[str] | None = None,
    open_blocked: set[str] | None = None,
    prereq_reviews_due=None,
    agent_boosted: set[str] | None = None,
    dangling_specs: list[tuple[str, str]] | None = None,
    dangling_gates: list[tuple[str, str]] | None = None,
    dangling_records: list[tuple[str, str, str | None]] | None = None,
    dangling_attempts: list[tuple[str, str]] | None = None,
) -> ImpactReport:
    """Compare two graph sides over one shared progress store. Pure of I/O.

    The command shell loads both sides (baseline via the git fetch seam or a
    second checkout) and calls this; nothing here touches disk. The dangling
    inputs are `(id, node_id)` pairs from the current working tree's
    evidence files (records additionally carry their spec id): any named
    node absent from the current node set is dangling (spec §2, D-Dangling).
    Nothing here writes, blocks, or revokes asserted progress.
    """
    current_ids = [node.id for node in current_nodes]

    report = ImpactReport()

    # --- Readiness flips (non-asserted nodes only) --------------------------
    baseline_ready = _readiness_map(
        [n.id for n in baseline_nodes], baseline_edges, store
    )
    current_ready = _readiness_map(current_ids, current_edges, store)
    for node_id in current_ids:
        if store.state_of(node_id) in ASSERTED_STATES:
            continue  # asserted progress stands; never reported as a flip
        before = baseline_ready.get(node_id)
        after = current_ready.get(node_id)
        if before is not None and before != after:
            report.flips.append(ReadinessFlip(node_id, before, after))
    report.flips.sort(key=lambda f: f.node_id)

    # --- Asserted nodes a current edge would re-lock (they stand) -------------
    # No baseline-edges guard: the headline case is a *new* prerequisite
    # (empty baseline) that would re-lock an asserted node — skipping it
    # would blind the diagnostic to exactly the edit it exists to review.
    for node_id in current_ids:
        if store.state_of(node_id) not in ASSERTED_STATES:
            continue
        if (
            baseline_ready.get(node_id) == "available"
            and current_ready.get(node_id) == "locked"
        ):
            report.asserted_standing.append(node_id)
    report.asserted_standing.sort()

    # --- Recommendation diff (identical inputs, two edge sets) --------------
    common_kwargs = dict(
        minutes=minutes,
        limit=limit,
        factor_weights=factor_weights,
        track_weights=track_weights,
        remediation_boosted=remediation_boosted or set(),
        open_blocked=open_blocked or set(),
        prereq_reviews_due=prereq_reviews_due or {},
        agent_boosted=agent_boosted or set(),
    )
    baseline_ranked = _ranked_ids(current_nodes, baseline_edges, store, **common_kwargs)
    current_ranked = _ranked_ids(current_nodes, current_edges, store, **common_kwargs)
    report.recommendation_changes = _rec_changes(baseline_ranked, current_ranked)

    # --- Dangling references: evidence names a node the tree deleted --------
    report.dangling = _dangling_refs(
        current_ids,
        specs=dangling_specs or [],
        gates=dangling_gates or [],
        records=dangling_records or [],
        attempts=dangling_attempts or [],
    )

    # --- No-op edges (counterfactual removal of active hard prereqs) --------
    report.no_op_edges = _no_op_edges(
        current_nodes, current_edges, store, current_ranked, **common_kwargs
    )

    return report


def _dangling_refs(
    current_ids: list[str],
    *,
    specs: list[tuple[str, str]],
    gates: list[tuple[str, str]],
    records: list[tuple[str, str, str | None]],
    attempts: list[tuple[str, str]],
) -> list[DanglingReference]:
    """Nodes the evidence trail still names but the working tree deleted.

    Records name a spec, not a node — resolve through the spec map built
    from the same `specs` input (an unknown spec resolves to its own id so
    it still surfaces rather than vanishing). Sorted by node id for a
    stable advisory report.
    """
    present = set(current_ids)
    spec_to_node = {spec_id: node_id for spec_id, node_id in specs}
    refs: dict[str, set[str]] = {}
    for spec_id, node_id in specs:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"spec:{spec_id}")
    for gate_id, node_id in gates:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"gate:{gate_id}")
    for record_id, spec_id, _location in records:
        node_id = spec_to_node.get(spec_id, spec_id)
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"record:{record_id}")
    for attempt_id, node_id in attempts:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"attempt:{attempt_id}")
    return [
        DanglingReference(node_id, tuple(sorted(names)))
        for node_id, names in sorted(refs.items())
    ]


def _no_op_edges(
    nodes: list[SkillNode],
    edges: list[GraphEdge],
    store: ProgressStore,
    current_ranked: list[str],
    **common_kwargs,
) -> list[NoOpEdge]:
    """Active hard-prereq edges whose removal changes no readiness and no rec.

    Counterfactual per edge: recompute readiness (asserted nodes cannot flip by
    construction) and re-rank with that one edge gone; an unchanged readiness
    map and an unchanged ranked list make the edge a no-op. Cheap at seed
    scale (100 nodes / 157 edges).
    """
    noop: list[NoOpEdge] = []
    baseline_ready = _readiness_map([n.id for n in nodes], edges, store)
    for edge in edges:
        if not (edge.active and edge.edge_type == "hard_prerequisite"):
            continue
        reduced = [e for e in edges if e.id != edge.id]
        reduced_ready = _readiness_map([n.id for n in nodes], reduced, store)
        if any(baseline_ready[nid] != reduced_ready[nid] for nid in baseline_ready):
            continue
        reduced_ranked = _ranked_ids(nodes, reduced, store, **common_kwargs)
        if reduced_ranked != current_ranked:
            continue
        noop.append(NoOpEdge(edge.id, edge.source, edge.target))
    noop.sort(key=lambda e: e.edge_id)
    return noop


# --- Baseline sources + diagnose() (issue #205) --------------------------------
#
# The diagnostic's production path. Baseline loading lives behind the
# `BaselineSource` protocol so tests exercise `diagnose()` with the in-memory
# adapter — no live git, no temp curriculum files — while the CLI's default
# path keeps the read-only git fetch seam. Ranking boosts come from the
# `prepare` seam behind `recommend()` (issue #201); nothing here hand-assembles
# boost kwargs. Advisory and read-only: `diagnose` writes nothing and blocks
# nothing; it raises `BaselineUnavailable` only when the baseline cannot be
# loaded at all.


class BaselineUnavailable(Exception):
    """The baseline side cannot be loaded at all (non-git dir, unknown ref)."""


@dataclass(frozen=True)
class Baseline:
    """One loaded baseline side: curriculum plus its display label."""

    nodes: list[SkillNode]
    edges: list[GraphEdge]
    label: str


class BaselineSource(Protocol):
    """Where the baseline side of a `diagnose()` run comes from."""

    @property
    def label(self) -> str:
        """Display label for the baseline side (rendered after `graph impact vs`)."""
        ...  # pragma: no cover - protocol surface

    def load(self) -> Baseline:
        """Load baseline nodes/edges; raise `BaselineUnavailable` when impossible."""
        ...  # pragma: no cover - protocol surface


def _is_missing_blob(exc: BaselineUnavailable) -> bool:
    """True when a `git show` failure just means the path is absent at the ref."""
    message = str(exc).lower()
    return "does not exist" in message or "exists on disk, but not in" in message


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


@dataclass(frozen=True)
class GitBaselineSource:
    """Baseline from the tracked `graph/nodes/*.md` blobs plus `edges.yaml` at `ref`.

    Blobs are parsed from text via `load_node_from_text` — no temp node files
    are dropped on disk. `run_git` is the injectable fetch seam (tests stub it;
    production uses the module `_run_git`).
    """

    root: Path
    ref: str = "HEAD"
    run_git: Callable[..., str] | None = None

    @property
    def label(self) -> str:
        return self.ref

    def _git(self, *argv: str) -> str:
        runner = self.run_git or _run_git
        return runner(self.root, *argv)

    def load(self) -> Baseline:
        run = self._git
        run("rev-parse", "--verify", "--quiet", f"{self.ref}^{{commit}}")
        out = run("ls-tree", "-r", "--name-only", self.ref, "--", "graph/nodes/")
        nodes: list[SkillNode] = []
        for relpath in (line for line in out.splitlines() if line.strip()):
            if not relpath.endswith(".md"):
                continue
            try:
                blob = run("show", f"{self.ref}:{relpath}")
            except BaselineUnavailable as exc:
                if _is_missing_blob(exc):
                    continue
                raise
            if not blob:
                continue
            try:
                nodes.append(
                    load_node_from_text(blob, self.root / relpath)
                )
            except NodeLoadError as exc:
                raise BaselineUnavailable(str(exc)) from exc
        try:
            edges_text = run("show", f"{self.ref}:graph/edges.yaml")
        except BaselineUnavailable as exc:
            if _is_missing_blob(exc):
                edges_text = ""
            else:
                raise
        edges = _baseline_edges_from_text(edges_text, self.root, self.ref)
        return Baseline(nodes=nodes, edges=edges, label=self.label)


def _baseline_edges_from_text(edges_text: str, root: Path, ref: str) -> list[GraphEdge]:
    """Parse baseline `edges.yaml` text with the legacy loader's tolerance.

    Matches the pre-deepening git baseline loader: an empty blob, a
    comments-only document, a non-mapping, or a mapping without an `edges:`
    list means the pre-edges era — no baseline edges — rather than a load
    failure. Genuinely unparseable YAML and invalid edge items still raise
    `BaselineUnavailable` (exit 1: the baseline cannot be loaded).
    """
    try:
        doc = yaml.safe_load(edges_text)
    except yaml.YAMLError as exc:
        raise BaselineUnavailable(
            f"baseline {ref}: unparseable edges.yaml: {exc}"
        ) from exc
    if not isinstance(doc, dict) or not doc.get("edges"):
        return []
    try:
        return load_edges_from_text(
            edges_text,
            source_path=root / "graph" / "edges.yaml",
            allow_empty=True,
        )
    except EdgeLoadError as exc:
        raise BaselineUnavailable(
            f"baseline {ref}: unparseable edges.yaml: {exc}"
        ) from exc


@dataclass(frozen=True)
class PathBaselineSource:
    """Baseline from a second checkout on disk (no git needed)."""

    path: Path

    @property
    def label(self) -> str:
        return f"baseline {self.path}"

    def load(self) -> Baseline:
        try:
            nodes = load_nodes(self.path)
        except NodeLoadError as exc:
            raise BaselineUnavailable(str(exc)) from exc
        try:
            edges = (
                load_edges(self.path)
                if (self.path / "graph" / "edges.yaml").exists()
                else []
            )
        except EdgeLoadError as exc:
            raise BaselineUnavailable(str(exc)) from exc
        return Baseline(nodes=nodes, edges=edges, label=self.label)


@dataclass(frozen=True)
class InMemoryBaselineSource:
    """Baseline from already-loaded nodes/edges (tests; no git, no files)."""

    nodes: tuple[SkillNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    baseline_label: str = "in-memory baseline"

    @property
    def label(self) -> str:
        return self.baseline_label

    def load(self) -> Baseline:
        return Baseline(
            nodes=list(self.nodes), edges=list(self.edges), label=self.label
        )


@dataclass(frozen=True)
class DiagnoseOutcome:
    """The computed advisory report plus the baseline label it was computed against."""

    report: ImpactReport
    baseline_label: str


def _dangling_inputs(joined: "JoinedView") -> dict:
    """Collect dangling-reference inputs from the current evidence trail."""
    return {
        "dangling_specs": [(s.id, s.node_id) for s in joined.specs],
        "dangling_gates": [(g.id, g.node_id) for g in joined.gates],
        "dangling_records": [
            (r.id, r.artifact_spec_id, r.location) for r in joined.records
        ],
        "dangling_attempts": [(a.id, a.node_id) for a in joined.attempts],
    }


def diagnose(
    joined: "JoinedView",
    baseline: BaselineSource,
    *,
    root: Path | None = None,
    minutes: int = 60,
    limit: int = 5,
    today: date | None = None,
) -> DiagnoseOutcome:
    """Run the graph-impact diagnostic: the production path behind `graph impact`.

    Loads the baseline side through `baseline` (raising `BaselineUnavailable`
    when it cannot be loaded), prepares ranking boost inputs once via the
    shared `prepare` seam, and diffs baseline against the joined view's
    current nodes/edges over the shared progress store. Read-only: writes
    nothing, blocks nothing, never revokes asserted progress.
    """
    loaded = baseline.load()
    inputs = prepare(joined, root, today)
    report = compute_impact(
        loaded.nodes,
        loaded.edges,
        joined.nodes,
        joined.edges,
        joined.store,
        minutes=minutes,
        limit=limit,
        **inputs.recommend_kwargs(),
        **_dangling_inputs(joined),
    )
    return DiagnoseOutcome(report=report, baseline_label=loaded.label)


def format_report(report: ImpactReport, baseline_label: str) -> list[str]:
    """Render the advisory findings as terminal lines. Pure of printing."""
    lines = [f"graph impact vs {baseline_label}:"]
    if report.quiet:
        lines.append("  no changes — the edit flips no readiness, moves no recommendation,")
        lines.append("  dangles no reference, and leaves no no-op edge.")
        return lines
    for flip in report.flips:
        lines.append(f"  flip: {flip.node_id}: {flip.baseline_state} -> {flip.current_state}")
    for node_id in report.asserted_standing:
        lines.append(f"  asserted progress stands (not revoked): {node_id}")
    for change in report.recommendation_changes:
        before = f"#{change.baseline_rank}" if change.baseline_rank is not None else "(unranked)"
        after = f"#{change.current_rank}" if change.current_rank is not None else "(unranked)"
        lines.append(f"  recommendation: {change.node_id}: {before} -> {after}")
    for dangling in report.dangling:
        lines.append(
            f"  dangling: {dangling.node_id} still named by "
            f"{', '.join(sorted(dangling.referenced_by))}"
        )
    for edge in report.no_op_edges:
        lines.append(f"  no-op edge: {edge.edge_id} ({edge.source} -> {edge.target})")
    return lines


