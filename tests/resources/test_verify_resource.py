"""`skilltrace verify-resource` — the human verification workflow (v0.7 slice 4).

Verified is a dated human assertion that a resource resolves and its claims hold;
the failure form records a dated broken marker with a reason and does not touch
`last_verified`. This is the registry's only mutating command, so it is the only
resource command that appends an audit event — exactly one per invocation,
success or failure. Every test drives the real CLI in-process through
`cli.run(argv, root=...)` — the single seam — asserting only exit codes, stdout,
and the YAML written to disk.
"""

from __future__ import annotations

from datetime import datetime, timezone

import yaml

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import read_registry, resource_named, write_node, write_registry


def _today() -> str:
    """Today (UTC) as `YYYY-MM-DD` — computed exactly as the command does."""
    return datetime.now(timezone.utc).date().isoformat()


def _resource(**fields) -> dict:
    """A minimal load-clean resource on `testing.res.subject_01`, plus `fields`."""
    base = {
        "id": "some-resource",
        "url": "https://example.com/course",
        "cost": "free",
        "supports": ["testing.res.subject_01"],
    }
    base.update(fields)
    return base


def _seed(resources_repo, resource: dict | None = None) -> None:
    """One node plus a one-resource registry (default: the minimal resource)."""
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [resource if resource is not None else _resource()])


# --- Criterion 1: a successful verify dates last_verified and exits 0 -------


def test_successful_verify_sets_last_verified_to_today(resources_repo, capsys):
    _seed(resources_repo)
    rc = cli.run(["verify-resource", "some-resource"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "verified" in out
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert entry["last_verified"] == _today()


def test_successful_verify_preserves_authored_fields(resources_repo):
    # The surgical edit touches only the verification facts — every other field,
    # and every other resource, survives untouched.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            _resource(cost="paid", free_tier=True, license="CC-BY-4.0"),
            _resource(id="other-resource"),
        ],
    )
    rc = cli.run(["verify-resource", "some-resource"], root=resources_repo)
    assert rc == 0
    entries = read_registry(resources_repo)
    entry = resource_named(entries, "some-resource")
    assert entry["cost"] == "paid"
    assert entry["free_tier"] is True
    assert entry["license"] == "CC-BY-4.0"
    assert entry["supports"] == ["testing.res.subject_01"]
    # The sibling resource is left entirely alone.
    other = resource_named(entries, "other-resource")
    assert "last_verified" not in other


# --- Criterion 2: the failure form requires a reason and marks broken -------


def test_broken_records_dated_marker_with_reason(resources_repo, capsys):
    _seed(resources_repo)
    rc = cli.run(
        ["verify-resource", "some-resource", "--broken", "--reason", "404 not found"],
        root=resources_repo,
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "broken" in out
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert entry["broken"] == {"date": _today(), "reason": "404 not found"}


def test_broken_does_not_touch_last_verified(resources_repo):
    # A previously-verified resource stays verified when a later check fails: a
    # failed check is not a verification, so `last_verified` is left alone and the
    # two facts coexist.
    _seed(resources_repo, _resource(last_verified="2020-01-01"))
    rc = cli.run(
        ["verify-resource", "some-resource", "--broken", "--reason", "paywalled now"],
        root=resources_repo,
    )
    assert rc == 0
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert entry["last_verified"] == "2020-01-01"
    assert entry["broken"]["reason"] == "paywalled now"


def test_broken_without_reason_is_an_error(resources_repo, capsys):
    _seed(resources_repo)
    rc = cli.run(
        ["verify-resource", "some-resource", "--broken"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "reason" in out.lower()
    # Nothing written: no broken marker appears.
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert "broken" not in entry
    assert load_events(resources_repo) == []


def test_reason_without_broken_is_an_error(resources_repo, capsys):
    _seed(resources_repo)
    rc = cli.run(
        ["verify-resource", "some-resource", "--reason", "stray reason"],
        root=resources_repo,
    )
    out = capsys.readouterr().out
    assert rc == 1
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert "last_verified" not in entry
    assert load_events(resources_repo) == []


# --- Criterion 3: a later successful verify clears the broken marker --------


def test_later_success_clears_broken_marker(resources_repo):
    _seed(
        resources_repo,
        _resource(broken={"date": "2020-01-01", "reason": "was down"}),
    )
    rc = cli.run(["verify-resource", "some-resource"], root=resources_repo)
    assert rc == 0
    entry = resource_named(read_registry(resources_repo), "some-resource")
    assert "broken" not in entry
    assert entry["last_verified"] == _today()


# --- Criterion 4: an unknown resource id is an error, writes nothing --------


def test_unknown_resource_is_an_error_and_writes_nothing(resources_repo, capsys):
    _seed(resources_repo)  # registry holds `some-resource` only
    before = read_registry(resources_repo)
    rc = cli.run(["verify-resource", "ghost-resource"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "ghost-resource" in out
    # The registry is byte-for-byte unchanged and no event was logged.
    assert read_registry(resources_repo) == before
    assert load_events(resources_repo) == []


def test_unloadable_registry_is_a_clean_error(resources_repo, capsys):
    # A schema-invalid registry is a reported failure, not a traceback, and
    # writes nothing.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [{"id": "no-pointer", "cost": "free"}])
    rc = cli.run(["verify-resource", "no-pointer"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAILED" in out
    assert load_events(resources_repo) == []


# --- Criterion 5: every invocation appends exactly one event ----------------


def test_successful_verify_appends_exactly_one_event(resources_repo):
    _seed(resources_repo)
    rc = cli.run(["verify-resource", "some-resource"], root=resources_repo)
    assert rc == 0
    events = load_events(resources_repo)
    assert len(events) == 1
    assert events[0]["command"] == "verify-resource"
    assert events[0]["records_touched"] == ["some-resource"]


def test_broken_verify_appends_exactly_one_event(resources_repo):
    # The failure form is a successful *command invocation* recording an
    # observation — it logs its one event just like the success form.
    _seed(resources_repo)
    rc = cli.run(
        ["verify-resource", "some-resource", "--broken", "--reason", "gone"],
        root=resources_repo,
    )
    assert rc == 0
    events = load_events(resources_repo)
    assert len(events) == 1
    assert events[0]["command"] == "verify-resource"


# --- Criterion 6: zero coupling — a broken resource changes nothing ---------


def _write_pass_eligible_node(root, node_id: str) -> None:
    """Write a node that is `available` and pass-eligible: spec + gate + record.

    Mirrors the policy suite's mastery-repo shape so the zero-coupling proof
    exercises the *real* pass path over real files.
    """
    write_node(root, node_id)
    spec_id = f"spec.{node_id}.main"
    _write_yaml(
        root,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": spec_id,
                    "node_id": node_id,
                    "title": "Main artifact",
                    "artifact_kind": "problem_set",
                    "required": True,
                    "minimum_count": 1,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/validation_gates.yaml",
        {
            "validation_gates": [
                {"id": f"gate.{node_id}", "node_id": node_id, "authority": "manual"}
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{node_id}.001",
                    "artifact_spec_id": spec_id,
                    "location": "evidence/a.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:aaa",
                    "created_at": "2026-07-01",
                }
            ]
        },
    )
    _write_yaml(root, "evidence/attempts.yaml", {"attempts": []})
    _write_yaml(
        root,
        "graph/state.yaml",
        {"progress": {node_id: {"state": "available", "changed_at": "2026-07-01"}}},
    )


def _write_yaml(root, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_broken_resource_does_not_block_pass(resources_repo, capsys):
    # The zero-coupling proof: a node is pass-eligible and one of its linked
    # resources is broken. Resource status is pure advice — the broken marker
    # touches nothing about the node, so `pass` proceeds normally.
    node_id = "testing.res.subject_01"
    _write_pass_eligible_node(resources_repo, node_id)
    write_registry(
        resources_repo,
        [
            _resource(broken={"date": "2020-01-01", "reason": "dead link"}),
        ],
    )

    # Pass eligibility is unaffected by the broken resource...
    rc = cli.run(["eligibility", node_id], root=resources_repo)
    elig_out = capsys.readouterr().out
    assert rc == 0
    assert "ELIGIBLE" in elig_out and "NOT ELIGIBLE" not in elig_out

    # ...and the pass itself is not blocked.
    rc = cli.run(["pass", node_id], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "is now passed" in out

    # Readiness/progress moved forward exactly as the graph dictates: the node is
    # passed, and nothing about the resource's brokenness intervened.
    state = yaml.safe_load(
        (resources_repo / "graph" / "state.yaml").read_text(encoding="utf-8")
    )
    assert state["progress"][node_id]["state"] == "passed"
