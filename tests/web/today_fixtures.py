"""The Today states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the *same* Today
states from the same kind of fixture, or a state could be pinned by one
gate and left unchecked by the other. This module owns the mutations that
turn a pinned repo into each named Today state (spec-v3-study-day §10.1):

* ``populated`` — the pinned repo unchanged (the default fixture);
* ``empty`` — a one-skill curriculum the learner has already passed:
  nothing to start, nothing waiting, nothing owed;
* ``limited`` — the window holds fewer sessions than the analytics policy
  threshold, while real values remain to retain;
* ``stale`` — one saved readiness the curriculum no longer agrees with;
* ``refusal`` — a one-skill curriculum whose only skill is locked: every
  visible skill waits on another, and unlock is never offered.

The authored stores are *fixture data*, exactly as the other web suites
seed state — no engine pass/master path runs here (see AGENTS.md safety
rule). Dates are absolute so the fixtures are wall-clock independent,
matching the frozen-clock convention of the suites that consume them.
The shared mechanics (variant materialisation, the deterministic stale
mutation) live in :mod:`fixture_repo`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fixture_repo import make_one_readiness_stale, materialise_variant, write_yaml

#: The named Today states a fixture can be reshaped into. ``populated`` is
#: the pinned repo itself, so it is not a mutation here.
TODAY_VARIANTS: tuple[str, ...] = ("empty", "limited", "stale", "refusal")

_SINGLE_NODE = "demo.single_01"

_SINGLE_NODE_MARKDOWN = """---
id: demo.single_01
title: The one skill in this curriculum
summary: A single-skill curriculum, so Today's population is exact.
domain: demo
track: foundational
micro_session_fit:
  can_fit_15_min: true
  can_fit_30_min: true
  requires_long_block: false
created_at: 2026-06-28
updated_at: 2026-06-28
---

# The one skill in this curriculum
"""


def _drop_execution(root: Path) -> None:
    """Remove the learner's execution records — the day has no history."""
    for name in (
        "sessions.yaml",
        "session_work.yaml",
        "blockers.yaml",
        "reviews.yaml",
        "remediation_actions.yaml",
    ):
        path = root / "execution" / name
        if path.exists():
            path.unlink()


def _single_skill(root: Path, *, passed: bool) -> None:
    """A one-skill curriculum — the whole of Today's population in one node.

    ``passed`` leaves nothing to start and nothing waiting (the *empty*
    state); otherwise the skill is locked by a prerequisite the curriculum
    names but does not seed, so every visible skill waits on another and
    the engine treats the absent source as its locked floor (the *refusal*
    state). The saved store and the derived readiness agree either way, so
    the state is not reported as stale.
    """
    nodes = root / "graph" / "nodes"
    for path in nodes.glob("*.md"):
        path.unlink()
    (nodes / f"{_SINGLE_NODE}.md").write_text(
        _SINGLE_NODE_MARKDOWN, encoding="utf-8"
    )
    edges: list[dict[str, Any]] = []
    progress: dict[str, Any] = {}
    if passed:
        progress[_SINGLE_NODE] = {
            "state": "passed",
            "changed_at": "2026-11-01T09:00:00+00:00",
        }
    else:
        edges.append(
            {
                "id": f"edge.demo.ghost__{_SINGLE_NODE}",
                "source": "demo.ghost_01",
                "target": _SINGLE_NODE,
                "edge_type": "hard_prerequisite",
                "reason": (
                    "The curriculum names a prerequisite it does not seed "
                    "yet, so the skill stays locked until that source exists "
                    "and is passed."
                ),
                "active": True,
                "created_at": "2026-06-28",
                "updated_at": "2026-06-28",
            }
        )
    write_yaml(root, "graph/edges.yaml", {"edges": edges})
    write_yaml(root, "graph/state.yaml", {"progress": progress})
    _drop_execution(root)


def _first_node_id(root: Path) -> str:
    """The first skill id of the curriculum, for work items to bind to."""
    nodes = sorted((root / "graph" / "nodes").glob("*.md"))
    return nodes[0].stem if nodes else _SINGLE_NODE


def _minimal_history(root: Path) -> None:
    """Author a two-session history when the pinned repo carries none."""
    node_id = _first_node_id(root)
    write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.limited.001",
                    "status": "open",
                    "started_at": "2026-11-17T07:00:00+00:00",
                },
                {
                    "id": "ses.limited.002",
                    "status": "completed",
                    "started_at": "2026-11-15T09:00:00+00:00",
                    "ended_at": "2026-11-15T10:00:00+00:00",
                },
            ]
        },
    )
    write_yaml(
        root,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.limited.001.01",
                    "session_id": "ses.limited.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T07:30:00+00:00",
                    "minutes": 30,
                },
                {
                    "id": "wk.ses.limited.002.01",
                    "session_id": "ses.limited.002",
                    "node_id": node_id,
                    "created_at": "2026-11-15T09:30:00+00:00",
                    "minutes": 45,
                },
            ]
        },
    )


def _trim_window(root: Path) -> None:
    """Keep the open session and one completed one — below the threshold.

    The analytics policy wants ``min_sessions_for_full_data`` sessions in
    the window before the figures are called full data; two real sessions
    leave valid values that are retained while the threshold is stated.
    A pinned repo without execution records is given that history instead.
    """
    sessions_path = root / "execution" / "sessions.yaml"
    if not sessions_path.exists():
        _minimal_history(root)
        return
    doc = yaml.safe_load(sessions_path.read_text(encoding="utf-8")) or {}
    sessions = doc.get("sessions", [])
    kept = [s for s in sessions if s.get("status") == "open"]
    completed = sorted(
        (s for s in sessions if s.get("status") != "open"),
        key=lambda s: s.get("started_at") or "",
        reverse=True,
    )
    kept.extend(completed[:1])
    doc["sessions"] = kept
    write_yaml(root, "execution/sessions.yaml", doc)

    kept_ids = {s["id"] for s in kept}
    work_path = root / "execution" / "session_work.yaml"
    work_doc = yaml.safe_load(work_path.read_text(encoding="utf-8")) or {}
    work_doc["session_work"] = [
        w for w in work_doc.get("session_work", []) if w.get("session_id") in kept_ids
    ]
    write_yaml(root, "execution/session_work.yaml", work_doc)


_MUTATIONS = {
    "empty": lambda root: _single_skill(root, passed=True),
    "refusal": lambda root: _single_skill(root, passed=False),
    "limited": _trim_window,
    "stale": make_one_readiness_stale,
}


def build_today_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one Today state.

    The pinned repo itself is never touched; each call materialises a fresh
    temporary copy, so a render is repeatable and the shared fixture stays
    read-only.
    """
    return materialise_variant(
        pinned, kind, prefix=f"today-{kind}", mutations=_MUTATIONS
    )
