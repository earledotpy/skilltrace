"""Integration tests for warning-only retired handling (v1.8 spec §5, §6).

Hand-built resource dictionaries through the existing disposable-registry
helpers plus the pure `check_resources` seam. Exact assertions:

- dangling `supports` on a retired entry warns (exit 0) with the locked line
- duplicates still error (identity holds even for history)
- malformed retired shape still errors (loader closed-schema errors)
- orphan warning suppressed for retired entries
- redundant free-tier warning applies retired or not
- `replaced_by` naming an unknown resource still errors
- dangling `supports` on an active entry still errors
"""

from __future__ import annotations

import pytest

from skilltrace.resources.registry import ResourceLoadError, load_resource
from skilltrace.resources.validation import check_resources

NODE_IDS = ["mod.basics.python_01", "mod.math.algebra_01"]


def _active(resource_id, supports, **overrides):
    entry = {
        "id": resource_id,
        "url": f"https://example.com/{resource_id}",
        "cost": "free",
        "supports": supports,
    }
    entry.update(overrides)
    return load_resource(entry)


def _retired(resource_id, supports, **overrides):
    entry = {
        "id": resource_id,
        "url": f"https://example.com/{resource_id}",
        "cost": "free",
        "supports": supports,
        "retired": True,
        "retired_at": "2026-08-15",
        "replaced_by": "fresh-res",
    }
    entry.update(overrides)
    return load_resource(entry)


def _fresh():
    return _active("fresh-res", ["mod.basics.python_01"])


def test_dangling_supports_on_retired_warns_with_locked_line():
    resources = [
        _fresh(),
        _retired("old-res", ["mod.basics.python_01", "ghost.node.missing_01"]),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is True
    assert result.errors == []
    assert result.warnings == [
        "WARN retired-resource old-res — retired 2026-08-15; replaced by "
        "fresh-res (supports unknown node ghost.node.missing_01 preserved as history)"
    ]


def test_dangling_supports_on_active_still_errors():
    resources = [
        _fresh(),
        _active("live-res", ["ghost.node.missing_01"]),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is False
    assert result.errors == [
        "resource live-res: supports names unknown node ghost.node.missing_01."
    ]
    assert result.warnings == []


def test_duplicate_ids_still_error_even_for_history():
    resources = [
        _fresh(),
        _retired("old-res", ["mod.basics.python_01"]),
        _active("old-res", ["mod.basics.python_01"]),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is False
    assert any("duplicate resource id: old-res" in e for e in result.errors)


def test_unknown_replaced_by_still_errors():
    resources = [
        _retired(
            "old-res", ["mod.basics.python_01"], replaced_by="ghost-replacement"
        ),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is False
    assert result.errors == [
        "resource old-res: replaced_by names unknown resource ghost-replacement."
    ]


def test_orphan_warning_suppressed_for_retired():
    resources = [
        _fresh(),
        _retired("old-res", []),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is True
    assert result.warnings == []


def test_orphan_warning_still_fires_for_active():
    resources = [
        _fresh(),
        _active("lonely-res", []),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is True
    assert len(result.warnings) == 1
    assert "lonely-res" in result.warnings[0]


def test_free_tier_warning_applies_retired_or_not():
    resources = [
        _fresh(),
        _active("live-free", ["mod.basics.python_01"], free_tier=True),
        _retired("old-free", ["mod.basics.python_01"], free_tier=True),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is True
    assert sum("free tier" in w for w in result.warnings) == 2


def test_clean_retired_entry_warns_about_nothing():
    resources = [
        _fresh(),
        _retired("old-res", ["mod.basics.python_01"]),
    ]
    result = check_resources(NODE_IDS, resources)
    assert result.ok is True
    assert result.errors == []
    assert result.warnings == []


@pytest.mark.parametrize(
    "entry,match",
    [
        (
            {
                "id": "old-res",
                "url": "https://example.com/old",
                "cost": "free",
                "retired": True,
                "replaced_by": "fresh-res",
            },
            "retired_at",
        ),
        (
            {
                "id": "old-res",
                "url": "https://example.com/old",
                "cost": "free",
                "retired": True,
                "retired_at": "2026-08-15",
            },
            "replaced_by",
        ),
        (
            {
                "id": "old-res",
                "url": "https://example.com/old",
                "cost": "free",
                "retired": True,
                "retired_at": "not-a-date",
                "replaced_by": "fresh-res",
            },
            "retired_at",
        ),
        (
            {
                "id": "old-res",
                "url": "https://example.com/old",
                "cost": "free",
                "retired": True,
                "retired_at": "2026-08-15",
                "replaced_by": "old-res",
            },
            "itself",
        ),
    ],
)
def test_malformed_retired_shape_still_errors(entry, match):
    with pytest.raises(ResourceLoadError, match=match):
        load_resource(entry)
