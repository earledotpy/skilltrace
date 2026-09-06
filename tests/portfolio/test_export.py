"""Export-layer tests for the portfolio builder (v2.0 spec §5, T-TestArch #180).

Drives ``portfolio export``/``preview`` through ``cli.run`` against a
disposable repo seeded from the ship's truth files plus hand-built
overrides (written via ``_write_yaml``). Markdown and HTML assert presence
only; JSON pins the exact published contract fields.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from skilltrace import cli

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE_A = "portfolio.project.slope_calculator_01"
NODE_B = "portfolio.project.data_cleaning_tool_01"
FIXED_NOW = datetime(2026, 9, 6, 12, 0, 0, tzinfo=timezone.utc)


def _clock():
    return FIXED_NOW


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _seed_repo(tmp_path: Path) -> Path:
    """Disposable copy of the live seed plus one passed node with evidence."""
    for dirname in ("graph", "evidence", "execution", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname, dirs_exist_ok=True)
    _write_yaml(
        tmp_path,
        "graph/state.yaml",
        {
            "progress": {
                NODE_A: {"state": "passed", "changed_at": "2026-08-20"},
                NODE_B: {"state": "mastered", "changed_at": "2026-08-21"},
            }
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{NODE_A}.001",
                    "artifact_spec_id": "spec.portfolio.project.slope_calculator",
                    "location": "evidence/artifacts/slope.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:aaa",
                    "created_at": "2026-08-20",
                },
                {
                    "id": f"ev.{NODE_B}.001",
                    "artifact_spec_id": "spec.portfolio.project.data_cleaning_tool",
                    "location": "evidence/artifacts/clean.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:bbb",
                    "created_at": "2026-08-21",
                },
            ]
        },
    )
    (tmp_path / "evidence" / "artifacts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evidence" / "artifacts" / "slope.py").write_text(
        "print('slope')\n", encoding="utf-8"
    )
    (tmp_path / "evidence" / "artifacts" / "clean.py").write_text(
        "print('clean')\n", encoding="utf-8"
    )
    return tmp_path


# --- Markdown --------------------------------------------------------------


def test_export_markdown_has_tables_and_banners(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md",
         "--include-paths"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    md = (root / "data" / "portfolio-2026-09-06" / "portfolio.md").read_text(
        encoding="utf-8"
    )
    assert "| Evidence | Location |" in md
    assert NODE_A in md and NODE_B in md
    # Honesty banner: both nodes carry live accepted evidence, resources are
    # verified within the window — but the nodes' specs... only presence when
    # triggered is asserted here; redaction banners appear for denied dims.
    assert "[redacted]" in md
    # Readable as plain text: no HTML elements leak into Markdown.
    assert "<style" not in md and "<table" not in md and "<div" not in md


def test_export_markdown_honesty_banner_when_superseded(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{NODE_A}.001",
                    "artifact_spec_id": "spec.portfolio.project.slope_calculator",
                    "location": "evidence/artifacts/slope.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:aaa",
                    "created_at": "2026-08-20",
                },
                {
                    "id": f"ev.{NODE_A}.002",
                    "artifact_spec_id": "spec.portfolio.project.slope_calculator",
                    "location": "evidence/artifacts/slope2.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:ccc",
                    "supersedes": f"ev.{NODE_A}.001",
                    "supersede_reason": "fixed edge case",
                    "created_at": "2026-08-22",
                },
            ]
        },
    )
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md",
         "--include-superseded", "--include-paths"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    md = (root / "data" / "portfolio-2026-09-06" / "portfolio.md").read_text(
        encoding="utf-8"
    )
    assert "[honesty]" in md and "superseded evidence" in md


# --- HTML ------------------------------------------------------------------


def test_export_html_is_self_contained_without_js(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "html"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    html_text = (root / "data" / "portfolio-2026-09-06" / "portfolio.html").read_text(
        encoding="utf-8"
    )
    assert html_text.count("<style") == 1
    assert "<script" not in html_text
    assert "preview-only" in html_text
    assert NODE_A in html_text


# --- JSON contract (exact fields) ------------------------------------------


def test_export_json_pins_exact_contract(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "json"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    payload = json.loads(
        (root / "data" / "portfolio-2026-09-06" / "portfolio.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(payload) == {
        "generated_at",
        "selection",
        "honesty_banners",
        "nodes",
        "summary",
    }
    assert set(payload["selection"]) == {
        "track",
        "include_active",
        "include_rejected",
        "include_superseded",
        "nodes",
        "include_paths",
        "include_notes",
        "include_blockers",
        "include_reviews",
        "include_free_text",
        "include_urls",
    }
    assert payload["selection"]["track"] == "portfolio"
    assert isinstance(payload["honesty_banners"], list)
    assert payload["summary"] == {
        "node_count": 2,
        "evidence_count": 2,
        "artifact_count": 2,
    }
    by_id = {n["node_id"]: n for n in payload["nodes"]}
    assert set(by_id) == {NODE_A, NODE_B}
    for node in payload["nodes"]:
        assert set(node) == {"node_id", "state", "title", "evidence", "artifacts"}
    assert by_id[NODE_A]["state"] == "passed"
    assert by_id[NODE_B]["state"] == "mastered"
    # Default-deny: paths redacted in the contract.
    assert by_id[NODE_A]["artifacts"] == ["[redacted]"]


def test_export_json_empty_nodes_only_when_no_match(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio",
         "--node", "portfolio.project.stats_simulation_01",
         "--format", "json", "--output", "-"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"] == []
    assert payload["summary"] == {
        "node_count": 0,
        "evidence_count": 0,
        "artifact_count": 0,
    }
    assert payload["honesty_banners"] == []
