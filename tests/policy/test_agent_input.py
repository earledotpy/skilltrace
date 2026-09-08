"""`agent_input` — the opaque Phase 3/4 advisory recommendations seam (v2.1).

``load_agent_recommendations`` reads ``data/agent_recommendations.yaml``
into a node->priority map, warn-and-ignore on anything unreadable or
malformed. It is advisory only: a missing file is a calm empty result, and
never an error.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skilltrace.policy.agent_input import load_agent_recommendations


def _write(root: Path, doc: dict) -> Path:
    path = root / "data" / "agent_recommendations.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def test_missing_file_yields_empty_with_no_warnings(tmp_path):
    recs, warns = load_agent_recommendations(tmp_path)
    assert recs == {}
    assert warns == []


def test_valid_entries_map_node_id_to_priority(tmp_path):
    _write(
        tmp_path,
        {
            "agent_recommendations": [
                {"node_id": "a.b.c_01", "priority": 0.8},
                {"node_id": "a.b.d_01"},  # defaults to 0.5
            ]
        },
    )
    recs, warns = load_agent_recommendations(tmp_path)
    assert recs == {"a.b.c_01": 0.8, "a.b.d_01": 0.5}
    assert warns == []


def test_malformed_top_level_warns_and_yields_empty(tmp_path):
    _write(tmp_path, {"agent_recommendations": "not a list"})
    recs, warns = load_agent_recommendations(tmp_path)
    assert recs == {}
    assert any("agent_recommendations" in w for w in warns)


def test_unreadable_file_warns(tmp_path):
    path = tmp_path / "data" / "agent_recommendations.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{: not yaml\n", encoding="utf-8")
    recs, warns = load_agent_recommendations(tmp_path)
    assert recs == {}
    assert warns and any("unreadable" in w for w in warns)


def test_entries_without_node_id_are_skipped_with_warning(tmp_path):
    _write(
        tmp_path,
        {
            "agent_recommendations": [
                {"priority": 0.5},
                {"node_id": 123},
                {"node_id": "a.b.ok_01"},
            ]
        },
    )
    recs, warns = load_agent_recommendations(tmp_path)
    assert recs == {"a.b.ok_01": 0.5}
    assert len(warns) == 2