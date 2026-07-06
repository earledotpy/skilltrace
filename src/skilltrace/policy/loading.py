"""Load the policy seed documents.

Each file carries one top-level key naming its policy document. Loading is
strict about shape (file exists, parses, top key is a mapping) and agnostic
about content — value-level rules live in `validation.py` and in the
consumers that read specific fields.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_POLICY_DIR = "policy"

# filename -> required top-level key. The seed documents of the layer.
POLICY_FILES: dict[str, str] = {
    "automation_boundary.yaml": "automation_boundary_policy",
    "mastery_promotion.yaml": "mastery_promotion_policy",
    "recommendation.yaml": "recommendation_policy",
    "remediation.yaml": "remediation_policy",
    "resource_verification.yaml": "resource_verification_policy",
    "review_cadence.yaml": "review_cadence_policy",
    "workload.yaml": "workload_policy",
}


class PolicyLoadError(Exception):
    """A policy seed file is missing, unparseable, or missing its document."""


def load_policy_doc(root: Path | str, filename: str) -> dict:
    """Load one policy file's document (the mapping under its top-level key)."""
    top_key = POLICY_FILES[filename]
    path = Path(root) / _POLICY_DIR / filename
    if not path.exists():
        raise PolicyLoadError(f"{path}: policy file is missing.")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PolicyLoadError(f"{path}: not valid YAML — {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get(top_key), dict):
        raise PolicyLoadError(
            f"{path}: expected a mapping under top-level key {top_key!r}."
        )
    return data[top_key]


def load_policy_docs(root: Path | str) -> dict[str, dict]:
    """Load every policy document, keyed by filename."""
    return {filename: load_policy_doc(root, filename) for filename in POLICY_FILES}
