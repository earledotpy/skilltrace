"""`skilltrace validate resources` — the resource registry's integrity check.

Every test drives the real CLI in-process through `cli.run(argv, root=...)` — the
single seam — and asserts only external behavior: exit code, stdout, and the
files on disk. The registry lives in the curriculum area (`graph/resources.yaml`);
`validate resources` judges its integrity and is read-only.
"""

from __future__ import annotations

from pathlib import Path

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import REPO_ROOT, write_node, write_registry


# --- Criterion 1 & 6: shipped repo is empty-but-valid, registry is curriculum ---


def test_shipped_registry_validates_clean(capsys):
    # The shipped repo ships a valid registry in the curriculum area (the math
    # bands populate it in v0.8 slice 2; earlier it was empty-but-valid).
    rc = cli.run(["validate", "resources"], root=REPO_ROOT)
    assert rc == 0
    assert "validate resources: OK" in capsys.readouterr().out


def test_registry_lives_in_curriculum_area_not_evidence():
    assert (REPO_ROOT / "graph" / "resources.yaml").exists()
    assert not (REPO_ROOT / "evidence" / "resources.yaml").exists()


def test_empty_registry_validates_clean(resources_repo, capsys):
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 0
    assert "validate resources: OK" in capsys.readouterr().out


# --- A well-formed resource validates clean --------------------------------


def test_resource_with_url_and_supported_node_is_clean(resources_repo, capsys):
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
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" not in out
    assert "[error]" not in out


def test_resource_with_only_local_path_is_clean(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "local-book",
                "local_path": "resources/python-book.pdf",
                "cost": "paid",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 0
    assert "validate resources: OK" in capsys.readouterr().out


# --- Criterion 2: duplicate resource ID is an error ------------------------


def test_duplicate_resource_id_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "same-id",
                "url": "https://example.com/a",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            },
            {
                "id": "same-id",
                "url": "https://example.com/b",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            },
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "same-id" in out


# --- Criterion 3: neither URL nor local path is an error -------------------


def test_resource_with_neither_url_nor_path_is_an_error(resources_repo, capsys):
    write_node(resources_repo, "testing.res.subject_01")
    write_registry(
        resources_repo,
        [
            {
                "id": "pointing-at-nothing",
                "cost": "free",
                "supports": ["testing.res.subject_01"],
            }
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "pointing-at-nothing" in out


# --- Criterion 4: naming a node that does not exist is an error ------------


def test_resource_naming_unknown_node_is_an_error(resources_repo, capsys):
    # No node file written — the reference dangles.
    write_registry(
        resources_repo,
        [
            {
                "id": "dangling-link",
                "url": "https://example.com/course",
                "cost": "free",
                "supports": ["testing.res.ghost_99"],
            }
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 1
    assert "validate resources: FAILED" in out
    assert "testing.res.ghost_99" in out


# --- Criterion 5: supporting no node is a warning, not an error ------------


def test_resource_supporting_no_node_warns_but_passes(resources_repo, capsys):
    write_registry(
        resources_repo,
        [
            {
                "id": "orphan-resource",
                "url": "https://example.com/unlinked",
                "cost": "free",
                "supports": [],
            }
        ],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "[warning]" in out
    assert "orphan-resource" in out


def test_resource_with_absent_supports_warns_but_passes(resources_repo, capsys):
    write_registry(
        resources_repo,
        [{"id": "no-supports-key", "url": "https://example.com/x", "cost": "free"}],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "validate resources: OK" in out
    assert "no-supports-key" in out


# --- Criterion 7: read-only, appends no event ------------------------------


def test_validate_resources_is_read_only_and_logs_nothing(resources_repo):
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
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 0
    assert load_events(resources_repo) == []


def test_validate_resources_logs_nothing_even_on_failure(resources_repo):
    write_registry(
        resources_repo,
        [{"id": "broken", "supports": ["testing.res.ghost_99"]}],
    )
    rc = cli.run(["validate", "resources"], root=resources_repo)
    assert rc == 1
    assert load_events(resources_repo) == []
