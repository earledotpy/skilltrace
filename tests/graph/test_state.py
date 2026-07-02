"""Progress store: five-state enum, guarded write API, seed load.

Decisions 1-3 and ADR 0001: learner state lives in `graph/state.yaml`, split
into *derived readiness* (`locked`/`available`, recomputable) and *asserted
progress* (`active`/`passed`/`mastered`, forward-only, never revoked). This
suite pins the two write guards that make that split code-authoritative — the
readiness writer refuses to touch asserted progress, the asserted writer refuses
to move backward — plus the enum and dangling-reference checks.

Like the node/edge loaders, `load_state` validates *shape* (the state enum)
only; cross-reference integrity (dangling node ids) is a separate function
(`check_state_references`) that issue #5's `validate graph` composes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skilltrace.graph.state import (
    ASSERTED_STATES,
    DERIVED_STATES,
    STATES,
    ProgressStore,
    ProgressStoreError,
    check_state_references,
    load_state,
    save_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_state(root: Path, progress: dict) -> Path:
    path = root / "graph" / "state.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"progress": progress}, sort_keys=False), encoding="utf-8")
    return path


# --- Enum / shape validation on load ---------------------------------------

def test_valid_states_load(tmp_path):
    progress = {f"a.b.node_{i}_01": {"state": s} for i, s in enumerate(sorted(STATES))}
    _write_state(tmp_path, progress)
    store = load_state(tmp_path)
    assert {e.state for e in store.entries.values()} == set(STATES)


def test_unknown_state_fails_naming_node_and_state(tmp_path):
    _write_state(tmp_path, {"a.b.node_01": {"state": "in_progress"}})
    with pytest.raises(ProgressStoreError) as excinfo:
        load_state(tmp_path)
    message = str(excinfo.value)
    assert "in_progress" in message
    assert "a.b.node_01" in message


def test_entry_missing_state_fails(tmp_path):
    _write_state(tmp_path, {"a.b.node_01": {"changed_at": "2026-07-02"}})
    with pytest.raises(ProgressStoreError):
        load_state(tmp_path)


def test_absent_state_file_loads_empty_store(tmp_path):
    # Mirror load_events: no file means an empty store, not an error.
    store = load_state(tmp_path)
    assert isinstance(store, ProgressStore)
    assert store.entries == {}


def test_changed_at_and_transitions_round_trip(tmp_path):
    _write_state(
        tmp_path,
        {"a.b.node_01": {"state": "active", "changed_at": "2026-07-02T10:00:00+00:00"}},
    )
    store = load_state(tmp_path)
    store.write_asserted("a.b.node_01", "passed")
    save_state(store, tmp_path)

    reloaded = load_state(tmp_path)
    entry = reloaded.entries["a.b.node_01"]
    assert entry.state == "passed"
    assert entry.transitions.get("passed") == entry.changed_at


# --- Readiness writer guards ------------------------------------------------

@pytest.mark.parametrize("state", sorted(DERIVED_STATES))
def test_readiness_writer_writes_derived_states(state):
    store = ProgressStore()
    store.write_readiness("a.b.node_01", state)
    assert store.state_of("a.b.node_01") == state


@pytest.mark.parametrize("state", sorted(ASSERTED_STATES))
def test_readiness_writer_refuses_asserted_target(state):
    store = ProgressStore()
    with pytest.raises(ProgressStoreError):
        store.write_readiness("a.b.node_01", state)


@pytest.mark.parametrize("asserted", sorted(ASSERTED_STATES))
def test_readiness_writer_refuses_to_touch_asserted_progress(asserted):
    store = ProgressStore()
    store.write_asserted("a.b.node_01", asserted)
    with pytest.raises(ProgressStoreError) as excinfo:
        store.write_readiness("a.b.node_01", "locked")
    assert "a.b.node_01" in str(excinfo.value)
    assert store.state_of("a.b.node_01") == asserted  # unchanged


def test_readiness_writer_allows_available_to_locked_flip():
    # A curriculum edit may flip an un-started node from available back to
    # locked; readiness is not forward-only.
    store = ProgressStore()
    store.write_readiness("a.b.node_01", "available")
    store.write_readiness("a.b.node_01", "locked")
    assert store.state_of("a.b.node_01") == "locked"


# --- Asserted writer guards -------------------------------------------------

@pytest.mark.parametrize("state", sorted(DERIVED_STATES))
def test_asserted_writer_refuses_derived_target(state):
    store = ProgressStore()
    with pytest.raises(ProgressStoreError):
        store.write_asserted("a.b.node_01", state)


def test_asserted_writer_advances_forward():
    store = ProgressStore()
    store.write_readiness("a.b.node_01", "available")
    for state in ("active", "passed", "mastered"):
        store.write_asserted("a.b.node_01", state)
        assert store.state_of("a.b.node_01") == state


@pytest.mark.parametrize(
    "current,target",
    [("passed", "active"), ("mastered", "passed"), ("mastered", "active")],
)
def test_asserted_writer_refuses_backward(current, target):
    store = ProgressStore()
    store.write_asserted("a.b.node_01", current)
    with pytest.raises(ProgressStoreError) as excinfo:
        store.write_asserted("a.b.node_01", target)
    assert "a.b.node_01" in str(excinfo.value)
    assert store.state_of("a.b.node_01") == current  # unchanged


def test_asserted_writer_from_absent_node_allowed():
    # Absent nodes default to derived readiness; asserting active is forward.
    store = ProgressStore()
    store.write_asserted("a.b.node_01", "active")
    assert store.state_of("a.b.node_01") == "active"


def test_asserted_writer_records_changed_at_on_transition():
    store = ProgressStore()
    store.write_asserted("a.b.node_01", "active", now="2026-07-02T10:00:00+00:00")
    store.write_asserted("a.b.node_01", "passed", now="2026-07-02T11:00:00+00:00")
    entry = store.entries["a.b.node_01"]
    assert entry.changed_at == "2026-07-02T11:00:00+00:00"
    assert entry.transitions["active"] == "2026-07-02T10:00:00+00:00"


def test_writers_return_touched_node_id():
    store = ProgressStore()
    assert store.write_readiness("a.b.node_01", "available") == "a.b.node_01"
    assert store.write_asserted("a.b.node_01", "active") == "a.b.node_01"


# --- Dangling-reference check -----------------------------------------------

def test_dangling_node_id_fails():
    store = ProgressStore()
    store.write_readiness("real.topic.node_01", "available")
    store.write_readiness("ghost.topic.node_01", "available")
    with pytest.raises(ProgressStoreError) as excinfo:
        check_state_references(store, {"real.topic.node_01"})
    assert "ghost.topic.node_01" in str(excinfo.value)


def test_all_known_references_pass():
    store = ProgressStore()
    store.write_readiness("real.topic.node_01", "available")
    assert check_state_references(store, {"real.topic.node_01"}) is store


# --- Integration against the real seed store -------------------------------

def test_seed_store_loads_all_nodes_in_derived_states():
    from skilltrace.graph.nodes import load_nodes

    store = load_state(REPO_ROOT)
    node_ids = {node.id for node in load_nodes(REPO_ROOT)}

    assert set(store.entries) == node_ids  # every seed node present
    assert len(store.entries) == 24
    assert all(entry.state in DERIVED_STATES for entry in store.entries.values())
    # No asserted progress is seeded — passing/mastering are learner acts only.
    assert not any(entry.state in ASSERTED_STATES for entry in store.entries.values())


def test_seed_store_references_are_all_known():
    from skilltrace.graph.nodes import load_nodes

    store = load_state(REPO_ROOT)
    node_ids = {node.id for node in load_nodes(REPO_ROOT)}
    assert check_state_references(store, node_ids) is store
