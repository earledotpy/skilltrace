"""
The contextual inspector (spec-v3-study-day §6 RT note 2, §11.2).

The inspector has **no route of its own**. It renders inside the route that
owns the fact, and the selected context rides a URL parameter of that route
(``/evidence?record=<id>``), so a view can be shared or reloaded exactly as
it was seen. A selection is presentation context, never domain state: nothing
about it is written, and no page load, link or reload is a learner command
(HB-6).

What it may show is canonical facts only — the ``EvidenceRecord``, its
derived standing (live / superseded / rejected), the ``SkillNode`` and
``ArtifactSpec`` it belongs to, the ``ValidationGate`` that judged it, and
its recent event provenance. The event log is read here for display only; it
is still never read to compute state.

A selection that names no record in this repository is a *refusal* with a
recovery path back to the unselected index — never a 500, and never a silent
fall back to the unselected page, which would tell a learner their link
worked when it did not.
"""

from __future__ import annotations

from urllib.parse import urlencode

from ._shared import _esc, record_standing
from .sections import NONE, Markup, Rows, Section

__all__ = ["SELECTED_PARAM", "evidence_inspector", "selected_value"]

# The parameter that carries the selected context on a route that owns a fact.
SELECTED_PARAM = "record"

# The selection-owning route's own filters — preserved when the inspector
# links back, so closing the inspector never loses the learner's filter set.
_FILTER_PARAMS = ("node", "outcome", "standing")


def selected_value(query: dict | None) -> str:
    """The selected context the URL asked for, or ``""`` for no selection."""
    values = (query or {}).get(SELECTED_PARAM) or []
    return (values[0] if values else "").strip()


def _kept_params(query: dict | None) -> dict[str, str]:
    """The route's own parameters, minus the selection and the mode.

    ``mode`` is presentation and is re-derived from the route's default on a
    bare link; everything else is the destination's context and is kept.
    """
    kept: dict[str, str] = {}
    for key in _FILTER_PARAMS:
        values = (query or {}).get(key) or []
        if values and values[0]:
            kept[key] = values[0]
    return kept


def _href(base: str, params: dict[str, str]) -> str:
    return f"{base}?{urlencode(params)}" if params else base


def _status_label(text: str, kind: str) -> str:
    """A status word: the word carries the meaning, the kind carries the shape."""
    return f'<span class="status-label {_esc(kind)}">{_esc(text)}</span>'


# How a record's recorded authority reads in the learner's language. An
# unknown value is shown as technical detail rather than guessed at.
_ACCEPTED_BY_WORDS = {
    "learner_manual": "You, on a manual review",
    "objective_gate": "The objective gate",
}


def _accepted_by_words(value: str) -> str:
    """The authority that froze the verdict, in words (VS-4: ids stay technical)."""
    words = _ACCEPTED_BY_WORDS.get(value)
    if words is None:
        return f"<code>{_esc(value)}</code>"
    return _esc(words)


def _provenance(view, record) -> str:
    """The record's recent event provenance, behind a disclosure.

    ``records_touched`` is how a mutation names the record it wrote; the
    index is precomputed once per join, so this is a display read, not a
    second derivation of state. The five most recent events are enough to
    answer "what happened to this record", and the count says how many
    there are.
    """
    events = view.events_by_node.get(record.id) or []
    if not events:
        inner = '<p class="small mut">No audit event names this record yet.</p>\n'
    else:
        items = []
        for event in events[-5:]:
            stamp = str(event.get("timestamp") or "")
            command = str(event.get("command") or "")
            items.append(
                '<li class="history-item">'
                f'<span class="history-when">{_esc(stamp)}</span>'
                f"<code>{_esc(command)}</code>"
                "</li>"
            )
        inner = '<ul class="history-list">\n' + "\n".join(items) + "\n</ul>\n"
    return (
        '<details class="disclosure">\n'
        f"<summary>Event provenance ({len(events)})</summary>\n"
        f"{inner}"
        "</details>\n"
    )


def _refusal(record_id: str, close: str) -> str:
    """A selection that names no record: refusal, with the way back."""
    return (
        '<aside class="inspector" aria-labelledby="inspector-title">\n'
        '<h2 class="inspector-title" id="inspector-title">'
        "Selected evidence record</h2>\n"
        '<div class="state state-refusal">\n'
        '<p class="state-title">That evidence record is not in this repository</p>\n'
        '<p class="state-body">Nothing here has the id '
        f"<code>{_esc(record_id)}</code>. Evidence records are never edited or "
        "deleted, so an id that resolves to nothing belongs to a different "
        "repository — history was not rewritten.</p>\n"
        f'<p><a href="{_esc(close)}">Back to the evidence index</a></p>\n'
        "</div>\n"
        "</aside>\n"
    )


def evidence_inspector(view, record_id: str, *, query: dict | None = None) -> str:
    """The selected ``EvidenceRecord`` as the contextual inspector (markup).

    ``record_id`` comes from the URL, so every value below is escaped. The
    selection is independent of the index's filters: a shared link whose
    record is filtered out of the list still shows the record.
    """
    close = _href("/evidence", _kept_params(query))
    record = next((r for r in view.records if r.id == record_id), None)
    if record is None:
        return _refusal(record_id, close)

    spec = next((s for s in view.specs if s.id == record.artifact_spec_id), None)
    node_id = spec.node_id if spec is not None else ""
    title = view.titles.get(node_id) or node_id
    gate = view.gates_by_node.get(node_id)
    standing = record_standing(view, record)

    skill = (
        f'<a href="/nodes/{_esc(node_id)}">{_esc(title)}</a> '
        f"<code>{_esc(node_id)}</code>"
        if node_id
        else '<span class="mut">This requirement names no skill.</span>'
    )
    requirement = (
        f"{_esc(spec.title)} <code>{_esc(spec.id)}</code>"
        if spec is not None
        else '<span class="mut">Requirement</span> '
        f"<code>{_esc(record.artifact_spec_id)}</code>"
    )
    if gate is None:
        gate_text = '<span class="mut">No gate is declared for this skill.</span>'
    elif gate.authority == "objective":
        gate_text = f"Objective gate <code>{_esc(gate.command or '')}</code>"
    else:
        gate_text = "Manual gate"
    verdict = _status_label(
        "Accepted" if record.accepted else "Rejected",
        "success" if record.accepted else "failure",
    )
    standing_kind = {
        "live": "success",
        "superseded": "neutral",
        "rejected": "failure",
    }.get(standing, "neutral")

    pairs: list[tuple[str, str]] = [
        ("Skill", skill),
        ("Requirement", requirement),
        ("Gate", gate_text),
        ("Verdict", verdict),
        ("Standing", _status_label(standing, standing_kind)),
        ("Submitted by", _accepted_by_words(record.accepted_by)),
        (
            "Submitted at",
            f'<span class="mono">{_esc(str(record.created_at or ""))}</span>',
        ),
        ("Artifact", f"<code>{_esc(record.location)}</code>"),
    ]
    if record.supersedes:
        reason = record.supersede_reason or ""
        pairs.append(
            (
                "Supersedes",
                f"<code>{_esc(record.supersedes)}</code>"
                + (f' <span class="mut">{_esc(reason)}</span>' if reason else ""),
            )
        )
    successor = next((r for r in view.records if r.supersedes == record.id), None)
    if successor is not None:
        pairs.append(
            (
                "Superseded by",
                f"<code>{_esc(successor.id)}</code> — the correction stands, and "
                "this record keeps its place in history.",
            )
        )
    if record.note:
        pairs.append(("Note", _esc(record.note)))

    inner = (
        '<aside class="inspector" aria-labelledby="inspector-title">\n'
        '<div class="section-head">\n'
        '<h2 class="inspector-title" id="inspector-title">'
        "Selected evidence record</h2>\n"
        f'<p class="section-meta">{_status_label("Selected", "info")}</p>\n'
        "</div>\n"
        f'<p class="inspector-raw"><code>{_esc(record.id)}</code></p>\n'
        + Rows(tuple(pairs), separated=True).render()
        + _provenance(view, record)
        + '<p class="command-bar">'
        f'<a class="btn secondary" href="{_esc(close)}">Close inspector</a></p>\n'
        "</aside>\n"
    )
    return Section("", "", (Markup(inner),), frame=NONE).render()
