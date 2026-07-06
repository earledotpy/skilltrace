"""Node loader: strict frontmatter schema, forbidden-key rejection, seed load.

Decisions 3/14/18 and ADR 0001: node markdown is pure curriculum. The loader
must make schema drift *impossible* — the four progress/relationship keys are
rejected outright, with the offending file named — not merely discouraged.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.graph.nodes import (
    FORBIDDEN_FRONTMATTER_KEYS,
    NodeLoadError,
    SkillNode,
    load_node,
    load_nodes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_FRONTMATTER = """\
---
id: test.topic.thing_01
title: A learnable thing
summary: Learn to do the thing.
domain: testing
track: foundational
level: beginner
roadmap_anchors:
  -
    phase: phase_1
    roadmap_topic: Things
    source_role: reference_only
estimated_effort:
  min_minutes: 10
  max_minutes: 20
micro_session_fit:
  can_fit_15_min: true
  can_fit_30_min: true
  requires_long_block: false
competency_dimensions:
  conceptual: Explain the thing.
  practical: Do the thing.
mastery_policy:
  closure_authority: manual_with_objective_evidence
  ai_review_is_advisory_only: true
tags:
  - alpha
  - beta
created_at: 2026-06-28
updated_at: 2026-06-28
---

# A learnable thing

## Learning target

Do the thing.

## Notes

state: locked  ← journal prose, not frontmatter, must be ignored

## Evidence
"""


def _write_node(dir_path: Path, text: str, name: str = "test.topic.thing_01.md") -> Path:
    path = dir_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _frontmatter_with(dir_path: Path, extra: str) -> Path:
    """A valid node with `extra` YAML injected before the closing delimiter."""
    injected = _VALID_FRONTMATTER.replace(
        "updated_at: 2026-06-28\n---",
        f"updated_at: 2026-06-28\n{extra}\n---",
        1,
    )
    return _write_node(dir_path, injected)


def test_valid_node_loads_all_model_fields(tmp_path):
    node = load_node(_write_node(tmp_path, _VALID_FRONTMATTER))

    assert isinstance(node, SkillNode)
    assert node.id == "test.topic.thing_01"
    assert node.title == "A learnable thing"
    assert node.summary == "Learn to do the thing."
    assert node.domain == "testing"
    assert node.track == "foundational"
    assert node.tags == ("alpha", "beta")
    assert node.estimated_effort["min_minutes"] == 10
    assert node.micro_session_fit["can_fit_15_min"] is True
    assert node.competency_dimensions["conceptual"] == "Explain the thing."
    assert node.mastery_policy["ai_review_is_advisory_only"] is True
    assert len(node.roadmap_anchors) == 1
    assert node.roadmap_anchors[0]["source_role"] == "reference_only"


def test_body_journal_sections_are_ignored(tmp_path):
    # The body contains a `state: locked` line as prose; it must not be read as
    # frontmatter, and the model carries no body at all.
    node = load_node(_write_node(tmp_path, _VALID_FRONTMATTER))
    assert not hasattr(node, "state")


def test_unknown_frontmatter_key_is_tolerated(tmp_path):
    # `level` is not a model field and not forbidden; it must load, not fail.
    node = load_node(_write_node(tmp_path, _VALID_FRONTMATTER))
    assert node.id == "test.topic.thing_01"


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_FRONTMATTER_KEYS))
def test_forbidden_scalar_key_fails_naming_file_and_key(tmp_path, forbidden):
    path = _frontmatter_with(tmp_path, f"{forbidden}: whatever")
    with pytest.raises(NodeLoadError) as excinfo:
        load_node(path)
    message = str(excinfo.value)
    assert forbidden in message
    assert path.name in message


def test_forbidden_block_key_with_list_fails(tmp_path):
    # `prerequisites` as a block list (the real seed shape) must also be caught.
    path = _frontmatter_with(tmp_path, "prerequisites:\n  - other.node_01")
    with pytest.raises(NodeLoadError) as excinfo:
        load_node(path)
    assert "prerequisites" in str(excinfo.value)


def test_malformed_frontmatter_no_closing_delimiter_fails(tmp_path):
    path = _write_node(tmp_path, "---\nid: test.topic.thing_01\ntitle: x\n")
    with pytest.raises(NodeLoadError) as excinfo:
        load_node(path)
    assert path.name in str(excinfo.value)


def test_missing_frontmatter_fails(tmp_path):
    path = _write_node(tmp_path, "# Just a heading\n\nNo frontmatter here.\n")
    with pytest.raises(NodeLoadError):
        load_node(path)


def test_unparseable_yaml_fails_naming_file(tmp_path):
    path = _write_node(tmp_path, "---\nid: test.topic.thing_01\ntitle: : :\n---\n")
    with pytest.raises(NodeLoadError) as excinfo:
        load_node(path)
    assert path.name in str(excinfo.value)


def test_non_reference_only_anchor_fails(tmp_path):
    bad = _VALID_FRONTMATTER.replace(
        "    source_role: reference_only", "    source_role: authoritative"
    )
    path = _write_node(tmp_path, bad)
    with pytest.raises(NodeLoadError) as excinfo:
        load_node(path)
    assert "reference_only" in str(excinfo.value)


@pytest.mark.parametrize(
    "bad_id",
    ["NotValid", "math", "math.algebra.no_suffix", "UPPER.case_01", "trailing.dot."],
)
def test_invalid_node_id_fails(tmp_path, bad_id):
    bad = _VALID_FRONTMATTER.replace(
        "id: test.topic.thing_01", f"id: {bad_id}"
    )
    path = _write_node(tmp_path, bad)
    with pytest.raises(NodeLoadError):
        load_node(path)


@pytest.mark.parametrize("field", ["id", "title", "summary", "domain", "track"])
def test_missing_required_field_fails(tmp_path, field):
    lines = [
        line
        for line in _VALID_FRONTMATTER.splitlines(keepends=True)
        if not line.startswith(f"{field}:")
    ]
    path = _write_node(tmp_path, "".join(lines))
    with pytest.raises(NodeLoadError):
        load_node(path)


# --- Integration against the real seed graph (fails until migration runs) ---

def test_all_seed_nodes_load():
    nodes = load_nodes(REPO_ROOT)
    assert len(nodes) == 47
    ids = [node.id for node in nodes]
    assert len(set(ids)) == len(ids)  # loader hands #5 the raw list; no dedupe here
    assert "math.algebra.linear_equations_01" in ids
    assert all(node.track for node in nodes)
