"""Fixtures for the resources-layer suite (v0.7).

`resources_repo` gives each test a disposable repo root in the style of the
policy suite's `policy_repo`: a fresh copy of the shipped `policy/` seeds plus
helpers to write minimal node files and the resource registry (`graph/
resources.yaml`). Tests mutate the registry freely and drive the real CLI
in-process via `cli.run(argv, root=<repo>)` — the single seam — asserting only
exit codes, stdout, and the YAML that lives on disk.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def resources_repo(tmp_path: Path) -> Path:
    """A disposable repo root: shipped policy seeds + an empty registry.

    Copying the real policy seeds keeps the fixture in the policy suite's style
    and forward-compatible with the later v0.7 slices (resource-report reads a
    policy window). This slice's `validate resources` needs only nodes and the
    registry, both written per-test.
    """
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    write_registry(tmp_path, [])
    return tmp_path


def write_registry(root: Path, resources: list[dict]) -> None:
    """Write `graph/resources.yaml` with the given resource entries."""
    _write_yaml(root, "graph/resources.yaml", {"resources": resources})


def write_node(root: Path, node_id: str, *, track: str = "foundational") -> None:
    """Write one minimal, load-clean node markdown file."""
    frontmatter = {
        "id": node_id,
        "title": f"Title for {node_id}",
        "summary": f"Summary for {node_id}.",
        "domain": "testing",
        "track": track,
    }
    block = yaml.safe_dump(frontmatter, sort_keys=False)
    path = root / "graph" / "nodes" / f"{node_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{block}---\n\n# {node_id}\n", encoding="utf-8")


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
