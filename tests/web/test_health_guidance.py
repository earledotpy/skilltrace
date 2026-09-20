"""The Health study-guidance roll-up build (#311, spec-tier1-serve §C-ter).

What only the built page can prove: the five cards render in the locked
hierarchy order with counts + one-line why + links; the empty-copy contract;
the limited-data prefix under the soft threshold; zero web-UI diagnostics
presence; and the guardrails — no score, no streak, no blocking language, no
zero-denominator percent.
"""

from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE_A = "math.arithmetic.order_operations_01"
NODE_B = "agents.frameworks.langgraph_01"


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _set_state(root: Path, node_id: str, state: str) -> None:
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


@pytest.fixture
def today() -> date:
    return date(2026, 9, 19)


def _seed_activity(repo: Path, today: date) -> None:
    """One active node, an open blocker, overdue + upcoming reviews, work."""
    _set_state(repo, NODE_A, "active")
    _write_yaml(
        repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.test.001",
                    "node_id": NODE_A,
                    "status": "open",
                    "description": "stuck on operator precedence",
                    "created_at": "2026-09-18T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rvw.test.001",
                    "node_id": NODE_B,
                    "status": "scheduled",
                    "scheduled_for": (today - timedelta(days=2)).isoformat(),
                    "created_at": "2026-09-01T10:00:00+00:00",
                },
                {
                    "id": "rvw.test.002",
                    "node_id": NODE_A,
                    "status": "scheduled",
                    "scheduled_for": (today + timedelta(days=5)).isoformat(),
                    "created_at": "2026-09-10T10:00:00+00:00",
                },
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.test.001",
                    "status": "completed",
                    "started_at": f"{(today - timedelta(days=1)).isoformat()}T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.test.001.01",
                    "session_id": "ses.test.001",
                    "node_id": NODE_A,
                    "created_at": f"{(today - timedelta(days=1)).isoformat()}T11:00:00+00:00",
                    "notes": "drilled precedence",
                    "minutes": 30,
                }
            ]
        },
    )


def test_hierarchy_order_and_card_contract(repo, today):
    _seed_activity(repo, today)
    _, body, status = views.health_body(repo)
    assert status == 200
    order = [body.index(t) for t in (
        "Stuck right now", "Due for review", "Evidence gaps",
        "Study rhythm", "Study resources",
    )]
    assert order == sorted(order)
    # counts + one-line why + link
    assert "1 open blocker holding up work." in body
    assert f'href="/nodes/{NODE_A}"' in body
    assert f'href="/nodes/{NODE_B}"' in body  # overdue review links its node
    assert "0 due today, 1 overdue" in body
    assert "suggestions" in body and "recomputed on each run" in body
    assert "Logged 1 work item this window." in body
    assert "Days practiced: 1." in body


def test_empty_copy_contract(repo, today):
    _, body, _ = views.health_body(repo)
    assert "No open blockers — smooth sailing." in body
    assert "Log one from a skill page" in body
    assert "No reviews scheduled — pass a skill to schedule checks" in body


def test_limited_data_prefix_under_soft_threshold(repo, today):
    _seed_activity(repo, today)  # 1 session < min_sessions_for_full_data (3)
    _, body, _ = views.health_body(repo)
    assert "Limited data (1 sessions) — " in body


def test_zero_diagnostics_presence(repo, today):
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    for banned in ("<table>", "FAILED", "health:", "states:", "verified=",
                   "Full roll-up", "graph impact", "validate evidence"):
        assert banned not in body, banned


def test_guardrails_no_score_streak_or_blocking(repo, today):
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    lowered = body.lower()
    for banned in ("score", "streak", "must complete", "blocked until"):
        assert banned not in lowered, banned


def test_header_pointer_renamed_without_a_route(repo, today):
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    assert "Full roll-up" not in body
    assert "Health →" in body  # header affordance, same single route
