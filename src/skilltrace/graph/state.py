"""Progress store (`graph/state.yaml`): five-state model and guarded write API.

ADR 0001 and decisions 1-2: learner state lives *outside* curriculum files, in
one store keyed by node id. The five states split into two kinds that the write
API keeps strictly separate, and that separation is the whole point of this
module — it is code-authoritative here, not merely a convention:

- **Derived readiness** (`locked`, `available`) — recomputed from the graph by
  sync (issue #6). `write_readiness` writes only these two, and refuses to touch
  a node whose state is already asserted. Readiness is *not* forward-only: a
  curriculum edit may flip an un-started node from `available` back to `locked`.
- **Asserted progress** (`active`, `passed`, `mastered`) — recorded by the
  learner and never revoked. `write_asserted` writes only these three and only
  *forward* along the state order; it refuses any backward transition.

Enforcing "learner-command-only" is not the mechanism's job — a function cannot
know its caller. `write_asserted` is the mechanism; the guarantee that nothing
*automates* a pass/master lives in the command layer and `automation.py`. This
loader validates the *shape* (the state enum) only; the dangling-node-id check
is a separate `check_state_references` that issue #5's `validate graph` composes,
mirroring how the node/edge loaders defer cross-reference integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..paths import find_root

# The five states, split by kind. `STATES` is the closed enum the loader
# validates against.
DERIVED_STATES: frozenset[str] = frozenset({"locked", "available"})
ASSERTED_STATES: frozenset[str] = frozenset({"active", "passed", "mastered"})
STATES: frozenset[str] = DERIVED_STATES | ASSERTED_STATES

# The single progression order `locked -> available -> active -> passed ->
# mastered`. Only `write_asserted` consults this (to reject backward moves);
# `write_readiness` does not, because `available -> locked` is a legal derived
# flip, not a regression.
_STATE_ORDER: tuple[str, ...] = ("locked", "available", "active", "passed", "mastered")
_RANK: dict[str, int] = {state: i for i, state in enumerate(_STATE_ORDER)}

_STATE_RELPATH = Path("graph") / "state.yaml"


class ProgressStoreError(Exception):
    """The progress store could not be loaded, or a write violated its rules.

    The message always names the offending node so a validation run or a refused
    command points the learner straight at it.
    """


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ProgressEntry:
    """One node's recorded state, its last-change timestamp, and (optionally)
    the timestamp at which it entered each state it has passed through."""

    state: str
    changed_at: Any = None
    transitions: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressStore:
    """The in-memory progress store: node id -> `ProgressEntry`.

    Commands load the store, mutate it through the two guarded writers, then
    persist it once with `save_state`. Nodes absent from the store default to
    derived readiness (their `locked`/`available` value is computed by sync).
    """

    entries: dict[str, ProgressEntry] = field(default_factory=dict)
    source_path: Path | None = None

    def state_of(self, node_id: str, default: str = "locked") -> str:
        """Return the recorded state, or `default` for an absent node.

        The default is `locked` — the conservative derived floor: an unseen node
        is treated as not-yet-startable until sync says otherwise.
        """
        entry = self.entries.get(node_id)
        return entry.state if entry is not None else default

    def write_readiness(self, node_id: str, state: str, *, now: str | None = None) -> str:
        """Write a *derived readiness* state (`locked`/`available`) for a node.

        Refuses a non-derived target, and refuses to touch a node whose state is
        already asserted — asserted progress is never revoked by readiness sync.
        Returns the touched node id (for the audit event's `records_touched`).
        """
        if state not in DERIVED_STATES:
            raise ProgressStoreError(
                f"{node_id}: readiness writer may only write derived states "
                f"({', '.join(sorted(DERIVED_STATES))}); refused {state!r}."
            )
        current = self.entries.get(node_id)
        if current is not None and current.state in ASSERTED_STATES:
            raise ProgressStoreError(
                f"{node_id}: readiness writer refuses to touch asserted progress "
                f"(state is {current.state!r}); asserted progress never moves back "
                "to derived readiness."
            )
        self._set(node_id, state, now, record_transition=False)
        return node_id

    def write_asserted(self, node_id: str, state: str, *, now: str | None = None) -> str:
        """Write an *asserted progress* state (`active`/`passed`/`mastered`).

        Refuses a non-asserted target and any *backward* transition along the
        state order (`passed -> active`, `mastered -> passed`); equal-rank
        re-assertion is idempotent and allowed. This is the mechanism only — the
        rule that passing/mastering are never automated lives in the command
        layer and `automation.py`, and hard-prerequisite gating lives in the
        start/pass commands. Returns the touched node id.
        """
        if state not in ASSERTED_STATES:
            raise ProgressStoreError(
                f"{node_id}: asserted writer may only write asserted states "
                f"({', '.join(sorted(ASSERTED_STATES))}); refused {state!r}."
            )
        current_state = self.state_of(node_id)  # absent -> derived floor (locked)
        if _RANK[state] < _RANK[current_state]:
            raise ProgressStoreError(
                f"{node_id}: asserted progress never moves backward; refused "
                f"{current_state!r} -> {state!r}."
            )
        self._set(node_id, state, now, record_transition=True)
        return node_id

    def _set(self, node_id: str, state: str, now: str | None, *, record_transition: bool) -> None:
        timestamp = now or _now_iso()
        entry = self.entries.get(node_id)
        if entry is None:
            entry = ProgressEntry(state=state)
            self.entries[node_id] = entry
        entry.state = state
        entry.changed_at = timestamp
        # Per-transition timestamps track the learner's journey through asserted
        # progress (started/passed/mastered); readiness flips only bump changed_at.
        if record_transition:
            entry.transitions[state] = timestamp


def _load_entry(node_id: str, data: Any, path: Path) -> ProgressEntry:
    if not isinstance(data, dict):
        raise ProgressStoreError(f"{path}: progress entry for {node_id!r} is not a mapping.")
    state = data.get("state")
    if not isinstance(state, str) or state not in STATES:
        raise ProgressStoreError(
            f"{path}: node {node_id!r} has invalid state {state!r} — expected one "
            f"of {', '.join(sorted(STATES))}."
        )
    transitions = data.get("transitions") or {}
    if not isinstance(transitions, dict):
        raise ProgressStoreError(
            f"{path}: node {node_id!r} has non-mapping transitions {transitions!r}."
        )
    return ProgressEntry(
        state=state, changed_at=data.get("changed_at"), transitions=dict(transitions)
    )


def load_state(root: Path | str | None = None) -> ProgressStore:
    """Load and validate `graph/state.yaml` (default root: auto-detected).

    Validates the state enum per entry (shape only). A missing file yields an
    empty store — a fresh repo has no recorded progress — mirroring `load_events`.
    The dangling-node-id check is `check_state_references`, run separately by
    graph validation (issue #5).
    """
    root_path = Path(root) if root is not None else find_root()
    path = root_path / _STATE_RELPATH
    store = ProgressStore(source_path=path)

    if not path.exists():
        return store

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProgressStoreError(f"{path}: unparseable state YAML: {exc}") from exc

    if doc is None or doc == {}:
        return store
    if not isinstance(doc, dict) or "progress" not in doc:
        raise ProgressStoreError(f"{path}: expected a top-level 'progress:' mapping.")

    raw = doc["progress"] or {}
    if not isinstance(raw, dict):
        raise ProgressStoreError(
            f"{path}: 'progress' must be a mapping of node id -> entry."
        )

    for node_id, entry_data in raw.items():
        store.entries[str(node_id)] = _load_entry(str(node_id), entry_data, path)
    return store


def save_state(store: ProgressStore, root: Path | str | None = None) -> Path:
    """Persist the store to `graph/state.yaml`, keyed by node id for clean diffs.

    Returns the written path. Empty per-node fields (`changed_at`, `transitions`)
    are omitted so seed and derived entries stay minimal.
    """
    root_path = Path(root) if root is not None else find_root()
    path = root_path / _STATE_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)

    progress: dict[str, dict[str, Any]] = {}
    for node_id in sorted(store.entries):
        entry = store.entries[node_id]
        record: dict[str, Any] = {"state": entry.state}
        if entry.changed_at is not None:
            record["changed_at"] = entry.changed_at
        if entry.transitions:
            record["transitions"] = dict(entry.transitions)
        progress[node_id] = record

    path.write_text(
        yaml.safe_dump({"progress": progress}, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return path


def check_state_references(store: ProgressStore, known_node_ids: Iterable[str]) -> ProgressStore:
    """Fail if any progress entry names a node id absent from `known_node_ids`.

    The cross-reference (dangling-reference) check, kept out of `load_state` to
    match the node/edge loaders' shape-only seam. Returns the store on success so
    it composes in a validation pipeline. Issue #5's `validate graph` calls it.
    """
    known = set(known_node_ids)
    dangling = sorted(node_id for node_id in store.entries if node_id not in known)
    if dangling:
        raise ProgressStoreError(
            "progress store references unknown node id(s): "
            f"{', '.join(dangling)} — every progress entry must name a real node."
        )
    return store
