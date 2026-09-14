"""Focused Web-layer contract tests for the v1.6 analytics dashboard."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "execution", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _seed_dashboard_data(tmp_path: Path) -> Path:
    root = _seed_repo(tmp_path)
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": f"ses.2026-08-{day}.001",
                    "status": "completed",
                    "started_at": f"2026-08-{day}T10:00:00Z",
                    "ended_at": f"2026-08-{day}T11:00:00Z",
                }
                for day in ("10", "20", "25")
            ]
        },
    )
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rev.dashboard.001",
                    "node_id": "math.arithmetic.order_operations_01",
                    "status": "scheduled",
                    "scheduled_for": "2026-08-01",
                    "created_at": "2026-07-01T10:00:00Z",
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
                    "id": f"blk.dashboard.{n:03d}",
                    "node_id": "math.arithmetic.order_operations_01",
                    "status": "open",
                    "description": f"stuck on step {n}",
                    "created_at": "2026-08-01T10:00:00Z",
                }
                for n in range(1, 4)
            ]
        },
    )
    return root


def test_dashboard_renders_one_theme_per_page_with_theme_control(tmp_path):
    """v2.4 S5: one theme per page; the theme= control swaps it, plain links."""
    root = _seed_dashboard_data(tmp_path)
    title, body, status = views.analytics_body(root)

    assert (title, status) == ("Analytics", 200)
    # One visible theme card, not four stacked charts (T4 §H: a plain card;
    # the table detail sits collapsed behind one Details).
    assert body.count('<div class="card analytics-card">') == 1
    assert body.count("<details>") == 1
    # The velocity theme renders its real multi-point weekly series.
    assert body.count("<svg") == 1
    assert 'name="theme"' in body
    assert "Velocity" in body
    # Plain-link theme switching reuses the export theme vocabulary.
    assert "theme=blockers" in body
    assert "theme=reviews" in body
    assert "theme=evidence" in body
    assert body.count('action="/analytics/export"') == 1
    assert "<script" not in body.lower()


def test_dashboard_theme_switch_selects_the_named_theme(tmp_path):
    root = _seed_dashboard_data(tmp_path)
    _, velocity, _ = views.analytics_body(root, {"theme": ["velocity"]})
    _, blockers, _ = views.analytics_body(root, {"theme": ["blockers"]})

    assert "Velocity" in velocity
    assert "Open blockers are counted now" in blockers
    # Single-point series render no pseudo-sparkline (P2.2).
    assert "<svg" not in blockers


def test_dashboard_unknown_theme_falls_back_to_velocity(tmp_path):
    root = _seed_dashboard_data(tmp_path)
    _, body, _ = views.analytics_body(root, {"theme": ["nope"]})
    assert "Velocity" in body


def test_dashboard_renders_overdue_banner_and_advisory_slot(tmp_path):
    root = _seed_dashboard_data(tmp_path)
    body = views.analytics_body(root)[1]

    assert "Overdue reviews:" in body
    advisory_banners = body
    assert "Active blocker spike" in advisory_banners


def test_dashboard_collapses_to_one_column_at_the_locked_breakpoint():
    assert "@media(max-width:960px){.analytics-grid{grid-template-columns:1fr}}" in views._STYLE


def test_dashboard_shows_limited_data_banner_below_threshold(tmp_path):
    title, body, status = views.analytics_body(_seed_repo(tmp_path))

    assert (title, status) == ("Analytics", 200)
    assert "Limited data — fewer than 3 sessions in the last 30 days." in body
    assert "Results may not reflect your full activity." in body


def test_dashboard_hides_limited_data_banner_with_full_data(tmp_path):
    from datetime import date, timedelta

    root = _seed_repo(tmp_path)
    today = date.today()
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": f"ses.dashboard.{n:03d}",
                    "status": "completed",
                    "started_at": f"{today - timedelta(days=n * 5)}T10:00:00Z",
                    "ended_at": f"{today - timedelta(days=n * 5)}T11:00:00Z",
                }
                for n in range(3)
            ]
        },
    )
    body = views.analytics_body(root)[1]

    assert "Limited data" not in body
