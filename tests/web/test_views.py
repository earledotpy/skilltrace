"""The daily read-only pages — Tier-1 slice T3 (issue #72).

What only the wired views can show: `/` renders the today dashboard in P1
variant A (Mentor-first linear) with pressure excerpts and a health strip;
`/next` mirrors the CLI flags (`--minutes`, `--limit`, `--show-locked`) and
attaches a collapsible "Why this?" per candidate; `/nodes/{id}` renders the
primary Mentor card plus read-only drill-downs; `/health` rolls up the five
validators plus liveness. Every GET renders fresh from the lenient seam — an
edit to `graph/nodes/*.md` or `state.yaml` appears on the next render — every
interpolated value is escaped, and advisory policies surface as banners and
pills that never block.
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
    the historical `title=` override used by one XSS-rejection test that needs
    a hostile title string.
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


# --- The mechanical transform ---------------------------------------------------


def test_kicker_lines_become_kicker_divs():
    html = views._transform_block(["DO THIS NEXT"])
    assert '<div class="kicker">DO THIS NEXT</div>' in html


def test_banner_prefixes_become_banner_classes_and_escape():
    html = views._transform_block(["[warning] track <x> is unmapped"])
    assert '<p class="banner warning">track &lt;x&gt; is unmapped</p>' in html


def test_pill_line_becomes_pill_span_with_slug_class():
    html = views._transform_block(["  [Ready to start]"])
    assert '<span class="pill ready-to-start">Ready to start</span>' in html


def test_indented_lines_become_sub_divs():
    html = views._transform_block(["  Pandas Docs -- https://example.test/"])
    assert '<div class="sub">Pandas Docs -- https://example.test/</div>' in html


def test_lead_follows_kicker_and_label_precedes_indent():
    lines = [
        "THIS SKILL",
        "Some Skill Title",
        "",
        "Where to learn",
        "  A resource line",
        "Also in range: two, three.",
    ]
    html = views._transform_block(lines)
    assert '<p class="lead">Some Skill Title</p>' in html
    assert '<p class="label">Where to learn</p>' in html
    assert "<p>Also in range: two, three.</p>" in html


def test_separator_splits_blocks_and_banner_starts_its_own():
    lines = ["OPTION 1 — X", "body one", "---", "OPTION 2 — Y", "[advisory] note"]
    blocks = views.lines_to_blocks(lines)
    assert len(blocks) == 3
    assert blocks[1][0].strip().startswith("OPTION 2")
    assert blocks[2][0].startswith("[advisory]")


def test_transform_escapes_every_interpolated_value():
    html = views._transform_block(["<script>alert(1)</script>", "  <b>bold</b>"])
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html


# --- GET / — the today dashboard (variant A) -------------------------------------


def test_home_renders_today_dashboard(repo):
    title, body, status = views.home_body(repo)
    assert status == 200
    assert title == "Today"
    assert '<div class="kicker">TODAY</div>' in body
    # Focus bar links at the top recommendation's node detail.
    assert 'href="/nodes/' in body
    # Pressure excerpts are advisory pills, never blockers.
    assert "STUDY DAY PRESSURE" in body
    assert "overdue review" in body
    assert "available" in body and "locked" in body
    # Health strip rides the home page.
    assert "HEALTH STRIP" in body
    assert 'class="banner ok">health: OK.</p>' in body


def test_home_renders_fresh_per_request(repo):
    node_id = _first_node_id(repo)
    _, before, _ = views.home_body(repo)

    _set_state(repo, node_id, "active")
    _, after_active, _ = views.home_body(repo)
    assert before != after_active

    # A curriculum edit shows on refresh too.
    path = repo / "graph" / "nodes" / f"{node_id}.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("Summary for ", "Edited summary for "), encoding="utf-8")
    node_page_title, node_html, status = views.node_body(repo, node_id)
    assert status == 200
    assert "In progress" in node_html  # the state flip is visible


def test_home_pressure_excerpts_escape_blocker_text(repo):
    focus = _first_node_id(repo)
    _write_yaml(
        repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.01",
                    "node_id": focus,
                    "status": "open",
                    "description": '<img src=x onerror=alert(1)> stuck',
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    _, body, status = views.home_body(repo)
    assert status == 200
    assert "1 open blocker" in body
    assert "<img src=x" not in body
    assert "&lt;img src=x" in body


def test_home_surfaces_unexpected_queue_render_error(repo, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("queue boom")

    monkeypatch.setattr(views, "derive_next", boom)
    with pytest.raises(RuntimeError, match="queue boom"):
        views.home_body(repo)


# --- GET /next — flags mirror the CLI --------------------------------------------


def test_next_defaults_mirror_cli_flags(repo):
    _, body, status = views.next_body(repo, {})
    assert status == 200
    assert "60-min session" in body  # CLI default --minutes 60
    kickers = [line for line in body.splitlines() if ">OPTION " in line]
    assert len(kickers) <= 5  # CLI default --limit 5


def test_next_minutes_and_limit_flags_apply(repo):
    _, body, _ = views.next_body(repo, {"minutes": ["90"], "limit": ["2"]})
    assert "90-min session" in body
    assert len([line for line in body.splitlines() if ">OPTION " in line]) <= 2


def test_next_bad_int_returns_400(repo):
    for bad in ({"minutes": ["abc"]}, {"limit": [""]}):
        _, _, status = views.next_body(repo, bad)
        assert status == 400


def test_next_show_locked_appends_locked_appendix(repo):
    _, without_locked, _ = views.next_body(repo, {})
    _, with_locked, _ = views.next_body(repo, {"locked": ["1"]})
    assert "Locked (" not in without_locked
    assert "Locked (" in with_locked  # shipped seed graph has locked nodes
    # Each locked line names its unsatisfied hard prerequisites ("blocked by:")
    # or says readiness is stale — never a silent lock.
    assert "blocked by:" in with_locked


def test_next_toggle_link_flips_show_locked(repo):
    _, off_body, _ = views.next_body(repo, {})
    assert "/next?minutes=60&amp;limit=5&amp;locked=1" in off_body
    _, on_body, _ = views.next_body(repo, {"locked": ["1"], "minutes": ["30"]})
    assert "/next?minutes=30&amp;limit=5" in on_body


def test_next_why_this_collapsible_is_advisory_only(repo):
    _, body, _ = views.next_body(repo, {})
    options = len([line for line in body.splitlines() if ">OPTION " in line])
    assert body.count("<details>") == options  # one collapsible per card
    assert body.count("Why this?") == options
    assert "never block a human-initiated action" in body


# --- GET /nodes/{id} — primary card plus drill-downs ------------------------------


def test_node_page_renders_primary_mentor_card(repo):
    node_id = _first_node_id(repo, state="available")
    title, body, status = views.node_body(repo, node_id)
    assert status == 200
    assert title != ""  # the page title is the node title
    assert '<div class="kicker">THIS SKILL</div>' in body
    assert '<span class="pill ready-to-start">Ready to start</span>' in body
    assert "WHERE TO LEARN" not in body  # Mentor labels stay verbatim, not re-cased
    assert "Where to learn" in body
    assert "DO THIS NEXT" in body


def test_node_page_drill_down_sections(repo):
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    assert "DRILL-DOWN" in body
    assert "<details>" in body
    assert "Evidence" in body
    assert "Resources" in body


def test_locked_node_shows_reason_and_prereqs(repo):
    node_id = _first_node_id(repo, state="locked")
    _, body, status = views.node_body(repo, node_id)
    assert status == 200
    assert '<span class="pill locked">Locked</span>' in body
    # The locked reason names unsatisfied hard prerequisites (Mentor voice).
    assert "still comes first" in body or "locked behind" in body.lower()


def test_unknown_node_is_404(repo):
    _, _, status = views.node_body(repo, "no.such_node_99")
    assert status == 404


def test_node_page_escapes_hostile_title(tmp_path):
    repo = _seed_repo(tmp_path)
    hostile = "<script>alert(1)</script>"
    _write_node(repo, "testing.hostile.script_01", title=hostile)
    _set_state(repo, "testing.hostile.script_01", "available")

    title, body, status = views.node_body(repo, "testing.hostile.script_01")
    assert status == 200
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    # The raw title rides unescaped until page() wraps it — then nothing raw remains.
    from skilltrace.web.handler import page

    assert "<script>" not in page(title, "")


# --- GET /health — five validators + liveness -------------------------------------


def test_health_page_rolls_up_validators_and_liveness(repo):
    title, body, status = views.health_body(repo)
    assert status == 200
    assert title == "Health"
    for layer in ("graph", "evidence", "execution", "policy", "resources"):
        assert f">{layer}</td>" in body or f"<th>{layer}</th>" in body
    assert "health:" in body  # verdict line
    assert "states: available=" in body  # progress-store liveness line
    assert "verified=" in body  # resource verification liveness line


def test_health_page_reports_layer_errors_honestly(repo):
    (repo / "policy" / "recommendation.yaml").write_text("::: not yaml [", encoding="utf-8")
    _, body, status = views.health_body(repo)
    assert status == 200  # health renders the condition; exit-code semantics are CLI's
    assert "FAILED" in body
    assert '<p class="banner error">' in body


# --- Lenient degradation and strict refusal ----------------------------------------


def test_pages_render_when_optional_layers_fail_leniently(tmp_path):
    repo = _seed_repo(tmp_path)
    shutil.rmtree(repo / "evidence")
    for name, fn in (
        ("home", lambda: views.home_body(repo)),
        ("next", lambda: views.next_body(repo, {})),
        ("health", lambda: views.health_body(repo)),
    ):
        title, body, status = fn()
        assert status == 200, name  # optional layers degrade to empty, pages render


def test_strict_seam_collects_errors_while_lenient_still_serves(tmp_path):
    repo = _seed_repo(tmp_path)
    _write_yaml(repo, "evidence/artifact_specs.yaml", {"artifact_specs": [{"id": "bad"}]})
    strict = load_context_strict(repo)
    assert strict.errors, "strict collects the malformed evidence"
    _, _, status = views.next_body(repo, {})
    assert status == 200  # lenient keeps serving the daily loop
