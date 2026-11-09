"""The read-only surfaces — the v3 route table (spec-v3-study-day §10, §11).

What only the wired views can show: every served destination renders from
the lenient seam — an edit to ``graph/nodes/*.md`` or ``state.yaml``
appears on the next render — every interpolated value is escaped, and
advisory policies surface as banners and labels that never block.

The per-surface contracts live with their own surfaces (the Today queue in
``test_today.py``, the discovery surfaces in ``test_discovery.py``, the
cockpit in ``test_session_cockpit.py``, the pass and mastery journeys in
``test_pass_master.py``, the review loop in ``test_reviews.py``). This
module covers what the surfaces share: a fresh render per request, the
escaping discipline, the unknown-node handling and the lenient seam.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from _builders import write_node as _shared_write_node

from skilltrace.context import load_context_lenient, load_context_strict
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]


# --- Seeded repos --------------------------------------------------------------


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _write_node(root: Path, node_id: str, title: str | None = None) -> None:
    """Write a node file via the shared helper; optionally override the title.

    The shared helper produces a default title; this in-suite wrapper preserves
    the historical ``title=`` override used by one XSS-rejection test that
    needs a hostile title string.
    """
    _shared_write_node(root, node_id)
    if title is not None:
        path = root / "graph" / "nodes" / f"{node_id}.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(f"title: Title for {node_id}", f"title: {title}"),
            encoding="utf-8",
        )


def _set_state(root: Path, node_id: str, state: str) -> None:
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _seed_repo(tmp_path)


def _first_node_id(root: Path, *, state: str | None = None) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError(f"no node with state {state!r}")


# --- the surfaces render --------------------------------------------------------


def test_every_destination_renders(repo):
    """Each destination in the normative table answers with its own body."""
    node_id = _first_node_id(repo)
    for name, body in (
        ("today", views.home_body(repo)),
        ("next", views.next_body(repo, {})),
        ("find", views.finder_body(repo, {})),
        ("node", views.node_body(repo, node_id)),
        ("session", views.session_body(repo)),
        ("session close", views.session_close_body(repo)),
        ("node evidence", views.node_evidence_body(repo, node_id)),
        ("evidence index", views.evidence_index_body(repo)),
        ("reviews", views.reviews_body(repo)),
        ("operations", views.operations_body(repo)),
        ("graph", views.graph_body(repo)),
        ("health", views.health_body(repo)),
        ("analytics", views.analytics_body(repo, {})),
        ("portfolio", views.portfolio_body(repo)),
    ):
        title, html, status = body
        assert status == 200, name
        assert title, name
        assert html, name


def test_home_renders_the_priority_queue(repo):
    """Today is a queue of items, not the retired bento recipe."""
    title, body, status = views.home_body(repo)
    assert status == 200
    assert title == "Today"
    assert 'class="queue"' in body
    assert '<div class="hero">' not in body
    assert "bento-card" not in body


def test_home_renders_fresh_per_request(repo):
    """Every GET reads truth fresh — an edit appears on the next render."""
    node_id = _first_node_id(repo)
    _write_node(repo, node_id, title="Freshly Renamed Skill")
    _, body, _ = views.node_body(repo, node_id)
    assert "Freshly Renamed Skill" in body


def test_home_never_renders_the_raw_backlog(repo):
    """The raw flat dump never renders (P1.2)."""
    _, body, _ = views.home_body(repo)
    assert "backlog lineup" not in body


# --- the node detail ------------------------------------------------------------


def test_node_page_leads_with_the_readable_title(repo):
    """The title leads; the raw id is labelled technical detail (R1)."""
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    title = load_context_lenient(repo).node_map[node_id].title
    assert title in body
    # The id is present, but only inside the labelled technical row.
    assert node_id in body
    assert "Node ID" in body


def test_node_page_shows_each_record_type_as_its_own_section(repo):
    """Records are never collapsed into a generic object."""
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    for section in (
        "Progress record",
        "Node details",
        "Relationships",
        "Where to learn",
        "Evidence wanted",
        "Checking",
        "Evidence recorded",
        "Attempts",
        "Blockers",
        "Remediation",
        "Reviews",
        "Recent activity",
    ):
        assert section in body, section


def test_node_page_shows_evidence_wanted_and_recorded_apart(repo):
    """Two distinct figures, never one ambiguous number (R2)."""
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    assert "Evidence wanted" in body
    assert "Evidence recorded" in body
    assert "wanted" in body.lower()
    assert "recorded" in body.lower()


def test_node_page_links_reach_the_other_destinations(repo):
    """The links reach the session, the evidence workspace and the panels."""
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    assert f'href="/nodes/{node_id}/evidence"' in body
    assert f'href="/nodes/{node_id}/pass"' in body
    assert f'href="/nodes/{node_id}/master"' in body
    assert 'href="/reviews"' in body
    assert 'href="/session"' in body


def test_log_work_appears_only_while_a_session_is_open(repo):
    """The contextual work action exists only with an open Session."""
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    assert "Log work here" not in body

    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.node.001",
                    "status": "open",
                    "started_at": "2026-11-17T07:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.node.001.01",
                    "session_id": "ses.node.001",
                    "node_id": node_id,
                    "created_at": "2026-11-17T07:30:00+00:00",
                    "minutes": 10,
                }
            ]
        },
    )
    _, body, _ = views.node_body(repo, node_id)
    assert "Log work here" in body
    assert f'name="node_id" value="{node_id}"' in body


def test_locked_node_shows_reason_and_prereqs(repo):
    """A locked node explains itself and offers no start."""
    view = load_context_lenient(repo)
    locked = [n.id for n in view.nodes if view.store.state_of(n.id) == "locked"]
    if not locked:
        pytest.skip("the seed graph has no locked node")
    _, body, _ = views.node_body(repo, sorted(locked)[0])
    assert "locked" in body.lower()
    assert 'action="/nodes/' not in body or "/start" not in body


def test_unknown_node_is_404(repo):
    title, body, status = views.node_body(repo, "no.such.node")
    assert status == 404
    assert title == "Not found"
    assert "not in the curriculum" in body


def test_node_page_escapes_hostile_title(tmp_path):
    """Every interpolated value passes through the one escaper."""
    root = _seed_repo(tmp_path)
    node_id = "data.evil.001"
    _write_node(root, node_id, title="<script>alert(1)</script>")
    _, body, _ = views.node_body(root, node_id)
    assert "<script>alert(1)</script>" not in body
    # The hostile title is escaped, not executed.
    assert "&lt;script&gt;" in body or "alert(1)" not in body


# --- the lenient seam ------------------------------------------------------------


def test_pages_render_when_optional_layers_fail_leniently(tmp_path):
    """A malformed optional layer degrades; the page still serves."""
    root = _seed_repo(tmp_path)
    (root / "execution").mkdir(exist_ok=True)
    (root / "execution" / "sessions.yaml").write_text(
        "sessions: [ this is not valid yaml", encoding="utf-8"
    )
    node_id = _first_node_id(root)
    for name, body in (
        ("home", views.home_body(root)),
        ("node", views.node_body(root, node_id)),
        ("reviews", views.reviews_body(root)),
    ):
        assert body[2] == 200, name


def test_strict_seam_collects_errors_while_lenient_still_serves(tmp_path):
    """The strict seam reports the failure; the lenient seam serves."""
    root = _seed_repo(tmp_path)
    (root / "execution").mkdir(exist_ok=True)
    (root / "execution" / "sessions.yaml").write_text(
        "sessions: [ this is not valid yaml", encoding="utf-8"
    )
    strict = load_context_strict(root)
    assert not strict.ok
    assert strict.errors
    lenient = load_context_lenient(root)
    assert lenient is not None
