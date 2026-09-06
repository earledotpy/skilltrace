"""Unit tests for honesty banners and bundle naming (v2.0 spec §4).

Pins exact banner text computed from hand-built selections against the
``policy/portfolio.yaml`` default staleness window (90 days).
"""

from __future__ import annotations

import datetime

from skilltrace.portfolio.bundle import (
    _is_external,
    _unique_name,
    bundle_dir_name,
)
from skilltrace.portfolio.export import compute_honesty_banners
from skilltrace.portfolio.models import SelectedNode

TODAY = datetime.date(2026, 9, 6)
WINDOW = 90  # policy/portfolio.yaml default resource_staleness_days


def _node(node_id: str = "portfolio.project.slope_calculator_01", **over) -> SelectedNode:
    base = {
        "node_id": node_id,
        "title": "Title",
        "track": "portfolio",
        "state": "passed",
    }
    base.update(over)
    return SelectedNode(**base)


def test_no_triggers_no_banner():
    assert compute_honesty_banners([], today=TODAY, staleness_days=WINDOW) == []
    node = _node(has_unverified_claim=False)
    assert compute_honesty_banners([node], today=TODAY, staleness_days=WINDOW) == []
    bare = _node("portfolio.project.bare_node_01", has_unverified_claim=True)
    assert compute_honesty_banners([bare], today=TODAY, staleness_days=WINDOW) == [
        "[honesty] This portfolio contains unverified claims. Review before sharing."
    ]


def test_superseded_evidence_trigger():
    node = _node(has_superseded=True, has_unverified_claim=False)
    (banner,) = compute_honesty_banners([node], today=TODAY, staleness_days=WINDOW)
    assert "superseded evidence" in banner
    assert banner.startswith("[honesty] ")
    assert banner.endswith("Review before sharing.")


def test_stale_resource_trigger_uses_policy_window():
    stale = TODAY - datetime.timedelta(days=WINDOW + 1)
    fresh = TODAY - datetime.timedelta(days=WINDOW - 1)
    stale_node = _node(
        "portfolio.project.stale_node_01",
        has_unverified_claim=False,
        resources=[{"id": "r", "url": None, "last_verified": stale.isoformat(), "broken": False}],
    )
    fresh_node = _node(
        "portfolio.project.fresh_node_01",
        has_unverified_claim=False,
        resources=[{"id": "r", "url": None, "last_verified": fresh.isoformat(), "broken": False}],
    )
    (banner,) = compute_honesty_banners(
        [stale_node], today=TODAY, staleness_days=WINDOW
    )
    assert "stale resources" in banner
    assert (
        compute_honesty_banners([fresh_node], today=TODAY, staleness_days=WINDOW)
        == []
    )


def test_broken_marker_surfaces_as_stale_resources():
    node = _node(
        has_unverified_claim=False,
        resources=[{"id": "r", "url": None, "last_verified": None, "broken": True}],
    )
    (banner,) = compute_honesty_banners([node], today=TODAY, staleness_days=WINDOW)
    assert "stale resources" in banner


def test_unverified_resource_trigger():
    node = _node(
        has_unverified_claim=False,
        resources=[{"id": "r", "url": None, "last_verified": None, "broken": False}],
    )
    (banner,) = compute_honesty_banners([node], today=TODAY, staleness_days=WINDOW)
    assert "unverified claims" in banner


def test_multiple_triggers_named_in_one_banner():
    node = _node(
        has_superseded=True,
        has_unverified_claim=True,
    )
    (banner,) = compute_honesty_banners([node], today=TODAY, staleness_days=WINDOW)
    assert "superseded evidence" in banner
    assert "unverified claims" in banner


def test_bundle_dir_name_is_date_keyed():
    assert bundle_dir_name(TODAY) == "portfolio-2026-09-06"


def test_external_detection_and_unique_names():
    assert _is_external("https://example.com/x") is True
    assert _is_external("http://example.com/x") is True
    assert _is_external("evidence/a.md") is False
    assert _unique_name(set(), "n", "evidence/a.md") == "a.md"
    assert _unique_name({"a.md"}, "n", "evidence/a.md") == "a__2.md"
