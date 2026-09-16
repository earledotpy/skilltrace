"""T4 — Surface sweep with per-surface visual gates (issue #235, map #231).

Asserts the locked section-H treatment on the live routes now that the
section-B tokens (T1), the de-CLI copy register (T2) and the Richer Card
seam (T3) are in place: the unified single-page home (amended §A — hero +
six-card bento, map #252), Next affordances, node collapse,
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


def test_rich_home_blocks_one_cta_and_one_table(repo):
    # Amended P5.3 (G-Preferences #247): rich-home cap ≤8 blocks, one CTA,
    # ≤1 grouped-count table; disclosures stay off the primary path.
    _, body, _ = views.home_body(repo)
    assert body.count("<table") <= 1
    assert body.count('class="btn primary"') == 1
    assert "<details" not in body
    blocks = body.count('<div class="hero">') + body.count('<div class="bento-card ')
    assert blocks <= 8


def test_today_focus_named_once_with_pronoun_cta(repo):
    from skilltrace.commands.today import derive_today

    view = load_context_lenient(repo)
    model = derive_today(view, repo)
    assert model.focus_node_id, "seed carries a focus for the Today sweep"
    title = view.node_map[model.focus_node_id].title
    _, body, _ = views.home_body(repo)
    # P1.1a as amended: the focus title appears once as a heading, plus at
    # most one locator repetition (the spine); the CTA is the pronoun form.
    assert body.count('<p class="display">') == 1
    assert body.count(title) <= 2
    assert "Start studying" in body
    assert f"Start studying {title}" not in body  # never `Start <title>`
    assert "Start this session" not in body


def test_today_drops_zero_counts_and_the_raw_backlog(repo):
    _, body, _ = views.home_body(repo)
    assert "0 reviews" not in body  # zero-count pills dropped (P1.3)
    assert "backlog lineup" not in body
    # Amended P1.2: ranked preview rows are permitted; the raw flat dump is not.
    assert body.count('class="queue-row"') <= 4
    assert "What is today about?" not in body  # the hero names the focus itself


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
    # Per-route budget (ADR 0008): at most the one granted tooltip script,
    # coupled to the real multi-point chart.
    assert len(re.findall(r"<script\b", body, re.IGNORECASE)) <= 1
    assert ("<script" in body.lower()) == ('data-tip="' in body)
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


def test_seam_current_exactly_once_where_nav_stop_zero_elsewhere(repo):
    # P-A11yShell (map 258): the seam marks exactly one nav link on nav-stop
    # views (today/next/analytics) and none on node, finder, or health —
    # never on the finder form, the health strip, or a flash line.
    node_id = _first_node_id(repo, state="available")
    one = {
        "home": views.home_body(repo)[1],
        "next": views.next_body(repo, {})[1],
        "analytics": views.analytics_body(repo, {})[1],
    }
    zero = {
        "node": views.node_body(repo, node_id)[1],
        "finder": views.finder_body(repo, {})[1],
        "health": views.health_body(repo)[1],
    }
    for name, html in one.items():
        assert _nav(html).count('aria-current="page"') == 1, name
    for name, html in zero.items():
        assert 'aria-current="page"' not in _nav(html), name
        assert 'aria-current="page"' not in _header(html), name
    for name, html in {**one, **zero}.items():
        assert 'aria-current="page"' not in views._flash_html(
            {"notice": ["x"], "kind": ["ok"]}, "/"
        ), name


def test_shell_skip_link_focus_ring_and_main_target(repo):
    # P-A11yShell (map 258): one :focus-visible accent rule, a skip link as
    # the first body element targeting main, on every surface via page().
    assert views._STYLE.count(":focus-visible{") == 1
    assert "outline:2px solid var(--accent)" in views._STYLE
    html = views.page("t", "<header></header><p>x</p>")
    assert html.index('class="skip" href="#content"') < html.index("<header>")
    assert '<main class="wrap" id="content">' in html
    for name, body in (
        ("home", views.home_body(repo)[1]),
        ("next", views.next_body(repo, {})[1]),
        ("health", views.health_body(repo)[1]),
    ):
        full = views.page("t", body)
        assert full.count('class="skip" href="#content"') == 1, name
        assert '<main class="wrap" id="content">' in full, name


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


def test_per_route_script_budget_analytics_velocity_only(repo):
    # Per-route budget (ADR 0008, landed): home/next/node/health emit no
    # script; the /analytics velocity chart carries exactly the one granted
    # tooltip script (DD6 goes green with the grant implemented).
    node_id = _first_node_id(repo, state="available")
    plain = [
        views.home_body(repo)[1],
        views.next_body(repo, {})[1],
        views.node_body(repo, node_id)[1],
        views.health_body(repo)[1],
    ]
    for html in plain:
        assert "<script" not in html.lower()
    _, velocity, _ = views.analytics_body(repo, {"theme": ["velocity"]})
    assert len(re.findall(r"<script\b", velocity, re.IGNORECASE)) == 1
    for theme in ("blockers", "reviews", "evidence"):
        _, body, _ = views.analytics_body(repo, {"theme": [theme]})
        assert "<script" not in body.lower(), theme


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
