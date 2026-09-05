"""Integration tests for the enriched broken marker (v1.8 spec §5.1, §6).

Hand-built resource dictionaries through the existing disposable-registry
helpers. Exact assertions:

- legacy `{date, reason}` markers stay valid, absent optionals read as `None`
- enriched markers (`status_code`/`final_url`) round-trip exactly
- `record_verification` failure path writes the enriched marker and omits
  `None` fields from the YAML (no explicit nulls, no backfill of legacy rows)
- wrong optional types fail with the clean `ResourceLoadError` shape
- an unknown fifth marker field fails
- success still sets `last_verified` and clears the whole marker
"""

from __future__ import annotations

import pytest

from skilltrace.resources.registry import (
    BrokenMarker,
    ResourceLoadError,
    load_resource,
    load_resources,
)
from skilltrace.resources.verification import record_verification

from .conftest import read_registry, resource_named, write_registry


def _base_entry(**overrides):
    entry = {
        "id": "fragile-res",
        "url": "https://example.com/fragile",
        "cost": "free",
    }
    entry.update(overrides)
    return entry


def test_legacy_marker_without_enrichment_reads_none(resources_repo):
    write_registry(
        resources_repo,
        [_base_entry(broken={"date": "2026-09-01", "reason": "status 404: not found"})],
    )
    (resource,) = load_resources(resources_repo)
    assert resource.broken == BrokenMarker(
        date="2026-09-01",
        reason="status 404: not found",
        status_code=None,
        final_url=None,
    )


def test_enriched_marker_round_trips_exactly(resources_repo):
    marker = {
        "date": "2026-09-01",
        "reason": "status 404: not found",
        "status_code": 404,
        "final_url": "https://example.com/renamed",
    }
    write_registry(resources_repo, [_base_entry(broken=dict(marker))])
    (resource,) = load_resources(resources_repo)
    assert resource.broken == BrokenMarker(
        date="2026-09-01",
        reason="status 404: not found",
        status_code=404,
        final_url="https://example.com/renamed",
    )
    # The stored YAML keeps exactly the four fields.
    stored = resource_named(read_registry(resources_repo), "fragile-res")["broken"]
    assert stored == marker


def test_enriched_marker_with_null_observation_reads_none(resources_repo):
    # A transport/timeout failure: observed ints/URLs absent.
    write_registry(
        resources_repo,
        [
            _base_entry(
                broken={
                    "date": "2026-09-01",
                    "reason": "timeout after 10s",
                }
            )
        ],
    )
    (resource,) = load_resources(resources_repo)
    assert resource.broken is not None
    assert resource.broken.status_code is None
    assert resource.broken.final_url is None


def test_record_verification_failure_writes_enriched_marker(resources_repo):
    write_registry(resources_repo, [_base_entry()])
    record_verification(
        resources_repo,
        "fragile-res",
        date="2026-09-02",
        broken_reason="status 404: not found",
        status_code=404,
        final_url="https://example.com/renamed",
    )
    stored = resource_named(read_registry(resources_repo), "fragile-res")
    assert stored["broken"] == {
        "date": "2026-09-02",
        "reason": "status 404: not found",
        "status_code": 404,
        "final_url": "https://example.com/renamed",
    }
    # Failure leaves any last_verified untouched and writes nothing positive.
    assert "last_verified" not in stored
    (resource,) = load_resources(resources_repo)
    assert resource.broken == BrokenMarker(
        date="2026-09-02",
        reason="status 404: not found",
        status_code=404,
        final_url="https://example.com/renamed",
    )


def test_record_verification_failure_omits_none_fields(resources_repo):
    write_registry(resources_repo, [_base_entry()])
    record_verification(
        resources_repo,
        "fragile-res",
        date="2026-09-02",
        broken_reason="timeout after 10s",
    )
    stored = resource_named(read_registry(resources_repo), "fragile-res")
    # No explicit nulls: a transport failure stores the legacy shape exactly.
    assert stored["broken"] == {"date": "2026-09-02", "reason": "timeout after 10s"}


def test_record_verification_failure_leaves_legacy_rows_untouched(resources_repo):
    write_registry(
        resources_repo,
        [
            _base_entry(
                broken={"date": "2026-08-01", "reason": "status 500: server error"}
            ),
            _base_entry(id="other-res", url="https://example.com/other"),
        ],
    )
    record_verification(
        resources_repo,
        "other-res",
        date="2026-09-02",
        broken_reason="status 404: not found",
        status_code=404,
        final_url="https://example.com/other-moved",
    )
    entries = read_registry(resources_repo)
    # No backfill: the legacy row keeps its two-field shape.
    assert resource_named(entries, "fragile-res")["broken"] == {
        "date": "2026-08-01",
        "reason": "status 500: server error",
    }
    assert resource_named(entries, "other-res")["broken"] == {
        "date": "2026-09-02",
        "reason": "status 404: not found",
        "status_code": 404,
        "final_url": "https://example.com/other-moved",
    }


def test_record_verification_success_clears_enriched_marker(resources_repo):
    write_registry(
        resources_repo,
        [
            _base_entry(
                broken={
                    "date": "2026-09-01",
                    "reason": "status 404: not found",
                    "status_code": 404,
                    "final_url": "https://example.com/renamed",
                }
            )
        ],
    )
    record_verification(resources_repo, "fragile-res", date="2026-09-03")
    stored = resource_named(read_registry(resources_repo), "fragile-res")
    assert stored["last_verified"] == "2026-09-03"
    assert "broken" not in stored


@pytest.mark.parametrize(
    "marker,match",
    [
        (
            {"date": "2026-09-01", "reason": "x", "status_code": "404"},
            "status_code",
        ),
        (
            {"date": "2026-09-01", "reason": "x", "status_code": True},
            "status_code",
        ),
        (
            {"date": "2026-09-01", "reason": "x", "status_code": 44.0},
            "status_code",
        ),
        (
            {"date": "2026-09-01", "reason": "x", "final_url": 404},
            "final_url",
        ),
        (
            {"date": "2026-09-01", "reason": "x", "final_url": ""},
            "final_url",
        ),
    ],
)
def test_wrong_optional_types_fail_clean(resources_repo, marker, match):
    write_registry(resources_repo, [_base_entry(broken=marker)])
    with pytest.raises(ResourceLoadError, match=match):
        load_resources(resources_repo)


def test_unknown_fifth_marker_field_fails(resources_repo):
    write_registry(
        resources_repo,
        [
            _base_entry(
                broken={
                    "date": "2026-09-01",
                    "reason": "status 404: not found",
                    "status_code": 404,
                    "final_url": "https://example.com/renamed",
                    "error_type": "http",
                }
            )
        ],
    )
    with pytest.raises(ResourceLoadError, match="unknown field"):
        load_resources(resources_repo)


def test_load_resource_unit_shapes():
    legacy = load_resource(_base_entry())
    assert legacy.broken is None
    enriched = load_resource(
        _base_entry(
            broken={
                "date": "2026-09-01",
                "reason": "r",
                "status_code": 301,
                "final_url": "https://example.com/new",
            }
        )
    )
    assert enriched.broken == BrokenMarker(
        date="2026-09-01", reason="r", status_code=301, final_url="https://example.com/new"
    )
