"""Evidence layer: the four evidence-trail record types and their strict loaders.

ArtifactSpec, ValidationGate, EvidenceRecord, and AssessmentAttempt, each with a
closed-schema loader in the mould of the graph layer (issue #10). Unknown fields
and unknown enum values fail loading — the schema is the boundary, so an AI
acceptance authority is unrepresentable and a stray `node_id` on a record fails
outright. Cross-record checks (duplicate IDs, dangling references, supersede
chains) belong to `validate evidence` (issue #11), not these loaders.

`ids` holds the ``ev.``/``att.`` ID validators and the per-node sequence
allocator used by the submit / attempt-record commands (issues #12, #13).
"""

from __future__ import annotations

from ._schema import EvidenceLoadError
from .attempts import (
    OUTCOMES,
    AssessmentAttempt,
    load_assessment_attempt,
    load_assessment_attempts,
)
from .gates import (
    AUTHORITIES,
    ValidationGate,
    load_validation_gate,
    load_validation_gates,
)
from .ids import (
    allocate_attempt_id,
    allocate_evidence_id,
    is_valid_attempt_id,
    is_valid_evidence_id,
    split_attempt_id,
    split_evidence_id,
)
from .records import (
    ACCEPTED_BY_VALUES,
    EvidenceRecord,
    load_evidence_record,
    load_evidence_records,
)
from .specs import (
    ArtifactSpec,
    load_artifact_spec,
    load_artifact_specs,
)

__all__ = [
    "ACCEPTED_BY_VALUES",
    "AUTHORITIES",
    "OUTCOMES",
    "ArtifactSpec",
    "AssessmentAttempt",
    "EvidenceLoadError",
    "EvidenceRecord",
    "ValidationGate",
    "allocate_attempt_id",
    "allocate_evidence_id",
    "is_valid_attempt_id",
    "is_valid_evidence_id",
    "load_artifact_spec",
    "load_artifact_specs",
    "load_assessment_attempt",
    "load_assessment_attempts",
    "load_evidence_record",
    "load_evidence_records",
    "load_validation_gate",
    "load_validation_gates",
    "split_attempt_id",
    "split_evidence_id",
]
