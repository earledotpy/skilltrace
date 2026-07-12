"""`skilltrace export markdown` — the compact Markdown snapshot."""

from __future__ import annotations

import yaml

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.markdown_export import MARKDOWN_EXPORT_RELPATH

from .conftest import AVAILABLE_NODE, MASTERED_NODE


def test_export_markdown_writes_the_snapshot_file(export_repo):
    rc = cli.run(["export", "markdown"], root=export_repo)
    assert rc == 0

    path = export_repo / MARKDOWN_EXPORT_RELPATH
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    # Contains graph/evidence/session summary (roadmap v0.9 test).
    assert "## Nodes" in text
    assert "## Evidence" in text
    assert "## Sessions" in text

    assert MASTERED_NODE in text
    assert AVAILABLE_NODE in text
    assert "### mastered" in text
    assert "### available" in text
    assert "accepted evidence: 1" in text  # the mastered node's accepted record
    assert "sess.001" in text


def test_export_markdown_is_mutating_and_logs_one_event(export_repo):
    rc = cli.run(["export", "markdown"], root=export_repo)
    assert rc == 0
    events = load_events(export_repo)
    assert len(events) == 1
    assert events[0]["command"] == "export markdown"
    assert events[0]["args"] == {}
    assert events[0]["records_touched"] == []


def test_export_markdown_overwrites_on_rerun(export_repo):
    cli.run(["export", "markdown"], root=export_repo)
    path = export_repo / MARKDOWN_EXPORT_RELPATH

    rc = cli.run(["export", "markdown"], root=export_repo)
    assert rc == 0
    second = path.read_text(encoding="utf-8")
    # Overwritten, not appended: exactly one header, one Nodes section.
    assert second.count("# SkillTrace export") == 1
    assert second.count("## Nodes") == 1


def test_export_markdown_summarizes_sessions_never_enumerates_in_full(export_repo):
    """Per the #33 resolution, sessions are 'summarized (totals + recent
    handful), never enumerated in full' — with 7 sessions, only the 5 most
    recent render, but the totals line still counts all 7."""
    sessions = [
        {
            "id": f"sess.{n:03d}",
            "status": "completed",
            "started_at": f"2026-06-{n:02d}T10:00:00+00:00",
            "ended_at": f"2026-06-{n:02d}T10:30:00+00:00",
        }
        for n in range(1, 8)
    ]
    (export_repo / "execution" / "sessions.yaml").write_text(
        yaml.safe_dump({"sessions": sessions}, sort_keys=False), encoding="utf-8"
    )

    rc = cli.run(["export", "markdown"], root=export_repo)
    assert rc == 0
    text = (export_repo / MARKDOWN_EXPORT_RELPATH).read_text(encoding="utf-8")

    assert "total: 7 " in text
    assert "recent (most recent 5):" in text
    for n in range(3, 8):  # the 5 most recent: sess.003..sess.007
        assert f"sess.{n:03d}" in text
    for n in (1, 2):  # the 2 oldest are summarized away, not enumerated
        assert f"sess.{n:03d}" not in text


def test_export_markdown_fails_cleanly_on_missing_evidence_files(tmp_path):
    """A repo missing its shipped evidence files refuses the export rather
    than writing a snapshot that silently omits evidence data."""
    (tmp_path / "graph" / "nodes").mkdir(parents=True)
    (tmp_path / "graph" / "edges.yaml").write_text("edges: []\n", encoding="utf-8")

    rc = cli.run(["export", "markdown"], root=tmp_path)
    assert rc == 1
    assert not (tmp_path / "data" / "export.md").exists()
    assert load_events(tmp_path) == []
