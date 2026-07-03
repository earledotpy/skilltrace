"""Shared on-disk graph fixtures for the v0.3 exit-gate suite (issue #8).

The unit tests hand-build `SkillNode`/`GraphEdge` objects and drive the pure
`check_graph` seam. That is the right seam for *logic* — but it bypasses the
loaders entirely, so it cannot prove the two loader-level rejections the roadmap
v0.3 test list calls for: node frontmatter carrying `state` and an edge carrying
a pruned `strength` field. Those only fail when a real file passes through
`load_nodes`/`load_edges` (and the failure is *folded into* `load_and_validate`'s
result, not raised).

`GraphBuilder` writes a real mini-repo under `tmp_path` — `graph/nodes/*.md` and
`graph/edges.yaml` — so a test can exercise the whole loader→validate path. It is
deliberately curriculum-agnostic scaffolding: a node is the minimum valid shape
plus whatever `overrides` a test injects (including a forbidden key), and an edge
is the minimum valid shape plus `extra` (including a pruned field).

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


class GraphBuilder:
    """Writes a real SkillTrace mini-repo so tests hit the loader path.

    Chainable: every mutator returns `self`. `root` is the repo root the CLI and
    `load_and_validate` operate on.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "graph" / "nodes").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def edge(
        source: str,
        target: str,
        *,
        edge_type: str = "hard_prerequisite",
        edge_id: str | None = None,
        active: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build one edge mapping (the shape `edges.yaml` stores under `edges:`).

        `extra` merges in additional keys — e.g. a pruned `strength` field — so a
        test can construct an edge the loader must reject.
        """
        edge: dict[str, Any] = {
            "id": edge_id or f"edge.{source}__{target}",
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "reason": "because",
            "active": active,
        }
        if extra:
            edge.update(extra)
        return edge

    def node(
        self,
        node_id: str,
        *,
        track: str = "foundational",
        can_fit_15: bool = True,
        can_fit_30: bool = True,
        anchors: list[dict[str, Any]] | None = None,
        overrides: dict[str, Any] | None = None,
        filename: str | None = None,
    ) -> "GraphBuilder":
        """Write one node markdown file with valid frontmatter plus `overrides`.

        `overrides` is merged last, so a test can inject a forbidden key
        (`overrides={"state": "active"}`) to exercise loader rejection. `filename`
        defaults to `<node_id>.md`; pass it to give two files the *same* id (the
        duplicate-id case) without a filename collision.
        """
        frontmatter: dict[str, Any] = {
            "id": node_id,
            "title": f"Title for {node_id}",
            "summary": f"Summary for {node_id}.",
            "domain": "testing",
            "track": track,
            "micro_session_fit": {
                "can_fit_15_min": can_fit_15,
                "can_fit_30_min": can_fit_30,
                "requires_long_block": False,
            },
        }
        if anchors is not None:
            frontmatter["roadmap_anchors"] = anchors
        if overrides:
            frontmatter.update(overrides)

        block = yaml.safe_dump(frontmatter, sort_keys=False)
        text = f"---\n{block}---\n\n# {node_id}\n"
        name = filename or f"{node_id}.md"
        (self.root / "graph" / "nodes" / name).write_text(text, encoding="utf-8")
        return self

    def edges(self, edges: list[dict[str, Any]]) -> "GraphBuilder":
        """Write `graph/edges.yaml` from a list of edge mappings."""
        doc = yaml.safe_dump({"edges": edges}, sort_keys=False)
        (self.root / "graph" / "edges.yaml").write_text(doc, encoding="utf-8")
        return self


@pytest.fixture
def graph_builder(tmp_path: Path) -> GraphBuilder:
    """A `GraphBuilder` rooted at a fresh temp repo."""
    return GraphBuilder(tmp_path)
