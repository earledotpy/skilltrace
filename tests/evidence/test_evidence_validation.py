"""Evidence-trail validation: the cross-record integrity contract (issue #11).

The four loaders validate one record's shape; `check_evidence` checks the trail
as a whole — duplicate ids, dangling references, one-gate-per-node, supersede
chains — and warns on uncovered nodes and artifact drift. The pure seam takes
already-loaded lists, so these fixtures are hand-built; `load_and_validate_evidence`
against the real seed and the command path live in the sibling test files.

Drift is exercised here with an injected probe (a dict lookup); the real
hash/file path is pinned in test_artifacts.py.
"""

from __future__ import annotations

from skilltrace.evidence.attempts import AssessmentAttempt
from skilltrace.evidence.gates import ValidationGate
from skilltrace.evidence.records import EvidenceRecord
from skilltrace.evidence.specs import ArtifactSpec
from skilltrace.evidence.validation import EvidenceValidationResult, check_evidence

NODE_A = "math.arithmetic.order_operations_01"
NODE_B = "math.algebra.linear_equations_01"


def _spec(spec_id: str, node_id: str = NODE_A, *, required: bool = True) -> ArtifactSpec:
    return ArtifactSpec(
        id=spec_id,
        node_id=node_id,
        title=spec_id,
        artifact_kind="problem_set",
        required=required,
        minimum_count=1,
    )


def _gate(gate_id: str, node_id: str = NODE_A) -> ValidationGate:
    return ValidationGate(id=gate_id, node_id=node_id, authority="manual")


def _record(
    record_id: str,
    spec_id: str = "spec.a",
    *,
    location: str = "evidence/a.md",
    artifact_hash: str = "sha256:aaa",
    supersedes: str | None = None,
    supersede_reason: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=record_id,
        artifact_spec_id=spec_id,
        location=location,
        accepted=True,
        accepted_by="learner_manual",
        artifact_hash=artifact_hash,
        supersedes=supersedes,
        supersede_reason=supersede_reason,
    )


def _attempt(attempt_id: str, node_id: str = NODE_A) -> AssessmentAttempt:
    return AssessmentAttempt(id=attempt_id, node_id=node_id, outcome="passed")


def _clean_trail():
    """A minimal internally-consistent trail: one covered node, no records."""
    return dict(
        node_ids=[NODE_A],
        specs=[_spec("spec.a")],
        gates=[_gate("gate.a")],
        records=[],
        attempts=[],
    )


# --- Happy path -------------------------------------------------------------


def test_clean_trail_passes_with_no_issues():
    result = check_evidence(**_clean_trail())
    assert isinstance(result, EvidenceValidationResult)
    assert result.ok
    assert result.errors == []
    assert result.warnings == []
    assert result.spec_count == 1
    assert result.gate_count == 1


# --- Duplicate ids, per type ------------------------------------------------


def test_duplicate_spec_id_is_error():
    trail = _clean_trail()
    trail["specs"] = [_spec("spec.dup"), _spec("spec.dup")]
    result = check_evidence(**trail)
    assert not result.ok
    assert any("duplicate artifact spec id: spec.dup" in e for e in result.errors)


def test_duplicate_gate_id_is_error():
    trail = _clean_trail()
    trail["gates"] = [_gate("gate.dup"), _gate("gate.dup", node_id=NODE_B)]
    trail["node_ids"] = [NODE_A, NODE_B]
    result = check_evidence(**trail)
    assert any("duplicate validation gate id: gate.dup" in e for e in result.errors)


def test_duplicate_record_id_is_error():
    trail = _clean_trail()
    trail["records"] = [_record("ev.x.001"), _record("ev.x.001")]
    result = check_evidence(**trail)
    assert any("duplicate evidence record id: ev.x.001" in e for e in result.errors)


def test_duplicate_attempt_id_is_error():
    trail = _clean_trail()
    trail["attempts"] = [_attempt("att.x.001"), _attempt("att.x.001")]
    result = check_evidence(**trail)
    assert any("duplicate assessment attempt id: att.x.001" in e for e in result.errors)


# --- Dangling references ----------------------------------------------------


def test_spec_dangling_node_is_error():
    trail = _clean_trail()
    trail["specs"] = [_spec("spec.a"), _spec("spec.ghost", node_id="ghost.node_99")]
    result = check_evidence(**trail)
    assert any("spec.ghost" in e and "ghost.node_99" in e for e in result.errors)


def test_gate_dangling_node_is_error():
    trail = _clean_trail()
    trail["gates"] = [_gate("gate.a"), _gate("gate.ghost", node_id="ghost.node_99")]
    result = check_evidence(**trail)
    assert any("gate.ghost" in e and "ghost.node_99" in e for e in result.errors)


def test_record_dangling_spec_is_error():
    trail = _clean_trail()
    trail["records"] = [_record("ev.x.001", spec_id="spec.missing")]
    result = check_evidence(**trail)
    assert any(
        "ev.x.001" in e and "spec.missing" in e for e in result.errors
    )


def test_attempt_dangling_node_is_error():
    trail = _clean_trail()
    trail["attempts"] = [_attempt("att.x.001", node_id="ghost.node_99")]
    result = check_evidence(**trail)
    assert any("att.x.001" in e and "ghost.node_99" in e for e in result.errors)


def test_record_dangling_supersedes_is_error():
    trail = _clean_trail()
    trail["records"] = [
        _record(
            "ev.a.002",
            spec_id="spec.a",
            supersedes="ev.a.001",
            supersede_reason="fix",
        )
    ]
    result = check_evidence(**trail)
    assert any(
        "ev.a.002" in e and "ev.a.001" in e and "unknown record" in e
        for e in result.errors
    )


# --- Two gates on one node --------------------------------------------------


def test_two_gates_on_one_node_is_error():
    trail = _clean_trail()
    trail["gates"] = [_gate("gate.a1"), _gate("gate.a2")]
    result = check_evidence(**trail)
    assert any(
        NODE_A in e and "gate.a1" in e and "gate.a2" in e for e in result.errors
    )


# --- Supersede chain: cross-spec and double-supersede -----------------------


def test_cross_spec_supersede_is_error():
    trail = _clean_trail()
    trail["specs"] = [_spec("spec.a"), _spec("spec.b", node_id=NODE_A)]
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a"),
        _record(
            "ev.a.002",
            spec_id="spec.b",  # different spec than its target
            supersedes="ev.a.001",
            supersede_reason="oops",
        ),
    ]
    result = check_evidence(**trail)
    assert any(
        "ev.a.002" in e and "different spec" in e for e in result.errors
    )


def test_double_supersede_is_error():
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a"),
        _record("ev.a.002", spec_id="spec.a", supersedes="ev.a.001", supersede_reason="a"),
        _record("ev.a.003", spec_id="spec.a", supersedes="ev.a.001", supersede_reason="b"),
    ]
    result = check_evidence(**trail)
    assert any(
        "ev.a.001" in e and "more than once" in e for e in result.errors
    )


def test_valid_supersede_chain_passes():
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a"),
        _record("ev.a.002", spec_id="spec.a", supersedes="ev.a.001", supersede_reason="fix"),
    ]
    result = check_evidence(**trail)
    assert result.ok, result.errors


# --- Warnings: per-node coverage --------------------------------------------


def test_node_with_no_gate_warns():
    trail = _clean_trail()
    trail["gates"] = []
    result = check_evidence(**trail)
    assert result.ok  # a warning, not an error
    assert any(NODE_A in w and "no gate" in w for w in result.warnings)


def test_node_with_no_required_spec_warns():
    trail = _clean_trail()
    trail["specs"] = [_spec("spec.a", required=False)]
    result = check_evidence(**trail)
    assert result.ok
    assert any(NODE_A in w and "no required artifact spec" in w for w in result.warnings)


def test_duplicate_node_id_does_not_double_warn():
    # A duplicated node id in the graph is a graph-layer concern; here it must
    # not produce two identical coverage warnings.
    trail = _clean_trail()
    trail["node_ids"] = [NODE_A, NODE_A]
    trail["gates"] = []
    result = check_evidence(**trail)
    no_gate = [w for w in result.warnings if "no gate" in w]
    assert len(no_gate) == 1


# --- Warnings: artifact drift (injected probe) ------------------------------


def _probe_from(mapping):
    return lambda location: mapping.get(location)


def test_no_drift_when_hash_matches():
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a", location="evidence/a.md", artifact_hash="sha256:aaa")
    ]
    result = check_evidence(**trail, probe=_probe_from({"evidence/a.md": "sha256:aaa"}))
    assert result.warnings == []


def test_drift_when_hash_differs_warns():
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a", location="evidence/a.md", artifact_hash="sha256:aaa")
    ]
    result = check_evidence(**trail, probe=_probe_from({"evidence/a.md": "sha256:zzz"}))
    assert result.ok
    assert any("ev.a.001" in w and "no longer matches" in w for w in result.warnings)


def test_drift_when_artifact_missing_warns():
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a", location="evidence/gone.md")
    ]
    result = check_evidence(**trail, probe=_probe_from({}))
    assert any("ev.a.001" in w and "is missing" in w for w in result.warnings)


def test_superseded_record_is_still_drift_checked():
    # Drift is checked across every record, superseded ones included.
    trail = _clean_trail()
    trail["records"] = [
        _record("ev.a.001", spec_id="spec.a", location="evidence/old.md", artifact_hash="sha256:old"),
        _record(
            "ev.a.002",
            spec_id="spec.a",
            location="evidence/new.md",
            artifact_hash="sha256:new",
            supersedes="ev.a.001",
            supersede_reason="fix",
        ),
    ]
    probe = _probe_from({"evidence/old.md": "sha256:CHANGED", "evidence/new.md": "sha256:new"})
    result = check_evidence(**trail, probe=probe)
    assert any("ev.a.001" in w and "no longer matches" in w for w in result.warnings)


def test_drift_not_checked_without_probe():
    trail = _clean_trail()
    trail["records"] = [_record("ev.a.001", spec_id="spec.a")]
    result = check_evidence(**trail)  # no probe
    assert result.warnings == []


# --- Reports every issue at once --------------------------------------------


def test_reports_multiple_issues_together():
    result = check_evidence(
        node_ids=[NODE_A],
        specs=[_spec("spec.dup"), _spec("spec.dup")],
        gates=[],
        records=[_record("ev.x.001", spec_id="spec.missing")],
        attempts=[],
    )
    # duplicate spec + dangling record spec are both errors; no-gate is a warning.
    assert len(result.errors) >= 2
    assert any("no gate" in w for w in result.warnings)
