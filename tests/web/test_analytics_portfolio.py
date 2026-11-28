"""Analytics and Portfolio v3 capability contracts (spec-v3-study-day §11.6–§11.7).

What only these surfaces show: the four analytics themes over real derived
facts with a table that carries the same values as the one chart, the
limited-data warning that retains those values, the empty/could-not-compute
states that never become zeros, and the Portfolio configurator whose
non-writing preview shows the redaction outcome before an explicitly
requested, dated disposable export leaves.

The named empty/limited/failure fixtures live in ``analytics_fixtures`` and
``portfolio_fixtures`` so the golden snapshots and the axe gate render the
same states.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest
import yaml
from analytics_fixtures import build_analytics_variant
from portfolio_fixtures import build_portfolio_variant
from test_route_snapshots import build_pinned_repo

from skilltrace.web import views
from skilltrace.web.views import analytics as analytics_view

THEMES = ("velocity", "blockers", "reviews", "evidence")


@pytest.fixture(scope="module")
def pinned() -> Path:
    """The pinned learner state shared by every focused assertion here."""
    return build_pinned_repo(Path(tempfile.mkdtemp(prefix="analytics-portfolio-")))


def _snapshot(root: Path) -> dict[str, bytes]:
    """Every truth file's bytes — what a read must never change."""
    paths = [
        *sorted((root / "graph").rglob("*.yaml")),
        *sorted((root / "graph").rglob("*.md")),
        *sorted((root / "evidence").rglob("*.yaml")),
        *sorted((root / "execution").rglob("*.yaml")),
        *sorted((root / "policy").rglob("*.yaml")),
    ]
    return {str(path.relative_to(root)): path.read_bytes() for path in paths}


# --- Analytics: four themes over real derived facts -------------------------


def test_exactly_four_themes_exist_and_are_definable() -> None:
    assert analytics_view.THEMES == THEMES


def test_each_theme_renders_its_derived_facts_and_a_table(pinned: Path) -> None:
    for theme in THEMES:
        title, body, status = views.analytics_body(pinned, {"theme": [theme]})
        assert (title, status) == ("Analytics", 200)
        assert f'aria-current="page">{theme.capitalize()}' in body
        assert '<div class="card analytics-card">' in body
        # Every theme is authoritative through a table (AX-9); only one
        # theme renders at a time.
        assert "<table" in body
        assert body.count('<div class="card analytics-card">') == 1


def test_the_velocity_chart_is_paired_with_the_same_values(pinned: Path) -> None:
    _, body, _ = views.analytics_body(pinned, {"theme": ["velocity"]})
    assert 'role="img"' in body
    assert "Weekly sessions with work" in body
    # Every plotted point appears verbatim in the visible weekly table.
    tips = re.findall(r'data-tip="(20\d\d-W\d\d): (\d+)"', body)
    assert len(tips) >= 2
    for week, count in tips:
        assert re.search(rf"<td>{week}</td>\s*<td>{count}</td>", body), (week, count)


def test_non_velocity_themes_render_no_chart(pinned: Path) -> None:
    for theme in ("blockers", "reviews", "evidence"):
        _, body, _ = views.analytics_body(pinned, {"theme": [theme]})
        assert "<svg" not in body, theme
        assert "data-tip=" not in body, theme


def test_available_data_says_the_threshold_was_met(pinned: Path) -> None:
    _, body, _ = views.analytics_body(pinned, {"theme": ["velocity"]})
    assert "Available data — 4 sessions in the last 30 days" in body
    assert "meeting the 3-session threshold" in body
    assert "Limited data" not in body


def test_limited_data_keeps_every_valid_value(pinned: Path) -> None:
    root = build_analytics_variant(pinned, "limited")
    for theme in THEMES:
        _, body, _ = views.analytics_body(root, {"theme": [theme]})
        assert "Limited data — fewer than 3 sessions in the last 30 days." in body
        assert "The recorded values are shown below." in body
        assert "<table" in body, theme
    _, velocity, _ = views.analytics_body(root, {"theme": ["velocity"]})
    assert "2 sessions, 75 minutes" in velocity


def test_empty_is_not_a_zero_and_has_no_limited_warning(pinned: Path) -> None:
    root = build_analytics_variant(pinned, "empty")
    for theme in THEMES:
        _, body, _ = views.analytics_body(root, {"theme": [theme]})
        assert "state-empty" in body, theme
        assert "Limited data" not in body, theme
        assert "0%" not in body, theme
        assert "<table" not in body, theme
    _, body, _ = views.analytics_body(root, {"theme": ["reviews"]})
    assert "no completion rate is computed" in body
    _, body, _ = views.analytics_body(root, {"theme": ["evidence"]})
    assert "no coverage rate is computed" in body


def test_a_failed_store_claims_no_numbers(pinned: Path) -> None:
    root = build_analytics_variant(pinned, "failure")
    _, body, _ = views.analytics_body(root, {"theme": ["velocity"]})
    assert "Analytics could not be worked out" in body
    assert "No numbers are being claimed" in body
    assert "sessions" in body
    assert "<table" not in body
    assert "0%" not in body


def test_no_prohibited_visual_or_composite_metric(pinned: Path) -> None:
    for theme in THEMES:
        _, body, _ = views.analytics_body(pinned, {"theme": [theme]})
        lowered = body.lower()
        for forbidden in (
            "gauge",
            "heatmap",
            "composite score",
            "target-attainment",
            "telemetry chart",
            "<meter",
            "<progress",
            'role="progressbar"',
        ):
            assert forbidden not in lowered, (theme, forbidden)


def test_analytics_never_writes_domain_state(pinned: Path) -> None:
    root = build_analytics_variant(pinned, "limited")
    before = _snapshot(root)
    for theme in THEMES:
        views.analytics_body(root, {"theme": [theme]})
    assert _snapshot(root) == before
    assert not (root / "data").exists()


# --- Portfolio: configurator, redaction preview, disposable export ----------


def test_portfolio_preview_is_non_writing(pinned: Path) -> None:
    root = build_portfolio_variant(pinned, "limited")
    before = _snapshot(root)
    _, body, status = views.portfolio_body(
        root, {"preview": ["1"], "node": ["programming.python.variables_01"]}
    )
    assert status == 200
    assert "Nothing was written" in body
    assert '<pre class="mono">' in body
    assert _snapshot(root) == before
    assert not (root / "data").exists()


def test_preview_shows_the_redaction_outcome_before_export(pinned: Path) -> None:
    root = build_portfolio_variant(pinned, "limited")
    _, body, _ = views.portfolio_body(
        root, {"preview": ["1"], "node": ["programming.python.variables_01"]}
    )
    assert "Redaction outcome" in body
    assert body.count("Redacted (default deny)") == 6
    assert "File paths redacted" in body
    assert "<pre class=\"mono\">" in body
    # The exact preview carries the honesty banner the selection earned.
    assert "[honesty]" in body
    assert "superseded evidence" in body

    _, revealed, _ = views.portfolio_body(
        root,
        {
            "preview": ["1"],
            "node": ["programming.python.variables_01"],
            "include_paths": ["1"],
        },
    )
    assert "File paths included" in revealed
    assert revealed.count("Redacted (default deny)") == 5


def test_preview_empty_selection_explains_itself(pinned: Path) -> None:
    root = build_portfolio_variant(pinned, "empty")
    _, body, _ = views.portfolio_body(root, {"preview": ["1"]})
    assert "This export has not been configured" in body
    assert 'action="/portfolio/export"' not in body

    # An explicit selection that matches nothing is a different state.
    _, no_match, _ = views.portfolio_body(
        root,
        {"preview": ["1"], "node": ["programming.python.variables_01"]},
    )
    assert "No skills match this selection" in no_match


def test_preview_failure_preserves_the_selection(pinned: Path) -> None:
    root = build_portfolio_variant(pinned, "failure")
    _, body, _ = views.portfolio_body(
        root,
        {
            "preview": ["1"],
            "node": ["programming.python.variables_01"],
            "include_paths": ["1"],
            "format": ["json"],
        },
    )
    assert "The preview could not be built" in body
    assert "Nothing was written and your selection is preserved" in body
    # The selection survives in the form and in the export's hidden fields.
    assert '<option value="json" selected>' in body
    assert '<input type="hidden" name="include_paths" value="1">' in body


def test_export_is_a_dated_disposable_snapshot_not_a_profile(pinned: Path) -> None:
    root = build_pinned_repo(Path(tempfile.mkdtemp(prefix="portfolio-export-")))
    _, body, _ = views.portfolio_body(
        root, {"node": ["programming.python.variables_01"]}
    )
    assert "dated, disposable snapshot" in body
    assert "it is not live truth" in body
    assert "not a user profile or an account" in body

    result = views.post_portfolio_export(
        root,
        {
            "next": ["/portfolio"],
            "format": ["md"],
            "node": ["programming.python.variables_01"],
            "include_paths": ["1"],
        },
    )
    assert isinstance(result, views.Redirect)
    bundles = sorted((root / "data").glob("portfolio-*"))
    assert len(bundles) == 1
    assert re.fullmatch(r"portfolio-\d{4}-\d{2}-\d{2}", bundles[0].name)
    events = yaml.safe_load(
        (root / "execution" / "events.yaml").read_text(encoding="utf-8")
    )["events"]
    assert [event["command"] for event in events].count("portfolio export") == 1


def test_an_explicit_skill_selection_reaches_the_preview(pinned: Path) -> None:
    """A checked skill is a real selection filter, exactly as the engine reads it."""
    root = build_pinned_repo(Path(tempfile.mkdtemp(prefix="portfolio-nodes-")))
    _, body, _ = views.portfolio_body(
        root,
        {
            "preview": ["1"],
            "node": ["programming.python.variables_01"],
        },
    )
    assert "Use variables and expressions in Python" in body
    assert "No skills match this selection" not in body


def test_export_without_a_selection_is_refused(pinned: Path) -> None:
    """Default-deny: nothing leaves until the learner names what to export."""
    root = build_pinned_repo(Path(tempfile.mkdtemp(prefix="portfolio-refuse-")))
    result = views.post_portfolio_export(
        root, {"next": ["/portfolio"], "format": ["md"]}
    )
    assert isinstance(result, views.Redirect)
    assert not (root / "data").exists()


def test_analytics_state_filter_rides_the_url(pinned: Path) -> None:
    _, body, status = views.analytics_body(
        pinned, {"theme": ["velocity"], "state": ["passed"]}
    )
    assert status == 200
    assert "states: passed" in body
    assert '<option value="passed" selected>passed</option>' in body

    _, bad, status = views.analytics_body(
        pinned, {"theme": ["velocity"], "state": ["nonsense"]}
    )
    assert status == 400
    assert "state filter" in bad.lower()
