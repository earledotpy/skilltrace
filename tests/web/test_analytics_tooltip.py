"""Granted tier-1 tooltip upgrade: chart hover/focus tooltips (ADR 0008).

The analytics velocity chart is the one surface carrying the single granted
inline script: focusable per-point markers (native ``<title>`` = the tier-0
tooltip, full function with script absent) plus exactly one script tag that
upgrades them to hover/focus tooltips. Every other theme and route carries
neither markers nor script (DD6 per-route budget).
"""

from __future__ import annotations

import re
import shutil
from datetime import timedelta
from pathlib import Path

import yaml

from skilltrace.analytics.sparkline import sparkline_svg
from skilltrace.execution.overdue import utc_today
from skilltrace.web import views
from skilltrace.web.analytics_tooltip import tooltip_script
from skilltrace.web.interface import forbidden_matches

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "execution", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _seed_multipoint_weeks(tmp_path: Path) -> Path:
    """Seed repo whose velocity weeks span several ISO buckets in-window."""
    root = _seed_repo(tmp_path)
    today = utc_today()
    dates = [today - timedelta(days=n) for n in (20, 9, 2)]
    sessions = {
        "sessions": [
            {"id": f"ses.{day.isoformat()}.001", "status": "completed",
             "started_at": f"{day.isoformat()}T10:00:00Z",
             "ended_at": f"{day.isoformat()}T11:00:00Z"}
            for day in dates
        ]
    }
    (root / "execution" / "sessions.yaml").write_text(
        yaml.safe_dump(sessions), encoding="utf-8")
    work = {
        "session_work": [
            {"id": f"wrk.{i + 1:03d}", "session_id": f"ses.{day.isoformat()}.001",
             "node_id": "math.arithmetic.order_operations_01",
             "created_at": f"{day.isoformat()}T10:30:00Z", "minutes": 30}
            for i, day in enumerate(dates)
        ]
    }
    (root / "execution" / "session_work.yaml").write_text(
        yaml.safe_dump(work), encoding="utf-8")
    return root


def test_velocity_theme_carries_exactly_the_granted_script(tmp_path):
    root = _seed_multipoint_weeks(tmp_path)
    _, body, _ = views.analytics_body(root, {"theme": ["velocity"]})
    assert len(re.findall(r"<script\b", body, re.IGNORECASE)) == 1
    assert 'data-tip="' in body
    # Tier-0 intact: every marker keeps its native title.
    assert body.count("<title>") >= 2


def test_non_velocity_themes_carry_no_script(tmp_path):
    root = _seed_multipoint_weeks(tmp_path)
    for theme in ("blockers", "reviews", "evidence"):
        _, body, _ = views.analytics_body(root, {"theme": [theme]})
        assert "<script" not in body.lower(), theme
        assert "data-tip=" not in body, theme


def test_script_is_read_only_and_escaped(tmp_path):
    script = tooltip_script()
    assert script.startswith("<script>") and script.rstrip().endswith("</script>")
    assert "textContent" in script
    assert "innerHTML" not in script
    assert "fetch(" not in script and "XMLHttpRequest" not in script
    # P3.1-clean by construction: no command names, flags, ids, or paths.
    assert forbidden_matches(script) == []


def test_seam_markers_opt_in_and_single_point_refused():
    multi = sparkline_svg([("a", 1), ("b", 3)], with_points=True)
    assert multi.count("<circle") == 2
    assert multi.count("<title>") == 2
    assert 'data-tip="a: 1"' in multi
    # P2.2: a single-point series never gains markers, even opted in.
    single = sparkline_svg([("a", 1)], with_points=True)
    assert "<circle" not in single
    # Defaults keep every existing caller byte-identical.
    plain = sparkline_svg([("a", 1), ("b", 3)])
    assert "<circle" not in plain and "<title>" not in plain
