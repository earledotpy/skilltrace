"""Fixtures for the export/backup suite (issue #38).

`export_repo` builds a small but *complete* mini-repo — one node of each
progress state, plus at least one row in every record type the exporters
mirror (specs, gates, evidence records, attempts, sessions, work, blockers,
remediation actions, reviews, resources) — so `export markdown`/`export
sqlite` exercise every section, not just the empty-repo path. Policy files are
copied from the real shipped `policy/` seed (like `tests/policy/conftest.py`'s
`policy_repo`), since hand-rolling all seven policy schemas would duplicate
that fixture's job.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

MASTERED_NODE = "testing.export.mastered_node_01"
AVAILABLE_NODE = "testing.export.available_node_01"


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _write_node(root: Path, node_id: str) -> None:
    frontmatter = {
        "id": node_id,
        "title": f"Title for {node_id}",
        "summary": f"Summary for {node_id}.",
        "domain": "testing",
        "track": "foundational",
        "tags": ["export-fixture"],
    }
    block = yaml.safe_dump(frontmatter, sort_keys=False)
    path = root / "graph" / "nodes" / f"{node_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{block}---\n\n# {node_id}\n", encoding="utf-8")


@pytest.fixture
def export_repo(tmp_path: Path) -> Path:
    root = tmp_path
    shutil.copytree(REPO_ROOT / "policy", root / "policy")

    _write_node(root, MASTERED_NODE)
    _write_node(root, AVAILABLE_NODE)

    _write_yaml(
        root,
        "graph/edges.yaml",
        {
            "edges": [
                {
                    "id": "edge.export.001",
                    "source": MASTERED_NODE,
                    "target": AVAILABLE_NODE,
                    "edge_type": "soft_prerequisite",
                    "reason": "fixture edge",
                    "active": True,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                MASTERED_NODE: {"state": "mastered", "changed_at": "2026-06-01T10:00:00+00:00"},
                AVAILABLE_NODE: {"state": "available"},
            }
        },
    )
    _write_yaml(root, "graph/resources.yaml", {
        "resources": [
            {
                "id": "fixture-book",
                "url": "https://example.invalid/book",
                "cost": "free",
                "supports": [MASTERED_NODE],
            }
        ]
    })

    _write_yaml(
        root,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": f"spec.{MASTERED_NODE}.main",
                    "node_id": MASTERED_NODE,
                    "title": "Main artifact",
                    "artifact_kind": "problem_set",
                    "required": True,
                    "minimum_count": 1,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/validation_gates.yaml",
        {
            "validation_gates": [
                {
                    "id": f"gate.{MASTERED_NODE}",
                    "node_id": MASTERED_NODE,
                    "authority": "manual",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{MASTERED_NODE}.001",
                    "artifact_spec_id": f"spec.{MASTERED_NODE}.main",
                    "location": "evidence/a.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:aaa",
                    "created_at": "2026-06-01",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{MASTERED_NODE}.001",
                    "node_id": MASTERED_NODE,
                    "outcome": "passed",
                    "created_at": "2026-06-01",
                }
            ]
        },
    )

    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.001",
                    "status": "completed",
                    "started_at": "2026-06-01T10:00:00+00:00",
                    "ended_at": "2026-06-01T10:30:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "work.001",
                    "session_id": "sess.001",
                    "node_id": MASTERED_NODE,
                    "created_at": "2026-06-01T10:15:00+00:00",
                    "minutes": 30,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.{AVAILABLE_NODE}.001",
                    "node_id": AVAILABLE_NODE,
                    "status": "open",
                    "description": "stuck on fixture setup",
                    "created_at": "2026-06-02T09:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{AVAILABLE_NODE}.001",
                    "node_id": AVAILABLE_NODE,
                    "status": "open",
                    "description": "review the fixture material",
                    "created_at": "2026-06-02T09:05:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{MASTERED_NODE}.001",
                    "node_id": MASTERED_NODE,
                    "status": "scheduled",
                    "scheduled_for": "2026-08-01",
                    "created_at": "2026-06-01T10:30:00+00:00",
                }
            ]
        },
    )

    return root
