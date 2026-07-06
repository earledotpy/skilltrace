"""Edge loader: closed frontmatter schema, pruned-field rejection, seed load.

Decisions 4/5: `edges.yaml` is the sole source of truth for relationships, and
the *semantics* live in the edge type. So the loader uses a **closed** schema —
the mirror-image of the node loader, which tolerates unknown keys. Any field
outside the allowed set fails validation naming the edge, which is what retires
the three pruned fields (`strength`, `can_override`, `activation_rule`) for good
rather than merely dropping them once.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.graph.edges import (
    EDGE_TYPES,
    PRUNED_EDGE_FIELDS,
    EdgeLoadError,
    GraphEdge,
    load_edge,
    load_edges,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_EDGE = {
    "id": "edge.a.topic.thing_01__b.topic.other_01",
    "source": "a.topic.thing_01",
    "target": "b.topic.other_01",
    "edge_type": "hard_prerequisite",
    "reason": "The other requires the thing.",
    "active": True,
    "created_at": "2026-06-28",
    "updated_at": "2026-06-28",
}


def _edge_with(**overrides):
    data = dict(_VALID_EDGE)
    data.update(overrides)
    return data


def test_valid_edge_loads_all_model_fields():
    edge = load_edge(dict(_VALID_EDGE))

    assert isinstance(edge, GraphEdge)
    assert edge.id == _VALID_EDGE["id"]
    assert edge.source == "a.topic.thing_01"
    assert edge.target == "b.topic.other_01"
    assert edge.edge_type == "hard_prerequisite"
    assert edge.reason == "The other requires the thing."
    assert edge.active is True
    assert edge.created_at == "2026-06-28"
    assert edge.updated_at == "2026-06-28"


def test_active_false_loads_and_is_not_treated_as_missing():
    # `active: false` is a legitimate value, not an absent required field; a
    # truthiness-based presence check would wrongly reject it.
    edge = load_edge(_edge_with(active=False))
    assert edge.active is False


@pytest.mark.parametrize("edge_type", sorted(EDGE_TYPES))
def test_each_known_edge_type_loads(edge_type):
    edge = load_edge(_edge_with(edge_type=edge_type))
    assert edge.edge_type == edge_type


def test_unknown_edge_type_fails_naming_edge_and_type():
    data = _edge_with(edge_type="prerequisite")
    with pytest.raises(EdgeLoadError) as excinfo:
        load_edge(data)
    message = str(excinfo.value)
    assert "prerequisite" in message
    assert data["id"] in message


@pytest.mark.parametrize("pruned", sorted(PRUNED_EDGE_FIELDS))
def test_pruned_field_fails_naming_edge_and_field(pruned):
    data = _edge_with(**{pruned: 1.0})
    with pytest.raises(EdgeLoadError) as excinfo:
        load_edge(data)
    message = str(excinfo.value)
    assert pruned in message
    assert data["id"] in message


def test_arbitrary_unknown_field_fails():
    # The schema is closed: any field outside the allowed set fails, not just
    # the three known-pruned ones.
    with pytest.raises(EdgeLoadError) as excinfo:
        load_edge(_edge_with(weight=3))
    assert "weight" in str(excinfo.value)


@pytest.mark.parametrize("field", ["id", "source", "target", "edge_type", "reason", "active"])
def test_missing_required_field_fails(field):
    data = {k: v for k, v in _VALID_EDGE.items() if k != field}
    with pytest.raises(EdgeLoadError) as excinfo:
        load_edge(data)
    assert field in str(excinfo.value)


def test_non_bool_active_fails():
    with pytest.raises(EdgeLoadError):
        load_edge(_edge_with(active="yes"))


def test_non_string_edge_type_fails_with_edge_load_error():
    # A malformed edge_type (e.g. a YAML list) is unhashable; the loader must
    # still raise EdgeLoadError naming the edge, not a raw TypeError.
    with pytest.raises(EdgeLoadError):
        load_edge(_edge_with(edge_type=["hard_prerequisite"]))


def test_non_mapping_edge_fails_naming_index():
    with pytest.raises(EdgeLoadError) as excinfo:
        load_edge(["not", "a", "mapping"], index=4)
    assert "4" in str(excinfo.value)


# --- Integration against the real (migrated) seed graph ---

def test_all_seed_edges_load():
    edges = load_edges(REPO_ROOT)
    assert len(edges) == 50
    ids = [edge.id for edge in edges]
    assert len(set(ids)) == len(ids)  # loader hands #5 the raw list; no dedupe here
    assert all(edge.edge_type in EDGE_TYPES for edge in edges)
    assert all(edge.reason for edge in edges)
    # Every seed edge keeps its current type; both types in use are present.
    types = {edge.edge_type for edge in edges}
    assert types == {"hard_prerequisite", "soft_prerequisite"}


def test_seed_edges_carry_no_pruned_fields():
    # Belt-and-suspenders: the closed schema means a load succeeding at all
    # already proves no pruned field survived, but assert the intent directly.
    edges = load_edges(REPO_ROOT)
    for edge in edges:
        for pruned in PRUNED_EDGE_FIELDS:
            assert not hasattr(edge, pruned)
