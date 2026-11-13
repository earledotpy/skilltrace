"""Shared fixture-repo plumbing for the web suites.

One place for the mechanics every fixture module needs, so the named
state mutations cannot drift between the suites that share them:

* temporary variant repos are materialised once per call and removed at
  process exit;
* :func:`make_one_readiness_stale` flips the **sorted-first** ``available``
  node, so the store's stale entry never depends on dict order;
* :func:`finish_every_startable_skill` authors an all-finished store
  through the engine's guarded writer (``ProgressStore.write_asserted``),
  passing only skills that are actually startable at the moment of
  writing — never a locked one — and re-deriving readiness between
  rounds, so the saved store stays consistent with the graph, every
  record carries a truthful ``changed_at`` and transition trail, and no
  asserted record moves backward;
* :func:`fresh_learner_store` empties the store and lets the engine's own
  ``sync_readiness`` derive every readiness, so a fixture that needs
  "nothing started" never hand-writes a state the engine would not
  record.

The authored stores are *fixture data*, exactly as the other web suites
seed state — no engine pass/master *command* runs here (see AGENTS.md
safety rule): the helpers shape the store file through the store's own
guarded write API with fixed dates, never by invoking ``pass_node`` or
the write routes.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

import yaml

#: The fixed stamp every authored record carries, so the fixtures are
#: wall-clock independent (the suites' frozen-clock convention).
FIXTURE_STAMP = "2026-11-01T09:00:00+00:00"

_VARIANT_DIRS: list[Path] = []


@atexit.register
def _cleanup_variants() -> None:
    """Remove the temporary variant repos this process materialised."""
    for path in _VARIANT_DIRS:
        shutil.rmtree(path, ignore_errors=True)


def write_yaml(root: Path, relpath: str, doc: dict[str, Any]) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def materialise_variant(
    pinned: Path,
    kind: str,
    *,
    prefix: str,
    mutations: dict[str, Callable[[Path], None]],
) -> Path:
    """A read-only copy of ``pinned`` reshaped into one named state.

    The pinned repo itself is never touched; each call materialises a
    fresh temporary copy, so a render is repeatable and the shared fixture
    stays read-only. Removed at process exit.
    """
    if kind not in mutations:
        raise ValueError(f"unknown variant: {kind!r}")
    dest = Path(tempfile.mkdtemp(prefix=f"{prefix}-"))
    _VARIANT_DIRS.append(dest)
    shutil.copytree(pinned, dest, dirs_exist_ok=True)
    mutations[kind](dest)
    return dest


def _progress_doc(root: Path) -> dict[str, Any]:
    path = root / "graph" / "state.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}


def make_one_readiness_stale(root: Path) -> None:
    """Save one readiness the curriculum no longer agrees with.

    A node whose derived readiness is ``available`` is recorded as
    ``locked``: the store was written before the curriculum changed, so
    the saved value no longer matches what the graph says today. The
    **sorted-first** such node is chosen, so the stale entry does not
    depend on the store's dict order.
    """
    doc = _progress_doc(root)
    stale = sorted(
        node_id
        for node_id, entry in doc.get("progress", {}).items()
        if entry.get("state") == "available"
    )
    if not stale:
        raise ValueError("no available node to make stale")
    doc["progress"][stale[0]]["state"] = "locked"
    write_yaml(root, "graph/state.yaml", doc)


def finish_every_startable_skill(root: Path, *, now: str = FIXTURE_STAMP) -> None:
    """Author the store of a learner who has finished everything startable.

    Rounds of the engine's own mechanics, in the engine's order: derive
    readiness (:func:`~skilltrace.graph.readiness.sync_readiness`), then
    record ``passed`` — through the guarded ``write_asserted``, so no
    record can move backward and every one carries a truthful
    ``changed_at`` — for the skills that are startable *right now*
    (``available`` / ``active``). A locked skill is never passed: it
    becomes startable only when its prerequisites finish, and a
    prerequisite that never finishes (a source the curriculum names but
    does not seed) leaves the skill locked, which is the truth the
    finished-everything story must keep.
    """
    from skilltrace.graph.edges import load_edges
    from skilltrace.graph.nodes import load_nodes
    from skilltrace.graph.readiness import sync_readiness
    from skilltrace.graph.state import load_state, save_state

    (root / "graph" / "state.yaml").write_text("progress: {}\n", encoding="utf-8")
    store = load_state(root)
    nodes = load_nodes(root)
    edges = load_edges(root)
    while True:
        sync_readiness(nodes, edges, store, now=now)
        startable = sorted(
            node.id
            for node in nodes
            if store.state_of(node.id) in ("available", "active")
        )
        if not startable:
            break
        for node_id in startable:
            store.write_asserted(node_id, "passed", now=now)
    save_state(store, root)


def fresh_learner_store(root: Path, *, now: str = FIXTURE_STAMP) -> None:
    """A fresh learner's store: nothing asserted, readiness derived.

    The store is emptied and every readiness is derived by the engine's
    own ``sync_readiness`` — the states ``sync`` would record, never
    hand-written ones — so a fixture that needs "nothing started" stays
    consistent with the graph.
    """
    from skilltrace.graph.edges import load_edges
    from skilltrace.graph.nodes import load_nodes
    from skilltrace.graph.readiness import sync_readiness
    from skilltrace.graph.state import load_state, save_state

    (root / "graph" / "state.yaml").write_text("progress: {}\n", encoding="utf-8")
    store = load_state(root)
    sync_readiness(load_nodes(root), load_edges(root), store, now=now)
    save_state(store, root)
