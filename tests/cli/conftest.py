"""Fixtures for the CLI integration test suite.

``resources_repo``
    A disposable repo root (tmp_path) with the shipped ``policy/`` seeds
    copied in and an empty ``graph/resources.yaml`` written.  CLI tests that
    exercise resource commands import this fixture so they get an isolated,
    policy-valid environment without touching the live repo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def resources_repo(tmp_path: Path) -> Path:
    """A disposable repo root: shipped policy seeds + an empty resource registry."""
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    _write_registry(tmp_path, [])
    return tmp_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _write_registry(root: Path, resources: list[dict]) -> None:
    path = root / "graph" / "resources.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"resources": resources}, sort_keys=False),
        encoding="utf-8",
    )
