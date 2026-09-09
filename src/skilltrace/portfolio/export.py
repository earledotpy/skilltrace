"""Portfolio derivation and rendering (v2.0 spec §4–§5).

``build_view`` derives the snapshot from live truth; ``render_markdown``,
``render_html``, and ``render_json`` render it. Preview and export share this
pipeline (CONTEXT.md: preview uses the same selection, redaction, and
rendering pipeline as export). The wall clock enters only as the injected
``today`` keyword — no module reads the clock itself (§8.1).
"""

from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

from ..context import JoinedView, load_context_strict
from .models import PortfolioView, SelectedNode, SelectionOptions
from .redaction import (
    REDACTED,
    block_to_report_dict,
    redaction_notices,
    redact_node_block,
    visible_receipt,
    visible_url,
)

#: Honesty-banner trigger phrases (spec §4.3). Named verbatim in the banner.
TRIGGER_SUPERSEDED = "superseded evidence"
TRIGGER_STALE = "stale resources"
TRIGGER_UNVERIFIED = "unverified claims"

_BANNER_TEMPLATE = (
    "[honesty] This portfolio contains {triggers}. Review before sharing."
)


class PortfolioExportError(Exception):
    """Raised when data cannot be loaded; the command refuses with no output."""


# ---------------------------------------------------------------------------
# Honesty banners
# ---------------------------------------------------------------------------


def _resource_is_stale(resource: dict, *, today: datetime.date, window: int) -> bool:
    """A linked resource whose ``last_verified`` exceeds the policy window.

    A stored broken marker dominates the derived statuses in reports, so it
    surfaces under the stale-resources trigger too.
    """
    if resource.get("broken"):
        return True
    last = resource.get("last_verified")
    if not last or not isinstance(last, str):
        return False
    try:
        verified_on = datetime.date.fromisoformat(last)
    except ValueError:
        return False
    return (today - verified_on).days > window


def _resource_is_unverified(resource: dict) -> bool:
    """A linked resource with no usable verification date (and no broken mark)."""
    if resource.get("broken"):
        return False
    last = resource.get("last_verified")
    if not last or not isinstance(last, str):
        return True
    try:
        datetime.date.fromisoformat(last)
    except ValueError:
        return True
    return False


def compute_honesty_banners(
    nodes: list[SelectedNode],
    *,
    today: datetime.date,
    staleness_days: int,
) -> list[str]:
    """Derive the informational honesty banner(s) for a selection.

    One banner naming every trigger present; empty when there is nothing to
    disclose. Never blocks export, never alters state or eligibility.
    """
    triggers: list[str] = []
    if any(n.has_superseded for n in nodes):
        triggers.append(TRIGGER_SUPERSEDED)
    if any(
        _resource_is_stale(res, today=today, window=staleness_days)
        for n in nodes
        for res in n.resources
    ):
        triggers.append(TRIGGER_STALE)
    if any(n.has_unverified_claim for n in nodes) or any(
        _resource_is_unverified(res) for n in nodes for res in n.resources
    ):
        triggers.append(TRIGGER_UNVERIFIED)
    if not triggers:
        return []
    return [_BANNER_TEMPLATE.format(triggers=", ".join(triggers))]


# ---------------------------------------------------------------------------
# View construction
# ---------------------------------------------------------------------------


def build_view(
    joined: JoinedView,
    options: SelectionOptions,
    *,
    today: datetime.date,
) -> PortfolioView:
    """Derive the portfolio snapshot from the joined truth files."""
    from .selection import select

    nodes = select(joined, options)
    window = joined.policy.portfolio.resource_staleness_days
    banners = compute_honesty_banners(
        nodes, today=today, staleness_days=window
    )
    return PortfolioView(
        selection=options,
        nodes=nodes,
        honesty_banners=banners,
        generated_at=f"{today.isoformat()}T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Shared report helpers
# ---------------------------------------------------------------------------


def _selection_summary(options: SelectionOptions) -> str:
    scope = f"track={options.track}" if options.track is not None else "all tracks"
    if options.nodes:
        scope += f", nodes={','.join(options.nodes)}"
    return scope


# ---------------------------------------------------------------------------
# Markdown renderer (spec §5.1)
# ---------------------------------------------------------------------------


def render_markdown(
    view: PortfolioView,
    options: SelectionOptions,
    *,
    links: dict[str, str] | None = None,
) -> str:
    """Compact per-project sections with tables; plain-text readable."""
    link_map = links or {}
    lines = [
        "# Portfolio",
        "",
        f"Generated: {view.generated_at}",
        f"Selection: {_selection_summary(options)} "
        f"({view.summary['node_count']} node(s))",
        "",
    ]
    for banner in view.honesty_banners:
        lines.append(banner)
        lines.append("")
    for notice in redaction_notices(options):
        lines.append(notice)
    if view.honesty_banners or redaction_notices(options):
        lines.append("")
    if not view.nodes:
        lines.append("(no nodes match the selection)")
        return "\n".join(lines) + "\n"
    for node in view.nodes:
        raw = block_to_report_dict(node, options)
        redacted = redact_node_block(raw, options)
        lines.append(f"## {node.title} ({node.node_id}) — {node.state}")
        lines.append("")
        lines.append("| Evidence | Location |")
        lines.append("| --- | --- |")
        if not redacted["evidence"]:
            lines.append("| (none) | - |")
        for item in redacted["evidence"]:
            loc = item["location"]
            if loc != REDACTED and loc in link_map:
                loc = link_map[loc]
            lines.append(f"| {item['id']} | {loc} |")
        if options.include_blockers and redacted["blockers"]:
            lines.append("")
            lines.append("| Blocker | Description |")
            lines.append("| --- | --- |")
            for item in redacted["blockers"]:
                lines.append(f"| {item['id']} | {item['description']} |")
        if options.include_reviews and redacted["reviews"]:
            lines.append("")
            lines.append("| Review | Summary |")
            lines.append("| --- | --- |")
            for item in redacted["reviews"]:
                lines.append(f"| {item['id']} | {item['result_summary']} |")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# HTML renderer (spec §5.2)
# ---------------------------------------------------------------------------

_HTML_STYLE = (
    "body { font-family: system-ui, sans-serif; margin: 1rem 2rem; "
    "background: #fff; color: #222; } "
    "h1 { font-size: 1.4rem; } "
    "h2 { font-size: 1.1rem; border-bottom: 1px solid #ddd; } "
    "table { border-collapse: collapse; font-size: 0.85rem; } "
    "th, td { border: 1px solid #ccc; padding: 0.2rem 0.5rem; text-align: left; } "
    ".honesty { background: #fff3e0; border-left: 3px solid #e65100; "
    "padding: 0.3rem 0.6rem; } "
    ".redacted { background: #f5f5f5; border-left: 3px solid #9e9e9e; "
    "padding: 0.3rem 0.6rem; } "
    ".preview-only { font-size: 0.8rem; color: #666; }"
)


def render_html(
    view: PortfolioView,
    options: SelectionOptions,
    *,
    links: dict[str, str] | None = None,
) -> str:
    """Self-contained HTML: one inline ``<style>``, zero JavaScript."""
    link_map = links or {}
    parts = [
        f"<h1>Portfolio</h1>",
        f"<p>Generated: {html.escape(view.generated_at)}</p>",
        (
            "<p>Selection: "
            f"{html.escape(_selection_summary(options))} "
            f"({view.summary['node_count']} node(s))</p>"
        ),
        '<p class="preview-only">Preview — generated snapshot, not a live view.</p>',
    ]
    for banner in view.honesty_banners:
        parts.append(f'<div class="honesty">{html.escape(banner)}</div>')
    for notice in redaction_notices(options):
        parts.append(f'<div class="redacted">{html.escape(notice)}</div>')
    if not view.nodes:
        parts.append("<p>(no nodes match the selection)</p>")
    for node in view.nodes:
        raw = block_to_report_dict(node, options)
        redacted = redact_node_block(raw, options)
        parts.append(
            f"<h2>{html.escape(node.title)} "
            f"({html.escape(node.node_id)}) — {html.escape(node.state)}</h2>"
        )
        rows = ""
        if not redacted["evidence"]:
            rows = "<tr><td>(none)</td><td>-</td></tr>"
        for item in redacted["evidence"]:
            loc = item["location"]
            if loc != REDACTED and loc in link_map:
                loc = link_map[loc]
            rows += (
                f"<tr><td>{html.escape(str(item['id']))}</td>"
                f"<td>{html.escape(str(loc))}</td></tr>"
            )
        parts.append(
            "<table><thead><tr><th>Evidence</th><th>Location</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )
        if redacted["resources"]:
            res_rows = "".join(
                f"<tr><td>{html.escape(str(r['id']))}</td>"
                f"<td>{html.escape(str(visible_url(r['url'], include_urls=options.include_urls)))}</td></tr>"
                for r in redacted["resources"]
            )
            parts.append(
                "<table><thead><tr><th>Resource</th><th>URL</th></tr></thead>"
                f"<tbody>{res_rows}</tbody></table>"
            )
    body = "\n".join(parts)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Portfolio</title>\n"
        f"<style>\n{_HTML_STYLE}\n</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# JSON renderer (spec §5.3 — the stable published contract)
# ---------------------------------------------------------------------------


def render_json(
    view: PortfolioView,
    options: SelectionOptions,
    *,
    links: dict[str, str] | None = None,
) -> str:
    """Render the stable JSON contract (never a 1:1 mirror of internals)."""
    link_map = links or {}
    nodes = []
    for node in view.nodes:
        raw = block_to_report_dict(node, options)
        redacted = redact_node_block(raw, options)
        evidence = []
        for item in redacted["evidence"]:
            loc = item["location"]
            if loc != REDACTED and loc in link_map:
                loc = link_map[loc]
            receipt = visible_receipt(item.get("gate_run"), include_paths=options.include_paths)
            entry = {"id": item["id"], "location": loc, "note": item["note"]}
            if receipt is not None:
                entry["gate_run"] = receipt
            evidence.append(entry)
        artifacts = [
            link_map.get(loc, loc) if loc != REDACTED else loc
            for loc in redacted["artifacts"]
        ]
        nodes.append(
            {
                "node_id": node.node_id,
                "state": node.state,
                "title": node.title,
                "evidence": evidence,
                "artifacts": artifacts,
            }
        )
    payload = {
        "generated_at": view.generated_at,
        "selection": {
            "track": options.track,
            "include_active": options.include_active,
            "include_rejected": options.include_rejected,
            "include_superseded": options.include_superseded,
            "nodes": list(options.nodes),
            "include_paths": options.include_paths,
            "include_notes": options.include_notes,
            "include_blockers": options.include_blockers,
            "include_reviews": options.include_reviews,
            "include_free_text": options.include_free_text,
            "include_urls": options.include_urls,
        },
        "honesty_banners": list(view.honesty_banners),
        "nodes": nodes,
        "summary": view.summary,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Preview entry point (stdout or single file — no bundle)
# ---------------------------------------------------------------------------

_PREVIEW_EXTENSIONS = {"md": "md", "html": "html", "json": "json"}


def normalize_format(fmt: str) -> str:
    """Accept ``md``/``markdown``, ``html``, ``json`` spellings."""
    normalized = (fmt or "md").lower()
    if normalized == "markdown":
        return "md"
    if normalized not in _PREVIEW_EXTENSIONS:
        raise PortfolioExportError(
            f"Unknown portfolio format: {fmt!r} (expected md, html, or json)."
        )
    return normalized


def render_preview(
    view: PortfolioView, options: SelectionOptions, *, fmt: str
) -> str:
    """Render one format through the shared pipeline (preview == export)."""
    fmt = normalize_format(fmt)
    if fmt == "md":
        return render_markdown(view, options)
    if fmt == "html":
        return render_html(view, options)
    return render_json(view, options)


def load_view_or_raise(
    root: Path,
    options: SelectionOptions,
    *,
    today: datetime.date,
) -> PortfolioView:
    """Strict-load truth files and derive the view; refuse on any load error."""
    joined: JoinedView = load_context_strict(root)
    if not joined.ok:
        raise PortfolioExportError(
            "Cannot build portfolio — data load failed:\n"
            + "\n".join(f"  {e}" for e in joined.errors)
        )
    return build_view(joined, options, today=today)
