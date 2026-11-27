"""The Health states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the **same** named
Health states from the same kind of fixture, or a state could be pinned by one
gate and left unchecked by the other. This module owns the mutations that turn
a pinned repo into each state the Health contract names
(spec-v3-study-day §11.5, SC-00a):

* ``populated`` — the pinned repo unchanged (the default fixture);
* ``empty`` — a learner with no execution history and no evidence records:
  the guidance cards have their empty copy, not their zero-facts;
* ``limited`` — two sessions inside the window, below the analytics policy's
  soft-data threshold, so the values stay visible under the limited warning;
* ``guidance-failure`` — the evidence store cannot be read, so study guidance
  claims nothing while repository diagnostics stays readable.

A diagnostics failure is not a repo mutation: every validator folds a bad
file into its own result, so a raised check is produced where the page reads
it (:func:`diagnostics_failure_body`).

The mutations are fixture data; no engine write path runs here.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from fixture_repo import materialise_variant, write_yaml

HEALTH_VARIANTS: tuple[str, ...] = ("empty", "limited", "guidance-failure")

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
    """No execution history and no evidence records — empty, not zeroed."""
    for name in _EXECUTION_FILES:
        path = root / "execution" / name
        if path.exists():
            path.unlink()
    write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": []})
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


def _guidance_failure(root: Path) -> None:
    """A malformed evidence record: the store cannot be read."""
    write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "not-a-record", "unknown_field": True}]},
    )


_MUTATIONS = {
    "empty": _empty,
    "limited": _limited,
    "guidance-failure": _guidance_failure,
}


def build_health_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one Health state."""
    return materialise_variant(
        pinned, kind, prefix=f"health-{kind}", mutations=_MUTATIONS
    )


def diagnostics_failure_body(root: Path) -> tuple[str, str, int]:
    """The Health body when the repository checks cannot run.

    Patches the page's one check seam, so this is the exact ``except`` branch
    a raised validator would land on — study guidance still renders.
    """
    from skilltrace.web import views

    with patch(
        "skilltrace.web.views.health.health_report",
        side_effect=OSError("the repository checks are unavailable"),
    ):
        return views.health_body(root, {})
