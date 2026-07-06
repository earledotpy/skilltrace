"""Fixtures and loaders for the seed-acceptance suite (v0.8).

Unlike the per-layer suites — which build disposable tmp-repo fixtures and
assert the *engine's* behavior on synthetic data — this suite's product is the
**shipped repository data**. Every check drives the real CLI in-process via
`cli.run(argv, root=REPO_ROOT)` (the single seam every layer already uses) or
reads the shipped YAML/Markdown directly. Files are the source of truth, so a
shipped-data invariant *is* external behavior (issue #14 testing decisions).

The helpers here read the shipped seed exactly as it sits on disk; the raw
frontmatter reader deliberately bypasses the node loader, because the loader
folds stripped keys (`mastery_policy`, `competency_dimensions`) into empty
dicts and silently tolerates `level` — so only the raw YAML can prove they are
gone.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

_NODES_DIR = REPO_ROOT / "graph" / "nodes"


def node_paths() -> list[Path]:
    """Every shipped node markdown file, in filename order."""
    return sorted(_NODES_DIR.glob("*.md"))


def raw_frontmatter(path: Path) -> dict:
    """The node file's frontmatter parsed straight from YAML (loader bypassed)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path}: no opening frontmatter"
    close = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"), None
    )
    assert close is not None, f"{path}: no closing frontmatter"
    data = yaml.safe_load("\n".join(lines[1:close]))
    assert isinstance(data, dict), f"{path}: frontmatter is not a mapping"
    return data


def _load_yaml(relpath: str) -> dict:
    doc = yaml.safe_load((REPO_ROOT / relpath).read_text(encoding="utf-8"))
    return doc or {}


def gates_by_node() -> dict[str, list[dict]]:
    """node_id -> its validation gates (from `evidence/validation_gates.yaml`)."""
    out: dict[str, list[dict]] = {}
    for gate in _load_yaml("evidence/validation_gates.yaml").get("validation_gates", []):
        out.setdefault(gate["node_id"], []).append(gate)
    return out


def required_specs_by_node() -> dict[str, list[dict]]:
    """node_id -> its *required* artifact specs (from `evidence/artifact_specs.yaml`)."""
    out: dict[str, list[dict]] = {}
    for spec in _load_yaml("evidence/artifact_specs.yaml").get("artifact_specs", []):
        if spec.get("required"):
            out.setdefault(spec["node_id"], []).append(spec)
    return out


def track_weights() -> dict[str, float]:
    """The shipped policy track-weight map."""
    policy = _load_yaml("policy/recommendation.yaml").get("recommendation_policy", {})
    return dict(policy.get("track_weights", {}))


def registry_resources() -> list[dict]:
    """The shipped LearningResource registry entries (may be empty)."""
    return _load_yaml("graph/resources.yaml").get("resources", []) or []


def state_by_node() -> dict[str, str]:
    """node_id -> its recorded readiness state (from the progress store)."""
    progress = _load_yaml("graph/state.yaml").get("progress", {})
    return {node_id: entry.get("state") for node_id, entry in progress.items()}


# Collection-time constants so tests can parametrize over the shipped node set
# and skip the resource floor while the registry is still empty.
NODE_IDS: list[str] = [raw_frontmatter(p)["id"] for p in node_paths()]
REGISTRY_IS_EMPTY: bool = len(registry_resources()) == 0
