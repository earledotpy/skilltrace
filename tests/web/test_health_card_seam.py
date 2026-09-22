"""The Health guidance cards render through the Card seam (#318).

What only the enforced seam can show:

* the five §C-ter cards are interface ``Card`` objects — composed by the
  pure derivation module (``web.health``), rendered by the one Card-to-HTML
  map (``interface.render``); no page-side producer owns card markup;
* the bespoke HTML renderer in the web health module is gone — the local
  escaper went with it, and the §C-ter guidance anatomy lives in exactly
  one place (the interface renderer's guidance variant);
* the guidance anatomy's bytes stay locked (golden route-body snapshots,
  #312, are the byte-exact evidence; this module pins the anatomy's shape
  directly on a hostile-valued card).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from skilltrace.web import health as web_health
from skilltrace.web import views
from skilltrace.web.interface.cards import Affordance, Card
from skilltrace.web.interface.render import render_guidance_cards
from skilltrace.web.views.health import _card_chrome

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB = REPO_ROOT / "src" / "skilltrace" / "web"
NODE_A = "math.arithmetic.order_operations_01"  # available in the seed


def _web_sources() -> dict[Path, str]:
    """Web module code text (docstrings and comments stripped), by path."""
    sources = {}
    for path in sorted(WEB.rglob("*.py")):
        text = re.sub(r'"""(?!").*?"""', "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        sources[path] = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("#")
        )
    return sources


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


# --- the derivation composes interface Cards ----------------------------------------


def test_guidance_page_cards_returns_interface_cards_with_the_derivation_copy():
    from skilltrace.context import load_context_lenient
    from skilltrace.execution.overdue import utc_today

    view = load_context_lenient(REPO_ROOT)
    guidance = web_health.derive_study_guidance(view, utc_today())
    cards, banner = web_health.guidance_page_cards(guidance)

    assert len(cards) == 5  # the §C-ter home hierarchy is locked
    assert all(isinstance(card, Card) for card in cards)
    assert [card.kicker for card in cards] == [
        "Stuck right now",
        "Due for review",
        "Evidence gaps",
        "Study rhythm",
        "Study resources",
    ]
    assert [card.why for card in cards] == [
        derivation_card.why for derivation_card in guidance.cards
    ]
    # The guidance card is a read-only mirror: the Richer-Card minimum
    # fields it must carry to be a Card at all ride neutral values.
    assert all(card.state == "active" for card in cards)
    assert all(
        card.affordances == (Affordance.from_intent("explore"),) for card in cards
    )
    expected_banner = (
        ("advisory", guidance.limited_data_line) if guidance.limited_data_line else None
    )
    assert banner == expected_banner


def test_derive_study_guidance_keeps_the_pure_derivation_record():
    import inspect

    source = inspect.getsource(web_health.derive_study_guidance)
    assert "Card" not in source  # the derivation stays untouched — composition is separate


# --- the bespoke renderer is gone ----------------------------------------------------


def test_the_local_renderer_is_gone_from_the_web_tree():
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path, source in _web_sources().items()
        if "render_guidance_html" in source
    ]
    assert offenders == []


def test_no_html_escaper_or_card_div_in_the_derivation_module():
    source = (WEB / "health.py").read_text(encoding="utf-8")
    assert "<div" not in source  # nothing here owns markup
    assert "esc(" not in source


def test_the_guidance_anatomy_lives_only_in_the_interface_renderer():
    # `<div class="card guidance">` is card markup — the one map owns it.
    # `guidance-links` is the links anatomy — the page's one attachment
    # composer owns it (escaping through the shared door).
    owners: dict[str, list[str]] = {"card guidance": [], "guidance-links": []}
    for path, source in _web_sources().items():
        rel = path.relative_to(REPO_ROOT).as_posix()
        for marker in owners:
            if marker in source:
                owners[marker].append(rel)
    assert owners["card guidance"] == ["src/skilltrace/web/interface/render.py"]
    assert owners["guidance-links"] == ["src/skilltrace/web/views/health.py"]


# --- the route renders through the seam ---------------------------------------------


def test_health_body_renders_the_derivation_cards_through_the_renderer(repo, monkeypatch):
    from skilltrace.web.views import health as health_view

    seen: list[list] = []
    real = health_view.render_guidance_cards

    def spy(cards, chromes=None, banner=None):
        seen.append(list(cards))
        return real(cards, chromes, banner)

    monkeypatch.setattr(health_view, "render_guidance_cards", spy)
    title, body, status = health_view.health_body(repo)
    assert status == 200 and title == "Health"
    assert seen, "the guidance cards never went through the interface renderer"
    assert all(isinstance(card, Card) for group in seen for card in group)


def test_guidance_links_render_inside_the_guidance_cards(repo):
    import yaml

    (repo / "execution").mkdir(exist_ok=True)
    (repo / "execution" / "blockers.yaml").write_text(
        yaml.safe_dump(
            {
                "blockers": [
                    {
                        "id": "blk.test.001",
                        "node_id": NODE_A,
                        "status": "open",
                        "description": "stuck on operator precedence",
                        "created_at": "2026-09-18T10:00:00+00:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    _, body, _ = views.health_body(repo)
    ul = body.index('<ul class="guidance-links">')
    card_start = body.rindex('<div class="card guidance">', 0, ul)
    card_close = body.index("</div>", ul)
    # the attachment renders inside the card div — nothing opens a new div
    # between the links list and the card's own close
    assert "<div" not in body[ul:card_close]
    assert card_start < ul < card_close


# --- the locked §C-ter anatomy, byte for byte ---------------------------------------


def test_the_guidance_anatomy_bytes_are_locked():
    derivation_card = web_health.GuidanceCard(
        title="Stuck <right> now",
        why="1 < 2 & 3",
        links=(("A <b> title", "/nodes/x&y?z"),),
        notes=("note ' quoted",),
    )
    cards, _ = web_health.guidance_page_cards(
        web_health.StudyGuidance(cards=(derivation_card,))
    )
    html = render_guidance_cards(
        cards, chromes={0: _card_chrome(derivation_card)}, banner="Limited <data> (1 sessions)"
    )
    assert html == (
        '<p class="banner advisory">Limited &lt;data&gt; (1 sessions)</p>\n'
        '<div class="card guidance">\n'
        "<div class=\"kicker\">Stuck &lt;right&gt; now</div>\n"
        "<p class=\"big\">1 &lt; 2 &amp; 3</p>\n"
        '<ul class="guidance-links">\n'
        '<li><a href="/nodes/x&amp;y?z">A &lt;b&gt; title</a></li>\n'
        "</ul>\n"
        "<p class=\"mut\">note &#x27; quoted</p>\n"
        "</div>\n"
    )


def test_anatomy_without_links_or_banner_stays_minimal():
    derivation_card = web_health.GuidanceCard(
        title="Evidence gaps", why=web_health.EVIDENCE_EMPTY
    )
    cards, _ = web_health.guidance_page_cards(
        web_health.StudyGuidance(cards=(derivation_card,))
    )
    html = render_guidance_cards(cards)
    assert html == (
        '<div class="card guidance">\n'
        "<div class=\"kicker\">Evidence gaps</div>\n"
        f'<p class="big">{web_health.EVIDENCE_EMPTY}</p>\n'
        "</div>\n"
    )
