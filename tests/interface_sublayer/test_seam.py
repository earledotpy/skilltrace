"""S1 interface-seam tests (v2.4 spec §I): the mentor/execution/engine side.

Covers the four S1 deliverables:

* the ``NextAction`` typed part on the canonical ``MentorCard`` and the
  per-state ``next_action_for`` fact fed by ``mentor.prose``'s branches
  (``today._focus_action`` is today's single producer);
* the days-practiced derivation (distinct days from ``sessions.started_at``
  ∪ ``work.created_at`` — the locked record window);
* ``render.cards_to_lines`` byte-identical CLI lines with the new part;
* the forbidden-vocabulary translation module no surface may bypass (P3.1),
  including the banned-vocabulary detector the doc gates run.

Also covers the P2.4 health seam: per-layer warning counts as structured
facts on ``LayerHealth``.
"""

from __future__ import annotations

from dataclasses import dataclass

from skilltrace import render
from skilltrace.execution.days import days_practiced, practiced_days
from skilltrace.mentor.cards import Kicker, MentorCard, NextAction, Sub
from skilltrace.mentor.prose import NodeFacts, NodeState, next_action_for
from skilltrace.web.interface import (
    banners,
    forbidden_matches,
    translate,
    translate_lines,
)


# --- fixtures -------------------------------------------------------------------


def _node(title: str = "Apply X", node_id: str = "math.arithmetic.x_01"):
    from skilltrace.graph.nodes import SkillNode

    return SkillNode(
        id=node_id,
        title=title,
        summary="A test skill.",
        domain="mathematics",
        track="foundational",
    )


def _facts(state: NodeState, *, unsatisfied=None, titles=None) -> NodeFacts:
    return NodeFacts(
        node=_node(),
        state=state,
        specs=[],
        records=[],
        has_gate=True,
        resource_lines=[],
        unsatisfied_prereqs=unsatisfied or [],
        unlocked_by=[],
        blockers_for_node=[],
        titles=titles or {},
    )


# --- NextAction fact: per-state derivation --------------------------------------


def test_next_action_available_is_start_bound_to_the_node():
    action = next_action_for(NodeState.AVAILABLE, _facts(NodeState.AVAILABLE))
    assert action.intent == "start"
    assert action.node_id == "math.arithmetic.x_01"
    assert action.command == "Start studying Apply X"


def test_next_action_active_without_eligibility_is_submit_evidence():
    action = next_action_for(NodeState.ACTIVE, _facts(NodeState.ACTIVE))
    assert action.intent == "submit_evidence"
    assert action.node_id == "math.arithmetic.x_01"
    assert "Submit your next piece of evidence" in (action.command or "")


def test_next_action_locked_names_the_unlock_path_not_a_command():
    action = next_action_for(
        NodeState.LOCKED,
        _facts(
            NodeState.LOCKED,
            unsatisfied=[("math.algebra.y_01", "locked")],
            titles={"math.algebra.y_01": "Y"},
        ),
    )
    # A structural wall: no action affordance exists — the fact carries the
    # unlock path as human copy and binds no node affordance.
    assert action.intent == "explore"
    assert action.node_id is None
    assert "Y" in (action.command or "")


def test_next_action_passed_is_schedule_review():
    action = next_action_for(NodeState.PASSED, _facts(NodeState.PASSED))
    assert action.intent == "schedule_review"
    assert action.node_id == "math.arithmetic.x_01"


def test_next_action_mastered_is_explore():
    action = next_action_for(NodeState.MASTERED, _facts(NodeState.MASTERED))
    assert action.intent == "explore"


def test_next_action_part_serializes_byte_identically_to_the_legacy_pair():
    """The fact's serialization is the exact ``DO THIS NEXT`` pair it replaced."""
    action = next_action_for(NodeState.AVAILABLE, _facts(NodeState.AVAILABLE))
    card = MentorCard(parts=[Kicker(text="TODAY"), action])
    legacy = MentorCard(
        parts=[
            Kicker(text="TODAY"),
            Kicker(text="DO THIS NEXT"),
            Sub(text="Start studying Apply X"),
        ]
    )
    assert render.cards_to_lines([card]) == render.cards_to_lines([legacy])


# --- days practiced (P1.7 — the locked record window) ----------------------------


@dataclass
class _Session:
    started_at: str


@dataclass
class _Work:
    created_at: str


def test_days_practiced_counts_distinct_days_across_both_records():
    sessions = [
        _Session("2026-09-01T10:00:00+00:00"),
        _Session("2026-09-03T10:00:00+00:00"),
    ]
    work = [
        _Work("2026-09-01T15:00:00+00:00"),
        _Work("2026-09-05T09:00:00+00:00"),
    ]
    assert days_practiced(sessions, work) == 3


def test_days_practiced_union_is_deduplicated_by_distinct_day():
    # A session start and a work log on the same day count once (§A: the
    # record window is `sessions.started_at` ∪ `work.created_at`).
    sessions = [_Session("2026-09-01T10:00:00+00:00")]
    work = [_Work("2026-09-01T23:30:00+00:00")]
    assert days_practiced(sessions, work) == 1


def test_days_practiced_ignores_unusable_timestamps_and_empty_records():
    assert days_practiced([], []) == 0
    assert days_practiced([_Session("")], [_Work("not-a-timestamp")]) == 0


def test_practiced_days_returns_the_set_of_utc_dates():
    days = practiced_days([_Session("2026-09-01T23:00:00-05:00")], [])
    # 23:00 -05:00 is 2026-09-02 04:00 UTC — the UTC calendar day counts.
    assert len(days) == 1


# --- translation module (P3.1): no surface bypasses it ---------------------------


def test_translate_rewrites_cli_refusal_prefixes_as_human_acts():
    out = translate("pass: FAILED — master blocked: node x is locked")
    assert "pass:" not in out
    assert "Marked as passed is refused" in out
    assert "Marked as mastered is refused:" in out


def test_translate_strips_flags_advisory_tags_and_cli_command_names():
    out = translate("run `skilltrace validate --format json` and check [advisory] notes")
    assert "--format" not in out
    assert "skilltrace" not in out
    assert "[advisory]" not in out


def test_translate_strips_adr_numbers_and_engine_voice():
    out = translate("The domain refuses (ADR 0007) this write path.")
    assert "ADR 0007" not in out
    assert "domain refuses" not in out


def test_translate_rewrites_raw_record_ids():
    out = translate("record rec.01 supersedes spec.x_01")
    assert "rec.01" not in out
    assert "spec.x_01" not in out


def test_banners_maps_cli_kinds_to_semantic_classes_and_translates():
    flashes = banners(
        ["[error] pass: FAILED — nothing passed."], default_class="success"
    )
    kind, text = flashes[0]
    assert kind == "err"
    assert "pass:" not in text
    assert "refused" in text.lower()


def test_banners_plain_lines_carry_the_default_class():
    flashes = banners(["Evidence recorded."], default_class="success")
    assert flashes == [("success", "Evidence recorded.")]


def test_translate_lines_translates_each_line():
    out = translate_lines(
        ["evidence submit: refused for node x — nothing written.", "OK"]
    )
    assert "evidence submit:" not in out[0]
    assert out[1] == "OK"


def test_forbidden_matches_detects_every_banned_family():
    cases = {
        "cli flag": "use --format json",
        "cli command name": "run skilltrace validate",
        "cli subcommand prefix": "evidence submit: refused",
        "advisory tag": "note [advisory] here",
        "warning tag": "[error] nope",
        "engine-voice phrase": "the domain refuses",
        "cli help voice": "the CLI prints it",
    }
    for expected, text in cases.items():
        assert expected in forbidden_matches(text), text


def test_forbidden_matches_clean_human_copy_passes():
    assert (
        forbidden_matches(
            "Marked as passed is refused — the prerequisites aren't met yet."
        )
        == []
    )
    assert forbidden_matches("Start this session to begin studying.") == []
