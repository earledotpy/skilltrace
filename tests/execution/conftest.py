"""Shared fixtures for the v0.5 execution suite.

The execution layer's commands read node states from the progress store and
write only `execution/*.yaml`. `exec_repo` returns a factory: pass it a
`{node_id: state}` mapping and get a repo root the CLI can operate on, with
`graph/state.yaml` seeded and a minimal node markdown file per node (so
`validate execution` can check node references against the real graph).
Execution files are created on demand by the commands themselves, exactly as
they would be in a fresh real repo.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def write_state(root: Path, states: dict[str, str]) -> None:
    """Write `graph/state.yaml` with one entry per node id."""
    path = root / "graph" / "state.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    progress = {node_id: {"state": state} for node_id, state in states.items()}
    path.write_text(yaml.safe_dump({"progress": progress}, sort_keys=False), encoding="utf-8")


def write_node(root: Path, node_id: str) -> None:
    """Write one minimal-valid node markdown file (mirrors EvidenceBuilder)."""
    frontmatter = {
        "id": node_id,
        "title": f"Title for {node_id}",
        "summary": f"Summary for {node_id}.",
        "domain": "testing",
        "track": "foundational",
        "micro_session_fit": {
            "can_fit_15_min": True,
            "can_fit_30_min": True,
            "requires_long_block": False,
        },
    }
    block = yaml.safe_dump(frontmatter, sort_keys=False)
    path = root / "graph" / "nodes" / f"{node_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{block}---\n\n# {node_id}\n", encoding="utf-8")


def write_workload_policy(root: Path) -> None:
    """Seed the workload policy values the execution layer reads.

    Only `session_templates` is seeded; `stale_session_hours` is left unset so
    tests exercise the engine's fallback default.
    """
    path = root / "policy" / "workload.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "workload_policy": {
            "session_templates": {
                "micro": {"expected_minutes": 15},
                "standard": {"expected_minutes": 45},
                "deep": {"expected_minutes": 90},
            },
        }
    }
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.fixture
def exec_repo(tmp_path: Path):
    """Factory: `exec_repo({node: state, ...})` -> repo root."""

    def make(states: dict[str, str]) -> Path:
        write_state(tmp_path, states)
        for node_id in states:
            write_node(tmp_path, node_id)
        write_workload_policy(tmp_path)
        return tmp_path

    return make
