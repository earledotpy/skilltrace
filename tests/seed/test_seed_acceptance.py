"""Seed-acceptance standard for the shipped foundations graph (v0.8, issue #15).

The acceptance bar every v0.8 slice must clear, enforced mechanically against
the shipped repo rather than eyeballed:

  - every node has exactly one ValidationGate and at least one required
    ArtifactSpec;
  - every objective gate's command is well-formed — it shlex-splits to a
    non-empty argv that runs a shipped `evidence/checks/*_check.py` checker (the
    learner's solution is not shipped and is not asserted);
  - every track a node uses is mapped in the recommendation policy;
  - the effort claim and the session-fit flags agree (a node cannot advertise a
    window its minimum effort overshoots), and no retrofitted-away frontmatter
    lingers;
  - the progress store holds derived readiness only — no asserted progress;
  - every validator exits 0 and `next` yields recommendations with reasons;
  - each node is supported by a resource once the registry has entries (staged:
    skipped while the registry is empty, so the bar is never weakened, only
    deferred).

Node-count and band-depth targets are curriculum editorial choices, not asserted
here — this suite enforces the structural bar, not the shape of the curriculum.
"""

from __future__ import annotations

import shlex

import pytest

from skilltrace import cli
from skilltrace.graph.nodes import load_nodes

from .conftest import (
    ACTIVE_RESOURCE_BANDS,
    NODE_IDS,
    REPO_ROOT,
    band_of,
    gates_by_node,
    node_paths,
    raw_frontmatter,
    registry_resources,
    required_specs_by_node,
    state_by_node,
    track_weights,
)

# Keys the v0.8 lean template strips; their presence in shipped frontmatter is a
# retrofit miss (`level` legacy, `mastery_policy` a shadow gate,
# `competency_dimensions` never read). See docs/curriculum-authoring.md.
_STRIPPED_KEYS = ("level", "mastery_policy", "competency_dimensions")

_NODE_PATHS = node_paths()


# --- Every node has exactly one gate and one required spec ------------------


@pytest.mark.parametrize("node_id", NODE_IDS)
def test_every_node_has_exactly_one_gate(node_id):
    gates = gates_by_node().get(node_id, [])
    assert len(gates) == 1, (
        f"{node_id}: expected exactly one validation gate, found {len(gates)}"
    )


@pytest.mark.parametrize("node_id", NODE_IDS)
def test_every_node_has_a_required_artifact_spec(node_id):
    specs = required_specs_by_node().get(node_id, [])
    assert specs, f"{node_id}: expected at least one required artifact spec, found none"


# --- Objective gate commands are well-formed and reference shipped checkers --

_OBJECTIVE_GATES = [
    gate
    for gates in gates_by_node().values()
    for gate in gates
    if gate.get("authority") == "objective"
]


@pytest.mark.parametrize("gate", _OBJECTIVE_GATES, ids=lambda g: g["id"])
def test_objective_gate_command_runs_a_shipped_checker(gate):
    # Mirror the engine's own parsing (submit.py uses shlex.split): the command
    # must split to a non-empty argv and invoke a checker that ships in the repo.
    # The learner's solution is deliberately NOT asserted — it is not shipped.
    argv = shlex.split(gate.get("command") or "")
    assert argv, f"{gate['id']}: objective gate command is empty"
    checkers = [
        tok
        for tok in argv
        if tok.startswith("evidence/checks/") and tok.endswith(".py")
    ]
    assert checkers, (
        f"{gate['id']}: command runs no evidence/checks/*.py checker: {argv}"
    )
    for tok in checkers:
        assert (REPO_ROOT / tok).is_file(), (
            f"{gate['id']}: checker {tok} is not shipped in the repo"
        )


# --- Every track in use is weight-mapped ------------------------------------


def test_every_used_track_is_weight_mapped():
    weights = track_weights()
    used = {node.track for node in load_nodes(REPO_ROOT)}
    unmapped = sorted(used - set(weights))
    assert not unmapped, (
        f"tracks used by nodes but absent from policy track_weights: {unmapped}"
    )


def test_new_v08_tracks_are_mapped():
    # Slice 1 adds the consolidation and remediation weights the later slices rely on.
    weights = track_weights()
    assert weights.get("consolidation") == 2.0
    assert weights.get("remediation") == 0.5


# --- Lean template: stripped keys gone; effort/session-fit consistent -------


@pytest.mark.parametrize("path", _NODE_PATHS, ids=lambda p: p.stem)
def test_no_stripped_frontmatter_keys(path):
    fm = raw_frontmatter(path)
    present = [key for key in _STRIPPED_KEYS if key in fm]
    assert not present, f"{path.name}: lean template forbids frontmatter keys {present}"


@pytest.mark.parametrize("path", _NODE_PATHS, ids=lambda p: p.stem)
def test_effort_and_session_fit_are_consistent(path):
    fm = raw_frontmatter(path)
    min_minutes = fm["estimated_effort"]["min_minutes"]
    fit = fm["micro_session_fit"]
    # The documented rule (docs/curriculum-authoring.md): a node cannot claim to
    # fit a window its minimum effort overshoots.
    assert fit["can_fit_15_min"] is (min_minutes <= 15), (
        f"{path.name}: can_fit_15_min disagrees with min_minutes={min_minutes}"
    )
    assert fit["can_fit_30_min"] is (min_minutes <= 30), (
        f"{path.name}: can_fit_30_min disagrees with min_minutes={min_minutes}"
    )
    assert fit["requires_long_block"] is (min_minutes > 30), (
        f"{path.name}: requires_long_block disagrees with min_minutes={min_minutes}"
    )


# --- Progress store holds derived readiness only ----------------------------


def test_no_asserted_progress_in_store():
    # The retrofit and edge audit are safe only because nothing is asserted;
    # every node must sit in a derived state (locked/available), never
    # active/passed/mastered.
    states = state_by_node()
    asserted = {
        node_id: state
        for node_id, state in states.items()
        if state not in ("locked", "available")
    }
    assert not asserted, f"progress store carries asserted progress: {asserted}"


def test_progress_store_covers_every_node():
    states = state_by_node()
    missing = sorted(set(NODE_IDS) - set(states))
    assert not missing, f"nodes absent from the progress store (run sync): {missing}"


# --- Validators all green on the shipped repo -------------------------------


@pytest.mark.parametrize(
    "target", ["graph", "evidence", "execution", "policy", "resources"]
)
def test_validator_exits_zero(target, capsys):
    rc = cli.run(["validate", target], root=REPO_ROOT)
    out = capsys.readouterr().out
    assert rc == 0, f"validate {target} failed:\n{out}"


# --- `next` recommends real nodes, each with a reason -----------------------


def test_next_yields_recommendations_with_reasons(capsys):
    rc = cli.run(
        ["next", "--minutes", "60", "--limit", "5", "--show-locked"], root=REPO_ROOT
    )
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "next: top" in out, f"expected recommendations, got:\n{out}"
    # Each recommendation prints a reason line naming its track; with every track
    # now mapped, no unmapped-track warning should appear.
    assert "track '" in out, f"expected a reason naming the track, got:\n{out}"
    assert "not in policy/recommendation.yaml" not in out, (
        f"an in-use track is unmapped:\n{out}"
    )


# --- Per-node resource coverage (staged in per band) ------------------------


@pytest.mark.parametrize("node_id", NODE_IDS)
def test_every_node_has_a_supporting_resource(node_id):
    # The floor stages in per band: a node is held to it only once its band has
    # registry entries (resources land as each band is authored). By the final
    # slice every band is active, so this reduces to the full "every node has a
    # resource" bar with no band permanently exempt. See conftest.band_of.
    band = band_of(node_id)
    if band not in ACTIVE_RESOURCE_BANDS:
        pytest.skip(f"resource floor not yet active for band {band!r} (no entries)")
    supported = {
        node
        for resource in registry_resources()
        for node in resource.get("supports", [])
    }
    assert node_id in supported, f"{node_id}: no LearningResource supports this node"
