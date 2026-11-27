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

from skilltrace.execution.overdue import utc_today
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
    """The date the study-rhythm window is measured against.

    The guidance derivation reads the wall clock (the web layer has no
    ``Context.clock`` seam), so the fixture's records are dated relative
    to the real today. A pinned date would put the seeded records outside
    the window and the assertions would measure nothing.
    """
    return utc_today()


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
    assert "suggestions" in body and "recomputed on each run" in body
    assert "Logged 1 work item this window." in body
    assert "Days practiced: 1." in body


def test_empty_copy_contract(repo, today):
    _, body, _ = views.health_body(repo)
    assert "No open blockers — smooth sailing." in body
    assert "Log one from a skill page" in body
    assert "No reviews scheduled — pass a skill to schedule checks" in body
    # Zero sessions is the empty case, not a limited sample: there are no
    # valid values to retain, so no limited-data warning is claimed.
    assert "Limited data (0 sessions)" not in body


def test_limited_data_prefix_under_soft_threshold(repo, today):
    _seed_activity(repo, today)  # 1 session < min_sessions_for_full_data (3)
    _, body, _ = views.health_body(repo)
    assert "limited data (1 session" in body.lower()


def test_health_is_exactly_two_named_projections(repo, today):
    """Two projections, both named, neither an aggregate (VS-10).

    The v2.4 page carried one roll-up and no diagnostics at all; the v3
    contract splits the surface so that a learner fact never reads as a
    repository fault and neither can block the learner.
    """
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    assert "Study guidance" in body
    assert "Repository diagnostics" in body
    # The guidance section comes first: the learner before the repository.
    assert body.index("Study guidance") < body.index("Repository diagnostics")


def test_the_two_projections_are_declared_independent(repo, today):
    """Each projection says what it is about, and that it blocks nothing."""
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    assert "not your progress" in body
    assert "never block" in body


def test_the_guardrails_hold(repo, today):
    """No composite score, no streak, no blocking language (VS-10).

    The page may *say* it has no overall score — the ban is on a score
    being reported, not on the word appearing in a disclaimer.
    """
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    lowered = body.lower()
    for banned in ("streak", "must complete", "blocked until"):
        assert banned not in lowered, banned
    # No composite figure is reported: the only numbers are per-layer
    # counts and per-projection facts.
    assert "overall score" in lowered  # the disclaimer, not a figure
    assert "health score" not in lowered
    assert "composite" not in lowered


def test_diagnostics_are_a_separate_table_not_a_mixed_one(repo, today):
    """The diagnostics table lists layers, and holds no learner facts."""
    _seed_activity(repo, today)
    _, body, _ = views.health_body(repo)
    guidance, _, diagnostics = body.partition("Repository diagnostics")
    assert "<table" in diagnostics
    assert "<table" not in guidance
    # A layer's standing is its own; the guidance never carries one.
    for banned in ("Layer", "OK", "FAILED"):
        assert banned not in guidance, banned


def test_health_is_reachable_from_the_operations_navigation(repo, today):
    """Health is an Operations capability — reachable, not a stray link."""
    _seed_activity(repo, today)
    _, body, _ = views.operations_body(repo)
    assert 'href="/health"' in body


# --- could-not-compute: each section fails independently (SC-00a) ----------


def test_a_degraded_guidance_source_claims_nothing(repo, today):
    """An unreadable evidence store is not an empty study history.

    The five guidance cards would otherwise turn "not known" into "none" (and
    "0 work items"), which is exactly the fabricated health fact SC-00a
    forbids. Diagnostics is a different projection and stays readable.
    """
    _seed_activity(repo, today)
    (repo / "evidence" / "evidence_records.yaml").write_text(
        "evidence_records: [ { broken", encoding="utf-8"
    )
    _, body, _ = views.health_body(repo)
    assert "Study guidance could not be worked out" in body
    assert "not even that any of them are zero" in body
    assert "Sources unavailable: <code>records</code>" in body
    assert "diagnostics below name the source and its error" in body
    # No empty copy, no zero.
    for fabricated in (
        "No open blockers",
        "No reviews scheduled",
        "No gaps on active nodes",
        "Logged 0 work items",
        "All supporting materials",
    ):
        assert fabricated not in body, fabricated
    # The other projection is unaffected, and a failed layer never presents
    # its zero as a count.
    assert "Repository diagnostics" in body
    diagnostics = body.partition("Repository diagnostics")[2]
    assert "<table" in diagnostics
    assert "0 records" not in diagnostics
    assert "Not counted — this layer failed" in diagnostics
    assert "failing" in diagnostics


def test_diagnostics_failure_does_not_erase_study_guidance(repo, today, monkeypatch):
    """The other direction: a failed repository check leaves guidance intact."""
    from skilltrace.web.views import health as health_view

    _seed_activity(repo, today)

    def unavailable(_root):
        raise OSError("the repository checks are unavailable")

    monkeypatch.setattr(health_view, "health_report", unavailable)
    _, body, _ = views.health_body(repo)
    assert "Diagnostics could not be run" in body
    assert "your study guidance above is unaffected" in body
    assert "Try the checks again" in body
    assert "Study guidance" in body
    assert "1 open blocker holding up work." in body
    # The study-guidance projection still precedes the diagnostics one.
    assert body.index("Study guidance") < body.index("Repository diagnostics")


def test_diagnostics_carry_exact_source_detail(repo, today):
    """A dangling relationship names its source, never just "failing"."""
    _seed_activity(repo, today)
    path = repo / "graph" / "edges.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["edges"].append(
        {
            "id": "edge.no.such.node_99__data.pandas.dataframe_basics_01",
            "source": "no.such.node_99",
            "target": "data.pandas.dataframe_basics_01",
            "edge_type": "hard_prerequisite",
            "reason": "Authored fixture: a dangling reference.",
            "active": True,
        }
    )
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    _, body, _ = views.health_body(repo)
    diagnostics = body.partition("Repository diagnostics")[2]
    assert "failing" in diagnostics
    assert "graph findings" in diagnostics
    assert "source names unknown node no.such.node_99" in diagnostics


def test_a_diagnostic_warning_warns_without_authority(repo, today):
    """A warning is a finding, not a learner fact and not a blocker."""
    _seed_activity(repo, today)
    path = repo / "graph" / "resources.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["resources"].append(
        {
            "id": "resource-with-no-skill",
            "url": "https://example.com/unsupported",
            "cost": "free",
            "supports": [],
            "last_verified": "2026-07-10",
        }
    )
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    _, body, _ = views.health_body(repo)
    diagnostics = body.partition("Repository diagnostics")[2]
    assert "warning" in diagnostics
    assert "supports no node" in diagnostics
    # Warnings describe the repository, never the learner and never a block.
    assert "blocked until" not in diagnostics.lower()
    # The guidance section carries no repository finding.
    guidance = body.partition("Repository diagnostics")[0]
    assert "supports no node" not in guidance
