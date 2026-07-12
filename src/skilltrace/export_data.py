"""Load-everything-for-export: the one place `export markdown` and
`export sqlite` gather every layer's data.

Mirrors `graph.validation.load_and_validate` and
`execution.validation.load_and_validate_execution`: loader failures are
*folded into* `ExportData.errors` rather than raised, so a command can report
bad data cleanly. Unlike those validators, a non-empty `errors` here means the
export **refuses to write** (`ok` is false) — a snapshot or mirror built from
partially-loaded data would misrepresent the repository, which is worse than
refusing (issue #38).

`graph/edges.yaml` is the one file treated as legitimately absent (mirrors
`sync`): a fresh repo with nodes but no edges yet is not broken. Every other
source here — evidence, execution, policy, resources — ships with the seed or
is created on first use (execution files, `events.yaml`), and its loader
already tolerates a missing file where that is legitimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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
from .resources.registry import LearningResource, ResourceLoadError, load_resources

_EDGES_RELPATH = Path("graph") / "edges.yaml"


@dataclass
class ExportData:
    """Every record type an export mirrors, plus any load errors encountered."""

    nodes: list[SkillNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    state: ProgressStore = field(default_factory=ProgressStore)
    artifact_specs: list[ArtifactSpec] = field(default_factory=list)
    validation_gates: list[ValidationGate] = field(default_factory=list)
    evidence_records: list[EvidenceRecord] = field(default_factory=list)
    attempts: list[AssessmentAttempt] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)
    session_work: list[SessionWork] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    remediation_actions: list[RemediationAction] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    resources: list[LearningResource] = field(default_factory=list)
    policies: dict[str, dict] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_export_data(root: Path | str) -> ExportData:
    """Load every record type from `root`, folding loader failures into errors."""
    root_path = Path(root)
    data = ExportData()
    errors = data.errors

    try:
        data.nodes = load_nodes(root_path)
    except NodeLoadError as exc:
        errors.append(str(exc))

    if (root_path / _EDGES_RELPATH).exists():
        try:
            data.edges = load_edges(root_path)
        except EdgeLoadError as exc:
            errors.append(str(exc))

    try:
        data.state = load_state(root_path)
    except ProgressStoreError as exc:
        errors.append(str(exc))

    try:
        data.artifact_specs = load_artifact_specs(root_path)
    except EvidenceLoadError as exc:
        errors.append(str(exc))
    try:
        data.validation_gates = load_validation_gates(root_path)
    except EvidenceLoadError as exc:
        errors.append(str(exc))
    try:
        data.evidence_records = load_evidence_records(root_path)
    except EvidenceLoadError as exc:
        errors.append(str(exc))
    try:
        data.attempts = load_assessment_attempts(root_path)
    except EvidenceLoadError as exc:
        errors.append(str(exc))

    try:
        data.sessions = load_sessions(root_path)
    except ExecutionLoadError as exc:
        errors.append(str(exc))
    try:
        data.session_work = load_session_work(root_path)
    except ExecutionLoadError as exc:
        errors.append(str(exc))
    try:
        data.blockers = load_blockers(root_path)
    except ExecutionLoadError as exc:
        errors.append(str(exc))
    try:
        data.remediation_actions = load_remediation_actions(root_path)
    except ExecutionLoadError as exc:
        errors.append(str(exc))
    try:
        data.reviews = load_reviews(root_path)
    except ExecutionLoadError as exc:
        errors.append(str(exc))

    # The event log is audit-only and never a defect when absent (a fresh
    # repo has logged nothing yet) — `load_events` already returns [].
    data.events = load_events(root_path)

    try:
        data.resources = load_resources(root_path)
    except ResourceLoadError as exc:
        errors.append(str(exc))

    for filename in POLICY_FILES:
        try:
            data.policies[filename] = load_policy_doc(root_path, filename)
        except PolicyLoadError as exc:
            errors.append(str(exc))

    return data
