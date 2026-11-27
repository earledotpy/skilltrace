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

import re
from pathlib import Path

from ...commands.health import health_report
from ...execution.overdue import utc_today
from ..health import (
    derive_study_guidance,
    guidance_page_cards,
)
from ..interface.cards import Affordance, Card
from ..interface.render import render_guidance_cards
from ._shared import _esc, _table, plural
from .sections import section
from .shell import _page_head

#: The layers a study-guidance card reads. If any of them did not load, the
#: section's facts are *unknown*, never empty or zero (SC-00a). ``events`` and
#: ``remediations`` are not read by any guidance card, so their absence claims
#: nothing here.
_GUIDANCE_SOURCES = frozenset(
    {
        "attempts",
        "blockers",
        "policies",
        "records",
        "resources",
        "reviews",
        "sessions",
        "specs",
        "work",
    }
)


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


def _plain_counts(counts: str) -> str:
    """The layer's counts in plain words, without the command's pluralisation.

    The validator prints ``45 resource(s)`` — the command's own shorthand.
    A learner-facing page says "45 resources".
    """
    return re.sub(r"\(s\)", "s", counts or "")


def _layer_headline(layer) -> str:
    """What this layer checks, in words.

    The layer's own line is the command the CLI would print. A page never
    shows a command, so the headline is the layer's subject instead.
    """
    target = layer.target or ""
    subject = target.split(".")[-1] if target else "checks"
    return f"the {subject} of the curriculum"


def _guidance_section(view) -> str:
    """The study-guidance projection — the learner's own facts.

    A source that did not load makes the section *unknown*, never empty and
    never zero: the cards claim what they were derived from, so a degraded
    source would turn "not known" into "none" (SC-00a). The section fails
    alone — Repository diagnostics below is a different projection and stays
    readable (spec-v3-study-day §11.5).
    """
    unavailable = sorted(_GUIDANCE_SOURCES & set(view.degraded))
    if unavailable:
        return _guidance_failure_section(unavailable)

    guidance = derive_study_guidance(view, utc_today())
    cards, banner = guidance_page_cards(guidance)
    return section(
        "Study guidance",
        "Your execution, evidence and retention facts. These describe your "
        "study, not your repository.",
        render_guidance_cards(
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
        ),
    )


def _guidance_failure_section(unavailable: list[str]) -> str:
    """Could-not-compute for study guidance: claim nothing, name the sources.

    The wording never reads as a learner problem and never becomes a warning
    about the learner: it is an operational failure of the repository's own
    records. The recovery path is a fresh load of this same page; the
    diagnostics section is unaffected.
    """
    names = ", ".join(unavailable)
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Study guidance</h2>\n'
        "</div>\n"
        '<div class="state state-failure">\n'
        '<p class="state-title">Study guidance could not be worked out</p>\n'
        '<p class="state-body">Some of the records behind these facts did not '
        "load, so nothing is claimed about your blockers, reviews, evidence "
        "gaps, study rhythm or resources — not even that any of them are zero. "
        "Nothing about your progress changed, and the repository diagnostics "
        "below are unaffected.</p>\n"
        '<p class="state-body">Sources unavailable: '
        f"<code>{_esc(names)}</code></p>\n"
        '<p>The repository diagnostics below name the source and its error. '
        '<a href="/health">Try loading this page again</a> once it is '
        "readable.</p>\n"
        "</div>\n"
        "</section>\n"
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
            f'<p class="state-body">The reason: '
            f"{_esc(_relative_detail(exc, root))}</p>\n"
            '<p><a href="/health">Try the checks again</a>.</p>\n'
            "</div>\n"
            "</section>\n"
        )

    rows = []
    details = []
    for layer in report.layers:
        counts = (
            _esc(_plain_counts(layer.counts))
            if layer.ok
            else "Not counted — this layer failed"
        )
        rows.append(
            [
                _esc(layer.target),
                counts,
                "ok" if layer.ok else "failing",
                _esc(_plain_counts(_layer_headline(layer))),
                _findings_summary(layer),
            ]
        )
        detail = _findings_details(layer, root)
        if detail:
            details.append(detail)

    failure_state = ""
    if not report.layers:
        failure_state = (
            '<div class="state state-failure">\n'
            '<p class="state-title">No layers were checked</p>\n'
            '<p class="state-body">The repository checks produced no layers, '
            "so nothing is reported. No health fact is being claimed.</p>\n"
            "</div>\n"
        )

    return section(
        "Repository diagnostics",
        "The curriculum's and the resources' integrity. These describe the "
        "repository, not your progress — and they never block anything you "
        "do.",
        failure_state
        + _table(
            ["Layer", "Counts", "Standing", "What was checked", "Findings"],
            rows,
        )
        + "".join(details),
        meta_markup=True,
    )


def _findings_phrase(layer) -> str:
    """One layer's own finding tally — never a total shared across layers.

    Errors and warnings stay split so a reader never has to guess which kind
    a merged count represents.
    """
    errors = len(layer.error_lines)
    warnings = layer.warning_count
    parts = []
    if errors:
        parts.append(f"{errors} error{plural(errors)}")
    if warnings:
        parts.append(f"{warnings} warning{plural(warnings)}")
    return ", ".join(parts)


def _findings_summary(layer) -> str:
    phrase = _findings_phrase(layer)
    return _esc(phrase) if phrase else "None"


def _relative_detail(line, root) -> str:
    """A validator finding with the repository root removed from its paths.

    The command's lines name the file that failed; a served page must name the
    *repository-relative* location, both because the absolute checkout path is
    noise to a learner and because the page must not depend on where the repo
    happens to live.
    """
    text = str(line)
    bases = {str(Path(root).resolve()), str(root)}
    for base in sorted(bases, key=len, reverse=True):
        text = text.replace(base.rstrip("/") + "/", "")
    return text


def _findings_details(layer, root) -> str:
    """The exact source/location detail behind one layer's findings.

    A diagnostic warns; it never becomes an acceptance authority, so this is
    plain technical detail behind a disclosure. Each line is escaped and
    shown verbatim (repository-relative) — a summarised diagnostic would hide
    the source a repository correction needs.
    """
    lines = [
        _relative_detail(line, root)
        for line in list(layer.error_lines) + list(layer.warning_lines)
    ]
    if not lines:
        return ""
    items = "".join(
        f'<li class="history-item"><code>{_esc(line)}</code></li>' for line in lines
    )
    phrase = _findings_phrase(layer)
    return (
        '<details class="disclosure">\n'
        f"<summary>{_esc(layer.target)} findings"
        f"{f' ({_esc(phrase)})' if phrase else ''}</summary>\n"
        f'<ul class="history-list">{items}</ul>\n'
        "</details>\n"
    )


# The page's intro card — the study-guidance opener, page chrome (#318).
# The five study-guidance cards below it are the §C-ter derivation; this
# one is the page's own constant copy introducing them, in the same
# guidance anatomy.
_ROLLUP_CARD = Card(
    state="active",
    title="Health",
    why="Two independent projections: your study guidance and the "
    "repository's diagnostics.",
    resources=[
        "Study guidance and repository diagnostics are separate projections."
    ],
    affordances=(Affordance.from_intent("explore"),),
    kicker="Health",
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
