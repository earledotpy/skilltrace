"""Graph layer: nodes (curriculum) and edges (relationships).

Nodes are pure curriculum; all learner state lives in the progress store
(ADR 0001). `edges.yaml` is the sole source of truth for relationships, so node
frontmatter never carries prerequisites, unlocks, node_type, or state.
"""

from __future__ import annotations

from .nodes import (
    FORBIDDEN_FRONTMATTER_KEYS,
    NodeLoadError,
    SkillNode,
    load_node,
    load_nodes,
)

__all__ = [
    "FORBIDDEN_FRONTMATTER_KEYS",
    "NodeLoadError",
    "SkillNode",
    "load_node",
    "load_nodes",
]
