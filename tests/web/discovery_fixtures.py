"""The named discovery states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the *same*
discovery states from the same kind of fixture, or a state could be pinned
by one gate and left unchecked by the other. This module owns the mutations
that turn a pinned repo into each named discovery state (spec-v3-study-day
§10.2, §10.3):

* ``next-empty`` — a learner who has passed everything: nothing is
  recommendable, so Next states the authoritative reason and offers the
  recovery path;
* ``next-stale`` — the pinned repo already carries out-of-date readiness;
  one more saved readiness (available → locked) the curriculum no longer
  agrees with, so Next prompts a safe refresh instead of trusting the
  store;
* ``finder-empty`` — a curriculum source with no skills at all: Find explains
  the source, never the learner.

The authored stores are *fixture data*, exactly as the other web suites
seed state — no engine pass/master path runs here (see AGENTS.md safety
rule). Dates are absolute so the fixtures are wall-clock independent,
matching the frozen-clock convention of the suites that consume them.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

_VARIANT_DIRS: list[Path] = []


@atexit.register
def _cleanup_variants() -> None:
    """Remove the temporary variant repos this process materialised."""
    for path in _VARIANT_DIRS:
        shutil.rmtree(path, ignore_errors=True)


def _write_yaml(root: Path, relpath: str, doc: dict[str, Any]) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _all_passed(root: Path) -> None:
    """Asserted ``passed`` everywhere — nothing left to start or resume."""
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    for entry in doc.get("progress", {}).values():
        entry["state"] = "passed"
    _write_yaml(root, "graph/state.yaml", doc)


def _stale_one(root: Path) -> None:
    """Save one readiness the curriculum no longer agrees with.

    A node whose derived readiness is ``available`` is recorded as
    ``locked``: the store was written before the curriculum changed, so the
    saved value no longer matches what the graph says today.
    """
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    for entry in doc.get("progress", {}).values():
        if entry.get("state") == "available":
            entry["state"] = "locked"
            break
    _write_yaml(root, "graph/state.yaml", doc)


def _empty_curriculum(root: Path) -> None:
    """Remove every skill from the curriculum source."""
    nodes = root / "graph" / "nodes"
    for node in nodes.glob("*.md"):
        node.unlink()
    _write_yaml(root, "graph/edges.yaml", {"edges": []})
    _write_yaml(root, "graph/state.yaml", {"progress": {}})


_MUTATIONS = {
    "next-empty": _all_passed,
    "next-stale": _stale_one,
    "finder-empty": _empty_curriculum,
}


def build_discovery_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one discovery state.

    The pinned repo itself is never touched; each call materialises a fresh
    temporary copy, so a render is repeatable and the shared fixture stays
    read-only.
    """
    if kind not in _MUTATIONS:
        raise ValueError(f"unknown discovery variant: {kind!r}")
    dest = Path(tempfile.mkdtemp(prefix=f"discovery-{kind}-"))
    _VARIANT_DIRS.append(dest)
    shutil.copytree(pinned, dest, dirs_exist_ok=True)
    _MUTATIONS[kind](dest)
    return dest
