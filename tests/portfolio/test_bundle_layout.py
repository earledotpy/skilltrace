"""Bundle-layer tests for the portfolio builder (v2.0 spec §4, T-TestArch #180).

Asserts the exact ``data/portfolio-<date>/`` directory structure, the
``portfolio.json`` manifest presence, artifact files with rewritten relative
links, and no absolute host paths in output.
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
    (tmp_path / "evidence" / "artifacts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evidence" / "artifacts" / "slope.py").write_text(
        "print('slope')\n", encoding="utf-8"
    )
    return tmp_path


def _bundle(root: Path) -> Path:
    return root / "data" / "portfolio-2026-09-06"


def test_bundle_directory_structure_exact(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md",
         "--include-paths"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    bundle = _bundle(root)
    assert bundle.is_dir()
    assert (bundle / "portfolio.md").is_file()
    assert (bundle / "portfolio.html").is_file()
    assert (bundle / "portfolio.json").is_file()
    assert (bundle / "artifacts").is_dir()
    assert (bundle / "nodes").is_dir()
    assert (bundle / "nodes" / f"{NODE_A}.md").is_file()


def test_bundle_manifest_and_rewritten_links(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md",
         "--include-paths"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    bundle = _bundle(root)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {
        "generated_at",
        "selection",
        "honesty_banners",
        "nodes",
        "summary",
    }
    assert manifest["nodes"] == {NODE_A: ["artifacts/slope.py"]}
    assert (bundle / "artifacts" / "slope.py").is_file()
    assert (bundle / "artifacts" / "slope.py").read_text(
        encoding="utf-8"
    ) == "print('slope')\n"

    md = (bundle / "portfolio.md").read_text(encoding="utf-8")
    assert "artifacts/slope.py" in md
    node_md = (bundle / "nodes" / f"{NODE_A}.md").read_text(encoding="utf-8")
    assert "artifacts/slope.py" in node_md

    for path in (
        bundle / "portfolio.md",
        bundle / "portfolio.html",
        bundle / "portfolio.json",
        bundle / "manifest.json",
        bundle / "nodes" / f"{NODE_A}.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert str(root) not in text
        assert "evidence/artifacts/slope.py" not in text


def test_bundle_external_urls_never_copied(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{NODE_A}.001",
                    "artifact_spec_id": "spec.portfolio.project.slope_calculator",
                    "location": "https://example.com/slope",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:aaa",
                    "created_at": "2026-08-20",
                }
            ]
        },
    )
    rc = cli.run(
        ["portfolio", "export", "--track", "portfolio", "--format", "md",
         "--include-paths", "--include-urls"],
        root=root,
        clock=_clock,
    )
    assert rc == 0
    capsys.readouterr()
    bundle = _bundle(root)
    assert list((bundle / "artifacts").iterdir()) == []
    md = (bundle / "portfolio.md").read_text(encoding="utf-8")
    assert "https://example.com/slope" in md
