"""
The confirmation panels (ADR 0009): the pass panel and the two-step
mastery journey.

Both are **full-page safety panels** (spec-v3-study-day §6 RT-07..RT-09,
IC-2): their own route, their own title, their own step affordances. The
overlay *confirmation modal* is the earlier Tier 1 form they replace —
nothing here is an overlay, and passing and mastering are never combined
into one control (HB-1).

The pass panel discloses, before the learner confirms anything: the
evidence the engine accepts, what the gate decided about each record, the
freshly derived eligibility decision, the state the pass would assert and
the review-scheduling consequence. The confirming POST revalidates against
current truth, so a stale panel can never assert what eligibility no
longer supports: a refusal writes nothing, returns to this same step with
refreshed facts, and names the next valid route (IC-8, IC-9, R4, R5).
"""

from __future__ import annotations

from ...commands.eligibility import passed_at_of
from ...context import JoinedView
from ...evidence.eligibility import (
    compute_eligibility,
    live_accepted_count,
)
from ...policy.mastery import compute_mastery_eligibility
from ..interface.text import plural
from ._shared import (
    _esc,
    _normalize_pill_label,
    _output_banners,
    superseded_ids,
)
from .sections import (
    BARE,
    EMPTY,
    INLINE,
    LIMITED,
    REFUSAL,
    Markup,
    Rows,
    Section,
    State,
    Table,
)
from .shell import (
    MASTER_CONFIRM_PANEL,
    MASTER_FACTS_PANEL,
    PASS_PANEL,
    PASSED_PANEL,
    _mode_from,
    _page_head,
    _panel_dismiss,
    _panel_shell,
    _status_page,
)

#: The anchor the pass panel carries — the fragment a redirect lands on, so
#: the learner (and the keyboard) start at the panel, not at the top of the
#: document (IC-5, AX-7).
PASS_PANEL_ANCHOR = "pass-panel"


def _accepted_records(view: JoinedView, node_id: str) -> list:
    """The live accepted records a pass rests on — the required evidence.

    Only accepted, non-superseded records for a **required** specification
    count toward pass eligibility, so only those are listed here: an
    optional specification's records are kept and shown in the evidence
    workspace, never counted (CONTEXT.md "ArtifactSpec"). The list is
    derived on read from the same records the engine computes eligibility
    from, so the panel can never claim a record the engine would not count.
    """
    required_ids = {
        spec.id for spec in view.specs_by_node.get(node_id, []) if spec.required
    }
    superseded = superseded_ids(view)
    return [
        record
        for record in view.records
        if record.artifact_spec_id in required_ids
        and record.accepted
        and record.id not in superseded
    ]


def _gate_kind_line(view: JoinedView, node_id: str) -> str:
    """How this skill's evidence is judged — the gate's kind, in plain words.

    The same fact the evidence workspace states, in the panel's register:
    here the learner is reading a verdict that already happened, not
    choosing one.
    """
    gate = view.gates_by_node.get(node_id)
    if gate is None:
        return "No checking method is set up — evidence cannot count here yet."
    if gate.command:
        return (
            "Checked automatically — the check's result is recorded with "
            "your evidence."
        )
    return "Checked by you — you state the verdict when you submit."


def _gate_decision(record) -> str:
    """What the gate decided about one record, in plain words.

    A manual gate's decision is the learner's own verdict; an objective
    gate's decision is the check's result, carried by the record. The
    verdict is a historical fact about the artifact as submitted — it is
    never re-run to fill this page.
    """
    run = record.gate_run or {}
    if record.accepted_by == "learner_manual":
        return "You accepted it."
    exit_class = run.get("exit_class")
    if exit_class == "passed":
        return "The automatic check passed it."
    if exit_class == "failed":
        return "The automatic check failed it."
    return "An automatic check accepted it."


def _pass_wanted_rows(view: JoinedView, node_id: str, eligibility) -> str:
    """What the skill wants: every required spec with its minimum and standing."""
    titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(node_id, [])
    }
    rows = [
        [
            _esc(titles.get(spec.spec_id, spec.spec_id)),
            _esc(str(spec.minimum_count)),
            _esc(str(spec.accepted_count)),
            "met" if spec.met else "below minimum",
        ]
        for spec in eligibility.specs
    ]
    if not rows:
        return State(
            EMPTY,
            "No required evidence is defined for this skill",
            "This skill names no required artifact, so there is no proof to "
            "gather before it can be passed.",
        ).render()
    return Table(
        ("What you show", "Minimum", "Accepted live", "Standing"), tuple(rows)
    ).render()


def _accepted_table(view: JoinedView, node_id: str) -> str:
    """The accepted records themselves — the evidence the engine accepts."""
    records = _accepted_records(view, node_id)
    titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(node_id, [])
    }
    if not records:
        return State(
            EMPTY,
            "No accepted evidence yet",
            "Nothing has been accepted for this skill yet. Submit your work in "
            "the evidence workspace, and the accepted records appear here.",
        ).render()
    rows = [
        (
            _esc(titles.get(record.artifact_spec_id, record.artifact_spec_id)),
            _esc(_gate_decision(record)),
            _esc(record.location),
            _esc(str(record.created_at or "")),
        )
        for record in sorted(records, key=lambda r: (str(r.created_at or ""), r.id))
    ]
    return Table(
        ("Artifact", "What the gate decided", "Where it lives", "Submitted"),
        tuple(rows),
    ).render()


def _rejected_note(view: JoinedView, node_id: str) -> str:
    """A rejected record is an honest record, and it never counts."""
    required_ids = {
        spec.id for spec in view.specs_by_node.get(node_id, []) if spec.required
    }
    rejected = [
        record
        for record in view.records
        if record.artifact_spec_id in required_ids and not record.accepted
    ]
    if not rejected:
        return ""
    count = len(rejected)
    return (
        f'<p class="section-meta">{count} rejected record{plural(count)} '
        "on file — a rejection is an honest record, and it never counts "
        "toward passing.</p>\n"
    )


def _eligibility_facts(view: JoinedView, node_id: str, eligibility) -> list[str]:
    """Why the skill is not pass-eligible — in the learner's words.

    The engine's own reasons name the node and the specification by id;
    the panel states the same facts in plain words, so the learner reads
    what is missing rather than which record id is short (R1).
    """
    facts: list[str] = []
    if not eligibility.has_gate:
        facts.append(
            "No checking method is set up for this skill, so no evidence can "
            "count toward passing it."
        )
    if not eligibility.has_required_spec:
        facts.append(
            "This skill names no required artifact, so there is no proof to "
            "gather before it can be passed."
        )
    titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(node_id, [])
    }
    for spec in eligibility.specs:
        if spec.met:
            continue
        facts.append(
            f"{titles.get(spec.spec_id, spec.spec_id)} needs "
            f"{spec.minimum_count} accepted record"
            f"{plural(spec.minimum_count)}; {spec.accepted_count} accepted "
            "so far."
        )
    return facts


def _eligibility_section(view: JoinedView, node_id: str, eligibility) -> str:
    """The freshly derived decision, with the reasons when it is negative."""
    if eligibility.eligible:
        verdict = _output_banners(
            ["This skill is ready to mark as passed, on this fresh read."],
            default_class="ok",
        )
    else:
        verdict = _output_banners(
            _eligibility_facts(view, node_id, eligibility), default_class="warning"
        )
    return Section(
        "Eligibility",
        "Decided again just now from the records above.",
        (Markup(verdict),),
    ).render()


def _review_note(view: JoinedView) -> str:
    """What passing does to the Review state — visible before it happens."""
    cadence = view.policy.cadence
    if cadence.schedule_reviews_after_pass and cadence.intervals:
        days = ", ".join(
            str(interval.days_after_pass) for interval in cadence.intervals
        )
        return (
            "Marking as passed schedules reviews for "
            f"{days} days after the pass."
        )
    return (
        "No checks are scheduled automatically — policy leaves scheduling "
        "manual for this skill."
    )


def _next_step(view: JoinedView, node_id: str, state: str, eligibility) -> str:
    """The next valid route, named on the panel itself (IC-8, R5).

    A panel the learner cannot act on names the way forward in the same
    view: the evidence workspace when evidence is the gap, the skill's own
    page when a prerequisite — or the curriculum itself — is. The route
    offered is always one that can actually move the learner forward: a
    skill with no checking method has no evidence to record, so the
    evidence workspace is not offered for it.
    """
    if state == "locked":
        kind = REFUSAL
        title = "This skill cannot be passed yet"
        body = (
            "It is locked until the skills it depends on are passed. No "
            "evidence can unlock it, and nothing here offers a way around "
            "that."
        )
        actions = (
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "See what this skill depends on</a>"
        )
    elif not eligibility.has_gate:
        kind = REFUSAL
        title = "No checking method is set up yet"
        body = (
            "Evidence only counts when a checking method can judge it, "
            "and this skill has none."
        )
        actions = (
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "See this skill</a>"
        )
    elif not eligibility.has_required_spec:
        kind = REFUSAL
        title = "This skill names no required evidence"
        body = (
            "There is no proof to gather before this skill can be "
            "passed, so there is nothing to confirm."
        )
        actions = (
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "See this skill</a>"
        )
    elif _accepted_records(view, node_id):
        kind = LIMITED
        title = "Some required evidence is still short"
        body = (
            "The records on file stand — the requirement above is simply "
            "not met yet."
        )
        actions = (
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/evidence">'
            "Record the missing evidence</a>"
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "Back to the skill</a>"
        )
    else:
        kind = EMPTY
        title = "No accepted evidence yet"
        body = (
            "Nothing has been accepted for this skill yet, so the "
            "requirement above cannot be met yet."
        )
        actions = (
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/evidence">'
            "Record the missing evidence</a>"
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "Back to the skill</a>"
        )
    return Section(
        "Next step",
        "The way forward from here, named so you never have to hunt for it.",
        (
            Markup(
                State(kind, title, body).render()
                + '<div class="command-bar"><div class="actions">'
                + actions
                + "</div></div>"
            ),
        ),
    ).render()


def _confirm_form(node_id: str, node_title: str, mode: str) -> str:
    """The one explicit pass command — a plain form posting to this route.

    The button is never pre-disabled by a derived precondition: the
    engine's refusal on click is the truth, so a stale panel cannot
    pretend to know what eligibility no longer supports. The hidden mode
    field carries the learner's presentation context through the redirect.
    """
    return (
        f'<form method="post" action="/nodes/{_esc(node_id)}/pass">'
        f'<input type="hidden" name="mode" value="{_esc(mode)}">'
        '<div class="actions">'
        f'<button type="submit" class="btn primary">Mark {_esc(node_title)} passed</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
        "</div></form>"
    )


def _review_consequence(view: JoinedView, node_id: str) -> str:
    """What passing did to the Review state — shown on the pass result.

    Passing visibly changes the Review state (R3): either scheduled
    Reviews appear, or the page says plainly that policy leaves scheduling
    manual and offers the action. Either way the learner sees the
    consequence rather than having it happen silently.
    """
    scheduled = [
        r for r in view.reviews if r.node_id == node_id and r.status == "scheduled"
    ]
    if scheduled:
        rows = [
            (_esc(r.scheduled_for), "scheduled")
            for r in sorted(scheduled, key=lambda r: r.scheduled_for)
        ]
        return (
            "<p><strong>What passing changed</strong></p>"
            '<p class="big">These checks are now scheduled for this skill:</p>'
            + Table(("Due", "State"), tuple(rows)).render()
            + '<p class="small mut">A check only becomes overdue once its '
            "date has passed. Completing or cancelling one stays your own "
            "action.</p>"
        )
    return (
        "<p><strong>What passing changed</strong></p>"
        '<p class="big">No checks were scheduled automatically — policy '
        "leaves scheduling manual for this skill.</p>"
        '<div class="command-bar"><div class="actions">'
        '<a class="btn secondary" href="/reviews">Schedule a check</a>'
        "</div></div>"
    )


def pass_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/pass` — the full-page pass panel (RT-07, §10.7).

    Passing is one deliberate, explicit, revalidated step. The panel shows
    the evidence the engine accepts and what the gate decided about it,
    states the eligibility decision freshly derived from those records,
    and names the review-scheduling consequence — all before the learner
    confirms. The confirming POST revalidates against current truth: a
    stale or ineligible confirmation refuses, writes nothing, and returns
    to this same step with refreshed facts and the next valid route named.
    """
    query = query or {}
    mode = _mode_from(query, "guided")
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path=_panel_dismiss(node_id, PASS_PANEL),
        current_view="node-pass",
        path=f"/nodes/{node_id}/pass",
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    eligibility = compute_eligibility(
        node_id,
        view.specs_by_node.get(node_id, []),
        has_gate=node_id in view.has_gate,
        records=view.records,
        node_state=state,
    )
    node_title = view.node_map[node_id].title

    if state in ("passed", "mastered"):
        # The pass already happened: this page is now the **result**, and it
        # must show the visible Review-state consequence (R3) — the scheduled
        # Reviews that appeared, or the explicit statement that policy leaves
        # scheduling manual, with the action offered.
        inner = (
            Section(
                "What passing changed",
                "",
                (Markup(_review_consequence(view, node_id)),),
                frame=BARE,
            ).render()
            + '<div class="command-bar"><div class="actions">'
            f'<a class="btn primary" href="/nodes/{_esc(node_id)}">'
            "Back to the skill</a>"
            f'<a class="btn secondary" href="/reviews">See all reviews</a>'
            "</div></div>"
        )
        return _panel_shell(
            view, node_id, PASSED_PANEL, inner, head=head, anchor=PASS_PANEL_ANCHOR
        )

    not_backed = ""
    if eligibility.passed_but_not_backed:
        not_backed = (
            '<p class="banner warning">Already passed but no longer backed by live '
            "proof — the pass stands regardless, never moves backward.</p>"
        )

    # A locked skill is a **structural** wall: passing it can never succeed
    # as the record stands, so the action is omitted — absent markup, never
    # a disabled control (ADR 0007 §Validation). The wall itself is stated,
    # and the next route names what can actually move the learner forward.
    locked = state == "locked"
    confirm_section = ""
    if not locked:
        confirm_section = Section(
            "Confirm",
            "Marking as passed is your own explicit act. Nothing else here "
            "can pass this skill for you.",
            (Markup(_confirm_form(node_id, node_title, mode)),),
            frame=INLINE,
        ).render()

    inner = (
        Section(
            "Pass this skill",
            "This panel is about passing only. Mastering is a separate, later "
            "journey and is never combined with passing.",
            (
                Rows(
                    (
                        ("Current state", _esc(_normalize_pill_label(state))),
                        ("After you confirm", "Passed"),
                    ),
                    separated=True,
                ),
            ),
            frame=INLINE,
        ).render()
        + not_backed
        + Section(
            "Evidence wanted",
            "What this skill requires before it can be passed.",
            (Markup(_pass_wanted_rows(view, node_id, eligibility)),),
        ).render()
        + Section(
            "Evidence the engine accepts",
            "The records this pass rests on. Only accepted, non-superseded "
            "records for this skill's required evidence count.",
            (
                Markup(
                    f"<p>{_esc(_gate_kind_line(view, node_id))}</p>"
                    + _accepted_table(view, node_id)
                    + _rejected_note(view, node_id)
                ),
            ),
        ).render()
        + _eligibility_section(view, node_id, eligibility)
        + Section(
            "What passing changes",
            "",
            (
                Markup(
                    "<p><strong>Marking this skill as passed</strong> records it "
                    "as passed. Passed never moves backward.</p>"
                    f"<p>{_esc(_review_note(view))}</p>"
                ),
            ),
            frame=BARE,
        ).render()
        + ("" if eligibility.eligible else _next_step(view, node_id, state, eligibility))
        + confirm_section
    )
    return _panel_shell(
        view, node_id, PASS_PANEL, inner, head=head, anchor=PASS_PANEL_ANCHOR
    )


def _mastery_facts_html(view: JoinedView, node_id: str) -> tuple[str, str]:
    """Fresh mastery facts table + eligibility banners, shared by both steps (T5 §F).

    Recomputed from a fresh join on every render — step 2 re-renders the
    node and facts freshly rather than trusting step 1's read (P4.4).
    """
    state = view.store.state_of(node_id)
    values = view.policy.mastery
    passed_at = passed_at_of(view.store, node_id)
    mastery = compute_mastery_eligibility(
        node_id,
        current_state=state,
        passed_at=passed_at,
        specs=view.specs_by_node.get(node_id, []),
        records=view.records,
        reviews=view.reviews,
        values=values,
    )
    accepted_total = sum(
        live_accepted_count(view.records, s.id)
        for s in view.specs_by_node.get(node_id, [])
    )
    fact_rows = [
        ["Passed on", _esc(str(passed_at)[:10]) if passed_at else "—"],
        [
            "Live proof accepted",
            f"{accepted_total} of {values.min_accepted_evidence} required",
        ],
        [
            "Review spacing",
            f"a satisfactory completed review at least "
            f"{values.min_days_pass_to_review} day(s) after the pass",
        ],
    ]
    verdict_html = _output_banners(
        ["This skill is ready for the permanent confirm, on this fresh read."]
        if mastery.eligible
        else list(mastery.reasons),
        default_class="ok" if mastery.eligible else "warning",
    )
    return Table(("Fact", "Value"), tuple(tuple(row) for row in fact_rows)).render(), verdict_html


def master_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master` — step 1 of 2: mastery facts (T5 §B+§F+P4.1)."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path=_panel_dismiss(node_id, MASTER_FACTS_PANEL),
        current_view="node-master",
        path=f"/nodes/{node_id}/master",
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    facts_table, verdict_html = _mastery_facts_html(view, node_id)

    if state == "locked" or state != "passed":
        # P4.1 structural omission: Continue is omitted on a structural wall —
        # locked, or anything that is not passed — and the wall is shown with
        # its unmet prerequisites in plain words.
        if state == "locked":
            wall_note = (
                '<p class="mut">Continue is unavailable — this skill is locked '
                "until its prerequisites are passed.</p>"
            )
        else:
            wall_note = (
                '<p class="mut">Continue is unavailable — mastery needs '
                "a passed skill first.</p>"
            )
        actions = (
            '<div class="actions">'
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )
    else:
        # Judgment eligibility stays live with advisory text beside the action.
        wall_note = (
            '<p class="mut">Mastery needs a passed skill with accepted proof '
            "and a satisfactory spaced review.</p>"
        )
        actions = (
            '<div class="actions">'
            + f'<a class="btn master" href="/nodes/{_esc(node_id)}/master/confirm">'
            "Continue to permanent confirm &rarr;</a>"
            + f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )

    inner = (
        '<div class="kicker">Mastery facts</div>'
        '<p class="big">Mastering is a separate, later step from passing. '
        "This panel is about mastery only — passing has its own journey, and "
        "mastering is never combined with passing.</p>"
        + facts_table
        + "<p><strong>Eligibility</strong></p>"
        + verdict_html
        + wall_note
        + actions
    )
    return _panel_shell(
        view,
        node_id,
        MASTER_FACTS_PANEL,
        inner,
        head=head,
        anchor=MASTER_FACTS_PANEL.name,
    )


def master_confirm_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master/confirm` — step 2 of 2: permanence (T5 §B+§F+P4.4)."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path=_panel_dismiss(node_id, MASTER_CONFIRM_PANEL),
        current_view="master-confirm",
        path=f"/nodes/{node_id}/master/confirm",
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    node_title = view.node_map[node_id].title
    facts_table, verdict_html = _mastery_facts_html(view, node_id)
    inner = (
        '<div class="kicker">Mastery facts — checked again just now</div>'
        '<p class="big">Mastering is permanent. This is not passing: '
        "passing has its own journey, and mastering is never offered as part "
        "of it.</p>"
        + facts_table
        + verdict_html
        + '<p class="banner warning"><strong>This is permanent.</strong> '
        "Mastered never moves backward — this is permanent. "
        "A later unsatisfactory review creates pressure, but the state never "
        "moves backward. Confirm only if you intend this skill to remain mastered "
        "forever.</p>"
        f'<form method="post" action="/nodes/{_esc(node_id)}/master/confirm">'
        '<div class="actions">'
        f'<button type="submit" class="btn master">Mark {_esc(node_title)} mastered</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/master">Back</a>'
        "</div></form>"
    )
    return _panel_shell(
        view,
        node_id,
        MASTER_CONFIRM_PANEL,
        inner,
        head=head,
        anchor=MASTER_CONFIRM_PANEL.name,
    )
