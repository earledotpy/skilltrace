"""Policy weight maps — one deep module for recommendation weights (C1b / C5).

``policy/recommendation.yaml`` holds ``track_weights`` and ``factor_weights``
under the top-level key ``recommendation_policy``. This module is the single
place YAML float-coercion and missing-key tolerance lives.

Consumed by the JoinedView lenient seam (``context.py``) and by the
``next``/``today`` commands. The ``remediation`` threshold helper lives
nearby in ``remediation_edges.py`` — weights stay together here.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_POLICY_RELPATH = Path("policy") / "recommendation.yaml"


def _load_weight_map(root: Path, key: str) -> dict[str, float]:
    """Read one weight map; missing/malformed yields empty map."""
    path = root / _POLICY_RELPATH
    if not path.exists():
        return {}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    policy = doc.get("recommendation_policy") if isinstance(doc, dict) else None
    raw = policy.get(key) if isinstance(policy, dict) else None
    if not isinstance(raw, dict):
        return {}
    weights: dict[str, float] = {}
    for name, value in raw.items():
        try:
            weights[str(name)] = float(value)
        except (TypeError, ValueError):
            continue
    return weights


def load_track_weights(root: Path) -> dict[str, float]:
    """Opaque track-weight map (engine attaches no meaning to track names)."""
    return _load_weight_map(root, "track_weights")


def load_factor_weights(root: Path) -> dict[str, float]:
    """Factor-weight map; empty falls back to ranking's built-in defaults."""
    return _load_weight_map(root, "factor_weights")
