"""Opaque advisory agent recommendations (v2.1 D-AgentInput).

Phase 3/4 seed graphs may attach machine-generated study priorities to
nodes. This module reads them as an *opaque, advisory* input for the
``next`` / ``today`` sequencing: each flagged node gets a small
``agent_signal`` score contribution and a reason string. It is never an
acceptance authority and never writes; a missing or unreadable file is
warn-and-ignore, never an error. The schema is deliberately lenient:
entries that do not decode cleanly are skipped with a warning rather than
failing the command.
"""

from __future__ import annotations

from pathlib import Path

import yaml

AGENT_RECS_RELPATH = Path("data") / "agent_recommendations.yaml"
_TOP_KEY = "agent_recommendations"


def load_agent_recommendations(
    root: Path,
) -> tuple[dict[str, float], list[str]]:
    """Read agent recommendations from ``data/agent_recommendations.yaml``.

    Returns ``(node_id -> priority, warnings)``. Priorities default to 0.5
    when an entry omits one. A missing file yields empty output with no
    warnings; an unreadable or malformed file yields empty output plus
    warnings (warn-and-ignore). Entries without a usable ``node_id`` are
    skipped; non-finite priorities are defaulted.
    """
    if root is None:
        return {}, []
    path = root / AGENT_RECS_RELPATH
    if not path.exists():
        return {}, []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return {}, [f"agent recommendations unreadable — ignored: {exc}"]

    warnings: list[str] = []
    recommendations: dict[str, float] = {}
    if raw is None:
        return recommendations, warnings
    if not isinstance(raw, dict) or not isinstance(raw.get(_TOP_KEY), list):
        return recommendations, [
            f"agent recommendations: expected a list under {_TOP_KEY!r}; ignored."
        ]

    for index, item in enumerate(raw.get(_TOP_KEY) or []):
        if not isinstance(item, dict):
            warnings.append(f"agent recommendations[{index}] is not a mapping; skipped.")
            continue
        node_id = item.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            warnings.append(
                f"agent recommendations[{index}] has no usable node_id; skipped."
            )
            continue
        priority = item.get("priority", 0.5)
        if isinstance(priority, bool) or not isinstance(priority, (int, float)):
            priority = 0.5
        else:
            priority = float(priority)
        if priority < 0:
            warnings.append(
                f"agent recommendations[{index}] negative priority clamped to 0; skipped."
            )
            continue
        recommendations[node_id] = priority
    return recommendations, warnings