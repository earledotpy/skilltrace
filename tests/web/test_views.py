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
from skilltrace.mentor.cards import (
    Banner,
    Kicker,
    Label,
    Lead,
    MentorCard,
    Para,
    Pill,
    Sub,
    Title,
)
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


# --- Structured cards -----------------------------------------------------------


def test_kicker_parts_become_kicker_divs():
    html = views.render_cards([MentorCard(parts=[Kicker(text="DO THIS NEXT")])])
    # P3.6: _sentence_case normalises ALL-CAPS kickers → sentence case.
    assert '<div class="kicker">Do this next</div>' in html


def test_banner_parts_become_banner_classes_and_escape():
    html = views.render_cards(
        [MentorCard.banner_card("warning", "track <x> is unmapped")]
    )
    assert '<p class="banner warning">track &lt;x&gt; is unmapped</p>' in html


def test_pill_parts_become_pill_spans_with_slug_class():
    html = views.render_cards(
        [MentorCard(parts=[Pill(label="Ready to start")])]
    )
    # P3.4: _normalize_pill_label maps 'Ready to start' → 'Available' (canonical).
    assert '<span class="pill available">Available</span>' in html


def test_sub_parts_become_sub_divs():
    html = views.render_cards(
        [MentorCard(parts=[Sub(text="Pandas Docs -- https://example.test/")])]
    )
    assert '<div class="sub">Pandas Docs -- https://example.test/</div>' in html


def test_title_lead_label_and_para_render_with_structure():
    card = MentorCard(
        parts=[
            Kicker(text="THIS SKILL"),
            Title(text="Some Skill Title"),
            Label(text="Where to learn"),
            Sub(text="A resource line"),
            Para(text="Also in range: two, three."),
        ]
    )
    html = views.render_cards([card])
    assert '<p class="lead">Some Skill Title</p>' in html
    assert '<p class="label">Where to learn</p>' in html
    assert "<p>Also in range: two, three.</p>" in html


def test_lead_parts_render_as_lead_paragraphs():
    html = views.render_cards(
        [
            MentorCard(
                parts=[
                    Kicker(text="TODAY"),
                    Lead(text="Your best focus today is X."),
                ]
            )
        ]
    )
    assert '<p class="lead">Your best focus today is X.</p>' in html


def test_each_card_renders_its_own_card_div():
    cards = [
        MentorCard(parts=[Kicker(text="OPTION 1"), Para(text="body one")]),
        MentorCard(parts=[Kicker(text="OPTION 2")]),
        MentorCard.banner_card("advisory", "note"),
    ]
    html = views.render_cards(cards)
    assert html.count('<div class="card">') == 3
    assert '<p class="banner advisory">note</p>' in html


def test_render_escapes_every_interpolated_value():
    html = views.render_cards(
        [
            MentorCard(
                parts=[
                    Para(text="<script>alert(1)</script>"),
                    Sub(text="<b>bold</b>"),
                    Pill(label="<i>x</i>"),
                    Banner(kind="warning", text="<u>y</u>"),
                ]
            )
        ]
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html
    assert "&lt;i&gt;x&lt;/i&gt;" in html
    assert "&lt;u&gt;y&lt;/u&gt;" in html


# --- GET / — the today dashboard (variant A) -------------------------------------


def test_home_renders_today_dashboard(repo):
    title, body, status = views.home_body(repo)
    assert status == 200
    assert title == "Today"
    # The P3 card-stack: focus card + count set (+ resumable line only
    # while a session is open) — ≤ 4 card-level blocks.
    assert '<div class="card focus">' in body
    assert '<div class="card counts">' in body
    assert body.count('<div class="card') <= 4
    # Exactly one primary CTA; zero tables; no <details> on the primary path.
    assert body.count('class="btn primary"') + body.count('class="btn"') == 1
    assert "<table" not in body
    assert "<details" not in body
    # Count set: labeled counts + one muted pointer; queue/pressure recede.
    assert "ready" in body
    assert "See what to study" in body
    # Zero-count pills are dropped (§A): the fresh seed has no practiced
    # days, so no practiced pill may render.
    assert "practiced" not in body
    assert "STUDY DAY PRESSURE" not in body  # recedes behind /next
    assert "60-MINUTE QUEUE" not in body  # recedes behind /next


def test_home_renders_fresh_per_request(repo):
    from skilltrace.commands.today import derive_today
    from skilltrace.context import load_context_lenient

    node_id = _first_node_id(repo)
    _, before, _ = views.home_body(repo)

    # Flip the *focus* node — Today's subject — and the page changes.
    view = load_context_lenient(repo)
    focus_id = derive_today(view, repo, minutes=30).focus_node_id
    assert focus_id is not None
    _set_state(repo, focus_id, "active")
    _, after_active, _ = views.home_body(repo)
    assert before != after_active

    # A curriculum edit + a state flip show on refresh too (this node).
    path = repo / "graph" / "nodes" / f"{node_id}.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("Summary for ", "Edited summary for "), encoding="utf-8")
    _set_state(repo, node_id, "active")
    node_page_title, node_html, status = views.node_body(repo, node_id)
    assert status == 200
    assert "Active" in node_html  # the state flip is visible (canonical word, P3.4)


def test_home_never_renders_the_raw_backlog(repo):
    """Pressure excerpts never render on Today (§A: the backlog recedes)."""
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
                    "description": "stuck on the derivation",
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    _, body, status = views.home_body(repo)
    assert status == 200
    assert "stuck on the derivation" not in body  # raw backlog never renders
    assert "blk.01" not in body



# --- GET /next — flags mirror the CLI --------------------------------------------


def test_next_defaults_mirror_cli_flags(repo):
    _, body, status = views.next_body(repo, {})
    assert status == 200
    assert "How much time do you have" in body  # honest control, no flag name
    assert "How many ideas do you want" in body
    kickers = [line for line in body.splitlines() if ">Option " in line]  # P3.6: sentence-case
    assert len(kickers) <= 5  # CLI default --limit 5


def test_next_minutes_and_limit_flags_apply(repo):
    _, body, _ = views.next_body(repo, {"minutes": ["90"], "limit": ["2"]})
    assert 'value="90"' in body
    assert 'value="2"' in body
    assert len([line for line in body.splitlines() if ">Option " in line]) <= 2  # P3.6


def test_next_bad_int_returns_400(repo):
    for bad in ({"minutes": ["abc"]}, {"limit": [""]}):
        _, _, status = views.next_body(repo, bad)
        assert status == 400


def test_next_show_locked_appends_locked_appendix(repo):
    # T4 §H: the locked half is always one disclosure card — titles plus
    # reasons, never an id dump; the empty state says so outright.
    _, without_locked, _ = views.next_body(repo, {})
    _, with_locked, _ = views.next_body(repo, {"locked": ["1"]})
    assert "Not ready yet" in without_locked
    assert "Not ready yet" in with_locked  # shipped seed graph has locked nodes
    # Each locked row names its unlock path in human words — never an id dump.
    assert "waiting on" in with_locked


def test_next_toggle_link_flips_show_locked(repo):
    # T4 §H: the locked half is a card, never a flag name — the same card
    # renders with and without the query param.
    _, off_body, _ = views.next_body(repo, {})
    _, on_body, _ = views.next_body(repo, {"locked": ["1"], "minutes": ["30"]})
    assert "Not ready yet" in off_body
    assert "Not ready yet" in on_body


def test_next_why_this_collapsible_is_advisory_only(repo):
    _, body, _ = views.next_body(repo, {})
    options = len([line for line in body.splitlines() if ">Option " in line])  # P3.6: sentence-case
    assert body.count("<details>") == options  # one collapsible per card
    assert body.count("Why this?") == options
    assert "never block a human-initiated action" in body


# --- GET /nodes/{id} — primary card plus drill-downs ------------------------------


def test_node_page_renders_primary_mentor_card(repo):
    node_id = _first_node_id(repo, state="available")
    title, body, status = views.node_body(repo, node_id)
    assert status == 200
    assert title != ""  # the page title is the node title
    # P3.6: ALL-CAPS kicker → sentence case ("THIS SKILL" → "This skill").
    assert '<div class="kicker">This skill</div>' in body
    # P3.4: canonical state word — 'Available', not the synonym 'Ready to start'.
    assert '<span class="pill available">Available</span>' in body
    assert "WHERE TO LEARN" not in body  # Mentor labels stay verbatim, not re-cased
    assert "Where to learn" in body
    # v2.4: the next action renders as the human affordance from the
    # NextAction fact (data-intent), not the CLI's "DO THIS NEXT" kicker.
    assert '<p class="next-action" data-intent="start">Start this session</p>' in body


def test_node_page_drill_down_sections(repo):
    node_id = _first_node_id(repo)
    _, body, _ = views.node_body(repo, node_id)
    assert "Drill-down" in body  # P3.6: sentence-case kicker
    assert "<details>" in body
    assert "Evidence" in body
    assert "Resources" in body


def test_graph_edge_links_use_ids_not_titles(repo):
    # Issue #228: the Graph edges drill-down once built hrefs from node
    # titles (which 404, since /nodes/{id} resolves by id). The label
    # shows the title; the href carries the id — and every href must
    # resolve on the server.
    import html as _html

    node_id = _first_node_id(repo)
    _, body, status = views.node_body(repo, node_id)
    assert status == 200
    if "Graph edges" not in body:
        return  # seeded node has no graph edges; nothing to check
    section = body.split("Graph edges", 1)[1].split("</details>", 1)[0]
    for raw in section.split('href="/nodes/')[1:]:
        target = _html.unescape(raw.split('"', 1)[0])
        assert " " not in target, f"href built from a title: /nodes/{target}"
        _, _, rstatus = views.node_body(repo, target)
        assert rstatus == 200, f"edge link 404s: /nodes/{target}"


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
    # T4 §H: the ambient headline opens the roll-up.
    assert "Everything looks good." in body or "Needs attention" in body


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
