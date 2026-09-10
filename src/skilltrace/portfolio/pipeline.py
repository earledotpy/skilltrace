"""Deep portfolio pipeline — one seam for selection + redaction (issue #203).

``build_portfolio(joined, options, *, today)`` is the production pipeline:
from one ``JoinedView`` and share options it produces a share-ready
``PortfolioView``. Selection (``selection.select``) and share-profile
redaction (``redaction.redact_node_block`` over
``redaction.block_to_report_dict``) happen inside this module; Markdown /
HTML / JSON / bundle renderers only format what the view already carries.

The default-deny share profile is preserved: paths, notes, blockers,
reviews, free-text, and urls dimensions stay denied unless the matching
``include_*`` override is set. Gate-run receipts ride the *paths*
dimension via ``gate_receipt.for_share`` (through ``redaction``) — denied
paths drop the whole receipt.

The wall clock enters only as the injected ``today`` keyword — this module
never reads the clock itself.
"""

from __future__ import annotations

import datetime

from ..context import JoinedView
from .models import PortfolioView, SelectionOptions


def build_portfolio(
    joined: JoinedView,
    options: SelectionOptions,
    *,
    today: datetime.date,
) -> PortfolioView:
    """Derive the share-ready portfolio snapshot from joined truth.

    Single joined load: policy defaults (staleness window) and selection
    read the same ``joined`` — callers must not reload solely for policy
    values. Renderers must not re-apply redaction after this pipeline.
    """
    from .export import compute_honesty_banners
    from .redaction import block_to_report_dict, redact_node_block
    from .selection import select

    raw_nodes = select(joined, options)
    window = joined.policy.portfolio.resource_staleness_days
    banners = compute_honesty_banners(
        raw_nodes, today=today, staleness_days=window
    )
    redacted_blocks = [
        redact_node_block(block_to_report_dict(node, options), options)
        for node in raw_nodes
    ]
    return PortfolioView(
        selection=options,
        nodes=redacted_blocks,
        honesty_banners=banners,
        generated_at=f"{today.isoformat()}T00:00:00Z",
    )
