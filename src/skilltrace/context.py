"""Deep JoinedView module — one seam for the scattered read-only join (C1).

Every Mentor view and the disposable exports load the same five layers
(graph, evidence, execution, policy, resources) with slightly different
error policies. This module is the single deep module that owns the join:

* ``load_context_strict(root, loaders) -> JoinedView`` — expected repository
  loader failures are collected into ``view.errors``; unexpected programming
  exceptions propagate.
  For ``export`` and other snapshot concerns a non-empty ``errors`` means
  "refuse to write".

* ``load_context_lenient(root, loaders) -> JoinedView`` — the Skill graph
  (``SkillNodes`` + ``GraphEdges``) and the progress store are strict
  (a ``NodeLoadError``/``EdgeLoadError``/``ProgressStoreError`` is re-raised);
  evidence/execution/resources/policy degrade to empty collections and every
  degraded layer's name is recorded into ``view.degraded``, so surfaces that
  keep serving can warn honestly about what they could not see.
  For ``node``/``today``/``next``/``report`` this matches the existing
  try/except blocks.

The seam for testability is the injected ``Loaders`` record — two adapters
justify the seam (filesystem vs in-memory doubles). The view carries
precomputed derived indexes (``node_map``, ``titles``, ``resources_by_node``,
``has_gate``, ``specs_by_node``) so callers do a field lookup instead of
recomputing the same map. The module is stateless and has no per-process
cache.

Respect ADR 0001 (progress store) and ADR 0002 (CLI only, not a revived
top-level interface layer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from .evidence._schema import EvidenceLoadError
from .evidence.attempts import AssessmentAttempt, load_assessment_attempts
from .evidence.gates import ValidationGate, load_validation_gates
from .evidence.records import EvidenceRecord, load_evidence_records
from .evidence.specs import ArtifactSpec, load_artifact_specs
from .events import load_events
from .execution._store import ExecutionLoadError
from .execution.blockers import Blocker, load_blockers
from .execution.remediation import RemediationAction, load_remediation_actions
from .execution.reviews import Review, load_reviews
from .execution.sessions import Session, load_sessions
from .execution.work import SessionWork, load_session_work
from .graph.edges import EdgeLoadError, GraphEdge, load_edges
from .graph.nodes import NodeLoadError, SkillNode, load_nodes
from .graph.state import ProgressStore, ProgressStoreError, load_state
from .policy.loading import POLICY_FILES, PolicyLoadError, load_policy_doc
from .policy.retention_model import RetentionPolicySeed, retention_seed_from_doc
from .policy.cadence import Cadence, CadenceInterval
from .policy.mastery import MasteryValues
from .resources.registry import LearningResource, ResourceLoadError, load_resources
from .resources.registry import resources_for_node as _resources_for_node
from .resources.status import DEFAULT_STALE_AFTER_DAYS

_EDGES_RELPATH = Path("graph") / "edges.yaml"


def _default_load_nodes(root: Path) -> list[SkillNode]:
    return load_nodes(root)


def _default_load_edges(root: Path) -> list[GraphEdge]:
    # Mirrors export_data.py: missing edges.yaml is legitimate (fresh repo).
    if not (Path(root) / _EDGES_RELPATH).exists():
        return []
    return load_edges(root)


def _default_load_state(root: Path) -> ProgressStore:
    return load_state(root)


def _default_load_specs(root: Path) -> list[ArtifactSpec]:
    return load_artifact_specs(root)


def _default_load_gates(root: Path) -> list[ValidationGate]:
    return load_validation_gates(root)


def _default_load_records(root: Path) -> list[EvidenceRecord]:
    return load_evidence_records(root)


def _default_load_attempts(root: Path) -> list[AssessmentAttempt]:
    return load_assessment_attempts(root)


def _default_load_sessions(root: Path) -> list[Session]:
    return load_sessions(root)


def _default_load_work(root: Path) -> list[SessionWork]:
    return load_session_work(root)


def _default_load_blockers(root: Path) -> list[Blocker]:
    return load_blockers(root)


def _default_load_remediations(root: Path) -> list[RemediationAction]:
    return load_remediation_actions(root)


def _default_load_reviews(root: Path) -> list[Review]:
    return load_reviews(root)


def _default_load_resources(root: Path) -> list[LearningResource]:
    return load_resources(root)


def _default_load_events(root: Path) -> list[dict]:
    return load_events(root)


def _default_load_policies(root: Path) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    for filename in POLICY_FILES:
        docs[filename] = load_policy_doc(root, filename)
    return docs


@dataclass
class Loaders:
    """Injectable loader adapters. Two adapters (prod FS vs test doubles) justify the seam."""

    load_nodes: Callable[[Path], list[SkillNode]] = _default_load_nodes
    load_edges: Callable[[Path], list[GraphEdge]] = _default_load_edges
    load_state: Callable[[Path], ProgressStore] = _default_load_state
    load_specs: Callable[[Path], list[ArtifactSpec]] = _default_load_specs
    load_gates: Callable[[Path], list[ValidationGate]] = _default_load_gates
    load_records: Callable[[Path], list[EvidenceRecord]] = _default_load_records
    load_attempts: Callable[[Path], list[AssessmentAttempt]] = _default_load_attempts
    load_sessions: Callable[[Path], list[Session]] = _default_load_sessions
    load_work: Callable[[Path], list[SessionWork]] = _default_load_work
    load_blockers: Callable[[Path], list[Blocker]] = _default_load_blockers
    load_remediations: Callable[[Path], list[RemediationAction]] = _default_load_remediations
    load_reviews: Callable[[Path], list[Review]] = _default_load_reviews
    load_resources: Callable[[Path], list[LearningResource]] = _default_load_resources
    load_events: Callable[[Path], list[dict]] = _default_load_events
    load_policies: Callable[[Path], dict[str, dict]] = _default_load_policies


@dataclass(frozen=True)
class PolicyAccess:
    """Typed access to policy values loaded as part of a joined snapshot."""

    documents: dict[str, dict] = field(default_factory=dict)

    def _document(self, filename: str) -> dict:
        value = self.documents.get(filename)
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _float_value(value: object) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _weights(raw: object) -> dict[str, float]:
        if not isinstance(raw, dict):
            return {}
        weights: dict[str, float] = {}
        for name, value in raw.items():
            numeric = PolicyAccess._float_value(value)
            if numeric is not None:
                weights[str(name)] = numeric
        return weights

    @property
    def track_weights(self) -> dict[str, float]:
        return self._weights(self._document("recommendation.yaml").get("track_weights"))

    @property
    def factor_weights(self) -> dict[str, float]:
        return self._weights(self._document("recommendation.yaml").get("factor_weights"))

    @property
    def failed_attempt_threshold(self) -> int | None:
        value = self._document("remediation.yaml").get("failed_attempt_threshold")
        return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None

    @property
    def retention(self) -> RetentionPolicySeed | None:
        document = self._document("retention_model.yaml")
        required = (
            "default_half_life_days",
            "satisfactory_growth_factor",
            "unsatisfactory_reduction_factor",
            "attention_threshold",
        )
        if not all(key in document for key in required):
            return None
        try:
            return retention_seed_from_doc(document)
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def review_grace_days(self) -> int | None:
        value = self._document("review_cadence.yaml").get("missed_review_grace_days")
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @property
    def remediation_suggestion_defaults(self) -> tuple[int | None, int | None]:
        defaults = self._document("remediation.yaml").get("suggestion_defaults")
        if not isinstance(defaults, dict):
            return None, None
        minutes = defaults.get("suggested_minutes")
        due_in_days = defaults.get("due_in_days")
        return (
            minutes if isinstance(minutes, int) and not isinstance(minutes, bool) else None,
            due_in_days if isinstance(due_in_days, int) and not isinstance(due_in_days, bool) else None,
        )

    @property
    def resource_stale_after_days(self) -> int:
        value = self._document("resource_verification.yaml").get("stale_after_days")
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value > 0
            else DEFAULT_STALE_AFTER_DAYS
        )

    @property
    def session_templates(self) -> set[str]:
        document = self._document("workload.yaml")
        values = document.get("session_templates")
        if not isinstance(values, dict):
            return set()
        return {str(name) for name in values if not isinstance(name, bool)}

    @property
    def cadence(self) -> Cadence:
        document = self._document("review_cadence.yaml")
        cadence = Cadence(
            schedule_reviews_after_pass=document.get("schedule_reviews_after_pass") is True
        )
        for raw in document.get("intervals") or []:
            if not isinstance(raw, dict):
                continue
            day_count = raw.get("days_after_pass")
            if not isinstance(day_count, int) or isinstance(day_count, bool):
                continue
            expected_minutes = raw.get("expected_minutes")
            if isinstance(expected_minutes, bool):
                expected_minutes = None
            cadence.intervals.append(
                CadenceInterval(
                    label=str(raw.get("label", f"day_{day_count}")),
                    days_after_pass=day_count,
                    expected_minutes=(
                        expected_minutes if isinstance(expected_minutes, int) else None
                    ),
                )
            )
        return cadence

    @property
    def analytics(self) -> dict:
        """The analytics policy document (advisory only — never blocks commands)."""
        return self._document("analytics.yaml")

    @property
    def mastery(self) -> MasteryValues:
        document = self._document("mastery_promotion.yaml")
        values = MasteryValues()
        min_accepted = document.get("min_accepted_evidence")
        if isinstance(min_accepted, int) and not isinstance(min_accepted, bool):
            values.min_accepted_evidence = min_accepted
        min_days = document.get("min_days_pass_to_review")
        if isinstance(min_days, int) and not isinstance(min_days, bool):
            values.min_days_pass_to_review = min_days
        return values


@dataclass
class JoinedView:
    """Flat joined view over all layers plus precomputed derived indexes.

    ``errors`` is non-empty only for the strict entry point; the lenient
    entry point raises on graph/state failures and degrades the rest to
    empty lists, so ``errors`` stays empty there.
    """

    # raw
    nodes: list[SkillNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    store: ProgressStore = field(default_factory=ProgressStore)
    specs: list[ArtifactSpec] = field(default_factory=list)
    gates: list[ValidationGate] = field(default_factory=list)
    records: list[EvidenceRecord] = field(default_factory=list)
    attempts: list[AssessmentAttempt] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)
    work: list[SessionWork] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    remediations: list[RemediationAction] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    resources: list[LearningResource] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    policies: dict[str, dict] = field(default_factory=dict)
    policy: PolicyAccess = field(default_factory=PolicyAccess)
    errors: list[str] = field(default_factory=list)
    # Lenient-only: names of the optional layers that failed to load and were
    # degraded to empty (strict collects the same failures into ``errors``).
    degraded: list[str] = field(default_factory=list)

    # derived
    node_map: dict[str, SkillNode] = field(default_factory=dict)
    titles: dict[str, str] = field(default_factory=dict)
    resources_by_node: dict[str, list[LearningResource]] = field(default_factory=dict)
    has_gate: set[str] = field(default_factory=set)
    specs_by_node: dict[str, list[ArtifactSpec]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _build_derived(view: JoinedView) -> None:
    """Populate derived indexes from raw collections. Pure of I/O."""
    view.node_map = {n.id: n for n in view.nodes}
    view.titles = {n.id: n.title for n in view.nodes}
    # per-node reverse index — matches resources.registry.resources_for_node
    by_node: dict[str, list[LearningResource]] = {}
    for node in view.nodes:
        by_node[node.id] = _resources_for_node(node.id, view.resources)
    view.resources_by_node = by_node
    view.has_gate = {g.node_id for g in view.gates}
    specs_map: dict[str, list[ArtifactSpec]] = {}
    for spec in view.specs:
        specs_map.setdefault(spec.node_id, []).append(spec)
    view.specs_by_node = specs_map
    view.policy = PolicyAccess(view.policies)


def load_context_strict(root: Path | str, loaders: Loaders | None = None) -> JoinedView:
    """Strict: expected loader failures are collected; defects propagate."""
    root_path = Path(root)
    ld = loaders or Loaders()
    view = JoinedView(errors=[])
    errors = view.errors

    try:
        view.nodes = ld.load_nodes(root_path)
    except NodeLoadError as exc:
        errors.append(str(exc))
        view.nodes = []

    try:
        view.edges = ld.load_edges(root_path)
    except EdgeLoadError as exc:
        errors.append(str(exc))
        view.edges = []

    try:
        view.store = ld.load_state(root_path)
    except ProgressStoreError as exc:
        errors.append(str(exc))
        view.store = ProgressStore()

    for attr, loader in (
        ("specs", ld.load_specs),
        ("gates", ld.load_gates),
        ("records", ld.load_records),
        ("attempts", ld.load_attempts),
        ("sessions", ld.load_sessions),
        ("work", ld.load_work),
        ("blockers", ld.load_blockers),
        ("remediations", ld.load_remediations),
        ("reviews", ld.load_reviews),
        ("resources", ld.load_resources),
    ):
        try:
            setattr(view, attr, loader(root_path))
        except (EvidenceLoadError, ExecutionLoadError, ResourceLoadError) as exc:
            errors.append(str(exc))
            setattr(view, attr, [])

    # events is audit-only and never raises (load_events returns [] on miss)
    try:
        view.events = ld.load_events(root_path)
    except (OSError, yaml.YAMLError) as exc:
        errors.append(str(exc))
        view.events = []

    try:
        view.policies = ld.load_policies(root_path)
    except PolicyLoadError as exc:
        errors.append(str(exc))
        view.policies = {}

    _build_derived(view)
    return view


def load_context_lenient(root: Path | str, loaders: Loaders | None = None) -> JoinedView:
    """Lenient: graph/state re-raise; evidence/execution/resources degrade to empty.

    This matches the existing Mentor commands (``node``, ``today``, ``next``,
    reports) which fail fast on unloadable Skill graph or progress store but
    keep rendering when optional layers warn.
    """
    root_path = Path(root)
    ld = loaders or Loaders()
    view = JoinedView(errors=[])

    # Strict — re-raise (let caller exit non-zero, matching node/today/recommend)
    view.nodes = ld.load_nodes(root_path)
    view.edges = ld.load_edges(root_path)
    view.store = ld.load_state(root_path)

    # Lenient — degrade to empty on failure, never raise; record what degraded
    # so serving surfaces can warn ("forms stay enabled, domain refusal is truth").
    view.degraded = []
    for attr, loader in (
        ("specs", ld.load_specs),
        ("gates", ld.load_gates),
        ("records", ld.load_records),
        ("attempts", ld.load_attempts),
        ("sessions", ld.load_sessions),
        ("work", ld.load_work),
        ("blockers", ld.load_blockers),
        ("remediations", ld.load_remediations),
        ("reviews", ld.load_reviews),
        ("resources", ld.load_resources),
    ):
        try:
            setattr(view, attr, loader(root_path))
        except (EvidenceLoadError, ExecutionLoadError, ResourceLoadError):
            setattr(view, attr, [])
            view.degraded.append(attr)

    # events and policies are lenient too (today/next never fail on them)
    try:
        view.events = ld.load_events(root_path)
    except (OSError, yaml.YAMLError):
        view.events = []
        view.degraded.append("events")
    try:
        view.policies = ld.load_policies(root_path)
    except PolicyLoadError:
        view.policies = {}
        view.degraded.append("policies")

    _build_derived(view)
    return view
