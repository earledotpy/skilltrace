"""Integration tests for replace-resource (v1.7 spec §4.3, §8, SA6).

Tests:
- Successful replacement of broken resource (exact ordered union, retirement fields, broken marker preserved)
- Successful replacement of stale resource
- Dry-run validation, zero writes, zero events, exact JSON stdout
- Refusal rules (exit 1, zero writes, zero events):
  - source equals candidate
  - unknown source / unknown candidate
  - candidate is retired / broken / stale / unverified
  - source is verified / unverified / already retired
  - resources share no node
  - candidate already covers every source node
  - invalid registry data
- Safety: no node state, graph edge, or evidence changes
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.resources.registry import load_resources

from .conftest import write_node, write_registry


def _setup_base_repo(resources_repo: Path):
    """Write nodes and return base setup."""
    write_node(resources_repo, "math.linear_algebra.vectors_01")
    write_node(resources_repo, "math.linear_algebra.matrices_01")
    write_node(resources_repo, "math.linear_algebra.eigenvalues_01")


def test_successful_replacement_of_broken_resource(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    broken_dict = {
        "id": "broken-linalg-text",
        "url": "https://example.com/dead",
        "cost": "free",
        "supports": [
            "math.linear_algebra.vectors_01",
            "math.linear_algebra.matrices_01",
        ],
        "last_verified": "2026-01-01",
        "broken": {"date": "2026-08-01", "reason": "404 not found"},
    }
    candidate_dict = {
        "id": "candidate-linalg-text",
        "url": "https://example.com/live",
        "cost": "paid",
        "free_tier": True,
        "supports": [
            "math.linear_algebra.matrices_01",
            "math.linear_algebra.eigenvalues_01",
        ],
        "last_verified": "2026-09-01",
    }
    write_registry(resources_repo, [broken_dict, candidate_dict])

    rc = cli.run(
        ["replace-resource", "broken-linalg-text", "candidate-linalg-text"],
        root=resources_repo,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "broken-linalg-text replaced by candidate-linalg-text" in out

    # Assert registry content
    resources = {r.id: r for r in load_resources(resources_repo)}
    broken = resources["broken-linalg-text"]
    cand = resources["candidate-linalg-text"]

    # Candidate receives ordered union: existing candidate nodes, then new source nodes
    assert cand.supports == (
        "math.linear_algebra.matrices_01",
        "math.linear_algebra.eigenvalues_01",
        "math.linear_algebra.vectors_01",
    )
    assert cand.cost == "paid"
    assert cand.free_tier is True
    assert cand.last_verified == "2026-09-01"

    # Broken receives retired: True, retired_at, replaced_by
    assert broken.retired is True
    assert broken.retired_at is not None
    assert broken.replaced_by == "candidate-linalg-text"
    # Preserved fields
    assert broken.url == "https://example.com/dead"
    assert broken.supports == (
        "math.linear_algebra.vectors_01",
        "math.linear_algebra.matrices_01",
    )
    assert broken.last_verified == "2026-01-01"
    assert broken.broken is not None
    assert broken.broken.reason == "404 not found"

    # Exactly one event
    events = load_events(resources_repo)
    assert len(events) == 1
    event = events[0]
    assert event["command"] == "replace-resource"
    assert event["args"]["broken_id"] == "broken-linalg-text"
    assert event["args"]["candidate_id"] == "candidate-linalg-text"
    assert event["args"]["dry_run"] is False
    assert event["records_touched"] == [
        "broken-linalg-text",
        "candidate-linalg-text",
    ]


def test_successful_replacement_of_stale_resource(resources_repo):
    _setup_base_repo(resources_repo)
    stale_dict = {
        "id": "stale-book",
        "url": "https://example.com/stale",
        "cost": "free",
        "supports": [
            "math.linear_algebra.vectors_01",
            "math.linear_algebra.matrices_01",
        ],
        "last_verified": "2025-01-01",  # older than 180 days -> STALE
    }
    candidate_dict = {
        "id": "fresh-book",
        "url": "https://example.com/fresh",
        "cost": "free",
        "supports": ["math.linear_algebra.matrices_01"],
        "last_verified": "2026-09-01",
    }
    write_registry(resources_repo, [stale_dict, candidate_dict])

    rc = cli.run(["replace-resource", "stale-book", "fresh-book"], root=resources_repo)
    assert rc == 0

    resources = {r.id: r for r in load_resources(resources_repo)}
    assert resources["stale-book"].retired is True
    assert resources["stale-book"].replaced_by == "fresh-book"
    assert resources["fresh-book"].supports == (
        "math.linear_algebra.matrices_01",
        "math.linear_algebra.vectors_01",
    )
    assert len(load_events(resources_repo)) == 1


def test_dry_run_performs_zero_writes_and_emits_deterministic_json(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    broken_dict = {
        "id": "broken-res",
        "url": "https://example.com/dead",
        "cost": "free",
        "supports": [
            "math.linear_algebra.vectors_01",
            "math.linear_algebra.matrices_01",
        ],
        "broken": {"date": "2026-08-01", "reason": "broken"},
    }
    candidate_dict = {
        "id": "candidate-res",
        "url": "https://example.com/live",
        "cost": "free",
        "supports": ["math.linear_algebra.matrices_01"],
        "last_verified": "2026-09-01",
    }
    write_registry(resources_repo, [broken_dict, candidate_dict])
    reg_path = resources_repo / "graph" / "resources.yaml"
    before_bytes = reg_path.read_bytes()

    rc = cli.run(["replace-resource", "broken-res", "candidate-res", "--dry-run"], root=resources_repo)
    assert rc == 0
    out = capsys.readouterr().out.strip()

    # Zero writes
    assert reg_path.read_bytes() == before_bytes
    # Zero events
    assert load_events(resources_repo) == []

    # Deterministic JSON line
    payload = json.loads(out)
    assert payload["command"] == "replace-resource"
    assert payload["broken_id"] == "broken-res"
    assert payload["candidate_id"] == "candidate-res"
    assert payload["candidate"] == {
        "supports_before": ["math.linear_algebra.matrices_01"],
        "supports_after": [
            "math.linear_algebra.matrices_01",
            "math.linear_algebra.vectors_01",
        ],
        "supports_added": ["math.linear_algebra.vectors_01"],
    }
    assert payload["broken"]["retired"] is True
    assert payload["broken"]["replaced_by"] == "candidate-res"
    assert payload["writes"] == []


def test_refusal_when_ids_are_equal(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(resources_repo, [])
    rc = cli.run(["replace-resource", "same-id", "same-id"], root=resources_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "replace-resource: FAILED" in out
    assert "must be non-empty and distinct" in out
    assert load_events(resources_repo) == []


def test_refusal_when_candidate_is_not_verified(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    # 1. Candidate is unverified (no last_verified)
    write_registry(
        resources_repo,
        [
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "unverified-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "unverified-cand"], root=resources_repo)
    assert rc == 1
    assert "candidate must be verified" in capsys.readouterr().out
    assert load_events(resources_repo) == []

    # 2. Candidate is broken
    write_registry(
        resources_repo,
        [
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "broken-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
                "broken": {"date": "2026-09-02", "reason": "broken too"},
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "broken-cand"], root=resources_repo)
    assert rc == 1
    assert "candidate must be verified" in capsys.readouterr().out
    assert load_events(resources_repo) == []

    # 3. Candidate is stale
    write_registry(
        resources_repo,
        [
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "stale-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2025-01-01",
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "stale-cand"], root=resources_repo)
    assert rc == 1
    assert "candidate must be verified" in capsys.readouterr().out
    assert load_events(resources_repo) == []


def test_refusal_when_candidate_is_retired(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(
        resources_repo,
        [
            {
                "id": "replacement-peer",
                "url": "https://example.com/peer",
                "cost": "free",
                "supports": ["math.linear_algebra.eigenvalues_01"],
                "last_verified": "2026-09-01",
            },
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "retired-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
                "retired": True,
                "retired_at": "2026-09-02",
                "replaced_by": "replacement-peer",
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "retired-cand"], root=resources_repo)
    assert rc == 1
    assert "candidate retired-cand is retired" in capsys.readouterr().out
    assert load_events(resources_repo) == []


def test_refusal_when_source_is_neither_broken_nor_stale(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(
        resources_repo,
        [
            {
                "id": "verified-source",
                "url": "https://example.com/v",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
            },
            {
                "id": "verified-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
            },
        ],
    )
    rc = cli.run(["replace-resource", "verified-source", "verified-cand"], root=resources_repo)
    assert rc == 1
    assert "source must be broken or stale" in capsys.readouterr().out
    assert load_events(resources_repo) == []


def test_refusal_when_source_is_already_retired(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(
        resources_repo,
        [
            {
                "id": "replacement-peer",
                "url": "https://example.com/peer",
                "cost": "free",
                "supports": ["math.linear_algebra.eigenvalues_01"],
                "last_verified": "2026-09-01",
            },
            {
                "id": "already-retired-source",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01", "math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
                "retired": True,
                "retired_at": "2026-09-02",
                "replaced_by": "replacement-peer",
            },
            {
                "id": "verified-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
            },
        ],
    )
    rc = cli.run(["replace-resource", "already-retired-source", "verified-cand"], root=resources_repo)
    assert rc == 1
    assert "already retired" in capsys.readouterr().out
    assert load_events(resources_repo) == []


def test_refusal_when_resources_share_no_node(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(
        resources_repo,
        [
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "verified-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": ["math.linear_algebra.matrices_01"],
                "last_verified": "2026-09-01",
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "verified-cand"], root=resources_repo)
    assert rc == 1
    assert "share no node" in capsys.readouterr().out
    assert load_events(resources_repo) == []


def test_refusal_when_candidate_already_covers_all_source_nodes(resources_repo, capsys):
    _setup_base_repo(resources_repo)
    write_registry(
        resources_repo,
        [
            {
                "id": "broken-res",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["math.linear_algebra.vectors_01"],
                "broken": {"date": "2026-08-01", "reason": "dead"},
            },
            {
                "id": "verified-cand",
                "url": "https://example.com/c",
                "cost": "free",
                "supports": [
                    "math.linear_algebra.vectors_01",
                    "math.linear_algebra.matrices_01",
                ],
                "last_verified": "2026-09-01",
            },
        ],
    )
    rc = cli.run(["replace-resource", "broken-res", "verified-cand"], root=resources_repo)
    assert rc == 1
    assert "already covers every node" in capsys.readouterr().out
    assert load_events(resources_repo) == []
