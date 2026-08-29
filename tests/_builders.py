"""Shared test helpers for SkillTrace.

A single `write_node` factory that every layer's `conftest.py` previously
re-derived. It is the common subset of the seven `write_node` /
`_write_node` / `GraphBuilder.node` / `EvidenceBuilder._write_node` /
`policy._write_node` / `resources.write_node` / `web._write_node` /
`health._write_node` / `today._write_node` / `joined_view._write_node_file`
copies that the audit enumerated (issue #117, Slice B). Keeping the
defaults permissive — every flag on, every hook exposed — means each
caller can drop down to the simplest shape with a single keyword while
the rare test that needs the hooks (a forbidden-key loader check, an
anchor-derivation check) keeps one entry point.

This module lives under `tests/`, not under `src/skilltrace/`, because it
has no engine role — it is purely a test-fixture concern.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def write_node(
    root: Path,
    node_id: str,
    *,
    track: str = "foundational",
    micro_session_fit: bool = True,
    anchors: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    filename: str | None = None,
) -> Path:
    """Write one minimal-valid node markdown file under `root/graph/nodes/`.

    Returns the path written, so callers that want to assert on the file
    (e.g. a forbidden-key rejection that names the file) can chain.

    `micro_session_fit` defaults to `True` (writes the three
    `can_fit_15_min` / `can_fit_30_min` / `requires_long_block: false`
    block). Pass `False` to omit it for tests that exercise the
    minimal-frontmatter shape itself.

    `anchors`, when given, writes a `roadmap_anchors:` block — the
    `test_roadmap_anchor.py` reference-only test exercises it.

    `tags`, when given, writes a `tags:` sequence.

    `extra` merges in arbitrary additional frontmatter keys — the
    `GraphBuilder.node` test-only escape hatch for forbidden-key loader
    rejections and the `EvidenceBuilder.spec_dict` overrides follow the
    same shape.

    `filename`, when given, overrides the default `<node_id>.md` — used
    by tests that need two files with the same `id` to trigger the
    duplicate-id loader rejection without a filename collision.
    """
    frontmatter: dict[str, Any] = {
        "id": node_id,
        "title": f"Title for {node_id}",
        "summary": f"Summary for {node_id}.",
        "domain": "testing",
        "track": track,
    }
    if micro_session_fit:
        frontmatter["micro_session_fit"] = {
            "can_fit_15_min": True,
            "can_fit_30_min": True,
            "requires_long_block": False,
        }
    if anchors is not None:
        frontmatter["roadmap_anchors"] = anchors
    if tags is not None:
        frontmatter["tags"] = tags
    if extra:
        frontmatter.update(extra)

    block = yaml.safe_dump(frontmatter, sort_keys=False)
    name = filename or f"{node_id}.md"
    path = root / "graph" / "nodes" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{block}---\n\n# {node_id}\n", encoding="utf-8")
    return path
