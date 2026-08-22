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

from .context import JoinedView, load_context_strict
from .evidence.attempts import AssessmentAttempt
from .evidence.gates import ValidationGate
from .evidence.records import EvidenceRecord
from .evidence.specs import ArtifactSpec
from .execution.blockers import Blocker
from .execution.remediation import RemediationAction
from .execution.reviews import Review
from .execution.sessions import Session
from .execution.work import SessionWork
from .graph.edges import GraphEdge
from .graph.nodes import SkillNode
from .graph.state import ProgressStore
from .resources.registry import LearningResource


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


def _view_to_export_data(view: JoinedView) -> ExportData:
    """Translate the strict JoinedView into the legacy ExportData shape."""
    return ExportData(
        nodes=view.nodes,
        edges=view.edges,
        state=view.store,
        artifact_specs=view.specs,
        validation_gates=view.gates,
        evidence_records=view.records,
        attempts=view.attempts,
        sessions=view.sessions,
        session_work=view.work,
        blockers=view.blockers,
        remediation_actions=view.remediations,
        reviews=view.reviews,
        events=view.events,
        resources=view.resources,
        policies=dict(view.policies),
        errors=list(view.errors),
    )


def load_export_data(root: Path | str) -> ExportData:
    """Load every record type via the strict JoinedView seam (one seam, N consumers)."""
    view = load_context_strict(root)
    return _view_to_export_data(view)
