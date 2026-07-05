"""`validate resources` — the verifiable claim fields (v0.7 slice 2).

Cost, free tier, certificate, and license are the portfolio-relevant claims a
resource records. `cost` is a required two-value enum (`free` | `paid`) — the
*only* place cost lives, so a free/paid contradiction is unrepresentable rather
than merely checked. `free_tier`/`certificate` are optional booleans and
`license` optional free text. Validation gains two rules: an unknown or missing
`cost` is an error; `free_tier: true` on a `cost: free` resource is a redundancy
warning (representable, but flagged for cleanup).

Every test drives the real CLI in-process through `cli.run(argv, root=...)` — the
single seam — asserting only exit code, stdout, and files on disk.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import write_node, write_registry


def _linked_resource(**fields) -> dict:
    """A minimal load-clean resource on `testing.res.subject_01`, plus `fields`."""
    base = {
        "id": "some-resource",
        "url": "https://example.com/course",
        "supports": ["testing.res.subject_01"],
    }
    base.update(fields)
    return base


# --- Criterion 1: a resource can record every claim and validate clean -----


def test_resource_records_all_claims_and_validates_clean(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            _linked_resource(
                cost="paid",
                free_tier=True,
                certificate=True,
                license="CC-BY-4.0",
            )
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" not in out
    assert "[error]" not in out


def test_free_cost_validates_clean(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost="free")])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" not in out


def test_paid_cost_with_free_tier_validates_clean(resources_repo, capsys):
    # A free tier is exactly the claim a *paid* resource may make — no warning.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost="paid", free_tier=True)])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" not in out


# --- Criterion 4: cost required; the other claims optional -----------------


def test_missing_cost_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    # A well-formed resource in every other respect: only cost is absent.
    write_registry(
        resources_repo,
        [
            {
                "id": "no-cost",
                "url": "https://example.com/course",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "no-cost" in out
    assert "cost" in out


def test_optional_claims_absent_validates_clean(resources_repo, capsys):
    # cost present, every other claim absent — the optional ones are truly optional.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost="free")])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 0
    assert "validate resources: OK" in capsys.readouterr().out


# --- Criterion 2: an unknown cost value is an error ------------------------


def test_unknown_cost_value_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost="freemium")])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "some-resource" in out
    assert "freemium" in out


def test_non_scalar_cost_is_a_clean_error_not_a_traceback(resources_repo, capsys):
    # A malformed `cost` (a list, not a scalar) must be a reported validation
    # error, not an uncaught TypeError from testing list-membership in the enum.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost=["free"])])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "some-resource" in out


# --- Criterion 3: free_tier on a free resource is a warning, not an error --


def test_free_tier_on_free_resource_is_a_warning(resources_repo, capsys):
    # Mirror the orphan-warning shape: representable, exit 0, flagged for cleanup.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo, [_linked_resource(cost="free", free_tier=True)]
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" in out
    assert "some-resource" in out
    assert "[error]" not in out


def test_free_tier_false_on_free_resource_does_not_warn(resources_repo, capsys):
    # Only an *explicit* free-tier claim is redundant; a false claim is silent.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo, [_linked_resource(cost="free", free_tier=False)]
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" not in out


# --- Claim shape: booleans must be booleans, license a string --------------


def test_non_boolean_free_tier_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo, [_linked_resource(cost="paid", free_tier="yes")]
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "free_tier" in out


def test_non_boolean_certificate_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo, [_linked_resource(cost="free", certificate="yes")]
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "certificate" in out


def test_non_string_license_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_linked_resource(cost="free", license=42)])
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "license" in out


# --- Read-only discipline holds for the new checks too ---------------------


def test_claim_validation_appends_no_event(resources_repo):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo, [_linked_resource(cost="free", free_tier=True)]
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 0
    assert load_events(resources_repo) == []
