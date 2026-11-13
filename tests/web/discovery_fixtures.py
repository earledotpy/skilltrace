"""The named discovery states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the *same*
discovery states from the same kind of fixture, or a state could be pinned
by one gate and left unchecked by the other. This module owns the mutations
that turn a pinned repo into each named discovery state (spec-v3-study-day
§10.2, §10.3):

* ``next-empty`` — a learner who has finished every startable skill:
  nothing is recommendable, so Next states the authoritative reason and
  offers the recovery path;
* ``next-stale`` — the pinned repo already carries out-of-date readiness;
  one more saved readiness (available → locked) the curriculum no longer
  agrees with, so Next prompts a safe refresh instead of trusting the
  store;
* ``finder-empty`` — a curriculum with no skills at all: Find explains the
  curriculum, never the learner;
* ``finder-source-missing`` — the graph/nodes/ directory gone: Find
  reports an operational failure, never an empty-curriculum claim;
* ``finder-stale`` — the stale-readiness store behind Find, so the route's
  recovery prompt is pinned and scanned like its other states.

The state mutations live in :mod:`fixture_repo` (shared with the Today
fixtures) so they cannot drift between the suites; this module only names
them.
"""

from __future__ import annotations

from pathlib import Path

from fixture_repo import (
    finish_every_startable_skill,
    make_one_readiness_stale,
    materialise_variant,
    write_yaml,
)


def _empty_curriculum(root: Path) -> None:
    """Remove every skill from the curriculum."""
    nodes = root / "graph" / "nodes"
    for node in nodes.glob("*.md"):
        node.unlink()
    write_yaml(root, "graph/edges.yaml", {"edges": []})
    write_yaml(root, "graph/state.yaml", {"progress": {}})


def _source_missing(root: Path) -> None:
    """Remove the curriculum source directory itself."""
    nodes = root / "graph" / "nodes"
    for node in nodes.glob("*.md"):
        node.unlink()
    nodes.rmdir()
    write_yaml(root, "graph/edges.yaml", {"edges": []})
    write_yaml(root, "graph/state.yaml", {"progress": {}})


_MUTATIONS = {
    "next-empty": finish_every_startable_skill,
    "next-stale": make_one_readiness_stale,
    "finder-empty": _empty_curriculum,
    "finder-source-missing": _source_missing,
    "finder-stale": make_one_readiness_stale,
}


def build_discovery_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one discovery state.

    The pinned repo itself is never touched; each call materialises a
    fresh temporary copy, so a render is repeatable and the shared fixture
    stays read-only.
    """
    return materialise_variant(
        pinned, kind, prefix=f"discovery-{kind}", mutations=_MUTATIONS
    )
