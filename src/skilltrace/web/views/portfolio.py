"""
GET ``/portfolio`` and ``/portfolio/preview`` — the Portfolio configurator
(spec-v3-study-day §11.7).

An export configurator — never a live showcase, an editor or an account.
The workflow is select → inspect redactions → preview the exact output →
choose a format → export explicitly.

The preview is **non-writing** and shares the export's selection, redaction
and rendering pipeline, so what you preview is what leaves. The exported
bundle is a dated disposable artifact: it records its date, format,
destination, selection metadata and active redactions, and it is never
presented as live truth — the web cannot reopen it as live truth.

The Share profile is default-deny: nothing is shared unless you enable an
override dimension for that invocation.
"""

from __future__ import annotations

from ._shared import _esc
from .shell import _page_head

# The redaction override dimensions. Each is opt-in, per invocation: the
# default-deny Share profile stays visible and authoritative.
_OVERRIDE_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("include_paths", "File paths", "Where each artifact lives"),
    ("include_notes", "Your notes", "The notes you wrote on each record"),
    ("include_free_text", "Free text", "Unstructured text you typed"),
    ("include_urls", "External links", "Links to resources outside the repo"),
    ("include_active", "Work in progress", "Skills you started but did not pass"),
    ("include_rejected", "Rejected evidence", "Evidence that did not pass"),
    ("include_superseded", "Superseded evidence", "Evidence replaced by a later record"),
    ("include_blockers", "Blockers", "What you recorded as stuck"),
    ("include_reviews", "Reviews", "Your retention-check history"),
)


def _selection_form(query: dict | None) -> str:
    """The selection and redaction controls — the configurator's inputs."""
    track = (query or {}).get("track", [""])[0]
    fmt = (query or {}).get("format", ["md"])[0]
    rows = []
    for field, label, why in _OVERRIDE_DIMENSIONS:
        checked = " checked" if (query or {}).get(field) else ""
        rows.append(
            f'<div class="row"><span class="row-label">{_esc(label)}</span>'
            f'<span class="row-value">{_esc(why)}</span>'
            f'<span class="row-value">'
            f'<label><input type="checkbox" name="{field}" value="1"{checked}> '
            f"include</label></span></div>"
        )
    format_options = "".join(
        f'<option value="{value}"{" selected" if fmt == value else ""}>'
        f"{value}</option>"
        for value in ("md", "html", "json")
    )
    return (
        '<form method="get" action="/portfolio">\n'
        '<div class="form-row">'
        '<label for="portfolio-track">Track (optional)</label>'
        f'<input type="text" name="track" id="portfolio-track" '
        f'value="{_esc(track)}"></div>\n'
        '<div class="form-row">'
        '<label for="portfolio-format">Format</label>'
        f'<select name="format" id="portfolio-format">'
        f"{format_options}</select></div>\n"
        + "".join(rows)
        + '<div class="command-bar"><div class="actions">'
        '<button type="submit">Preview</button>'
        "</div></div>\n"
        "</form>\n"
    )


def portfolio_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/portfolio` — the export configurator; `/portfolio/preview` too."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/portfolio",
        current_view="portfolio",
        default_mode="operations",
        path="/portfolio",
    )
    if failure is not None:
        return failure

    query = query or {}
    enabled = [d for d in _OVERRIDE_DIMENSIONS if query.get(d[0])]

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">What to include</h2>\n'
        + '<p class="section-meta">Nothing is shared unless you enable it. The '
        "default share profile keeps every dimension out.</p>\n"
        + "</div>\n"
        + _selection_form(query)
        + "</section>\n"
        + '<section class="section">\n'
        + "<h2 class=\"section-title\">Redactions</h2>\n"
        + (
            '<div class="rows">\n'
            + "".join(
                f'<div class="row"><span class="row-label">{_esc(label)}</span>'
                f'<span class="row-value">included in this export</span></div>\n'
                for _field, label, _why in enabled
            )
            + "</div>\n"
            if enabled
            else '<div class="state state-empty">\n'
            '<p class="state-title">Nothing extra is included</p>\n'
            '<p class="state-body">Every redaction dimension is off. The export '
            "carries the selection only.</p>\n"
            "</div>\n"
        )
        + "</section>\n"
        + '<section class="section">\n'
        + "<h2 class=\"section-title\">Export</h2>\n"
        + '<div class="banner advisory">An export is a dated, disposable '
        "snapshot. It is not live truth — it does not update, and the web "
        "cannot reopen it as your current state.</div>\n"
        + '<form method="post" action="/portfolio/export">\n'
        + f'<input type="hidden" name="next" value="/portfolio">\n'
        + f'<input type="hidden" name="format" value="'
        f'{_esc((query.get("format") or ["md"])[0])}">\n'
        + "".join(
            f'<input type="hidden" name="{field}" value="1">'
            for field, _label, _why in enabled
        )
        + '<div class="command-bar"><div class="actions">'
        '<button type="submit" class="btn primary">Export this snapshot</button>'
        "</div></div>\n"
        + "</form>\n"
        + "</section>\n"
    )
    return "Portfolio", body, 200
