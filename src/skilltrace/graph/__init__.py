"""Graph layer: nodes (curriculum) and edges (relationships).

Nodes are pure curriculum; all learner state lives in the progress store
(ADR 0001). `edges.yaml` is the sole source of truth for relationships, so node
frontmatter never carries prerequisites, unlocks, node_type, or state.
"""

from __future__ import annotations

from .edges import (
    EDGE_TYPES,
    PRUNED_EDGE_FIELDS,
    EdgeLoadError,
    GraphEdge,
    load_edge,
    load_edges,
)
from .nodes import (
    FORBIDDEN_FRONTMATTER_KEYS,
    NodeLoadError,
    SkillNode,
    is_valid_node_id,
    load_node,
    load_nodes,
)

__all__ = [
    "EDGE_TYPES",
    "PRUNED_EDGE_FIELDS",
    "EdgeLoadError",
    "FORBIDDEN_FRONTMATTER_KEYS",
    "GraphEdge",
    "NodeLoadError",
    "SkillNode",
    "is_valid_node_id",
    "load_edge",
    "load_edges",
    "load_node",
    "load_nodes",
]
