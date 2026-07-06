"""`skilltrace resource-report` — the verification status snapshot (v0.7 slice 5).

resource-report is the lowest advisory tier: a read-only, always-exit-0 snapshot
of every resource's *derived* verification status (unverified / verified / stale
/ broken), with broken and stale grouped first so the next verification or
replacement action is obvious. Resource trouble warns here and nowhere else — it
never blocks a command, never touches node state, and never feeds `recommend`
ordering.

Every test drives the real CLI in-process through `cli.run(argv, root=...)` — the
single seam — asserting only exit codes, stdout, on-disk YAML, and the event log.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import REPO_ROOT, write_node, write_registry


def _today() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> str:
    return (_today() - timedelta(days=n)).date().isoformat()


def _resource(**fields) -> dict:
    """A minimal load-clean free resource on `testing.res.subject_01`, plus fields."""
    base = {
        "id": "some-resource",
        "url": "https://example.com/course",
        "cost": "free",
        "supports": ["testing.res.subject_01"],
    }
    base.update(fields)
    return base


def _set_window(root: Path, days: int) -> None:
    """Edit the copied policy seed's staleness window (proves it is read, not hardcoded)."""
    path = root / "policy" / "resource_verification.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["resource_verification_policy"]["stale_after_days"] = days
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Always exit 0, read-only, appends no event ----------------------------


def test_shipped_repo_report_exits_zero(capsys):
    # The exit-gate command: resource-report on the shipped repo is exit 0.
    rc = cli.run(["resource-report"], root=REPO_ROOT)
    assert rc == 0
    assert "resource-report:" in capsys.readouterr().out


def test_report_is_read_only_appends_no_event(resources_repo):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_resource(last_verified=_days_ago(1))])
    rc = cli.run(["resource-report"], root=resources_repo)
    assert rc == 0
    assert load_events(resources_repo) == []


def test_empty_registry_reports_and_exits_zero(resources_repo, capsys):
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "0 resource(s)" in out


def test_unreadable_registry_still_exits_zero(resources_repo, capsys):
    # A schema-invalid registry is a loud report line, not a non-zero exit —
    # integrity is `validate resources`' job; the snapshot degrades gracefully.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [{"id": "no-pointer", "cost": "free"}])
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[error]" in out
    assert "registry" in out.lower()


# --- Derived statuses: unverified / verified / stale -------------------------


def test_unverified_resource_is_reported_as_unverified(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_resource()])  # no last_verified
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[unverified] some-resource" in out


def test_recent_verification_is_verified(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_resource(last_verified=_days_ago(1))])
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[verified] some-resource" in out


def test_old_verification_is_stale(resources_repo, capsys):
    # Default window is 180 days; a verification 400 days old is stale.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_resource(last_verified=_days_ago(400))])
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[stale] some-resource" in out


def test_window_is_read_from_policy_not_hardcoded(resources_repo, capsys):
    # A resource verified 40 days ago: verified under the default 180-day window,
    # stale once the seed window is edited down to 30. The window is seed data.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [_resource(last_verified=_days_ago(40))])

    rc = cli.run(["resource-report"], root=resources_repo)
    assert rc == 0
    assert "[verified] some-resource" in capsys.readouterr().out

    _set_window(resources_repo, 30)
    rc = cli.run(["resource-report"], root=resources_repo)
    assert rc == 0
    assert "[stale] some-resource" in capsys.readouterr().out


# --- Broken dominates and floats to the top ---------------------------------


def test_broken_floats_to_top_with_reason_and_date(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            _resource(id="good-one", last_verified=_days_ago(1)),
            _resource(id="dead-one", broken={"date": "2020-01-01", "reason": "404 gone"}),
        ],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    # Broken sorts ahead of the verified sibling despite its later file position.
    broken_at = out.index("[broken] dead-one")
    verified_at = out.index("[verified] good-one")
    assert broken_at < verified_at
    assert "2020-01-01" in out
    assert "404 gone" in out


def test_broken_dominates_a_recent_verification(resources_repo, capsys):
    # A resource both recently verified AND broken reports broken — the marker
    # dominates the derived statuses (CONTEXT.md).
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            _resource(
                last_verified=_days_ago(1),
                broken={"date": "2026-07-01", "reason": "paywalled now"},
            )
        ],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[broken] some-resource" in out
    assert "[verified] some-resource" not in out


def test_stale_grouped_before_unverified_and_verified(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            _resource(id="fresh", last_verified=_days_ago(1)),
            _resource(id="never"),
            _resource(id="old", last_verified=_days_ago(400)),
        ],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    # stale floats above both unverified and verified.
    assert out.index("[stale] old") < out.index("[unverified] never")
    assert out.index("[stale] old") < out.index("[verified] fresh")


# --- Replacement candidates -------------------------------------------------


def test_live_resource_on_broken_node_is_a_candidate(resources_repo, capsys):
    node = "testing.res.subject_01"
    write_node(resources_repo, node)
    write_registry(
        resources_repo,
        [
            _resource(id="dead-one", broken={"date": "2020-01-01", "reason": "gone"}),
            _resource(id="live-alt", last_verified=_days_ago(1)),
        ],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "replacement candidates: live-alt" in out


def test_broken_sibling_is_not_a_candidate(resources_repo, capsys):
    # A second dead link on the same node is no replacement — candidates are live.
    node = "testing.res.subject_01"
    write_node(resources_repo, node)
    write_registry(
        resources_repo,
        [
            _resource(id="dead-one", broken={"date": "2020-01-01", "reason": "gone"}),
            _resource(id="dead-two", broken={"date": "2020-02-01", "reason": "also gone"}),
        ],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "replacement candidates: none on its node(s)" in out
    assert "candidates: dead-two" not in out


# --- Coverage: uncovered nodes are information, not warnings -----------------


def test_uncovered_node_is_informational_not_a_warning(resources_repo, capsys):
    write_node(resources_repo, "testing.res.covered_01")
    write_node(resources_repo, "testing.res.bare_02")
    write_registry(
        resources_repo,
        [_resource(id="only-one", supports=["testing.res.covered_01"])],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "coverage:" in out
    assert "testing.res.bare_02" in out
    # The bare node is informational — not flagged as a warning.
    coverage_section = out[out.index("coverage:"):]
    assert "[warning]" not in coverage_section


# --- Missing local file is a report warning; validate ignores it ------------


def test_missing_local_file_is_a_report_warning(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [_resource(id="with-path", url=None, local_path="resources/missing.pdf")],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[warning]" in out
    assert "missing.pdf" in out


def test_present_local_file_is_not_warned(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    present = resources_repo / "resources" / "present.pdf"
    present.parent.mkdir(parents=True, exist_ok=True)
    present.write_text("stub", encoding="utf-8")
    write_registry(
        resources_repo,
        [_resource(id="with-path", url=None, local_path="resources/present.pdf")],
    )
    rc = cli.run(["resource-report"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "present.pdf" not in out  # no warning line about it


def test_validate_resources_ignores_a_missing_local_file(resources_repo, capsys):
    # The environment observation belongs to resource-report only — `validate
    # resources` judges curriculum integrity and never touches the filesystem.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [_resource(id="with-path", url=None, local_path="resources/missing.pdf")],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "missing.pdf" not in out


# --- Zero coupling: resource status never affects recommend ordering --------


def test_resource_status_does_not_affect_recommend(resources_repo, capsys):
    # `next` output is byte-for-byte identical whether or not a broken resource is
    # linked to the recommended node — resource status never feeds recommendation.
    node = "testing.res.subject_01"
    write_node(resources_repo, node)
    _write_state(resources_repo, {node: "available"})

    write_registry(resources_repo, [])
    rc = cli.run(["next", "--minutes", "60"], root=resources_repo)
    assert rc == 0
    without_resource = capsys.readouterr().out

    write_registry(
        resources_repo,
        [_resource(broken={"date": "2020-01-01", "reason": "dead link"})],
    )
    rc = cli.run(["next", "--minutes", "60"], root=resources_repo)
    assert rc == 0
    with_broken_resource = capsys.readouterr().out

    assert without_resource == with_broken_resource
    assert node in with_broken_resource


def _write_state(root: Path, states: dict[str, str]) -> None:
    progress = {
        node_id: {"state": state, "changed_at": "2026-07-01"}
        for node_id, state in states.items()
    }
    path = root / "graph" / "state.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"progress": progress}, sort_keys=False), encoding="utf-8")
