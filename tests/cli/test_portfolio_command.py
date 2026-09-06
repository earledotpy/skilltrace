"""`skilltrace portfolio` command family tests (v2.0 spec §6, T-TestArch #180).

Registration and kind contract, the read-only/mutating audit split, section
presence (not exact text) in preview output, and refusal on data load error
with no partial output.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE_A = "portfolio.project.slope_calculator_01"
FIXED_NOW = datetime(2026, 9, 6, 12, 0, 0, tzinfo=timezone.utc)


def _clock():
    return FIXED_NOW


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "execution", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname, dirs_exist_ok=True)
    _write_yaml(
        tmp_path,
        "graph/state.yaml",
        {"progress": {NODE_A: {"state": "passed", "changed_at": "2026-08-20"}}},
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
                }
            ]
        },
    )
    return tmp_path


# --- Registration and kind -------------------------------------------------


def test_portfolio_commands_are_registered_with_kinds():
    preview = cli.REGISTRY.get("portfolio preview")
    export = cli.REGISTRY.get("portfolio export")
    assert preview is not None and preview.kind.value == "read_only"
    assert export is not None and export.kind.value == "mutating"


# --- Audit split -----------------------------------------------------------


def test_preview_logs_no_audit_event(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    before = len(load_events(root))
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--format", "md"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    assert len(load_events(root)) == before


def test_export_appends_exactly_one_portfolio_export_event(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    before = load_events(root)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    after = load_events(root)
    assert len(after) == len(before) + 1
    assert after[-1]["command"] == "portfolio export"


# --- Section presence ------------------------------------------------------


def test_preview_markdown_contains_node_block_and_redaction_banners(
    tmp_path, capsys
):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--format", "md"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert NODE_A in out
    assert "passed" in out
    # Default-deny: redaction banners name the hidden dimensions.
    assert "[redacted]" in out


def test_preview_json_contains_node_block(tmp_path, capsys):
    import json

    root = _seed_repo(tmp_path)
    rc = cli.run(
        [
            "portfolio", "preview", "--track", "portfolio", "--format", "json",
            "--include-paths", "--output", "-",
        ],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["node_count"] == 1
    assert payload["nodes"][0]["node_id"] == NODE_A


def test_preview_honesty_banner_when_superseded(tmp_path, capsys):
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
                    "artifact_hash": "sha256:bbb",
                    "supersedes": f"ev.{NODE_A}.001",
                    "supersede_reason": "fixed edge case",
                    "created_at": "2026-08-22",
                },
            ]
        },
    )
    rc = cli.run(
        [
            "portfolio", "preview", "--track", "portfolio", "--format", "md",
            "--include-superseded",
        ],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "[honesty]" in out
    assert "superseded evidence" in out


def test_preview_include_active_selects_active_node(tmp_path, capsys):
    import json

    root = _seed_repo(tmp_path)
    _write_yaml(
        root,
        "graph/state.yaml",
        {"progress": {NODE_A: {"state": "active", "changed_at": "2026-08-20"}}},
    )
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--format", "json",
         "--output", "-"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["summary"]["node_count"] == 0
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--format", "json",
         "--include-active", "--output", "-"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["summary"]["node_count"] == 1


# --- Refusal ---------------------------------------------------------------


def test_preview_refuses_on_data_load_error(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    (root / "evidence" / "evidence_records.yaml").write_text(
        "not: [valid", encoding="utf-8"
    )
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--format", "md"],
        root=root,
        clock=_clock,
    )
    assert rc == 1
    assert "FAILED" in capsys.readouterr().out


def test_export_refuses_without_partial_output(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    (root / "evidence" / "evidence_records.yaml").write_text(
        "not: [valid", encoding="utf-8"
    )
    before = len(load_events(root))
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md"],
        root=root,
        clock=_clock,
    )
    assert rc == 1
    capsys.readouterr()
    assert not (root / "data" / "portfolio-2026-09-06").exists()
    assert len(load_events(root)) == before


def test_preview_honors_policy_default_format(tmp_path, capsys):
    import json

    root = _seed_repo(tmp_path)
    policy_path = root / "policy" / "portfolio.yaml"
    doc = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    doc["portfolio_policy"]["default_format"] = "json"
    policy_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    rc = cli.run(
        ["portfolio", "preview", "--track", "portfolio", "--output", "-"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["node_count"] == 1
