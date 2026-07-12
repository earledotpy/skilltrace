"""`skilltrace backup` — a timestamped zip of the five data layers."""

from __future__ import annotations

import re
import zipfile

from skilltrace import cli
from skilltrace.events import load_events

_NAME_RE = re.compile(r"^skilltrace-backup-\d{8}-\d{6}\.zip$")


def test_backup_creates_a_timestamped_archive(export_repo):
    rc = cli.run(["backup"], root=export_repo)
    assert rc == 0

    backups_dir = export_repo / "backups"
    archives = list(backups_dir.glob("*.zip"))
    assert len(archives) == 1
    assert _NAME_RE.match(archives[0].name)


def test_backup_archive_contains_the_five_layers_including_gitignored_artifacts(export_repo):
    (export_repo / "evidence" / "artifacts").mkdir(parents=True, exist_ok=True)
    (export_repo / "evidence" / "artifacts" / "solution.txt").write_text(
        "learner solution", encoding="utf-8"
    )
    (export_repo / "release").mkdir(parents=True, exist_ok=True)
    (export_repo / "release" / "manifest.yaml").write_text("manifest: {}\n", encoding="utf-8")

    rc = cli.run(["backup"], root=export_repo)
    assert rc == 0

    archive_path = next((export_repo / "backups").glob("*.zip"))
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()

    assert "graph/edges.yaml" in names
    assert "graph/state.yaml" in names
    assert "evidence/artifact_specs.yaml" in names
    assert "evidence/artifacts/solution.txt" in names
    assert "execution/sessions.yaml" in names
    assert "policy/workload.yaml" in names
    assert "release/manifest.yaml" in names
    assert not any(name.startswith("data/") for name in names)
    assert not any(name.startswith("backups/") for name in names)
    assert not any("\\" in name for name in names)


def test_backup_is_mutating_and_logs_one_event(export_repo):
    rc = cli.run(["backup"], root=export_repo)
    assert rc == 0
    events = load_events(export_repo)
    assert len(events) == 1
    assert events[0]["command"] == "backup"
    assert events[0]["args"] == {}
    assert events[0]["records_touched"] == []
