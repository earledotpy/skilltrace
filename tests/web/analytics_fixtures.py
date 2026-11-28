"""The named Analytics states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the **same** named
Analytics states from the same kind of fixture, or a state could be pinned by
one gate and left unchecked by the other. This module owns the mutations that
turn a pinned repo into each state the Analytics contract names
(spec-v3-study-day §11.6, SC-00a):

* ``populated`` — the pinned repo unchanged: real sessions, work items,
  blockers, reviews and evidence requirements;
* ``empty`` — no execution history and no artifact specs, so every theme has
  an honest empty population instead of a fabricated zero;
* ``limited`` — two sessions inside the window, below the analytics policy's
  soft-data threshold, so the values stay visible under the limited warning;
* ``failure`` — the sessions store cannot be read, so the page is a
  could-not-compute state that claims no zero.

The mutations are fixture data; no engine write path runs here.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from fixture_repo import materialise_variant, write_yaml

ANALYTICS_VARIANTS: tuple[str, ...] = ("empty", "limited", "failure")

_EXECUTION_FILES = (
    "sessions.yaml",
    "session_work.yaml",
    "blockers.yaml",
    "reviews.yaml",
    "remediation_actions.yaml",
)


def _read_yaml(root: Path, relpath: str) -> dict:
    return yaml.safe_load((root / relpath).read_text(encoding="utf-8")) or {}


def _empty(root: Path) -> None:
    """No execution history and no evidence requirements — empty, not zeroed."""
    for name in _EXECUTION_FILES:
        path = root / "execution" / name
        if path.exists():
            path.unlink()
    write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": []})
    write_yaml(root, "evidence/artifact_specs.yaml", {"artifact_specs": []})
    write_yaml(root, "execution/events.yaml", {"events": []})


def _limited(root: Path) -> None:
    """Two sessions inside the window — valid values under a stated threshold."""
    doc = _read_yaml(root, "execution/sessions.yaml")
    sessions = doc.get("sessions", [])
    kept = [s for s in sessions if s.get("status") == "open"]
    completed = sorted(
        (s for s in sessions if s.get("status") != "open"),
        key=lambda s: s.get("started_at") or "",
        reverse=True,
    )
    kept.extend(completed[:1])
    doc["sessions"] = kept
    write_yaml(root, "execution/sessions.yaml", doc)

    kept_ids = {s["id"] for s in kept}
    work = _read_yaml(root, "execution/session_work.yaml")
    work["session_work"] = [
        item for item in work.get("session_work", []) if item.get("session_id") in kept_ids
    ]
    write_yaml(root, "execution/session_work.yaml", work)


def _failure(root: Path) -> None:
    """A malformed session record: the execution store cannot be read."""
    write_yaml(
        root,
        "execution/sessions.yaml",
        {"sessions": [{"id": "not-a-session", "unknown_field": True}]},
    )


_MUTATIONS = {
    "empty": _empty,
    "limited": _limited,
    "failure": _failure,
}


def build_analytics_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one Analytics state."""
    return materialise_variant(
        pinned, kind, prefix=f"analytics-{kind}", mutations=_MUTATIONS
    )
