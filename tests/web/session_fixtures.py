"""The Study cockpit and Session-close states as fixture repos.

The golden snapshot suite and the axe harness render the *same* cockpit
states from the same fixture, or a state could be pinned by one gate and
left unchecked by the other. This module owns those states
(spec-v3-study-day §10.5, §10.6):

* ``populated`` — the pinned repo unchanged (its open Session, two hours
  old, with recorded work);
* ``stale`` — the same Session started three days before the frozen
  moment, past the policy staleness window, so the warning and the honest
  past-end closure are visible;
* ``refusal`` — the fresh page after a **refused second start**: the
  submission is real (it goes through the dispatcher), it writes nothing,
  and the cockpit it lands on states the two real options and the way back
  to the existing Session (R5).

The stale mutation is fixture data, exactly as the other web suites seed
state. The refusal page is produced by the write path itself, which is the
point of the state: a refusal writes no records.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs

import yaml
from fixture_repo import materialise_variant, write_yaml

#: Three days before the suites' frozen moment (2026-11-17T09:00Z) — well
#: past the 12-hour default staleness window.
STALE_STARTED_AT = "2026-11-14T09:00:00+00:00"


def _make_session_stale(root: Path) -> None:
    """Start the open Session three days ago — a forgotten Session."""
    path = root / "execution" / "sessions.yaml"

    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sessions = doc.get("sessions") or []
    for session in sessions:
        if session.get("status") == "open":
            session["started_at"] = STALE_STARTED_AT
    write_yaml(root, "execution/sessions.yaml", {"sessions": sessions})


_MUTATIONS = {"stale": _make_session_stale}


def build_session_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one named cockpit state."""
    return materialise_variant(
        pinned, kind, prefix=f"session-{kind}", mutations=_MUTATIONS
    )


def refused_start_body(
    root: Path, node_id: str
) -> tuple[str, str, int]:
    """The served cockpit after a refused second start — the refusal state.

    Drives the real write path: the engine refuses (a Session is already
    open), writes no record, and redirects to the cockpit with the
    translated refusal. Rendering the redirect target pins exactly what the
    learner sees at the moment the refusal fires (IC-8, R5).
    """
    from skilltrace.web import views
    from skilltrace.web.views import Redirect

    result = views.post_start(root, node_id, {"next": ["/session"]})
    assert isinstance(result, Redirect), "a second start must be refused"
    query = parse_qs(result.location.partition("?")[2])
    return views.session_body(root, query)
