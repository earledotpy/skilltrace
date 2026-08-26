"""`skilltrace export sqlite` — the boring table-per-record-type mirror."""

from __future__ import annotations

import json
import sqlite3

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.sqlite_export import SQLITE_EXPORT_RELPATH

from .conftest import AVAILABLE_NODE, MASTERED_NODE

_EXPECTED_TABLES = {
    "nodes", "edges", "artifact_specs", "validation_gates", "evidence_records",
    "attempts", "sessions", "session_work", "blockers", "remediation_actions",
    "reviews", "events", "resources", "policies", "retention_memory",
}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def test_export_sqlite_contains_every_record_type(export_repo):
    rc = cli.run(["export", "sqlite"], root=export_repo)
    assert rc == 0

    db_path = export_repo / SQLITE_EXPORT_RELPATH
    assert db_path.exists()

    conn = sqlite3.connect(str(db_path))
    try:
        assert _EXPECTED_TABLES <= _table_names(conn)

        nodes = conn.execute(
            "SELECT id, state FROM nodes ORDER BY id"
        ).fetchall()
        assert (MASTERED_NODE, "mastered") in nodes
        assert (AVAILABLE_NODE, "available") in nodes

        edges = conn.execute("SELECT id, source, target FROM edges").fetchall()
        assert len(edges) == 1

        specs = conn.execute("SELECT node_id FROM artifact_specs").fetchall()
        assert specs == [(MASTERED_NODE,)]

        records = conn.execute("SELECT accepted FROM evidence_records").fetchall()
        assert records == [(1,)]

        sessions = conn.execute("SELECT status FROM sessions").fetchall()
        assert sessions == [("completed",)]

        resources = conn.execute("SELECT id, supports FROM resources").fetchall()
        assert resources[0][0] == "fixture-book"
        assert json.loads(resources[0][1]) == [MASTERED_NODE]

        policies = conn.execute("SELECT filename FROM policies").fetchall()
        assert len(policies) == 8  # one row per shipped policy file (incl. retention_model)
    finally:
        conn.close()


def test_export_sqlite_is_mutating_and_logs_one_event(export_repo):
    rc = cli.run(["export", "sqlite"], root=export_repo)
    assert rc == 0
    events = load_events(export_repo)
    assert len(events) == 1
    assert events[0]["command"] == "export sqlite"
    assert events[0]["args"] == {}


def test_export_sqlite_is_rebuilt_from_scratch_on_rerun(export_repo):
    cli.run(["export", "sqlite"], root=export_repo)
    db_path = export_repo / SQLITE_EXPORT_RELPATH

    # Poison the file: if the exporter opened-and-updated it, a stray table
    # would survive the second run.
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE stray (x)")
    conn.commit()
    conn.close()

    rc = cli.run(["export", "sqlite"], root=export_repo)
    assert rc == 0

    conn = sqlite3.connect(str(db_path))
    try:
        assert "stray" not in _table_names(conn)
    finally:
        conn.close()


def test_export_sqlite_fails_cleanly_on_missing_evidence_files(tmp_path):
    (tmp_path / "graph" / "nodes").mkdir(parents=True)
    (tmp_path / "graph" / "edges.yaml").write_text("edges: []\n", encoding="utf-8")

    rc = cli.run(["export", "sqlite"], root=tmp_path)
    assert rc == 1
    assert not (tmp_path / "data" / "skilltrace.db").exists()
    assert load_events(tmp_path) == []


def test_export_sqlite_includes_retention_memory_row_for_mastered_node(export_repo):
    """The disposable mirror gains a derived row per passed/mastered node.

    Tier 2 G-Storage: the engine never reads the db; the table is
    computed during the mirror's rebuild pass.
    """
    rc = cli.run(["export", "sqlite"], root=export_repo)
    assert rc == 0

    db_path = export_repo / SQLITE_EXPORT_RELPATH
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT node_id, asserted_state, anchor_kind, half_life_days, confidence "
            "FROM retention_memory"
        ).fetchall()
        # The export_repo fixture has one mastered node; the available node
        # does not enter the table per spec §5.2.
        assert len(rows) == 1
        node_id, asserted_state, anchor_kind, half_life, confidence = rows[0]
        assert node_id == MASTERED_NODE
        assert asserted_state == "mastered"
        assert anchor_kind == "pass"
        assert half_life == 7.0
        # Confidence is 0 < c <= 1 — no exact value pinned (today is variable).
        assert 0.0 < confidence <= 1.0
    finally:
        conn.close()
