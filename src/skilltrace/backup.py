"""`skilltrace backup` — a timestamped zip of the five data layers.

Per the #33 resolution: `graph/`, `evidence/` (including the gitignored
`evidence/artifacts/` — the one thing with no history anywhere else, so
backup is its only net), `execution/`, `policy/`, and `release/`, exactly as
they sit on disk. Not `src/`, `docs/`, or `data/` — code and docs are git's
job, and `data/` is disposable by definition. Plain zip (stdlib, no new
dependency, Windows-native) at `backups/skilltrace-backup-YYYYMMDD-HHMMSS.zip`
— a name that sorts chronologically. `backup` only ever adds files; there is
no pruning and no restore command (restore is a documented RUNBOOK procedure,
v1.0.0-rc1).
"""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path

BACKUP_DIRS: tuple[str, ...] = ("graph", "evidence", "execution", "policy", "release")
_BACKUP_RELDIR = Path("backups")


def _timestamp(moment: datetime) -> str:
    return moment.strftime("%Y%m%d-%H%M%S")


def create_backup(root: Path | str, *, now: datetime | None = None) -> Path:
    """Zip the five data layers into a fresh timestamped archive. Returns its path."""
    root_path = Path(root)
    moment = now or datetime.now(timezone.utc)

    backups_dir = root_path / _BACKUP_RELDIR
    backups_dir.mkdir(parents=True, exist_ok=True)
    archive_path = backups_dir / f"skilltrace-backup-{_timestamp(moment)}.zip"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for dirname in BACKUP_DIRS:
            source = root_path / dirname
            if not source.is_dir():
                continue
            for file_path in sorted(source.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(root_path).as_posix()
                    archive.write(file_path, arcname)

    return archive_path
