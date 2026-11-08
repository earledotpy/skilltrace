"""
GET ``/health`` — the Health capability (spec-v3-study-day §11.5).

Health is **exactly two explicitly named, independent projections** — never
an aggregate:

* **Study guidance** — the learner's execution, evidence and retention
  facts. It links findings to the owning SkillNodes or records and may
  offer only canonical learner commands.
* **Repository diagnostics** — the curriculum's and the resources'
  integrity.

There is **no composite Health score**, no shared warning total and no
cross-source severity (VS-10): a warning in the curriculum never reads as
a problem with the learner, and a learner fact never counts as a
repository fault. Diagnostics **warn**; they never become acceptance
authority.

A source that could not load is an operational failure with a precise
recovery path — never a zero and never a fabricated health fact (SC-00a).
"""

from __future__ import annotations

from ...commands.health import health_report
from ...execution.overdue import utc_today
from ..health import (
    derive_study_guidance,
    guidance_page_cards,
)
from ..interface.cards import Affordance, Card
from ..interface.render import render_guidance_cards
from ._shared import _esc, _table
from .shell import _page_head


def health_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/health` — study guidance and repository diagnostics, kept apart."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/health",
        current_view="health",
        default_mode="operations",
        path="/health",
    )
    if failure is not None:
        return failure

    body = head + _guidance_section(view) + _diagnostics_section(root)
    return "Health", body, 200


def _guidance_section(view) -> str:
    """The study-guidance projection — the learner's own facts."""
    guidance = derive_study_guidance(view, utc_today())
    cards, banner = guidance_page_cards(guidance)
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Study guidance</h2>\n'
        '<p class="section-meta">Your execution, evidence and retention '
        "facts. These describe your study, not your repository.</p>\n"
        "</div>\n"
        + render_guidance_cards(
            [_ROLLUP_CARD],
            chromes={0: _ROLLUP_CHROME},
        )
        + render_guidance_cards(
            cards,
            chromes={
                index: _card_chrome(derivation_card)
                for index, derivation_card in enumerate(guidance.cards)
            },
            banner=banner[1] if banner else None,
        )
        + "</section>\n"
    )


def _diagnostics_section(root) -> str:
    """The repository-diagnostics projection — the curriculum's integrity.

    Each validator layer reports its own state. The layers are listed
    separately: there is no composite score and no shared warning total,
    so a warning here never reads as a problem with the learner.
    """
    try:
        report = health_report(root)
    except Exception as exc:  # noqa: BLE001 — an operational failure, not a zero
        return (
            '<section class="section">\n'
            '<div class="section-head">\n'
            '<h2 class="section-title">Repository diagnostics</h2>\n'
            "</div>\n"
            '<div class="state state-failure">\n'
            '<p class="state-title">Diagnostics could not be run</p>\n'
            '<p class="state-body">The repository checks did not run, so '
            "nothing is reported here. No health fact is being claimed, and "
            "your study guidance above is unaffected.</p>\n"
            f'<p class="state-body">The reason: {_esc(str(exc))}</p>\n'
            "</div>\n"
            "</section>\n"
        )

    rows = []
    for layer in report.layers:
        rows.append(
            [
                _esc(layer.target),
                _esc(layer.counts),
                "ok" if layer.ok else "failing",
                _esc(layer.line),
            ]
        )

    failure_state = ""
    if not report.layers:
        failure_state = (
            '<div class="state state-failure">\n'
            '<p class="state-title">No layers were checked</p>\n'
            '<p class="state-body">The repository checks produced no layers, '
            "so nothing is reported. No health fact is being claimed.</p>\n"
            "</div>\n"
        )

    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Repository diagnostics</h2>\n'
        '<p class="section-meta">The curriculum\'s and the resources\' '
        "integrity. These describe the repository, not your progress — and "
        "they never block anything you do.</p>\n"
        "</div>\n"
        + failure_state
        + _table(["Layer", "Counts", "Standing", "What was checked"], rows)
        + "</section>\n"
    )


# The page's intro card — the study-guidance opener, page chrome (#318).
# The five study-guidance cards below it are the §C-ter derivation; this
# one is the page's own constant copy introducing them, in the same
# guidance anatomy.
_ROLLUP_CARD = Card(
    state="active",
    title="Health roll-up",
    why="Your study guidance for today.",
    resources=["The Health page is study guidance only."],
    affordances=(Affordance.from_intent("explore"),),
    kicker="Health roll-up",
)
_ROLLUP_CHROME = (
    '<p class="mut">Study guidance and repository diagnostics are two '
    "separate projections — there is no overall score, and nothing here "
    "blocks your next move.</p>\n"
)


def _card_chrome(card) -> str:
    """One guidance card's links and notes — the per-card attachment.

    The §C-ter guidance anatomy (links list, muted notes) rides the
    renderer's per-card raw-markup channel. Values escape through the one
    door here, exactly as every other attachment does.
    """
    parts: list[str] = []
    if card.links:
        parts.append('<ul class="guidance-links">\n')
        for label, href in card.links:
            parts.append(f'<li><a href="{_esc(href)}">{_esc(label)}</a></li>\n')
        parts.append("</ul>\n")
    if card.notes:
        parts.extend(f'<p class="mut">{_esc(note)}</p>\n' for note in card.notes)
    return "".join(parts)
