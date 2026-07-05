"""Session template presets.

A template is an opaque label on a session — like a Track, the engine
attaches no meaning to it. Presets (expected minutes per label) are seed
data under `session_templates:` in `policy/workload.yaml`, read only to
warn on an unmapped label; advisory policy consumes them in v0.6.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_WORKLOAD_RELPATH = Path("policy") / "workload.yaml"


def known_templates(root: Path | str) -> set[str]:
    """Template labels with a seed preset; empty when none are seeded."""
    path = Path(root) / _WORKLOAD_RELPATH
    if not path.exists():
        return set()
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    policy = doc.get("workload_policy") if isinstance(doc, dict) else None
    presets = policy.get("session_templates") if isinstance(policy, dict) else None
    if isinstance(presets, dict):
        return {str(name) for name in presets}
    return set()
