"""Fixtures for the policy-layer suite (v0.6).

`policy_repo` gives each test a disposable repo root carrying a fresh copy of
the shipped `policy/` seed files — the real seeds are the contract `validate
policy` guards, so tests run against copies of the genuine article and mutate
them freely.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def policy_repo(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


NODE = "testing.policy.subject_node_01"


@pytest.fixture
def mastery_repo(policy_repo):
    """A full mini-repo factory for mastery-eligibility scenarios.

    Writes one node backed by a spec, gate, and accepted evidence record, a
    progress store with the given state (and pass timestamp), and a review
    history — everything the mastery derivation reads, all through real files.
    """

    def build(
        *,
        state: str = "passed",
        passed_at: str | None = "2026-07-01T10:00:00+00:00",
        accepted: bool = True,
        reviews: list[dict] | None = None,
    ) -> Path:
        root = policy_repo
        _write_node(root, NODE)
        _write_yaml(
            root,
            "evidence/artifact_specs.yaml",
            {
                "artifact_specs": [
                    {
                        "id": "spec.testing.policy.subject_node_01.main",
                        "node_id": NODE,
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
                        "id": "gate.testing.policy.subject_node_01",
                        "node_id": NODE,
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
                        "id": f"ev.{NODE}.001",
                        "artifact_spec_id": "spec.testing.policy.subject_node_01.main",
                        "location": "evidence/a.md",
                        "accepted": accepted,
                        "accepted_by": "learner_manual",
                        "artifact_hash": "sha256:aaa",
                        "created_at": "2026-07-01",
                    }
                ]
            },
        )
        _write_yaml(root, "evidence/attempts.yaml", {"attempts": []})

        entry: dict = {"state": state, "changed_at": passed_at}
        if passed_at is not None and state in ("passed", "mastered"):
            entry["transitions"] = {"passed": passed_at}
        _write_yaml(root, "graph/state.yaml", {"progress": {NODE: entry}})

        _write_yaml(root, "execution/reviews.yaml", {"reviews": reviews or []})
        return root

    return build


def review_dict(
    review_id: str = "rev.2026-07-04.01",
    *,
    status: str = "completed",
    outcome: str | None = "satisfactory",
    completed_at: str | None = "2026-07-04T10:00:00+00:00",
) -> dict:
    record = {
        "id": review_id,
        "node_id": NODE,
        "status": status,
        "scheduled_for": "2026-07-04",
        "created_at": "2026-07-01T10:00:00+00:00",
    }
    if status == "completed":
        record["outcome"] = outcome
        record["result_summary"] = "recalled the material"
        record["completed_at"] = completed_at
    return record


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _write_node(root: Path, node_id: str, *, track: str = "foundational") -> None:
    frontmatter = {
        "id": node_id,
        "title": f"Title for {node_id}",
        "summary": f"Summary for {node_id}.",
        "domain": "testing",
        "track": track,
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
