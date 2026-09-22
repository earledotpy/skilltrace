"""
GET ``/next`` — grouped action-verb affordances, honestly
controlled (ADR 0009).

"""

from __future__ import annotations

from pathlib import Path

from ...commands.recommend import derive_next
from ..interface.cards import (
    ActiveViewState,
    view_by_name,
)
from ..interface.render import render_rich_cards
from ..interface.translate import (
    rich_cards as _rich_cards_from_model,
)
from ._shared import (
    _esc,
    _parse_int,
)
from .shell import (
    _page_head,
    _status_page,
)


def next_body(root, query: dict) -> tuple[str, str, int]:
    """GET `/next` — grouped action-verb affordances, honestly controlled (T4 §H).

    Honest controls (session window, option count, and a show-locked
    disclosure) replace the CLI mirror: flag names never render. ``Why
    this?`` is one human sentence plus an optional disclosure — ranker
    internals (scores, weights, leverage counts) stay hidden. A
    ``Not ready yet — and why`` card replaces the show-locked id dump;
    candidate titles are links (via the Card seam's ``node_id``).
    """
    minutes = _parse_int(query, "minutes", 60)
    limit = _parse_int(query, "limit", 5)
    if minutes is None or limit is None:
        body, status = _status_page(400, "Minutes and options must be numbers.", root)
        return "Next", body, status

    view, head, failure = _page_head(
        root, query, dismiss_path="/next", current_view="next"
    )
    if failure is not None:
        return failure

    # T4 §H: the locked half is the "Not ready yet — and why" card rather
    # than a flag, so the derivation always carries the locked candidates
    # (its own id-dump appendix is dropped in ``_candidate_stack``).
    model = derive_next(
        view, Path(root), minutes=minutes, limit=limit, show_locked=True
    )

    # Honest controls: the session window and option count phrased as
    # questions; the locked half is one disclosure card, never a flag name.
    filters = (
        '<div class="card">\n'
        '<form class="filters" method="get" action="/next">'
        f'<label>How much time do you have <input type="number" name="minutes" value="{minutes}" min="1" size="4"></label>'
        f'<label>How many ideas do you want <input type="number" name="limit" value="{limit}" min="1" size="3"></label>'
        '<button type="submit">Update ideas</button>'
        "</form>\n"
        "</div>\n"
    )

    locked_section = _not_ready_card(model, view)

    return (
        "Next",
        head
        + filters
        + _candidate_stack(view, model)
        + locked_section,
        200,
    )


def _not_ready_card(model, view) -> str:
    """The ``Not ready yet — and why`` card (T4 §H): titles + reasons, no ids."""
    if not model.locked:
        return (
            '<div class="card">\n'
            '<div class="kicker">Not ready yet — and why</div>\n'
            "<p>Everything in reach is already listed above.</p>\n"
            "</div>\n"
        )
    return (
        '<div class="card">\n'
        '<div class="kicker">Not ready yet — and why</div>\n'
        f"{_not_ready_list(model, view)}\n"
        "</div>\n"
    )


def _not_ready_list(model, view) -> str:
    """The locked rows: titles + states in human words, never raw ids.

    The derivation's own ``LockedCandidate.reason`` carries node ids and a
    CLI-voice hint, so the web composes the reason from the structured
    ``unsatisfied`` pairs instead (P3.1/P3.2).
    """
    rows = []
    for cand in model.locked:
        title = view.titles.get(cand.node_id) or "Another skill"
        if cand.unsatisfied:
            waiting = ", ".join(
                f"{view.titles.get(pid) or 'an earlier skill'} ({state})"
                for pid, state in cand.unsatisfied
            )
            reason = f"waiting on {waiting}"
        else:
            reason = "its readiness looks out of date — sync your readiness"
        rows.append(f"<li><strong>{_esc(title)}</strong> — {_esc(reason)}</li>")
    return f"<ul>{''.join(rows)}</ul>"


def _why_details(rec) -> str:
    """``Why this?`` — one human sentence plus an optional disclosure (T4 §H).

    Ranker internals (scores, weights, leverage counts, session-fit flags)
    never render: the candidate cards already carry the one-line why, and
    the advisory note is the only disclosure.
    """
    return (
        "<details>\n<summary>Why this?</summary>\n"
        f'<div class="sub">{_esc(rec.reason)}</div>\n'
        '<p class="mut">Advisory reasoning — policies reorder recommendations; '
        "they never block a human-initiated action.</p>\n</details>\n"
    )


def _candidate_stack(view, model) -> str:
    """Candidate Richer Cards with the per-card advisory "Why this?" attached.

    Candidates are the OPTION cards in the derivation's order; the k-th
    such card receives model.recommendations[k]'s reasoning as its
    attached facts block. Banner/appendix cards ride the banner channel —
    except the derivation's ``locked`` appendix, whose id dump is replaced
    by the page's own ``Not ready yet — and why`` card (T4 §H, P3.2).
    """
    cards, banners = _rich_cards_from_model(model.cards, titles=view.titles)
    banners = [(kind, text) for kind, text in banners if kind != "locked"]
    rec_iter = iter(model.recommendations)
    extras: dict[int, str] = {}
    for index, card in enumerate(cards):
        if (card.kicker or "").strip().upper().startswith("OPTION"):
            rec = next(rec_iter, None)
            if rec is not None:
                extras[index] = _why_details(rec)
    return render_rich_cards(
        cards,
        banners,
        state=ActiveViewState(view=view_by_name("next")),
        extras=extras,
    )

