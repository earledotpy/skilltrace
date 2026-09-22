"""Daily pages — reads (T3) and browser writes (T4) over structured cards.

The GET routes (`/`, `/next`, `/nodes/{id}`, `/health`) compose
:class:`web.interface.cards.Card` objects — the Richer Card vocabulary
(v2.4 §E) — and render them through ``interface.render.render_rich_cards``.
Derived ``MentorCard`` lists cross into Cards only through the one
translation seam (``interface.translate.rich_cards``); the old part-to-HTML
map (:func:`render_cards`) survives solely as the deprecated-compat
serializer behind :func:`cards_html` for out-of-scope line producers
(health liveness, report exports) — no route body composes MentorCards
directly any more.

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
on click is the truth (G2), so a stale modal can never assert what eligibility
no longer supports.

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
from ...commands.eligibility import passed_at_of
from ...commands.health import health_report
from ...commands.node_detail import (
    derive_node_drilldown,
    derive_node_detail,
)
from ...commands.recommend import derive_next
from ...commands.today import derive_today
from ...mentor.cards import (
    Banner,
    Kicker,
    Label,
    Lead,
    MentorCard,
    NextAction,
    Pill,
    Sub,
    Title,
    lines_to_cards,
)
from ...context import JoinedView, load_context_lenient
from ...dispatch import Context, dispatch
from ..discovery import (
    ENTRY_NODES,
    DiscoveryCard,
    browse_cards,
    browse_subjects,
    card_for,
    discover,
)
from ..health import derive_study_guidance, render_guidance_html
from ..interface.affordances import intent_label
from ..interface.cards import ActiveViewState, Affordance, Card, view_by_name
from ..interface.handoff import handoff_html
from ..interface.render import render_rich_cards
from ..interface.translate import rich_cards as _rich_cards_from_model
from ...analytics.derive import derive_analytics
from ...analytics.models import AnalyticsParams
from ...analytics.policy import limited_data_sentence
from ...analytics.sparkline import sparkline_svg
from ..analytics_tooltip import tooltip_script
from ...evidence.eligibility import compute_eligibility, live_accepted_count
from ...execution.overdue import parse_date, utc_today
from ...execution.records import open_session
from ...graph.edges import EdgeLoadError
from ...graph.nodes import NodeLoadError
from ...graph.state import ProgressStoreError
from ...policy.mastery import compute_mastery_eligibility
from ...policy.advisory import analytics_warnings
from ...resources.status import VerificationStatus

from ._shared import (  # noqa: F401
    _CANONICAL_STATE_LABELS,
    _degraded_banner,
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
    _slug,
    _table,
    plural,
)
from .shell import (  # noqa: F401
    _STYLE,
    _chrome,
    _error_body,
    _fresh_join,
    _modal_shell,
    _nav_html,
    _status_page,
    not_found_body,
    page,
)
from .compat import (  # noqa: F401
    _render_card_inner,
    _render_part,
    cards_html,
    render_cards,
)
from .forms import (  # noqa: F401
    _evidence_submit_form,
    _resolve_blocker_form,
    _start_confirm_form,
    _template_select,
    _work_form_fields,
)
from .writes import (  # noqa: F401
    Redirect,
    _dispatch_web,
    _finish_write,
    _redirect_with_notice,
    _safe_next,
    post_analytics_export,
    post_blocker_create,
    post_blocker_resolve,
    post_evidence,
    post_master_confirm,
    post_pass,
    post_session_close,
    post_start,
    post_work,
)
from .today import (  # noqa: F401
    _MONTH_ABBREVS,
    _STATE_REASONS,
    _WEEKDAY_NAMES,
    _browse_card,
    _continue_cta,
    _date_label,
    _focus_resources,
    _hero_block,
    _hero_why,
    _history_card,
    _pressure_card,
    _queue_card,
    _spine_card,
    _utc_day,
    _week_card,
    home_body,
)
from .next import (  # noqa: F401
    _candidate_stack,
    _not_ready_card,
    _not_ready_list,
    _why_details,
    next_body,
)
from .finder import (  # noqa: F401
    _browse_html,
    _discovery_card_html,
    _no_results_html,
    finder_body,
)
from .node import (  # noqa: F401
    _drill_down_card,
    _node_actions_card,
    node_body,
)
from .health import (  # noqa: F401
    health_body,
)
from .analytics import (  # noqa: F401
    _analytics_card,
    _analytics_export_form,
    _analytics_view,
    analytics_body,
)
from .steps import (  # noqa: F401
    _STATUS_PILL_CLASSES,
    _mastery_facts_html,
    master_body,
    master_confirm_body,
    pass_modal_body,
)
