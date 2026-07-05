"""`skilltrace resources --node-id <node_id>` — the per-node reverse index.

The listing is derived on demand from each resource's `supports` list — nothing
stored — so a learner starting work on a node can see what to study from. Every
test drives the real CLI in-process through `cli.run(argv, root=...)` — the
single seam — and asserts only external behavior: exit code and stdout. The
command is read-only and appends no event.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import write_node, write_registry


# --- Lists resources naming the node, with pointer and claims --------------


def test_lists_resource_supporting_the_node(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "python-crash-course",
                "url": "https://example.com/course",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "python-crash-course" in out
    assert "https://example.com/course" in out
    assert "free" in out


def test_shows_both_url_and_local_path_and_claims(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "python-book",
                "url": "https://example.com/book",
                "local_path": "resources/python-book.pdf",
                "cost": "paid",
                "free_tier": True,
                "certificate": True,
                "license": "CC-BY-4.0",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "python-book" in out
    assert "https://example.com/book" in out
    assert "resources/python-book.pdf" in out
    assert "paid" in out
    assert "free tier" in out
    assert "certificate" in out
    assert "CC-BY-4.0" in out


def test_lists_every_resource_naming_the_node(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_node(resources_repo, "testing.res.subject_02")
    write_registry(
        resources_repo,
        [
            {
                "id": "shared-book",
                "url": "https://example.com/book",
                "cost": "paid",
                "supports": ["testing.res.subject_01", "testing.res.subject_02"],
            },
            {
                "id": "focused-course",
                "url": "https://example.com/course",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            },
            {
                "id": "other-node-only",
                "url": "https://example.com/other",
                "cost": "free",
                "supports": ["testing.res.subject_02"],
            },
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 0
    # A resource supporting several nodes surfaces on each of them.
    assert "shared-book" in out
    assert "focused-course" in out
    # A resource that does not name this node stays out of the listing.
    assert "other-node-only" not in out


# --- A node with no linked resources: informational, exit 0 ----------------


def test_node_with_no_resources_reports_plainly_and_exits_zero(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(resources_repo, [])
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    # Many nodes legitimately need no external material — this is information,
    # not an error.
    assert rc == 0
    assert "testing.res.subject_01" in out
    assert "[error]" not in out


def test_node_with_resources_but_none_linked_here_exits_zero(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_node(resources_repo, "testing.res.subject_02")
    write_registry(
        resources_repo,
        [
            {
                "id": "elsewhere",
                "url": "https://example.com/elsewhere",
                "cost": "free",
                "supports": ["testing.res.subject_02"],
            }
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "elsewhere" not in out


# --- An unknown node ID is an error (non-zero exit) ------------------------


def test_unknown_node_is_an_error(resources_repo, capsys):
    # No node file written — the node does not exist in the graph.
    write_registry(resources_repo, [])
    rc = cli.run(
        ["resources", "--node-id", "testing.res.ghost_99"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "testing.res.ghost_99" in out


# --- Integrity issues elsewhere never block the listing --------------------


def test_registry_with_orphan_sibling_still_lists_the_node(resources_repo, capsys):
    # An orphan resource is a validation *warning*, not a load error, so the
    # reverse index (which loads and filters, never validates) still works.
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "orphan-resource",
                "url": "https://example.com/unlinked",
                "cost": "free",
                "supports": [],
            },
            {
                "id": "good-resource",
                "url": "https://example.com/course",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            },
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "good-resource" in out


# --- Read-only, appends no event ------------------------------------------


def test_resources_index_is_read_only_and_logs_nothing(resources_repo):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "some-resource",
                "url": "https://example.com/course",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(
        ["resources", "--node-id", "testing.res.subject_01"], root=resources_repo
    )
    assert rc == 0
    assert load_events(resources_repo) == []


def test_resources_index_logs_nothing_even_on_unknown_node(resources_repo):
    write_registry(resources_repo, [])
    rc = cli.run(
        ["resources", "--node-id", "testing.res.ghost_99"], root=resources_repo
    )
    assert rc == 1
    assert load_events(resources_repo) == []
