"""T4 — the v3 surface sweep (docs/spec-v3-study-day.md §5, §6, §7, §8).

What only this module shows: the **shell** contract every served surface
inherits — the mode-aware chrome, the section navigation that follows the
mode, the current-section seam, the skip link and the focus ring, the one
unified error body, markup hygiene, the tier-0 script budget, and the
view seam's route table.

The per-surface contracts live with their own surfaces (the Today queue,
the discovery surfaces, the node detail, the safety panels); this module
asserts only what every surface shares. The v2.4 chrome — two nav
groups, a health pill strip, a serif/sans split — is superseded history
(spec §20 SUP-4, SUP-5).
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
    """Only the nav groups — the mode switch is chrome, not a nav stop."""
    return "".join(re.findall(r"<nav\b.*?</nav>", _header(body), re.S))


# --- the chrome: one shell, two modes --------------------------------------------


def test_the_chrome_carries_the_brand_and_the_mode_switch(repo):
    """One URL-addressable shell carries both modes (IA-1)."""
    _, body, _ = views.home_body(repo)
    header = _header(body)
    assert "SkillTrace" in header
    assert "mode=guided" in header
    assert "mode=operations" in header
    assert header.count('class="mode-switch"') == 1


def test_the_section_navigation_follows_the_mode(repo):
    """Guided shows the task-led destinations; Operations the capabilities."""
    _, guided, _ = views.home_body(repo, {})
    guided_nav = _nav(guided)
    assert 'aria-label="Guided"' in guided_nav
    assert 'href="/next"' in guided_nav
    assert 'href="/find"' in guided_nav
    assert 'href="/graph"' not in guided_nav

    _, operations, _ = views.operations_body(repo, {})
    operations_nav = _nav(operations)
    assert 'aria-label="Operations"' in operations_nav
    for capability in ("/graph", "/evidence", "/reviews", "/health", "/analytics"):
        assert f'href="{capability}"' in operations_nav, capability
    assert 'href="/portfolio"' in operations_nav


def test_the_mode_switch_preserves_the_destination_and_its_context(repo):
    """Switching mode changes the presentation, never the destination (IA-4)."""
    _, body, _ = views.next_body(repo, {"minutes": ["45"]})
    header = _header(body)
    # The switch keeps the path and the filter; it only changes the mode.
    assert "/next?minutes=45&amp;mode=operations" in header or (
        "/next?mode=operations" in header and "minutes=45" in header
    )
    assert "mode=guided" in header


def test_a_bare_deep_link_renders_a_sensible_default_presentation(repo):
    """Mode rides a URL parameter, so a bare link still lands somewhere sane."""
    for name, body in (
        ("today", views.home_body(repo)[1]),
        ("graph", views.graph_body(repo)[1]),
        ("health", views.health_body(repo)[1]),
    ):
        assert "mode-guided" in _mode_class(body) or "mode-operations" in _mode_class(
            body
        ), name


def _mode_class(body: str) -> str:
    """The body mode class of a rendered page (``page()`` sets it)."""
    html = views.page("t", body)
    match = re.search(r'<body class="(mode-[a-z]+)">', html)
    return match.group(1) if match else ""


def test_an_unknown_mode_falls_back_to_the_route_default(repo):
    """A mistyped parameter must never dead-end a deep link.

    The fallback is the *route's* default, read from the declared view
    seam — so an Operations capability stays in its own register and a
    Guided destination stays in its own.
    """
    from skilltrace.web.views.shell import _mode_from, route_default_mode

    assert route_default_mode("/health") == "operations"
    assert route_default_mode("/today") == "guided"
    assert route_default_mode("/nodes/some.id") == "guided"
    assert route_default_mode("/nodes/some.id/pass") == "guided"

    assert _mode_from({"mode": ["nonsense"]}, route_default_mode("/health")) == (
        "operations"
    )
    assert _mode_from({"mode": ["nonsense"]}, route_default_mode("/today")) == (
        "guided"
    )
    assert _mode_from({"mode": ["operations"]}, route_default_mode("/today")) == (
        "operations"
    )


def test_the_current_section_is_marked_exactly_once(repo):
    """``aria-current`` comes from the declared view seam, not the path."""
    node_id = _first_node_id(repo, state="available")
    nav_stops = {
        "today": views.home_body(repo)[1],
        "next": views.next_body(repo, {})[1],
        "find": views.finder_body(repo, {})[1],
        "operations": views.operations_body(repo)[1],
        "graph": views.graph_body(repo)[1],
    }
    for name, html in nav_stops.items():
        assert _nav(html).count('aria-current="page"') == 1, name
    # A destination that is not a nav stop marks nothing.
    for name, html in (
        ("node", views.node_body(repo, node_id)[1]),
        ("pass", views.pass_modal_body(repo, node_id)[1]),
    ):
        assert 'aria-current="page"' not in _nav(html), name


def test_the_view_seam_carries_the_v3_route_table():
    """The seam is the route table's one source of truth (ARC-5)."""
    assert VIEWS["master-confirm"].route == "/nodes/{id}/master/confirm"
    assert VIEWS["find"].route == "/find"
    assert VIEWS["session"].route == "/session"
    assert VIEWS["operations"].route == "/operations"
    assert VIEWS["portfolio"].route == "/portfolio"
    assert VIEWS["health"].group == "operations"
    assert VIEWS["analytics"].group == "operations"
    assert VIEWS["health"].default_mode == "operations"
    assert VIEWS["today"].default_mode == "guided"


# --- the shell's accessibility floor --------------------------------------------


def test_shell_skip_link_focus_ring_and_main_target(repo):
    """One focus rule, a skip link as the first body element, one main."""
    assert views._STYLE.count(":focus-visible{") == 1
    assert "outline:2px solid var(--status-focus)" in views._STYLE
    html = views.page("t", "<header></header><p>x</p>")
    assert html.index('class="skip" href="#content"') < html.index("<header>")
    assert '<main class="shell" id="content">' in html
    for name, body in (
        ("home", views.home_body(repo)[1]),
        ("next", views.next_body(repo, {})[1]),
        ("health", views.health_body(repo)[1]),
    ):
        full = views.page("t", body)
        assert full.count('class="skip" href="#content"') == 1, name
        assert '<main class="shell" id="content">' in full, name


def test_the_unified_full_chrome_error_body(repo):
    """404 and 500 share the one error body (IC-7)."""
    not_found, status_404 = views._status_page(404, "Unknown node x.", repo)
    failure, status_500 = views._status_page(500, "Boom.", repo)
    assert (status_404, status_500) == (404, 500)
    for html in (not_found, failure):
        assert "<header>" in html and "SkillTrace" in html
        assert "Back to Today" in html
        assert "Something went wrong" in html


# --- tier 0: no script outside the one grant -------------------------------------


def test_per_route_script_budget_analytics_velocity_only(repo):
    """Only the granted analytics tooltip script exists (ADR 0008)."""
    node_id = _first_node_id(repo, state="available")
    plain = [
        views.home_body(repo)[1],
        views.next_body(repo, {})[1],
        views.node_body(repo, node_id)[1],
        views.health_body(repo)[1],
        views.operations_body(repo)[1],
        views.graph_body(repo)[1],
        views.reviews_body(repo)[1],
        views.session_body(repo)[1],
    ]
    for html in plain:
        assert "<script" not in html.lower()
    _, velocity, _ = views.analytics_body(repo, {"theme": ["velocity"]})
    assert len(re.findall(r"<script\b", velocity, re.IGNORECASE)) == 1
    for theme in ("blockers", "reviews", "evidence"):
        _, body, _ = views.analytics_body(repo, {"theme": [theme]})
        assert "<script" not in body.lower(), theme


# --- markup hygiene ---------------------------------------------------------------


def test_no_unterminated_class_attribute_anywhere(repo):
    """Every rendered page's ``class`` attributes are closed."""
    node_id = _first_node_id(repo, state="available")
    pages = {
        "home": views.home_body(repo)[1],
        "next": views.next_body(repo, {})[1],
        "node": views.node_body(repo, node_id)[1],
        "health": views.health_body(repo)[1],
        "analytics": views.analytics_body(repo, {})[1],
        "session": views.session_body(repo)[1],
        "session close": views.session_close_body(repo)[1],
        "evidence index": views.evidence_index_body(repo)[1],
        "reviews": views.reviews_body(repo)[1],
        "operations": views.operations_body(repo)[1],
        "graph": views.graph_body(repo)[1],
        "portfolio": views.portfolio_body(repo)[1],
        "pass": views.pass_modal_body(repo, node_id)[1],
        "404": views._status_page(404, "Unknown node x.", repo)[0],
    }
    pattern = re.compile(r'class="[^">]*>')
    for name, html in pages.items():
        assert not pattern.search(html), f"{name}: unterminated class attribute"


def test_no_cli_vocabulary_leaks_into_the_shell(repo):
    """No surface speaks in command-line vocabulary (P3.1)."""
    node_id = _first_node_id(repo, state="available")
    pages = [
        views.home_body(repo)[1],
        views.next_body(repo, {})[1],
        views.node_body(repo, node_id)[1],
        views.health_body(repo)[1],
        views.operations_body(repo)[1],
        views.graph_body(repo)[1],
        views.reviews_body(repo)[1],
        views.portfolio_body(repo)[1],
    ]
    for html in pages:
        lowered = html.lower()
        for vocabulary in ("skilltrace next", "skilltrace serve", "--show-locked"):
            assert vocabulary not in lowered, vocabulary
