"""Structured Mentor cards — model constructors and the CLI serializer.

Covers ``mentor.cards`` (pure data: banners carry a ``kind`` field, pills a
``label`` field, kickers/leads/subs are typed parts) and ``render``'s
``cards_to_lines`` (the sole owner of the legacy terminal shape, byte-stable
with the retired per-handler line builders).
"""

from __future__ import annotations

from skilltrace import render
from skilltrace.mentor.cards import (
    Banner,
    Kicker,
    Label,
    Lead,
    MentorCard,
    NextAction,
    Para,
    Pill,
    Sub,
    Title,
)


# --- Model constructors --------------------------------------------------------


def test_banner_carries_kind_as_a_field():
    card = MentorCard.banner_card("warning", "track 'x' is unmapped")
    assert card.kind == "warning"
    (part,) = card.parts
    assert isinstance(part, Banner)
    assert part.kind == "warning"
    assert part.text == "track 'x' is unmapped"


def test_pill_carries_label_as_a_field():
    part = Pill(label="Ready to start")
    assert part.label == "Ready to start"


def test_each_section_type_constructs():
    assert Kicker(text="TODAY").text == "TODAY"
    assert Title(text="Some Skill").text == "Some Skill"
    assert Lead(text="brief").text == "brief"
    assert Label(text="Where to learn").text == "Where to learn"
    assert Para(text="context").text == "context"
    assert Sub(text="a resource").text == "a resource"


def test_content_cards_have_no_kind():
    card = MentorCard(parts=[Kicker(text="TODAY"), Para(text="hi")])
    assert card.kind is None
    assert len(card.parts) == 2


# --- NextAction: the structured next-action fact (v2.4 S1) ----------------------


def test_next_action_is_a_typed_part_with_the_locked_fact_shape():
    """§E: intent (closed Literal set), node_id, command, eligible — no prose."""
    action = NextAction(
        intent="pass",
        node_id="math.arithmetic.x_01",
        command="Mark Apply X passed: `skilltrace pass math.arithmetic.x_01`",
        eligible=True,
    )
    assert action.intent == "pass"
    assert action.node_id == "math.arithmetic.x_01"
    assert action.eligible is True
    card = MentorCard(parts=[Kicker(text="TODAY"), action])
    assert card.parts[1] is action


def test_next_action_serializes_byte_identically_to_the_legacy_pair():
    """`NextAction` replaces the ``DO THIS NEXT`` Kicker+Sub pair one-for-one."""
    action = NextAction(
        intent="pass",
        node_id="x_01",
        command="Mark Apply X passed: `skilltrace pass x_01`",
        eligible=True,
    )
    legacy = MentorCard(
        parts=[
            Sub(text="How to proceed"),
            Sub(text="evidence line"),
            Kicker(text="DO THIS NEXT"),
            Sub(text="Mark Apply X passed: `skilltrace pass x_01`"),
        ]
    )
    replaced = MentorCard(
        parts=[
            Sub(text="How to proceed"),
            Sub(text="evidence line"),
            action,
        ]
    )
    assert render.cards_to_lines([replaced]) == render.cards_to_lines([legacy])


def test_next_action_without_command_still_serializes():
    action = NextAction(intent="explore", node_id=None, command=None, eligible=None)
    lines = render.cards_to_lines([MentorCard(parts=[action])])
    assert lines == ["DO THIS NEXT"]


def test_next_action_blank_line_rules_match_the_legacy_pair():
    card = MentorCard(
        parts=[
            Sub(text="evidence line"),
            NextAction(
                intent="submit_evidence",
                node_id="x_01",
                command="Submit your next piece of evidence for x_01",
            ),
            Para(text="Also in range: A, B."),
        ]
    )
    assert render.cards_to_lines([card]) == [
        "  evidence line",
        "",
        "DO THIS NEXT",
        "  Submit your next piece of evidence for x_01",
        "",
        "Also in range: A, B.",
    ]


# --- cards_to_lines: legacy terminal shape -------------------------------------


def test_today_card_serializes_to_legacy_lines():
    cards = [
        MentorCard(
            parts=[
                Kicker(text="TODAY"),
                Lead(text="brief text"),
                Label(text="Where to learn (top focus)"),
                Sub(text="Pandas Docs -- https://example.test/"),
                Label(text="How to proceed"),
                Sub(text="Start studying X."),
                Kicker(text="DO THIS NEXT"),
                Sub(text="Start studying x.y_01."),
                Para(text="Also in range: Y."),
            ]
        )
    ]
    assert render.cards_to_lines(cards) == [
        "TODAY",
        "",
        "brief text",
        "",
        "Where to learn (top focus)",
        "  Pandas Docs -- https://example.test/",
        "",
        "How to proceed",
        "  Start studying X.",
        "",
        "DO THIS NEXT",
        "  Start studying x.y_01.",
        "",
        "Also in range: Y.",
    ]


def test_candidate_cards_join_with_separators():
    cards = [
        MentorCard(
            parts=[
                Kicker(text="OPTION 1 — 60-MIN SESSION"),
                Title(text="Skill A"),
                Pill(label="Ready to start"),
                Para(text="brief A"),
                Label(text="Where to learn"),
                Sub(text="Res A"),
                Label(text="How to proceed"),
                Sub(text="Study A."),
                Kicker(text="DO THIS NEXT"),
                Sub(text="Start A."),
            ]
        ),
        MentorCard(
            parts=[
                Kicker(text="OPTION 2 — 60-MIN SESSION"),
                Title(text="Skill B"),
                Pill(label="In progress"),
                Para(text="brief B"),
            ]
        ),
    ]
    assert render.cards_to_lines(cards) == [
        "OPTION 1 — 60-MIN SESSION",
        "Skill A",
        "  [Ready to start]",
        "",
        "brief A",
        "",
        "Where to learn",
        "  Res A",
        "",
        "How to proceed",
        "  Study A.",
        "",
        "DO THIS NEXT",
        "  Start A.",
        "",
        "---",
        "OPTION 2 — 60-MIN SESSION",
        "Skill B",
        "  [In progress]",
        "",
        "brief B",
    ]


def test_banner_and_appendix_cards_use_blank_separators():
    cards = [
        MentorCard.banner_card("warning", "track 'x' is unmapped"),
        MentorCard(parts=[Kicker(text="OPTION 1"), Title(text="Skill A")]),
        MentorCard.banner_card("advisory", "remediation edge active: r supports t."),
        MentorCard(
            parts=[
                Label(text="Locked (1):"),
                Sub(text="a.b_01 — blocked by: c.d_01"),
            ],
            kind="locked",
        ),
    ]
    assert render.cards_to_lines(cards) == [
        "[warning] track 'x' is unmapped",
        "OPTION 1",
        "Skill A",
        "",
        "[advisory] remediation edge active: r supports t.",
        "",
        "Locked (1):",
        "  a.b_01 — blocked by: c.d_01",
    ]
