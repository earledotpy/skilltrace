"""The Health study-guidance roll-up (spec-tier1-serve §C-ter, build #311).

The Health view is the daily study-guidance roll-up: five cards in a fixed
order — Stuck right now → Due for review → Evidence gaps → Study rhythm →
Study resources — each carrying counts + one-line why + links. Full prose and
ranking live at the link target; Health points at ``today``/``node`` pages and
never repeats their recommendations.

Guardrails (§C-ter): repository diagnostics stay CLI-only with zero web-UI
presence; no composite health score; no streak/break/loss language; no
completion-ratio percent when the denominator is zero; below-target advisories
are suppressed under the soft data threshold in favor of limited-data copy;
nothing here blocks or implies blocking — every card is a read-only mirror or
advisory over already-computed facts.

All derivation reads the lenient ``JoinedView`` — one fresh join per request,
the same seam as every other GET page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..context import JoinedView
from ..execution.days import days_practiced
from ..resources.status import DEFAULT_STALE_AFTER_DAYS, VerificationStatus, derive_status

# The empty-copy contract (§C-ter) — locked wording, one source.
STUCK_EMPTY = "No open blockers — smooth sailing."
STUCK_EMPTY_HOWTO = "Log one from a skill page when you hit a wall."
REVIEWS_EMPTY = "No reviews scheduled — pass a skill to schedule checks."
EVIDENCE_EMPTY = "No gaps on active nodes."
RESOURCES_HEALTHY = "All supporting materials for your current skills are verified."

# Rhythm framing: the days-practiced mirror, never a metronome.
RHYTHM_MIRROR = "Days practiced is a mirror, not a metronome."

WINDOW_DAYS_FALLBACK = 30


@dataclass(frozen=True)
class GuidanceCard:
    """One Health card: counts + one-line why + links (§C-ter card contract)."""

    title: str
    why: str
    links: tuple[tuple[str, str], ...] = ()  # (human label, href) — page targets only
    notes: tuple[str, ...] = ()  # muted advisory/pointer lines


@dataclass(frozen=True)
class StudyGuidance:
    """The five-card derivation, order locked by §C-ter's home hierarchy."""

    cards: tuple[GuidanceCard, ...] = field(default_factory=tuple)
    limited_data_line: str | None = None


def _as_date(value: object) -> date | None:
    """Parse the leading ISO date out of a record timestamp, or None."""
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _node_links(view: JoinedView, node_ids: list[str]) -> tuple[tuple[str, str], ...]:
    """De-duplicated (title, /nodes/{id}) links for the given nodes, in order."""
    seen: set[str] = set()
    links: list[tuple[str, str]] = []
    for node_id in node_ids:
        if node_id in seen or node_id not in view.node_map:
            continue
        seen.add(node_id)
        links.append((view.node_map[node_id].title, f"/nodes/{node_id}"))
    return tuple(links)


def _stuck_card(view: JoinedView) -> GuidanceCard:
    """Stuck right now — open blockers plus the failed-attempts pointer.

    Blocked work never counts toward anything else; this card only mirrors it.
    """
    open_blockers = [b for b in view.blockers if b.status == "open"]
    failed_attempts = [a for a in view.attempts if a.outcome == "failed"]
    failed_reviews = [
        r for r in view.reviews if r.status == "completed" and r.outcome == "failed"
    ]
    notes: list[str] = []
    if failed_attempts or failed_reviews:
        notes.append(
            f"Recent failed attempts ({len(failed_attempts)}) and failed reviews "
            f"({len(failed_reviews)}) may need attention."
        )
    if not open_blockers:
        return GuidanceCard(
            title="Stuck right now",
            why=STUCK_EMPTY,
            notes=tuple(notes) if notes else (STUCK_EMPTY_HOWTO,),
        )
    why = (
        f"{len(open_blockers)} open blocker"
        f"{'s' if len(open_blockers) != 1 else ''} holding up work."
    )
    return GuidanceCard(
        title="Stuck right now",
        why=why,
        links=_node_links(view, [b.node_id for b in open_blockers]),
        notes=tuple(notes),
    )


def _due_card(view: JoinedView, today: date) -> GuidanceCard:
    """Due for review — due-now / overdue / next-scheduled counts only.

    No completion-ratio percent (the denominator can be zero); retention
    suggestions are labeled as suggestions with recomputed dates; the single
    due-date predicate and full ranking live at the detail surfaces Health
    links to, never duplicated here.
    """
    scheduled = [r for r in view.reviews if r.status == "scheduled"]
    dated = [(r, _as_date(r.scheduled_for)) for r in scheduled]
    overdue = [r for r, d in dated if d is not None and d < today]
    due_now = [r for r, d in dated if d == today]
    upcoming = sorted(
        ((d, r) for r, d in dated if d is not None and d > today), key=lambda p: p[0]
    )
    if not scheduled:
        return GuidanceCard(title="Due for review", why=REVIEWS_EMPTY)
    parts = [f"{len(due_now)} due today, {len(overdue)} overdue"]
    if upcoming:
        parts.append(f"{len(upcoming)} coming up (next {upcoming[0][0].isoformat()})")
    why = "; ".join(parts) + " — retention checks are suggestions, dates recomputed on each run"
    return GuidanceCard(
        title="Due for review",
        why=why,
        links=_node_links(view, [r.node_id for r in overdue + due_now]),
    )


def _gaps_card(view: JoinedView) -> GuidanceCard:
    """Evidence gaps — per-active-node missing-spec list.

    Attempt counts never read as eligibility; the missing proof, not the
    attempt tally, is what the card mirrors.
    """
    active = [n for n in view.nodes if view.store.state_of(n.id) == "active"]
    missing = [n for n in active if not view.specs_by_node.get(n.id)]
    if not missing:
        return GuidanceCard(title="Evidence gaps", why=EVIDENCE_EMPTY)
    why = (
        f"{len(missing)} active skill"
        f"{'s' if len(missing) != 1 else ''} still missing proof to pass."
    )
    return GuidanceCard(
        title="Evidence gaps",
        why=why,
        links=_node_links(view, [n.id for n in missing]),
        notes=("Attempts alone never count as eligibility — proof does.",),
    )


def _rhythm_card(view: JoinedView, today: date) -> tuple[GuidanceCard, str | None]:
    """Study rhythm — the days-practiced mirror plus logged-work context.

    Returns the card and, when the session count sits under the soft data
    threshold, the limited-data line that replaces any below-target advisory.
    """
    policy = view.policy.analytics_policy
    window_days = (
        policy.default_window_days
        if policy.default_window_days >= 1
        else WINDOW_DAYS_FALLBACK
    )
    min_sessions = policy.min_sessions_for_full_data
    cutoff = date.fromordinal(today.toordinal() - window_days)
    sessions_in_window = [
        s for s in view.sessions if (_as_date(s.started_at) or date.min) >= cutoff
    ]
    work_in_window = [
        w for w in view.work if (_as_date(w.created_at) or date.min) >= cutoff
    ]
    if len(sessions_in_window) < min_sessions:
        limited = (
            f"Limited data ({len(sessions_in_window)} sessions) — "
            "counts may not reflect your full activity."
        )
    else:
        limited = None
    why = (
        f"Logged {len(work_in_window)} work item"
        f"{'s' if len(work_in_window) != 1 else ''} this window."
    )
    return (
        GuidanceCard(
            title="Study rhythm",
            why=why,
            notes=(
                f"Days practiced: {days_practiced(view.sessions, view.work)}.",
                RHYTHM_MIRROR,
            ),
        ),
        limited,
    )


def _resources_card(view: JoinedView, today: date) -> GuidanceCard:
    """Study resources — only materials supporting active/available nodes.

    Broken/stale flags surface here; the full registry and the full
    verification report stay out (point + link, not a copy of the report).
    """
    current_nodes = {
        n.id for n in view.nodes if view.store.state_of(n.id) in {"active", "available"}
    }
    stale_after = DEFAULT_STALE_AFTER_DAYS
    seed = view.policies.get("resource_verification.yaml") or {}
    raw_window = seed.get("stale_after_days")
    if isinstance(raw_window, int) and not isinstance(raw_window, bool) and raw_window >= 1:
        stale_after = raw_window

    flagged_by_node: dict[str, list[str]] = {}
    total = 0
    seen: set[str] = set()
    for node_id, resources in view.resources_by_node.items():
        if node_id not in current_nodes:
            continue
        for resource in resources:
            if resource.id in seen:
                continue
            seen.add(resource.id)
            total += 1
            status = derive_status(resource, today=today, stale_after_days=stale_after)
            if status in (VerificationStatus.BROKEN, VerificationStatus.STALE):
                flagged_by_node.setdefault(node_id, []).append(status.value)
    if total == 0:
        return GuidanceCard(title="Study resources", why=RESOURCES_HEALTHY)
    flagged = sum(len(v) for v in flagged_by_node.values())
    if flagged == 0:
        return GuidanceCard(title="Study resources", why=RESOURCES_HEALTHY)
    why = (
        f"{flagged} of {total} supporting material"
        f"{'s' if total != 1 else ''} need re-checking (broken or stale)."
    )
    return GuidanceCard(
        title="Study resources",
        why=why,
        links=_node_links(view, sorted(flagged_by_node)),
        notes=("The full verification report lives on the command line.",),
    )


def derive_study_guidance(view: JoinedView, today: date) -> StudyGuidance:
    """The five Health cards in the §C-ter home-hierarchy order."""
    rhythm, limited = _rhythm_card(view, today)
    cards = (
        _stuck_card(view),
        _due_card(view, today),
        _gaps_card(view),
        rhythm,
        _resources_card(view, today),
    )
    return StudyGuidance(cards=cards, limited_data_line=limited)


def render_guidance_html(guidance: StudyGuidance) -> str:
    """The five cards as server-side HTML — order is the §C-ter hierarchy."""
    import html

    def esc(value: str) -> str:
        return html.escape(value, quote=True)

    parts: list[str] = []
    if guidance.limited_data_line:
        parts.append(f'<p class="banner advisory">{esc(guidance.limited_data_line)}</p>\n')
    for card in guidance.cards:
        parts.append('<div class="card guidance">\n')
        parts.append(f'<div class="kicker">{esc(card.title)}</div>\n')
        parts.append(f'<p class="big">{esc(card.why)}</p>\n')
        if card.links:
            parts.append('<ul class="guidance-links">\n')
            for label, href in card.links:
                parts.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>\n')
            parts.append("</ul>\n")
        for note in card.notes:
            parts.append(f'<p class="mut">{esc(note)}</p>\n')
        parts.append("</div>\n")
    return "".join(parts)
