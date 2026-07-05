"""The resource layer: the LearningResource registry (v0.7).

Resources are Curriculum (CONTEXT.md), so the registry is a single YAML list
file in the graph area — `graph/resources.yaml` — alongside nodes and edges.
Earlier slices shipped the registry skeleton, `validate resources` (the
curriculum-integrity check), and the claim fields; `resources_for_node` derives
the per-node reverse index that `resources --node-id` lists. Verification
metadata and the resource report land in later v0.7 slices.
"""
