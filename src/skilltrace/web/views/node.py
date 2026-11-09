"""GET ``/nodes/{id}`` — the SkillNode detail destination.

One canonical destination for one skill, composed differently by mode
(spec-v3-study-day §10.4):

* **Guided** — the learner's journey. The readable title and its brief
  facts come first; every record type follows as its own section in plain
  words.
* **Operations** — the engine's view of the same records: denser, with the
  canonical identifiers shown as labelled technical detail.

The composition changes; the facts do not (VS-6). Each record type the
contract names — the progress record, node metadata, ``GraphEdge``,
``LearningResource``, ``ArtifactSpec``, ``ValidationGate``,
``EvidenceRecord``, ``AssessmentAttempt``, ``Blocker``, ``RemediationAction``,
``Review`` and the recent event facts — keeps its own section: records are
never collapsed into one generic progress / skill-health / evidence-state
object. A section with nothing in it says so in an empty state instead of
vanishing or rendering a zero-as-truth (SC-00a).

Nothing here performs or implies ``pass_node``, ``master_node`` or
``delete_record``. Those stay explicit commands behind their own panels;
this page only links to them (HB-1).
"""

from __future__ import annotations

from ...evidence.eligibility import compute_eligibility, live_accepted_count
from ...execution.overdue import utc_today
from ...execution.records import open_session
from ...resources.status import derive_status
from ._shared import _esc, _table
from .forms import _resolve_blocker_form, _work_form_fields
from .shell import _mode_from, _page_head, _status_page

#: The five canonical node states, as the learner sees them.
_STATE_WORDS = {
    "locked": "Locked",
    "available": "Available",
    "active": "Active",
    "passed": "Passed",
    "mastered": "Mastered",
}

#: How each relationship kind reads in plain words.
_EDGE_WORDS = {
    "hard_prerequisite": "Hard prerequisite",
    "soft_prerequisite": "Soft prerequisite",
    "remediation": "Remediation",
}


def node_body(root, node_id: str, query: dict | None = None) -> tuple[str, str, int]:
    """GET ``/nodes/{id}`` — the one canonical SkillNode destination.

    The route's default presentation is Guided; ``?mode=operations`` shows
    the same records with their canonical identifiers as labelled technical
    detail. The page reads fresh from the lenient join on every request.
    """
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path=f"/nodes/{node_id}",
        current_view="node",
        path=f"/nodes/{node_id}",
    )
    if failure is not None:
        return failure

    if node_id not in view.node_map:
        body, status = _status_page(
            404, "That skill is not in the curriculum.", root
        )
        return "Not found", body, status

    operations = _mode_from(query, "guided") == "operations"
    node = view.node_map[node_id]
    state = view.store.state_of(node_id)

    body = (
        head
        + _degraded_notice(view)
        + _brief_section(view, node_id, state)
        + _node_actions_card(view, node_id)
        + _drill_down_card(node_id, view, operations=operations)
    )
    return node.title, body, 200


# --------------------------------------------------------------------------- #
# Page primitives
# --------------------------------------------------------------------------- #


def _section(title: str, meta: str, inner: str) -> str:
    """One stacked section — the page frame is sections, not cards."""
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        f'<h2 class="section-title">{_esc(title)}</h2>\n'
        f'<p class="section-meta">{_esc(meta)}</p>\n'
        "</div>\n"
        f"{inner}\n"
        "</section>\n"
    )


def _row(label: str, value: str) -> str:
    """One fact row — a labelled value, the v3 fact primitive."""
    return (
        '<div class="row">'
        f'<span class="row-label">{_esc(label)}</span>'
        f'<span class="row-value">{value}</span>'
        "</div>"
    )


def _rows(pairs: list[tuple[str, str]]) -> str:
    """A block of fact rows."""
    return '<div class="rows">\n' + "".join(_row(k, v) for k, v in pairs) + "</div>\n"


def _empty(title: str, body: str) -> str:
    """An honest empty state — the population is empty, and that is a fact."""
    return (
        '<div class="state state-empty">\n'
        f'<p class="state-title">{_esc(title)}</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        "</div>\n"
    )


def _limited(title: str, body: str) -> str:
    """A limited state — valid values exist, a threshold is not met yet."""
    return (
        '<div class="state state-limited">\n'
        f'<p class="state-title">{_esc(title)}</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        "</div>\n"
    )


def _failure(title: str, body: str) -> str:
    """A could-not-compute state — the source failed, so nothing is claimed."""
    return (
        '<div class="state state-failure">\n'
        f'<p class="state-title">{_esc(title)}</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        "</div>\n"
    )


def _degraded_notice(view) -> str:
    """The advisory notice when a supporting layer could not be loaded."""
    from ._shared import _degraded_banner

    return _degraded_banner(view)


def _state_word(state: str) -> str:
    """The canonical word for a node state."""
    return _STATE_WORDS.get(state, state.capitalize())


def _state_label(state: str) -> str:
    """The node state as a labelled status pill (the word always shows)."""
    return f'<span class="pill {_esc(state)}">{_esc(_state_word(state))}</span>'


def _technical(label: str, value: str) -> str:
    """One labelled technical detail — a raw identifier, never prose."""
    return _row(label, f"<code>{_esc(value)}</code>")


# --------------------------------------------------------------------------- #
# Facts
# --------------------------------------------------------------------------- #


def _node_specs(view, node_id: str) -> list:
    """The node's artifact specifications, required ones first."""
    specs = list(view.specs_by_node.get(node_id, []))
    specs.sort(key=lambda spec: (not spec.required, spec.id))
    return specs


def _node_records(view, node_id: str) -> list:
    """The evidence records filed against this node's specifications."""
    spec_ids = {spec.id for spec in view.specs_by_node.get(node_id, [])}
    return [record for record in view.records if record.artifact_spec_id in spec_ids]


def _evidence_figures(view, node_id: str) -> tuple[str, str]:
    """The two evidence figures: what is wanted, and what is recorded.

    They are separate labelled facts (R2). Optional specifications never
    count toward the wanted figure, so an optional artifact can never read
    as an eligibility gap.
    """
    specs = _node_specs(view, node_id)
    required = [spec for spec in specs if spec.required and spec.minimum_count > 0]
    records = _node_records(view, node_id)

    if not required:
        wanted = "No required evidence is defined for this skill."
    else:
        wanted = (
            f"{len(required)} required specification"
            f"{'' if len(required) == 1 else 's'}, "
            f"{sum(spec.minimum_count for spec in required)} record"
            f"{'' if sum(spec.minimum_count for spec in required) == 1 else 's'} wanted"
        )

    if not records:
        recorded = "Nothing has been submitted for this skill yet."
    else:
        superseded = {r.supersedes for r in records if r.supersedes}
        accepted = len([r for r in records if r.accepted and r.id not in superseded])
        rejected = len([r for r in records if not r.accepted])
        replaced = len([r for r in records if r.id in superseded])
        recorded = (
            f"{accepted} accepted, {rejected} rejected, {replaced} superseded"
        )
    return wanted, recorded


def _unmet_specs(view, node_id: str) -> list:
    """Required specifications whose accepted count is still below the minimum."""
    unmet = []
    for spec in _node_specs(view, node_id):
        if not spec.required:
            continue
        accepted = live_accepted_count(view.records, spec.id)
        if accepted < spec.minimum_count:
            unmet.append((spec, accepted))
    return unmet


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


def _brief_section(view, node_id: str, state: str) -> str:
    """The brief — the readable title and its brief facts, first on the page."""
    node = view.node_map[node_id]
    wanted, recorded = _evidence_figures(view, node_id)
    facts = [
        ("State", _state_label(state)),
        ("What this skill is", _esc(node.summary)),
        ("Subject", f"{_esc(node.domain)} &middot; {_esc(node.track)}"),
        ("Evidence wanted", _esc(wanted)),
        ("Evidence recorded", _esc(recorded)),
    ]
    inner = _rows(facts)

    if state in ("passed", "mastered"):
        eligibility = compute_eligibility(
            node_id,
            view.specs_by_node.get(node_id, []),
            has_gate=node_id in view.has_gate,
            records=view.records,
            node_state=state,
        )
        if eligibility.passed_but_not_backed:
            inner += (
                '<div class="banner advisory">Your recorded pass is no longer '
                "backed by live evidence. The pass stands and never moves "
                "backward &mdash; this is advice, not a change.</div>\n"
            )

    return _section(node.title, "One skill in your curriculum.", inner)


def _node_actions_card(view, node_id: str) -> str:
    """The contextual actions and the destinations this skill links to.

    ``Log work here`` appears **only** while a Session is open, and it
    binds the work to this skill explicitly. ``Start this session`` is the
    same explicit ``start`` command the cockpit uses; it is offered only
    when there is no open Session and the skill is available to start.
    Passing and mastering are separate, explicit commands behind their own
    panels &mdash; this page links to those panels and never performs them.
    """
    node = view.node_map[node_id]
    title = node.title
    state = view.store.state_of(node_id)
    session = open_session(view.sessions)

    inner = ""
    if session is not None:
        inner += (
            '<div class="command-bar">\n'
            '<div class="actions">\n'
            '<a class="btn secondary" href="/session">Open the session</a>\n'
            "</div>\n"
            "</div>\n"
            '<h3>Log work here</h3>\n'
            '<p class="section-meta">A session is open, so work logged here '
            "joins it and is recorded against this skill.</p>\n"
            '<form method="post" action="/work">\n'
            f'<input type="hidden" name="node_id" value="{_esc(node_id)}">\n'
            f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">\n'
            f"{_work_form_fields()}"
            '<button type="submit" class="btn primary">Log work here</button>\n'
            "</form>\n"
        )
    elif state == "available":
        inner += (
            '<div class="command-bar">\n'
            '<div class="actions">\n'
            '<form method="post" action="/nodes/'
            f'{_esc(node_id)}/start">\n'
            f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">\n'
            '<button type="submit" class="btn primary" data-intent="start">'
            "Start this session</button>\n"
            "</form>\n"
            "</div>\n"
            "</div>\n"
            '<p class="section-meta">Starting records this skill as active. '
            "Progress never moves backward.</p>\n"
        )
    else:
        inner += (
            '<div class="state state-empty">\n'
            '<p class="state-title">No session is open</p>\n'
            '<p class="state-body">Work is recorded inside a session. Open or '
            "start one from the session page, then log work here.</p>\n"
            "</div>\n"
        )

    inner += (
        '<h3>Where this skill leads</h3>\n'
        '<div class="command-bar">\n'
        '<div class="actions">\n'
        '<a class="btn secondary" href="/session">Open the session</a>\n'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/evidence">'
        "Open the evidence workspace</a>\n"
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/pass">'
        f"Mark {_esc(title)} passed&hellip;</a>\n"
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/master">'
        "Open the mastery panel</a>\n"
        '<a class="btn secondary" href="/reviews">Open reviews</a>\n'
        "</div>\n"
        "</div>\n"
        '<p class="section-meta">Passing and mastering are separate, explicit '
        "decisions. Each one is confirmed on its own panel &mdash; nothing "
        "here records them for you.</p>\n"
    )

    blockers = [b for b in view.blockers if b.node_id == node_id and b.status == "open"]
    if blockers:
        rows = [
            [
                _esc(blocker.description),
                _resolve_blocker_form(blocker.id, f"/nodes/{node_id}"),
            ]
            for blocker in blockers
        ]
        inner += (
            "<h3>Blockers on this skill</h3>\n"
            + _table(["What is in the way", "Resolve"], rows)
            + '<p class="section-meta">A blocker is an explicit record that '
            "you are stuck. Resolving it changes no node state and passes "
            "nothing.</p>\n"
        )

    return _section(
        "What you can do here", "The actions this skill offers right now.", inner
    )


def _drill_down_card(node_id: str, view, *, operations: bool = False) -> str:
    """Every record type this skill holds, each in its own section.

    The v2.4 drill-down was one collapsed card of mixed rows; v3 keeps the
    records apart so a learner can tell a progress record from an evidence
    record from a review at a glance.
    """
    sections = [
        _progress_section(view, node_id),
        _metadata_section(view, node_id, operations=operations),
        _relationships_section(view, node_id, operations=operations),
        _resources_section(view, node_id, operations=operations),
        _specs_section(view, node_id),
        _gate_section(view, node_id),
        _records_section(view, node_id, operations=operations),
        _attempts_section(view, node_id, operations=operations),
        _blockers_section(view, node_id, operations=operations),
        _remediation_section(view, node_id, operations=operations),
        _reviews_section(view, node_id, operations=operations),
        _events_section(view, node_id, operations=operations),
    ]
    return "".join(sections)


def _progress_section(view, node_id: str) -> str:
    """The progress record — this learner's state for this one skill."""
    entry = view.store.entries.get(node_id)
    if entry is None:
        inner = _empty(
            "No progress recorded",
            "Nothing has been recorded against this skill yet. Its readiness "
            "is derived from the graph, not asserted by you.",
        )
        return _section(
            "Progress record", "What you have recorded on this skill.", inner
        )

    facts = [
        ("State", _state_label(entry.state)),
        ("Last changed", _esc(str(entry.changed_at or "not recorded"))),
    ]
    for state, stamp in (entry.transitions or {}).items():
        facts.append((f"Reached {state}", _esc(str(stamp))))
    inner = _rows(facts)
    inner += (
        '<p class="section-meta">Asserted progress &mdash; active, passed, '
        "mastered &mdash; never moves backward.</p>\n"
    )
    return _section(
        "Progress record", "What you have recorded on this skill.", inner
    )


def _metadata_section(view, node_id: str, *, operations: bool) -> str:
    """Node metadata — the curriculum's own description of this skill."""
    node = view.node_map[node_id]
    facts = [
        ("Domain", _esc(node.domain)),
        ("Track", _esc(node.track)),
        ("Tags", _esc(", ".join(node.tags) or "none recorded")),
    ]
    effort = node.estimated_effort or {}
    if effort:
        facts.append(
            (
                "Estimated effort",
                _esc(
                    f"{effort.get('min_minutes', '?')}&ndash;"
                    f"{effort.get('max_minutes', '?')} minutes"
                ),
            )
        )
    for anchor in node.roadmap_anchors or ():
        # An anchor is a mapping whose values may be numbers or lists; the
        # page renders the words, so every part is stringified first.
        label = str(anchor.get("phase_label") or anchor.get("phase") or "")
        months = str(anchor.get("month_range") or "")
        topic = str(anchor.get("roadmap_topic") or "")
        facts.append(
            (
                "Roadmap anchor (reference only)",
                _esc(" · ".join(part for part in (label, months, topic) if part)),
            )
        )
    facts.append(("Node ID", f"<code>{_esc(node.id)}</code>"))
    inner = _rows(facts)
    inner += (
        '<p class="section-meta">A roadmap anchor is reference material '
        "only. It never controls readiness, locking or recommendation.</p>\n"
    )
    return _section("Node details", "The curriculum's description of this skill.", inner)


def _relationships_section(view, node_id: str, *, operations: bool) -> str:
    """The ``GraphEdge`` records — what comes before this skill, and after."""
    edges = [
        edge
        for edge in view.edges
        if edge.source == node_id or edge.target == node_id
    ]
    if not edges:
        inner = _empty(
            "No relationships recorded",
            "The graph records no relationship between this skill and any "
            "other. It stands on its own.",
        )
        return _section(
            "Relationships", "How this skill sits in the graph.", inner
        )

    rows = []
    for edge in sorted(edges, key=lambda e: (e.edge_type, e.source, e.target)):
        other = edge.source if edge.target == node_id else edge.target
        other_title = view.titles.get(other, "Another skill")
        if edge.target == node_id:
            direction = "comes before this skill"
        else:
            direction = "follows this skill"
        cells = [
            f'<a href="/nodes/{_esc(other)}">{_esc(other_title)}</a>',
            _esc(_EDGE_WORDS.get(edge.edge_type, edge.edge_type)),
            _esc(direction),
            "yes" if edge.active else "no",
            _esc(edge.reason),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(edge.id)}</code>")
        rows.append(cells)

    headers = ["Edge ID", "Skill", "Relationship", "Direction", "Active", "Why"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    inner += (
        '<p class="section-meta">A hard prerequisite must be passed before '
        "this skill can start. A remediation relationship never unlocks "
        "anything.</p>\n"
    )
    return _section("Relationships", "How this skill sits in the graph.", inner)


def _resources_section(view, node_id: str, *, operations: bool) -> str:
    """The ``LearningResource`` records — where to learn this skill."""
    resources = list(view.resources_by_node.get(node_id, []))
    if not resources:
        inner = _empty(
            "No resources linked",
            "Nothing in the resource registry supports this skill yet, so "
            "there is nowhere to read or watch for it.",
        )
        return _section(
            "Where to learn", "The materials that support this skill.", inner
        )

    window = view.policy.resource_stale_after_days
    today = utc_today()
    rows = []
    for resource in resources:
        status = derive_status(
            resource, today=today, stale_after_days=window
        ).value
        where = resource.url or resource.local_path or ""
        cells = [
            f'<a href="{_esc(where)}">{_esc(where)}</a>' if where else "—",
            _esc(resource.cost),
            _esc(status),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(resource.id)}</code>")
        rows.append(cells)

    headers = ["Resource ID", "Where", "Cost", "Verification"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    inner += (
        '<p class="section-meta">Verification says whether the material was '
        "last checked. It never affects readiness or eligibility.</p>\n"
    )
    return _section("Where to learn", "The materials that support this skill.", inner)


def _specs_section(view, node_id: str) -> str:
    """The ``ArtifactSpec`` records — the evidence this skill wants."""
    specs = _node_specs(view, node_id)
    if not specs:
        inner = _empty(
            "No artifact specifications",
            "No artifact is defined for this skill, so there is no proof to "
            "gather before passing it.",
        )
        return _section(
            "Evidence wanted",
            "The proof this skill asks for, before any work begins.",
            inner,
        )

    rows = []
    for spec in specs:
        accepted = live_accepted_count(view.records, spec.id)
        rows.append(
            [
                _esc(spec.title or spec.id),
                _esc(spec.artifact_kind),
                "required" if spec.required else "optional",
                _esc(str(spec.minimum_count)),
                _esc(str(accepted)),
                _esc(spec.description or ""),
            ]
        )
    inner = _table(
        ["What you show", "Kind", "Requirement", "Minimum", "Accepted", "Description"],
        rows,
    )
    inner += (
        '<p class="section-meta">Only required specifications count toward '
        "passing. An optional specification is additional, never an "
        "eligibility gap.</p>\n"
    )
    return _section(
        "Evidence wanted",
        "The proof this skill asks for, before any work begins.",
        inner,
    )


def _gate_section(view, node_id: str) -> str:
    """The ``ValidationGate`` — who decides whether evidence counts."""
    gate = view.gates_by_node.get(node_id)
    if gate is None:
        inner = _empty(
            "No checking method",
            "Nothing decides the verdict on evidence for this skill yet, so "
            "no evidence can be accepted here.",
        )
        return _section(
            "Checking", "Who judges the evidence you submit.", inner
        )

    if gate.command:
        authority = "An automatic check decides the verdict."
    else:
        authority = "You state the verdict yourself when you submit."
    facts = [
        ("Authority", _esc(authority)),
        ("Gate", _esc(gate.title or gate.id)),
    ]
    if gate.description:
        facts.append(("Description", _esc(gate.description)))
    if gate.command:
        facts.append(("Check command", f"<code>{_esc(gate.command)}</code>"))
    inner = _rows(facts)
    inner += (
        '<p class="section-meta">Acceptance freezes at submission. A record '
        "is corrected by a new record that supersedes it &mdash; never "
        "edited or deleted.</p>\n"
    )
    return _section("Checking", "Who judges the evidence you submit.", inner)


def _records_section(view, node_id: str, *, operations: bool) -> str:
    """The ``EvidenceRecord`` rows — what has actually been submitted."""
    if "records" in view.degraded:
        inner = _failure(
            "Evidence records could not be loaded",
            "The evidence layer did not load, so nothing is claimed about "
            "what is on record. Your progress is unaffected.",
        )
        return _section(
            "Evidence recorded", "What has been submitted for this skill.", inner
        )

    records = _node_records(view, node_id)
    if not records:
        inner = _empty(
            "Nothing recorded yet",
            "No evidence has been submitted for this skill. That is a fact "
            "about the record, not a problem with you.",
        )
        return _section(
            "Evidence recorded", "What has been submitted for this skill.", inner
        )

    spec_titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(node_id, [])
    }
    superseded = {r.supersedes for r in records if r.supersedes}
    rows = []
    for record in sorted(records, key=lambda r: (r.artifact_spec_id, r.created_at or "")):
        if record.id in superseded:
            standing = "superseded"
        elif record.accepted:
            standing = "live"
        else:
            standing = "rejected"
        cells = [
            _esc(spec_titles.get(record.artifact_spec_id, record.artifact_spec_id)),
            "accepted" if record.accepted else "rejected",
            _esc(standing),
            _esc(record.location),
            _esc(str(record.created_at or "")),
            _esc(record.accepted_by),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(record.id)}</code>")
        rows.append(cells)

    headers = ["Record ID", "Artifact", "Verdict", "Standing", "Location", "Submitted", "Accepted by"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)

    unmet = _unmet_specs(view, node_id)
    if unmet:
        parts = "; ".join(
            f"{spec.title or spec.id} needs {spec.minimum_count}, {accepted} accepted"
            for spec, accepted in unmet
        )
        inner += _limited(
            "Some required evidence is still short",
            f"{parts}. The records on file stand; the requirement is simply "
            "not met yet.",
        )
    return _section(
        "Evidence recorded", "What has been submitted for this skill.", inner
    )


def _attempts_section(view, node_id: str, *, operations: bool) -> str:
    """The ``AssessmentAttempt`` rows — attempts at this skill."""
    if "attempts" in view.degraded:
        inner = _failure(
            "Attempts could not be loaded",
            "The evidence layer did not load, so no attempt is claimed either "
            "way.",
        )
        return _section("Attempts", "Attempts at this skill.", inner)

    attempts = [a for a in view.attempts if a.node_id == node_id]
    if not attempts:
        inner = _empty(
            "No attempts recorded",
            "No attempt at this skill has been recorded. A failed attempt is "
            "recorded as a failed attempt &mdash; it never changes the "
            "skill's state.",
        )
        return _section("Attempts", "Attempts at this skill.", inner)

    rows = []
    for attempt in sorted(attempts, key=lambda a: a.created_at or ""):
        cells = [
            _esc(attempt.outcome),
            _esc(str(attempt.created_at or "")),
            _esc(attempt.note or ""),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(attempt.id)}</code>")
        rows.append(cells)

    headers = ["Attempt ID", "Outcome", "When", "Note"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    return _section("Attempts", "Attempts at this skill.", inner)


def _blockers_section(view, node_id: str, *, operations: bool) -> str:
    """The ``Blocker`` rows — where this skill is stuck."""
    if "blockers" in view.degraded:
        inner = _failure(
            "Blockers could not be loaded",
            "The execution layer did not load, so nothing is claimed about "
            "blockers.",
        )
        return _section("Blockers", "Where this skill is stuck.", inner)

    blockers = [b for b in view.blockers if b.node_id == node_id]
    if not blockers:
        inner = _empty(
            "No blockers recorded",
            "Nothing is recorded as persistently stuck on this skill. "
            "Blocked work inside a session is a session-scoped observation "
            "and never creates a blocker on its own.",
        )
        return _section("Blockers", "Where this skill is stuck.", inner)

    rows = []
    for blocker in sorted(blockers, key=lambda b: b.created_at or ""):
        cells = [
            _esc(blocker.status),
            _esc(blocker.description),
            _esc(str(blocker.created_at or "")),
            _esc(blocker.resolution_summary or ""),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(blocker.id)}</code>")
        rows.append(cells)

    headers = ["Blocker ID", "Status", "What is in the way", "Recorded", "Resolution"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    return _section("Blockers", "Where this skill is stuck.", inner)


def _remediation_section(view, node_id: str, *, operations: bool) -> str:
    """The ``RemediationAction`` rows — the remedial work on this skill."""
    if "remediations" in view.degraded:
        inner = _failure(
            "Remediation could not be loaded",
            "The execution layer did not load, so nothing is claimed about "
            "remediation.",
        )
        return _section("Remediation", "Remedial work on this skill.", inner)

    actions = [a for a in view.remediations if a.node_id == node_id]
    if not actions:
        inner = _empty(
            "No remediation recorded",
            "No remedial work has been recorded against this skill.",
        )
        return _section("Remediation", "Remedial work on this skill.", inner)

    rows = []
    for action in sorted(actions, key=lambda a: a.created_at or ""):
        cells = [
            _esc(action.status),
            _esc(action.description),
            _esc(str(action.created_at or "")),
            _esc(action.result_summary or ""),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(action.id)}</code>")
        rows.append(cells)

    headers = ["Action ID", "Status", "What to redo", "Recorded", "Result"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    return _section("Remediation", "Remedial work on this skill.", inner)


def _reviews_section(view, node_id: str, *, operations: bool) -> str:
    """The ``Review`` rows — the retention checks on this skill."""
    if "reviews" in view.degraded:
        inner = _failure(
            "Reviews could not be loaded",
            "The execution layer did not load, so nothing is claimed about "
            "reviews.",
        )
        return _section("Reviews", "Retention checks on this skill.", inner)

    reviews = [r for r in view.reviews if r.node_id == node_id]
    if not reviews:
        # The dead-end offers the action that continues the work, in the
        # product: a review is created only by an explicit scheduling
        # action, and that action is right here.
        inner = _empty(
            "No reviews scheduled",
            "A review is created only by an explicit scheduling action. A "
            "suggested check is advisory and never creates a record.",
        )
        inner += _schedule_review_form(node_id)
        return _section("Reviews", "Retention checks on this skill.", inner)

    rows = []
    for review in sorted(reviews, key=lambda r: r.scheduled_for):
        if review.status == "completed":
            detail = review.outcome or "no outcome"
            summary = review.result_summary or ""
        elif review.status == "cancelled":
            detail = "cancelled"
            summary = review.cancel_reason or ""
        else:
            detail = review.status
            summary = ""
        cells = [
            _esc(review.status),
            _esc(str(review.scheduled_for)),
            _esc(detail),
            _esc(summary),
        ]
        if operations:
            cells.insert(0, f"<code>{_esc(review.id)}</code>")
        rows.append(cells)

    headers = ["Review ID", "Status", "Scheduled for", "What happened", "Detail"]
    if not operations:
        headers = headers[1:]
    inner = _table(headers, rows)
    inner += (
        '<p class="section-meta">An unsatisfactory review creates pressure '
        "only. It never demotes a skill you have passed.</p>\n"
    )
    return _section("Reviews", "Retention checks on this skill.", inner)


def _schedule_review_form(node_id: str) -> str:
    """The explicit scheduling action — the way a review comes to exist.

    A review is never created by a suggestion, a sweep or a timer. This
    form is the only path, and it is the learner's action.
    """
    return (
        '<details class="disclosure">\n'
        "<summary>Schedule a review for this skill</summary>\n"
        '<p class="section-meta">A scheduled review asks you to come back '
        "and recall this skill later. Scheduling one is your explicit "
        "action — nothing is scheduled automatically here.</p>\n"
        '<form method="post" action="/reviews/schedule">\n'
        f'<input type="hidden" name="node_id" value="{_esc(node_id)}">\n'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">\n'
        '<div class="form-row">'
        '<label for="node-review-date">When should it come back?</label>'
        '<input type="date" name="date" id="node-review-date" '
        "required></div>\n"
        '<button type="submit" class="btn secondary">Schedule this review'
        "</button>\n"
        "</form>\n"
        "</details>\n"
    )


def _events_section(view, node_id: str, *, operations: bool) -> str:
    """The recent event facts — the audit trail for this skill."""
    events = list(view.events_by_node.get(node_id, []))
    if not events:
        inner = _empty(
            "No recorded activity",
            "Nothing has been recorded against this skill in the audit log.",
        )
        return _section(
            "Recent activity", "What has been recorded against this skill.", inner
        )

    rows = []
    for event in reversed(events[-10:]):
        cells = [
            _esc(str(event.get("timestamp", ""))),
            _esc(str(event.get("command", ""))),
        ]
        if operations:
            touched = ", ".join(str(t) for t in event.get("records_touched") or [])
            cells.append(f"<code>{_esc(touched)}</code>")
        rows.append(cells)

    headers = ["When (UTC)", "What happened"]
    if operations:
        headers.append("Records touched")
    inner = _table(headers, rows)
    inner += (
        '<p class="section-meta">The audit log is a record only. It is never '
        "read back to work out your state.</p>\n"
    )
    return _section(
        "Recent activity", "What has been recorded against this skill.", inner
    )
