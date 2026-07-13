"""`skilltrace health` — cross-layer roll-up plus liveness facts (issue #37).

Per the #34 resolution: health runs the same five layer validators as the
`validate` suite (one summary line each) plus liveness facts validate doesn't
cover (progress store presence, content-based sync drift, stale open
sessions, resource verification summary). It inherits validate's exit
contract exactly — any layer *error* fails the run; every liveness finding is
a *warning* and never affects the exit code.

Every test drives the real CLI in-process through `cli.run(argv, root=...)` —
the single seam — asserting only exit codes, stdout, and the event log.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


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
    }
    block = yaml.safe_dump(frontmatter, sort_keys=False)
    path = root / "graph" / "nodes" / f"{node_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{block}---\n\n# {node_id}\n", encoding="utf-8")


@pytest.fixture
def health_repo(tmp_path: Path) -> Path:
    """A disposable repo root: shipped policy seeds, an empty (but present)
    evidence trail and resource registry, no graph nodes or progress store.

    Evidence files ship with the seed and their absence is itself a defect
    (see `evidence/_schema.py`), so they're written empty here to isolate each
    test to the one layer/liveness fact it means to exercise.
    """
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    _write_yaml(tmp_path, "evidence/artifact_specs.yaml", {"artifact_specs": []})
    _write_yaml(tmp_path, "evidence/validation_gates.yaml", {"validation_gates": []})
    _write_yaml(tmp_path, "evidence/evidence_records.yaml", {"evidence_records": []})
    _write_yaml(tmp_path, "evidence/attempts.yaml", {"attempts": []})
    _write_yaml(tmp_path, "graph/resources.yaml", {"resources": []})
    return tmp_path


# --- Registration and exit gate ----------------------------------------------


def test_health_is_registered_read_only():
    command = cli.REGISTRY.get("health")
    assert command is not None
    assert command.kind.value == "read_only"


def test_shipped_repo_health_exits_zero(capsys):
    # The exit-gate command: health on the shipped seed repo is exit 0.
    rc = cli.run(["health"], root=REPO_ROOT)
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip().splitlines()[-1].startswith("health: OK")


def test_health_is_read_only_and_logs_nothing(health_repo):
    rc = cli.run(["health"], root=health_repo)
    assert rc == 0
    assert load_events(health_repo) == []


def test_clean_minimal_repo_is_ok_on_every_layer(health_repo, capsys):
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    for target in ("graph", "evidence", "execution", "policy", "resources"):
        assert f"{target}:" in out
    assert "FAILED" not in out


# --- Layer roll-up: errors fail the run, warnings don't ----------------------


def test_layer_error_fails_health(health_repo, capsys):
    # A dangling edge endpoint is a graph *error* (validate graph's contract).
    _write_node(health_repo, "testing.health.subject_01")
    _write_yaml(
        health_repo,
        "graph/edges.yaml",
        {
            "edges": [
                {
                    "id": "edge.health.001",
                    "source": "testing.health.subject_01",
                    "target": "testing.health.missing_02",
                    "edge_type": "hard_prerequisite",
                    "reason": "fixture edge",
                    "active": True,
                }
            ]
        },
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "graph:" in out
    assert "FAILED" in out
    assert "[error]" in out
    assert "unknown node" in out
    assert "health: FAILED" in out


# --- Liveness: progress store presence and content-based sync drift ---------


def test_no_progress_store_warns_but_exits_zero(health_repo, capsys):
    _write_node(health_repo, "testing.health.subject_01")
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no progress store found" in out
    assert "skilltrace sync" in out
    assert "health: OK (" in out


def test_sync_drift_warns_when_store_present_but_incomplete(health_repo, capsys):
    _write_node(health_repo, "testing.health.subject_01")
    _write_node(health_repo, "testing.health.subject_02")
    _write_yaml(
        health_repo,
        "graph/state.yaml",
        {"progress": {"testing.health.subject_01": {"state": "available"}}},
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 node(s) missing from the progress store" in out
    # The store *is* present — the two liveness facts must not both fire.
    assert "no progress store found" not in out


def test_synced_repo_reports_state_counts_with_no_drift_warning(health_repo, capsys):
    _write_node(health_repo, "testing.health.subject_01")
    _write_yaml(
        health_repo,
        "graph/state.yaml",
        {"progress": {"testing.health.subject_01": {"state": "available"}}},
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "progress store: 1 node(s); states: available=1" in out
    assert "missing from the progress store" not in out


# --- Liveness: stale open session --------------------------------------------


def test_stale_open_session_warns(health_repo, capsys):
    _write_yaml(
        health_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.001",
                    "status": "open",
                    "started_at": "2020-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "stale" in out.lower()
    assert "session close" in out


def test_fresh_open_session_does_not_warn(health_repo, capsys):
    from datetime import datetime, timezone

    _write_yaml(
        health_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.001",
                    "status": "open",
                    "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
            ]
        },
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "has been open" not in out
    assert "session close" not in out


# --- Liveness: resource verification summary ---------------------------------


def test_broken_resource_warns_in_summary(health_repo, capsys):
    _write_node(health_repo, "testing.health.subject_01")
    _write_yaml(
        health_repo,
        "graph/resources.yaml",
        {
            "resources": [
                {
                    "id": "dead-one",
                    "url": "https://example.invalid/dead",
                    "cost": "free",
                    "supports": ["testing.health.subject_01"],
                    "broken": {"date": "2020-01-01", "reason": "404 gone"},
                }
            ]
        },
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "broken=1" in out
    assert "resource(s) stale or broken" in out
    assert "resource-report" in out


def test_all_verified_resources_do_not_warn(health_repo, capsys):
    from datetime import datetime, timezone

    _write_node(health_repo, "testing.health.subject_01")
    _write_yaml(
        health_repo,
        "graph/resources.yaml",
        {
            "resources": [
                {
                    "id": "good-one",
                    "url": "https://example.invalid/good",
                    "cost": "free",
                    "supports": ["testing.health.subject_01"],
                    "last_verified": datetime.now(timezone.utc).date().isoformat(),
                }
            ]
        },
    )
    rc = cli.run(["health"], root=health_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "verified=1" in out
    assert "stale or broken" not in out
