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
    Para,
    Pill,
    Sub,
    Title,
    lines_to_cards,
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


# --- lines_to_cards: compat parser for out-of-scope line producers -------------


def test_compat_parser_recovers_typed_parts():
    cards = lines_to_cards(
        [
            "OPTION 1 — X",
            "Some Skill Title",
            "  [Ready to start]",
            "",
            "Where to learn",
            "  A resource line",
            "---",
            "OPTION 2 — Y",
            "[advisory] note",
        ]
    )
    assert len(cards) == 3
    kinds = [type(part) for part in cards[0].parts]
    assert kinds == [Kicker, Lead, Pill, Label, Sub]
    assert cards[0].parts[0] == Kicker(text="OPTION 1 — X")
    assert cards[0].parts[1] == Lead(text="Some Skill Title")
    assert cards[0].parts[2] == Pill(label="Ready to start")
    assert cards[1].parts == (Kicker(text="OPTION 2 — Y"),)
    assert cards[2].kind == "advisory"
    assert cards[2].parts == (Banner(kind="advisory", text="note"),)
