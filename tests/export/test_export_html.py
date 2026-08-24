"""`skilltrace export html` — the derived, self-contained HTML snapshot.

Mirrors the markdown/sqlite sibling tests: it writes a disposable file, logs
exactly one audit event, overwrites on rerun, and refuses cleanly on any load
error. It additionally asserts the file is genuinely self-contained (inline CSS,
zero JS, no external assets) and that no engine path ever reads it back.
"""

from __future__ import annotations

from pathlib import Path

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.html_export import HTML_EXPORT_RELPATH

from .conftest import AVAILABLE_NODE, MASTERED_NODE


def test_export_html_writes_self_contained_file(export_repo):
    rc = cli.run(["export", "html"], root=export_repo)
    assert rc == 0

    path = export_repo / HTML_EXPORT_RELPATH
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    # Self-contained: one inline style block, no JS, no external assets.
    assert "<!doctype html>" in text
    assert "<style>" in text
    assert "<script" not in text
    assert "<link" not in text
    assert "<img" not in text

    # Frozen-view banner + generated-at stamp present.
    assert "NOT LIVE" in text
    assert "Generated at" in text
    assert "skilltrace ui" in text

    # All five-layer sections present, plus real content.
    assert "Progress / overview" in text
    assert "Blockers" in text
    assert "Reviews due / overdue" in text
    assert "Evidence coverage + gates" in text
    assert "Resource verification" in text
    assert "HEALTH STRIP" in text

    assert MASTERED_NODE in text
    assert AVAILABLE_NODE in text
    assert "fixture-book" in text  # the fixture resource


def test_export_html_is_mutating_and_logs_one_event(export_repo):
    rc = cli.run(["export", "html"], root=export_repo)
    assert rc == 0
    events = load_events(export_repo)
    assert len(events) == 1
    assert events[0]["command"] == "export html"
    assert events[0]["args"] == {}
    assert events[0]["records_touched"] == []


def test_export_html_overwrites_on_rerun(export_repo):
    cli.run(["export", "html"], root=export_repo)
    path = export_repo / HTML_EXPORT_RELPATH

    rc = cli.run(["export", "html"], root=export_repo)
    assert rc == 0
    second = path.read_text(encoding="utf-8")
    # Whole-file rewrite, not appended: exactly one document.
    assert second.count("<!doctype html>") == 1


def test_export_html_fails_cleanly_on_missing_evidence_files(tmp_path):
    """A repo missing its shipped evidence files refuses the export rather
    than writing a snapshot built from partially-loaded data."""
    (tmp_path / "graph" / "nodes").mkdir(parents=True)
    (tmp_path / "graph" / "edges.yaml").write_text("edges: []\n", encoding="utf-8")

    rc = cli.run(["export", "html"], root=tmp_path)
    assert rc == 1
    assert not (tmp_path / HTML_EXPORT_RELPATH).exists()
    assert load_events(tmp_path) == []


def test_export_html_relpath_not_read_by_engine():
    """The disposable HTML is written only; no engine module may read it back."""
    src = Path(__file__).resolve().parents[2] / "src" / "skilltrace"
    # The writers (export.py, html_export.py) and the CLI help string (cli.py)
    # reference the path; nothing should open it for reading.
    allowed = {"html_export.py", "export.py", "cli.py"}
    offenders = [
        p.name
        for p in src.rglob("*.py")
        if p.name not in allowed and "export.html" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []
