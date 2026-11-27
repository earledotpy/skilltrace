"""Daily pages — reads (T3) and browser writes (T4) over structured cards.

The GET routes (`/`, `/next`, `/nodes/{id}`, `/health`) compose
:class:`web.interface.cards.Card` objects — the Richer Card vocabulary
(v2.4 §E) — and render them through ``interface.render`` (``render_rich_cards``,
``render_guidance_cards``, ``render_discovery_cards``). Derived ``MentorCard``
lists cross into Cards only through the one translation seam
(``interface.translate.rich_cards``); the interface renderer is the only
Card-to-HTML map (#320: the deprecated compat serializer is retired).

The write routes (T4+T5, G2#66 + G5#69) are thin glue over the *same* registry the
CLI dispatches through: a confirmed action builds ``Context(root, args,
source="web")`` and calls ``dispatch(REGISTRY.get(name), ctx)`` in-process —
no second write path, sole-caller invariant intact. Handler stdout is captured
and rendered through the one P3.1 translation module; ``CommandResult.exit_code``
is the contract: every POST → 303 + translated flash (``0`` ok, ``2`` domain
refusal as a warning flash, ``1`` operational failure as an error flash
pointing at /health). Pass/master refusals flash back to their own acceptance
step; every other write flashes back to the host page. Heavyweight confirmation stays
exclusive to ``pass``/``master`` (P4.3); every other daily write is a plain
single-step form. Buttons are never pre-disabled by derived preconditions — the domain's refusal
on click is the truth (G2), so a stale confirmation panel can never assert what
eligibility no longer supports.

Information architecture: the unified single-page home (v2.4 §A as amended by
map #243) — one hero focus viewport plus a six-card bento at the dense
register; every bento card is links-only and the hero carries the page's only
primary CTA; drill-downs and disclosures stay off the primary path, so no
JavaScript anywhere. Reads go through
the lenient ``JoinedView`` fresh per request.
"""

from __future__ import annotations

import re
from argparse import Namespace
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from ...analytics.derive import derive_analytics
from ...analytics.models import AnalyticsParams
from ...analytics.policy import limited_data_sentence
from ...analytics.sparkline import sparkline_svg
from ...commands.eligibility import passed_at_of
from ...commands.health import health_report
from ...commands.node_detail import (
    derive_node_detail,
    derive_node_drilldown,
)
from ...commands.recommend import derive_next
from ...commands.today import derive_today
from ...context import JoinedView, load_context_lenient
from ...dispatch import Context, dispatch
from ...evidence.eligibility import compute_eligibility, live_accepted_count
from ...execution.overdue import parse_date, utc_today
from ...execution.records import open_session
from ...execution.staleness import (  # noqa: F401 — the session views' seam
    stale_session_hours,
)
from ...graph.edges import EdgeLoadError
from ...graph.nodes import NodeLoadError
from ...graph.state import ProgressStoreError
from ...mentor.cards import (  # noqa: F401 — re-exported for view modules/tests
    Banner,
    Kicker,
    Label,
    Lead,
    MentorCard,
    NextAction,
    Pill,
    Sub,
    Title,
)
from ...policy.advisory import analytics_warnings
from ...policy.mastery import compute_mastery_eligibility
from ...resources.status import VerificationStatus
from ..analytics_tooltip import tooltip_script
from ..discovery import (
    ENTRY_NODES,
    DiscoveryCard,
    browse_cards,
    browse_subjects,
    card_for,
    curriculum_source_present,
    discover,
    discovery_page_cards,
)
from ..health import derive_study_guidance, guidance_page_cards, rhythm_facts
from ..interface.affordances import intent_label
from ..interface.cards import ActiveViewState, Affordance, Card, view_by_name
from ..interface.handoff import handoff_html
from ..interface.render import render_discovery_cards, render_guidance_cards, render_rich_cards
from ..interface.translate import rich_cards as _rich_cards_from_model

# The package's union surface (ADR 0009): every module's own names
# resolve on the facade, so a consumer never has to reach into a
# module to find one. The private helpers are re-exported for the same
# reason the public ones are — the union is the surface.
from ._clock import now_utc  # noqa: F401
from ._readiness import (  # noqa: F401
    ASSERTED_STATES,
    derive_readiness,
    every_skill_locked,
    hard_prerequisite_sources,
    stale_readiness,
    stale_readiness_section,
)
from ._reasons import (  # noqa: F401
    DEFAULT_MINUTES,
    Fact,
    downstream_count,
    facts_for,
    reason_for,
)
from ._shared import (  # noqa: F401  # noqa: F401
    _CANONICAL_STATE_LABELS,
    ASSURANCE,
    _curriculum_unreadable_section,
    _degraded_banner,
    _edge_is_valid,
    _empty_side,
    _esc,
    _field,
    _flash_html,
    _flash_tuples,
    _int_field,
    _linkify_health,
    _normalize_pill_label,
    _output_banners,
    _parse_int,
    _sentence_case,
    _session_node_id,
    _slug,
    _state_pill,
    _table,
    derive_status,
    plural,
    record_standing,
    resources_with_status,
    superseded_ids,
)
from .analytics import (  # noqa: F401
    _analytics_card,
    _analytics_controls,
    _analytics_export_form,
    _analytics_view,
    analytics_body,
)
from .evidence import (  # noqa: F401  # noqa: F401
    EvidenceFigures,
    _gate_line,
    _limited_state,
    _receipts_section,
    _recorded_rows,
    _still_to_do,
    _summary_facts,
    _wanted_rows,
    evidence_figures,
    node_evidence_body,
)
from .evidence_index import (  # noqa: F401  # noqa: F401
    _ACCEPTED_WORDS,
    _REJECTED_WORDS,
    _REQUIRED_SOURCES,
    _STANDING_KINDS,
    _empty_state,
    _failure_state,
    _filter_form,
    _gate_words,
    _matches,
    _node_options,
    _outcome_matches,
    _record_row,
    evidence_index_body,
)
from .finder import (  # noqa: F401
    _browse_html,
    _discovery_chrome,
    _link_or_name,
    _no_results_html,
    _render_results,
    finder_body,
)
from .forms import (  # noqa: F401
    START_ANNOUNCEMENT,
    _evidence_correction_form,
    _evidence_submit_form,
    _location_field,
    _manual_verdict_field,
    _note_field,
    _resolve_blocker_form,
    _spec_field,
    _start_confirm_form,
    _template_select,
    _work_form_fields,
)
from .graph import (  # noqa: F401  # noqa: F401
    _STATES,
    _ancestors,
    _dangling_section,
    _edge_rows,
    _edges_for,
    _graph_href,
    _neighborhood_rows,
    _node_rows,
    _state_filter_form,
    _valid_edges,
    graph_body,
)
from .health import (  # noqa: F401  # noqa: F401
    _GUIDANCE_SOURCES,
    _ROLLUP_CARD,
    _ROLLUP_CHROME,
    _card_chrome,
    _diagnostics_section,
    _findings_details,
    _findings_phrase,
    _findings_summary,
    _guidance_failure_section,
    _guidance_section,
    _layer_headline,
    _plain_counts,
    _relative_detail,
    health_body,
)
from .inspector import (  # noqa: F401  # noqa: F401
    _ACCEPTED_BY_WORDS,
    _FILTER_PARAMS,
    GRAPH_EDGE_PARAM,
    GRAPH_NODE_PARAM,
    SELECTED_PARAM,
    _accepted_by_words,
    _graph_refusal,
    _href,
    _inspector_aside,
    _kept_params,
    _provenance,
    _refusal,
    _related_lines,
    _status_label,
    evidence_inspector,
    graph_edge_inspector,
    graph_node_inspector,
    graph_selection,
    selected_value,
)
from .next import (  # noqa: F401  # noqa: F401
    MAX_EXPLAINED,
    MAX_OPTIONS,
    _candidate_stack,
    _not_ready_card,
    _not_ready_list,
    _why_details,
    next_body,
)
from .node import (  # noqa: F401  # noqa: F401
    _EDGE_WORDS,
    _STATE_WORDS,
    _attempts_section,
    _blockers_section,
    _brief_section,
    _degraded_notice,
    _drill_down_card,
    _empty,
    _events_section,
    _evidence_figures,
    _failure,
    _gate_section,
    _limited,
    _metadata_section,
    _node_actions_card,
    _node_records,
    _node_specs,
    _progress_section,
    _records_section,
    _relationships_section,
    _remediation_section,
    _resources_section,
    _reviews_section,
    _row,
    _rows,
    _schedule_review_form,
    _section,
    _specs_section,
    _state_label,
    _state_word,
    _technical,
    _unmet_specs,
    node_body,
)
from .operations import (  # noqa: F401
    THEMES,
    _capability_cards,
    _cards_section,
    _empty_curriculum_state,
    _recent_facts_section,
    operations_body,
    overdue_reviews,
)
from .portfolio import (  # noqa: F401  # noqa: F401
    _preview_section,
    _selection_form,
    portfolio_body,
)
from .receipts import (  # noqa: F401
    receipt_disclosure,
    receipt_rows,
)
from .reviews import (  # noqa: F401  # noqa: F401
    _derivation_failure_state,
    _history_section,
    _no_records_state,
    _nothing_to_check_state,
    _overdue_section,
    _records_failure_section,
    _retention_suggestions,
    _review_actions,
    _review_worthy_nodes,
    _schedule_form,
    _schedule_section,
    _scheduled_section,
    _suggestions_section,
    _unsatisfactory_section,
    is_overdue,  # noqa: F401
    reviews_body,
)
from .session import (  # noqa: F401  # noqa: F401
    _available_remediation,
    _blocked_work,
    _blocker_section,
    _create_blocker_offer,
    _duration,
    _evidence_section,
    _open_blocker_detail,
    _open_for_label,
    _open_hours,
    _other_open_note,
    _pass_facts,
    _resolved_blockers,
    _session_facts,
    _session_minutes,
    _session_rows,
    _stale,
    _stale_banner,
    _study_material,
    session_body,
    session_close_body,
)
from .shell import (  # noqa: F401  # noqa: F401
    _GUIDED_ORDER,
    _OPERATIONS_ORDER,
    _STYLE,
    MASTER_CONFIRM_PANEL,
    MASTER_FACTS_PANEL,
    PASS_PANEL,
    PASSED_PANEL,
    PanelKind,
    _chrome,
    _error_body,
    _fresh_join,
    _mode_from,
    _mode_link,
    _nav_html,
    _nav_links,
    _page_head,
    _panel_card,
    _panel_dismiss,
    _panel_shell,
    _status_page,
    not_found_body,
    page,
    route_default_mode,
)
from .steps import (  # noqa: F401  # noqa: F401
    MASTER_CONFIRM_ANCHOR,
    PASS_PANEL_ANCHOR,
    MasteryEligibility,
    MasteryReading,
    _accepted_records,
    _accepted_table,
    _accepted_total,
    _already_mastered_section,
    _confirm_form,
    _eligibility_facts,
    _eligibility_section,
    _gate_decision,
    _gate_kind_line,
    _master_confirm_form,
    _mastery_commands,
    _mastery_next_step,
    _mastery_reading,
    _mastery_reason_lines,
    _mastery_state_rows,
    _next_step,
    _pass_wanted_rows,
    _rejected_note,
    _review_consequence,
    _review_note,
    _satisfactory_review_line,
    date,
    first_spaced_satisfactory_review,
    master_body,
    master_confirm_body,
    pass_body,
)
from .styles import (  # noqa: F401
    _COMPONENT_RULES,
    root_blocks,
)
from .today import (  # noqa: F401  # noqa: F401
    MINUTES,
    _Action,
    _blocker_item,
    _derivation_state,
    _discovery_section,
    _empty_day_state,
    _Item,
    _open_blocker_records,
    _overdue_reviews,
    _pass_eligible_node,
    _pass_item,
    _queue_item,
    _queue_items,
    _queue_section,
    _recommendation_item,
    _refusal_state,
    _review_item,
    _session_item,
    _study_day_section,
    _unavailable_parts,
    _unavailable_state,
    home_body,
)
from .writes import (  # noqa: F401
    Redirect,
    _context_params,
    _dispatch_web,
    _finish_write,
    _redirect_with_notice,
    _safe_next,
    _start_refusal_url,
    post_analytics_export,
    post_blocker_create,
    post_blocker_resolve,
    post_evidence,
    post_master_confirm,
    post_pass,
    post_portfolio_export,
    post_review_cancel,
    post_review_complete,
    post_review_schedule,
    post_session_close,
    post_start,
    post_work,
)

# The package's public surface. The union of every module's names
# resolves on the facade (ADR 0009), and this list names the public
# half of it: the names a consumer may import, and the private
# helpers the package's own modules share.
__all__ = [
    "ASSERTED_STATES",
    "Affordance",
    "AnalyticsParams",
    "BARE",
    "Card",
    "Context",
    "DEFAULT_MINUTES",
    "DiscoveryCard",
    "EMPTY",
    "ENTRY_NODES",
    "EvidenceFigures",
    "EdgeLoadError",
    "FAILURE",
    "Fact",
    "HEAD",
    "INLINE",
    "JoinedView",
    "LIMITED",
    "MAX_EXPLAINED",
    "MAX_OPTIONS",
    "Markup",
    "NONE",
    "Namespace",
    "NodeLoadError",
    "Path",
    "ProgressStoreError",
    "RECOVERY",
    "REFUSAL",
    "Redirect",
    "Rows",
    "SELECTED_PARAM",
    "START_ANNOUNCEMENT",
    "STATES",
    "Section",
    "State",
    "StringIO",
    "Table",
    "VerificationStatus",
    "analytics_body",
    "analytics_warnings",
    "annotations",
    "ASSURANCE",
    "browse_cards",
    "browse_subjects",
    "compute_eligibility",
    "compute_mastery_eligibility",
    "curriculum_source_present",
    "dataclass",
    "derive_analytics",
    "derive_next",
    "derive_readiness",
    "derive_status",
    "derive_study_guidance",
    "discover",
    "discovery_page_cards",
    "dispatch",
    "downstream_count",
    "every_skill_locked",
    "evidence_figures",
    "evidence_index_body",
    "evidence_inspector",
    "_evidence_correction_form",
    "_gate_line",
    "_limited_state",
    "_location_field",
    "_manual_verdict_field",
    "_note_field",
    "_receipts_section",
    "_spec_field",
    "_still_to_do",
    "_summary_facts",
    "receipt_disclosure",
    "receipt_rows",
    "facts_for",
    "field",
    "finder_body",
    "graph_body",
    "guidance_page_cards",
    "hard_prerequisite_sources",
    "health_body",
    "health_report",
    "home_body",
    "is_overdue",
    "limited_data_sentence",
    "live_accepted_count",
    "load_context_lenient",
    "master_body",
    "master_confirm_body",
    "next_body",
    "node_body",
    "node_evidence_body",
    "not_found_body",
    "now_utc",
    "open_session",
    "operations_body",
    "page",
    "pass_body",
    "passed_at_of",
    "plural",
    "portfolio_body",
    "post_analytics_export",
    "post_blocker_create",
    "post_blocker_resolve",
    "post_evidence",
    "post_master_confirm",
    "post_pass",
    "post_portfolio_export",
    "post_review_cancel",
    "post_review_complete",
    "post_review_schedule",
    "post_session_close",
    "post_start",
    "post_work",
    "re",
    "reason_for",
    "record_standing",
    "resources_with_status",
    "redirect_stdout",
    "render",
    "render_discovery_cards",
    "render_guidance_cards",
    "reviews_body",
    "rhythm_facts",
    "root_blocks",
    "route_default_mode",
    "section",
    "selected_value",
    "session_body",
    "session_close_body",
    "sparkline_svg",
    "stale_readiness",
    "stale_readiness_section",
    "superseded_ids",
    "tooltip_script",
    "urlencode",
    "utc_today",

]

# The structured section data the pages render from (ADR 0006
# escalation 1). Its names resolve on the facade with the rest of the
# union.
from dataclasses import field  # noqa: F401 — the sections module's own import

from .sections import (  # noqa: F401
    BARE,
    EMPTY,
    FAILURE,
    HEAD,
    INLINE,
    LIMITED,
    NONE,
    RECOVERY,
    REFUSAL,
    STATES,
    Markup,
    Rows,
    Section,
    State,
    Table,
    render,
    section,
)
