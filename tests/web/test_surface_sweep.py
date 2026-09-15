"""T4 — Surface sweep with per-surface visual gates (issue #235, map #231).

Asserts the locked section-H treatment on the live routes now that the
section-B tokens (T1), the de-CLI copy register (T2) and the Richer Card
seam (T3) are in place: Today card-stack, Next affordances, node collapse,
health ambient register, analytics one-theme page, chrome groups, and the
unified error body. ``pytest`` green; no ``<script>``.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pytest

from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.interface import VIEWS

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's GET sweeps."""
    root = Path(tempfile.mkdtemp(prefix="t4-surface-sweep-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _first_node_id(root: Path, *, state: str | None = None) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError(f"no node with state {state!r}")


def _header(body: str) -> str:
    start = body.index("<header>")
    return body[start : body.index("</header>") + len("</header>")]


def _nav(body: str) -> str:
    """Only the nav groups — the header's health pill strip is not a nav stop."""
    return "".join(re.findall(r"<nav\b.*?</nav>", _header(body), re.S))


def test_today_display_heading_present_only_on_today(repo):
    home = views.home_body(repo)[1]
    assert home.count('<p class="display">') == 1
    node_id = _first_node_id(repo, state="available")
    for name, html in (
        ("next", views.next_body(repo, {})[1]),
        ("node", views.node_body(repo, node_id)[1]),
        ("health", views.health_body(repo)[1]),
        ("analytics", views.analytics_body(repo, {})[1]),
    ):
        assert '<p class="display">' not in html, name


def test_today_zero_tables_no_details_bounded_cards_one_cta(repo):
    _, body, _ = views.home_body(repo)
    assert "<table" not in body
    assert "<details" not in body
    assert body.count('<div class="card') <= 4
    assert body.count('class="btn primary"') == 1


def test_today_focus_named_once_and_pronoun_cta(repo):
    from skilltrace.commands.today import derive_today

    view = load_context_lenient(repo)
    model = derive_today(view, repo)
    assert model.focus_node_id, "seed carries a focus for the Today sweep"
    title = view.node_map[model.focus_node_id].title
    _, body, _ = views.home_body(repo)
    # Exactly one card-level block presents the focus (the card-stack shape:
    # no competing queue/pressure block repeats it).
    blocks = body.split('<div class="card')[1:]
    assert sum(1 for block in blocks if title in block) == 1
    # The single primary CTA speaks in pronoun form (§E/T2 label).
    assert "Start this session" in body
    assert "Start studying" not in body


def test_today_counts_drop_zero_pills_and_hide_the_backlog(repo):
    _, body, _ = views.home_body(repo)
    section = body.split('<div class="card counts">', 1)[1].split("</div>", 1)[0]
    assert "0 reviews" not in section
    assert "backlog lineup" not in body
    assert "What is today about?" in body


def test_today_resumable_line_only_while_a_session_is_open(repo):
    assert "Resume your open session" not in views.home_body(repo)[1]


def test_next_candidate_titles_are_links(repo):
    _, body, _ = views.next_body(repo, {})
    assert re.search(r'<p class="lead"><a href="/nodes/[^"]+">[^<]+</a></p>', body), (
        "candidate titles must be anchors (T4 section-H)"
    )


def test_next_has_no_flag_text(repo):
    for params in ({}, {"locked": ["1"]}):
        _, body, _ = views.next_body(repo, params)
        lowered = body.lower()
        for flag in ("--minutes", "--limit", "--show-locked", "show-locked", "show locked"):
            assert flag not in lowered, params
        assert "skilltrace next" not in body


def test_next_why_this_is_one_sentence_plus_disclosure(repo):
    _, body, _ = views.next_body(repo, {})
    for hidden in ("track weight", "downstream leverage", "fits session", "remediation boost"):
        assert hidden not in body
    assert "Why this?" in body
    assert "never block a human-initiated action" in body


def test_next_not_ready_card_replaces_the_id_dump(repo):
    _, body, _ = views.next_body(repo, {"locked": ["1"]})
    assert "Not ready yet" in body
    assert "Locked (" not in body


def test_node_single_muted_id_and_single_mono_use(repo):
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    assert f'<p class="small mut">{node_id}</p>' in body
    assert body.count("<code>") <= 1


def test_node_pass_requirements_stated_once(repo):
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    assert body.count("How to proceed") <= 1


def test_node_noop_evidence_form_omitted(repo):
    view = load_context_lenient(repo)
    gateless = [n.id for n in view.nodes if n.id not in view.has_gate]
    assert gateless, "fixture graph has a gateless node for the no-op check"
    _, body, _ = views.node_body(repo, sorted(gateless)[0])
    assert "Submit your next piece of evidence" not in body


def test_nothing_marked_current_on_node_pages(repo):
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    assert 'aria-current="page"' not in _nav(body)


def test_health_ambient_headline_and_warning_counts(repo):
    _, body, status = views.health_body(repo)
    assert status == 200
    assert "Everything looks good." in body or "Needs attention" in body
    assert "Warnings" in body


def test_health_absent_from_nav_but_reachable_from_the_pill(repo):
    _, home, _ = views.home_body(repo)
    assert 'href="/health"' not in _nav(home)
    header = _header(home)
    assert "Full roll-up" in header
    assert 'href="/health"' in header


def test_analytics_theme_switch_is_server_rendered_links(repo):
    _, body, _ = views.analytics_body(repo, {})
    assert body.count('<div class="card analytics-card">') == 1
    assert "theme=blockers" in body
    assert "theme=velocity" in body  # the segmented control is plain links
    assert "<script" not in body.lower()
    # The theme's tables/rows live collapsed behind the one disclosure.
    assert "<details>" in body
    assert "<details open" not in body


def test_analytics_real_multipoint_svg_only(repo):
    _, body, _ = views.analytics_body(repo, {})
    assert body.count("<svg") == 1


def test_chrome_brand_two_nav_groups_and_seam_current(repo):
    _, body, _ = views.home_body(repo)
    nav = _nav(body)
    header = _header(body)
    assert "SkillTrace" in header
    assert nav.count("<nav") == 2
    assert 'aria-label="Daily loop"' in nav
    assert 'aria-label="Periodic"' in nav
    assert 'href="/health"' not in nav
    assert nav.count('aria-current="page"') == 1


def test_unified_full_chrome_error_body(repo):
    not_found, status_404 = views._status_page(404, "Unknown node x.", repo)
    failure, status_500 = views._status_page(500, "Boom.", repo)
    assert (status_404, status_500) == (404, 500)
    for html in (not_found, failure):
        assert "<header>" in html and "SkillTrace" in html
        assert "Back to Today" in html
        assert "Something went wrong" in html


def test_no_unterminated_class_attribute_anywhere(repo):
    """Every rendered page's `class` attributes are closed (markup hygiene)."""
    node_id = _first_node_id(repo, state="available")
    pages = {
        "home": views.home_body(repo)[1],
        "next": views.next_body(repo, {})[1],
        "next locked": views.next_body(repo, {"locked": ["1"]})[1],
        "node": views.node_body(repo, node_id)[1],
        "health": views.health_body(repo)[1],
        "analytics": views.analytics_body(repo, {})[1],
        "pass": views.pass_modal_body(repo, node_id)[1],
        "404": views._status_page(404, "Unknown node x.", repo)[0],
    }
    pattern = re.compile(r'class="[^">]*>')
    for name, html in pages.items():
        assert not pattern.search(html), f"{name}: unterminated class attribute"


def test_no_script_anywhere_until_s5(repo):
    # Per-route budget held so far (ADR 0008): no route emits <script> until
    # S5 grants the single /analytics tooltip script (DD6 goes green in S5).
    node_id = _first_node_id(repo, state="available")
    bodies = [
        views.home_body(repo)[1],
        views.next_body(repo, {})[1],
        views.node_body(repo, node_id)[1],
        views.health_body(repo)[1],
        views.analytics_body(repo, {})[1],
    ]
    for html in bodies:
        assert "<script" not in html.lower()


def test_frozen_route_table_gains_master_confirm_and_periodic_group():
    assert VIEWS["master-confirm"].route == "/nodes/{id}/master/confirm"
    assert VIEWS["analytics"].group == "periodic"
    assert VIEWS["health"].group is None
    assert set(VIEWS) == {
        "today",
        "next",
        "node",
        "finder",
        "health",
        "analytics",
        "node pass",
        "node master",
        "master-confirm",
    }
