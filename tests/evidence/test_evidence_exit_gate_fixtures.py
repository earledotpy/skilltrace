"""v0.4 exit gate — the invalid-evidence matrix, driven through the CLI.

`test_evidence_validation.py` proves the *logic* of every cross-record check
against the pure `check_evidence` seam, and the per-loader unit tests prove each
shape rule. This module proves the same failures survive a round trip through the
real loaders and the `validate evidence` command on real files: every
`raise EvidenceLoadError` (the four loaders + `_schema`) and every
`result.errors.append(...)` site (`validation.py`) maps to one case here, and each
case asserts on its *distinctive* offender substring — not merely `rc == 1`, which
a single blanket failure would satisfy.

Two groups can be caught *only* here — they are loader/structural rejections the
pure seam never sees, because it takes already-loaded objects: an `ai` authority,
a stray `node_id` on a record (an unknown field), and the structural YAML errors
(unparseable, missing top key, non-list). The rest are re-proved end to end so the
fixture matrix mirrors the roadmap's v0.4 test list.

The one raise-site deliberately *not* exercised is `_schema.read_yaml_list`'s
`OSError` "cannot read file" branch: it is not portably triggerable through a
YAML fixture (a present-but-unreadable file is platform-specific on Windows), and
a merely *absent* file is a clean empty-list load, not an error.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from skilltrace import cli

# Node ids the fixtures reference. A valid node must exist so a dangling-reference
# case tests "references an *absent* id", not "there are no nodes at all".
NODE = "a.b.n_01"
NODE_B = "a.b.n_02"

# Well-formed evidence ids (`ev.<node_id>.NNN`) for the record cases.
EV1 = f"ev.{NODE}.001"
EV2 = f"ev.{NODE}.002"
EV3 = f"ev.{NODE}.003"
ATT1 = f"att.{NODE}.001"


def _run_validate(root) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.run(["validate", "evidence"], root=root)
    return rc, buf.getvalue()


def _covered(b):
    """A baseline: one node with a matching required spec + manual gate.

    Returns the builder so a caller can add the one defective entry it is testing;
    the baseline keeps every *other* node/spec/gate consistent so the only failure
    is the injected one.
    """
    return (
        b.node(NODE)
        .specs([b.spec_dict("spec.a", NODE)])
        .gates([b.gate_dict("gate.a", NODE)])
    )


# --- Happy path -------------------------------------------------------------


def test_minimal_valid_trail_validates_clean(evidence_builder):
    root = _covered(evidence_builder).write()
    rc, out = _run_validate(root)
    assert rc == 0, out
    assert "validate evidence: OK" in out


# --- Loader-only rejections (invisible to the pure check_evidence seam) ------


def test_ai_authority_gate_fails_through_the_cli(evidence_builder):
    # An AI acceptance authority is unrepresentable — the gate loader rejects it.
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.a", NODE, overrides={"authority": "ai"})])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "ai" in out and "authority" in out


def test_record_with_stray_node_id_fails_as_unknown_field(evidence_builder):
    # A record carries no node_id (the spec is the only linkage); a stray one is
    # an unknown field the closed schema rejects.
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict(EV1, "spec.a", overrides={"node_id": NODE})])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "unknown field" in out and "node_id" in out


def test_unparseable_yaml_fails_through_the_cli(evidence_builder):
    root = (
        _covered(evidence_builder)
        .raw_file("evidence/attempts.yaml", "attempts: [unclosed\n")
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "unparseable" in out


def test_missing_top_key_fails_through_the_cli(evidence_builder):
    root = (
        _covered(evidence_builder)
        .raw_file("evidence/attempts.yaml", "wrong_key: []\n")
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "top-level 'attempts:'" in out


def test_non_list_top_key_fails_through_the_cli(evidence_builder):
    root = (
        _covered(evidence_builder)
        .raw_file("evidence/artifact_specs.yaml", "artifact_specs: 5\n")
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "'artifact_specs' must be a list" in out


def test_non_mapping_entry_fails_through_the_cli(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs(["not-a-mapping"])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "is not a mapping" in out


# --- Artifact spec shape errors --------------------------------------------


def test_spec_unknown_field_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE, overrides={"bogus": 1})])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "unknown field" in out and "bogus" in out


def test_spec_missing_required_field_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE, omit=("title",))])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "missing required field" in out and "title" in out


def test_spec_invalid_node_id_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", "Not A Node")])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "invalid node_id" in out


def test_spec_non_boolean_required_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE, overrides={"required": "yes"})])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "non-boolean required" in out


def test_spec_zero_minimum_count_fails(evidence_builder):
    # An optional spec is `required: false`, never a zero count.
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE, minimum_count=0)])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "invalid minimum_count" in out


# --- Validation gate shape errors ------------------------------------------


def test_gate_objective_without_command_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.a", NODE, authority="objective")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "objective gate but has no command" in out


def test_gate_manual_with_command_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.a", NODE, authority="manual", command="pytest")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "manual gate but carries a command" in out


def test_gate_invalid_node_id_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.a", "Not A Node")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "invalid node_id" in out


# --- Evidence record shape errors ------------------------------------------


def test_record_malformed_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict("not-an-ev-id", "spec.a")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "malformed id" in out


def test_record_non_boolean_accepted_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict(EV1, "spec.a", overrides={"accepted": "true"})])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "non-boolean accepted" in out


def test_record_unknown_accepted_by_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict(EV1, "spec.a", accepted_by="ai_review")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "unknown accepted_by" in out


def test_record_supersede_pair_incomplete_fails(evidence_builder):
    # supersedes without supersede_reason — a correction names its target *and*
    # gives a reason, or neither.
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict(EV2, "spec.a", supersedes=EV1)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "supersedes and supersede_reason together" in out


def test_record_supersedes_malformed_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records(
            [
                evidence_builder.record_dict(
                    EV2, "spec.a", supersedes="bad-id", supersede_reason="fix"
                )
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "supersedes malformed id" in out


# --- Assessment attempt shape errors ---------------------------------------


def test_attempt_unknown_outcome_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .attempts([evidence_builder.attempt_dict(ATT1, NODE, outcome="partial")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "unknown outcome" in out and "partial" in out


def test_attempt_malformed_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .attempts([evidence_builder.attempt_dict("not-an-att-id", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "malformed id" in out


def test_attempt_id_node_mismatch_fails(evidence_builder):
    # The id embeds NODE but the field declares NODE_B — the id and the field must
    # name the same node.
    root = (
        evidence_builder.node(NODE)
        .node(NODE_B)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .attempts([evidence_builder.attempt_dict(ATT1, NODE_B)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "embeds node" in out


def test_attempt_invalid_node_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .attempts([evidence_builder.attempt_dict(ATT1, "Not A Node")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "invalid node_id" in out


# --- Cross-record errors (validation.py), re-proved end to end --------------


def test_duplicate_spec_id_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs(
            [
                evidence_builder.spec_dict("spec.dup", NODE),
                evidence_builder.spec_dict("spec.dup", NODE),
            ]
        )
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "duplicate artifact spec id: spec.dup" in out


def test_duplicate_gate_id_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .node(NODE_B)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates(
            [
                evidence_builder.gate_dict("gate.dup", NODE),
                evidence_builder.gate_dict("gate.dup", NODE_B),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "duplicate validation gate id: gate.dup" in out


def test_duplicate_record_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records(
            [
                evidence_builder.record_dict(EV1, "spec.a"),
                evidence_builder.record_dict(EV1, "spec.a"),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert f"duplicate evidence record id: {EV1}" in out


def test_duplicate_attempt_id_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .attempts(
            [
                evidence_builder.attempt_dict(ATT1, NODE),
                evidence_builder.attempt_dict(ATT1, NODE),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert f"duplicate assessment attempt id: {ATT1}" in out


def test_spec_dangling_node_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.ghost", "ghost.node_99")])
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "spec.ghost" in out and "ghost.node_99" in out


def test_gate_dangling_node_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates([evidence_builder.gate_dict("gate.ghost", "ghost.node_99")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "gate.ghost" in out and "ghost.node_99" in out


def test_record_dangling_spec_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records([evidence_builder.record_dict(EV1, "spec.missing")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert EV1 in out and "spec.missing" in out


def test_attempt_dangling_node_fails(evidence_builder):
    # A well-formed id whose embedded node agrees with the field, but names a node
    # absent from the graph — a dangling reference, not a shape error.
    root = (
        _covered(evidence_builder)
        .attempts([evidence_builder.attempt_dict("att.ghost.node_99.001", "ghost.node_99")])
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "ghost.node_99" in out


def test_record_supersedes_unknown_record_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records(
            [
                evidence_builder.record_dict(
                    EV2, "spec.a", supersedes=EV1, supersede_reason="fix"
                )
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert EV1 in out and "unknown record" in out


def test_two_gates_on_one_node_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs([evidence_builder.spec_dict("spec.a", NODE)])
        .gates(
            [
                evidence_builder.gate_dict("gate.a1", NODE),
                evidence_builder.gate_dict("gate.a2", NODE),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert "more than one gate" in out and "gate.a1" in out and "gate.a2" in out


def test_cross_spec_supersede_fails(evidence_builder):
    root = (
        evidence_builder.node(NODE)
        .specs(
            [
                evidence_builder.spec_dict("spec.a", NODE),
                evidence_builder.spec_dict("spec.b", NODE),
            ]
        )
        .gates([evidence_builder.gate_dict("gate.a", NODE)])
        .records(
            [
                evidence_builder.record_dict(EV1, "spec.a"),
                evidence_builder.record_dict(
                    EV2, "spec.b", supersedes=EV1, supersede_reason="oops"
                ),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert EV2 in out and "different spec" in out


def test_double_supersede_fails(evidence_builder):
    root = (
        _covered(evidence_builder)
        .records(
            [
                evidence_builder.record_dict(EV1, "spec.a"),
                evidence_builder.record_dict(EV2, "spec.a", supersedes=EV1, supersede_reason="a"),
                evidence_builder.record_dict(EV3, "spec.a", supersedes=EV1, supersede_reason="b"),
            ]
        )
        .write()
    )
    rc, out = _run_validate(root)
    assert rc == 1
    assert EV1 in out and "more than once" in out
