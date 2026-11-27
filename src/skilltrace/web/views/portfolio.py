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
override dimension for that invocation. The redaction outcome is shown
before the preview, so the learner sees exactly what would leave.
"""

from __future__ import annotations

from ._shared import _esc
from .sections import section
from .shell import _page_head

#: Selection overrides: they widen what is *selected*, never a redaction.
_SELECTION_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("include_active", "Work in progress", "Skills you started but did not pass"),
    ("include_rejected", "Rejected evidence", "Evidence that did not pass"),
    (
        "include_superseded",
        "Superseded evidence",
        "Evidence replaced by a later record",
    ),
)

#: Redaction overrides: each is opt-in, per invocation. The default-deny
#: Share profile stays visible and authoritative.
_REDACTION_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("include_paths", "File paths", "Where each artifact lives"),
    ("include_notes", "Your notes", "The notes you wrote on each record"),
    ("include_free_text", "Free text", "Unstructured text you typed"),
    ("include_urls", "External links", "Links to resources outside the repo"),
    ("include_blockers", "Blockers", "What you recorded as stuck"),
    ("include_reviews", "Reviews", "Your retention-check history"),
)

def _track_value(query: dict | None) -> str:
    """The track preset shown in the form.

    The bare configurator starts with no preset: it lists every finished
    skill, and a preset is something the learner applies deliberately.
    Checked skills and a track are both selection filters, exactly as the
    engine's ``portfolio`` command applies them.
    """
    query = query or {}
    return (query.get("track") or [""])[0].strip()


def _has_explicit_selection(query: dict | None) -> bool:
    """True when the learner has named skills or a track preset.

    The spec's default-deny workflow starts with nothing selected: an
    export is configured explicitly, never silently widened to every
    finished skill.
    """
    query = query or {}
    nodes = tuple(node for node in (query.get("node") or ()) if node)
    return bool(nodes or _track_value(query))


def _format_value(view, query: dict | None) -> str:
    query = query or {}
    fmt = (query.get("format") or [view.policy.portfolio.default_format])[0]
    return fmt if fmt in {"md", "html", "json"} else "md"


def _eligible_nodes(view, query: dict | None) -> list:
    """The skills the engine's selection admits (finished, plus active on request)."""
    from ...portfolio.models import SelectionOptions
    from ...portfolio.selection import select

    query = query or {}
    options = SelectionOptions(
        track=None,
        include_active=bool(query.get("include_active")),
    )
    return sorted(
        select(view, options),
        key=lambda node: (node.title.lower(), node.node_id),
    )


def _selection_form(view, query: dict | None, track: str, fmt: str) -> str:
    """The selection and redaction controls — the configurator's inputs."""
    query = query or {}
    selected = set(query.get("node") or ())
    eligible = _eligible_nodes(view, query)
    skill_rows = "".join(
        '<div class="row"><span class="row-label">'
        f'<label><input type="checkbox" name="node" value="{_esc(node.node_id)}"'
        f'{" checked" if node.node_id in selected else ""}> {_esc(node.title)}</label>'
        f'</span><span class="row-value small mut">'
        f"{_esc(node.state)}</span></div>"
        for node in eligible
    )
    if not eligible:
        skill_rows = (
            '<p class="small mut">No finished skills to choose yet. Include '
            "work in progress below to export an active skill.</p>\n"
        )

    format_options = "".join(
        f'<option value="{value}"{" selected" if fmt == value else ""}>'
        f"{value}</option>"
        for value in ("md", "html", "json")
    )
    selection_rows = "".join(
        f'<div class="row"><span class="row-label">{_esc(label)}</span>'
        f'<span class="row-value">{_esc(why)}</span>'
        f'<span class="row-value">'
        f'<label><input type="checkbox" name="{field}" value="1"'
        f'{" checked" if query.get(field) else ""}> include</label></span></div>'
        for field, label, why in _SELECTION_DIMENSIONS
    )
    redaction_rows = "".join(
        f'<div class="row"><span class="row-label">{_esc(label)}</span>'
        f'<span class="row-value">{_esc(why)}</span>'
        f'<span class="row-value">'
        f'<label><input type="checkbox" name="{field}" value="1"'
        f'{" checked" if query.get(field) else ""}> include</label></span></div>'
        for field, label, why in _REDACTION_DIMENSIONS
    )

    return (
        '<form method="get" action="/portfolio/preview">\n'
        '<div class="form-row">'
        '<label for="portfolio-track">Track preset (optional)</label>'
        f'<input type="text" name="track" id="portfolio-track" '
        f'value="{_esc(track)}">'
        '<p class="small mut">Narrows the selection. Checked skills below take '
        "precedence; leave this blank to use them across tracks.</p></div>\n"
        '<div class="form-row">'
        '<label for="portfolio-format">Format</label>'
        f'<select name="format" id="portfolio-format">'
        f"{format_options}</select></div>\n"
        '<fieldset class="selection"><legend>Skills</legend>\n'
        f"{skill_rows}</fieldset>\n"
        '<fieldset class="selection"><legend>Selection overrides</legend>\n'
        f"{selection_rows}</fieldset>\n"
        '<fieldset class="selection"><legend>Redaction overrides</legend>\n'
        f"{redaction_rows}</fieldset>\n"
        '<div class="command-bar"><div class="actions">'
        '<button type="submit">Preview</button>'
        "</div></div>\n"
        "</form>\n"
    )


def _redaction_outcome(query: dict | None) -> str:
    """The redaction outcome, stated before anything leaves.

    Every redaction dimension is shown, included or redacted, so the
    default-deny profile is visible and authoritative rather than implied
    only by what happens to be absent.
    """
    query = query or {}
    rows = []
    for field, label, _why in _REDACTION_DIMENSIONS:
        revealed = bool(query.get(field))
        rows.append(
            f'<div class="row"><span class="row-label">{_esc(label)}</span>'
            f'<span class="row-value">'
            f'{"Included in this snapshot" if revealed else "Redacted (default deny)"}'
            "</span></div>"
        )
    return section(
        "Redaction outcome",
        "This is what the preview and export would contain. The Share profile "
        "keeps every redaction on by default; an override applies to this "
        "invocation only.",
        '<div class="rows">' + "".join(rows) + "</div>",
    )


def _outcome_sentence(query: dict | None) -> str:
    """One sentence naming each redaction dimension's outcome."""
    query = query or {}
    parts = [
        f"{label} {'included' if query.get(field) else 'redacted'}"
        for field, label, _why in _REDACTION_DIMENSIONS
    ]
    return "Redaction outcome: " + "; ".join(parts) + "."


def _export_section(
    query: dict | None, track: str, fmt: str, *, can_export: bool
) -> str:
    """The explicit export action, with the disposable-snapshot honesty banner."""
    if not can_export:
        return section(
            "Export",
            "An export is a dated, disposable snapshot — never live truth.",
            '<div class="state state-empty">\n'
            '<p class="state-title">This export has not been configured</p>\n'
            '<p class="state-body">No skill is ready to leave yet. A portfolio '
            "includes finished skills; work in progress joins only if you "
            "include it above.</p>\n"
            '<p><a href="/">Return to Today</a> to work on a skill.</p>\n'
            "</div>\n",
        )
    query = query or {}
    hidden = [
        '<input type="hidden" name="next" value="/portfolio">',
        f'<input type="hidden" name="format" value="{_esc(fmt)}">',
    ]
    if track:
        hidden.append(
            f'<input type="hidden" name="track" value="{_esc(track)}">'
        )
    for node_id in query.get("node") or ():
        hidden.append(
            f'<input type="hidden" name="node" value="{_esc(node_id)}">'
        )
    for field, _label, _why in _SELECTION_DIMENSIONS + _REDACTION_DIMENSIONS:
        if query.get(field):
            hidden.append(f'<input type="hidden" name="{field}" value="1">')
    return section(
        "Export",
        "An export is a dated, disposable snapshot — never live truth.",
        '<div class="banner advisory">A portfolio is a dated, disposable '
        "snapshot of the skills you selected. It is written to a dated "
        "folder under <code>data/</code>, it is not live truth, it does not "
        "update, and the web cannot reopen it as your current state. It is "
        "not a user profile or an account.</div>\n"
        '<form method="post" action="/portfolio/export">\n'
        + "".join(hidden)
        + '<div class="command-bar"><div class="actions">'
        '<button type="submit" class="btn primary">Export this dated snapshot</button>'
        "</div></div>\n"
        "</form>\n",
    )


def _preview_section(root, query: dict | None, view) -> str:
    """The preview — the exact output, rendered without writing anything.

    The preview shares the export's selection, redaction and rendering
    pipeline, so what it shows is what would leave. It writes nothing: the
    preview command is read-only, and no bundle is created.
    """
    query = query or {}
    if not query.get("preview"):
        return ""
    if not _has_explicit_selection(query):
        return section(
            "Preview",
            "Exactly what the export would contain. Nothing was written — "
            "this preview creates no bundle.",
            '<div class="state state-empty">\n'
            '<p class="state-title">This export has not been configured</p>\n'
            '<p class="state-body">Choose at least one finished skill, or '
            "apply a track preset, before previewing or exporting.</p>\n"
            "</div>\n",
        )
    fmt = _format_value(view, query)

    from ...context import load_context_strict
    from ...execution.overdue import utc_today
    from ...portfolio.export import PortfolioExportError, render_preview
    from ...portfolio.models import SelectionOptions
    from ...portfolio.pipeline import build_portfolio

    nodes = tuple(node for node in (query.get("node") or ()) if node)
    track = _track_value(query) or None
    options = SelectionOptions(
        nodes=nodes,
        track=track,
        include_active=bool(query.get("include_active")),
        include_rejected=bool(query.get("include_rejected")),
        include_superseded=bool(query.get("include_superseded")),
        include_paths=bool(query.get("include_paths")),
        include_notes=bool(query.get("include_notes")),
        include_blockers=bool(query.get("include_blockers")),
        include_reviews=bool(query.get("include_reviews")),
        include_free_text=bool(query.get("include_free_text")),
        include_urls=bool(query.get("include_urls")),
    )
    try:
        joined = load_context_strict(root)
        if not joined.ok:
            raise PortfolioExportError("data load failed")
        portfolio = build_portfolio(joined, options, today=utc_today())
        if not portfolio.nodes:
            return section(
                "Preview",
                "Exactly what the export would contain. Nothing was written — "
                "this preview creates no bundle.",
                '<div class="state state-empty">\n'
                '<p class="state-title">No skills match this selection</p>\n'
                '<p class="state-body">The preview is empty, so there is '
                "nothing to export. Choose a finished skill above, include "
                "work in progress, or widen the track preset.</p>\n"
                "</div>\n",
            )
        rendered = render_preview(portfolio, options, fmt=fmt)
    except Exception as exc:  # noqa: BLE001 — a failure writes nothing
        return section(
            "Preview",
            "Exactly what the export would contain. Nothing was written — "
            "this preview creates no bundle.",
            '<div class="state state-failure">\n'
            '<p class="state-title">The preview could not be built</p>\n'
            '<p class="state-body">Nothing was written and your selection is '
            "preserved — fix the cause and try again.</p>\n"
            f'<p class="state-body">{_esc(str(exc))}</p>\n'
            "</div>\n",
        )

    return section(
        "Preview",
        "Exactly what the export would contain. Nothing was written — this "
        "preview creates no bundle.",
        f'<p class="small mut">{_esc(_outcome_sentence(query))}</p>'
        f'<pre class="mono">{_esc(rendered)}</pre>',
    )


def portfolio_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/portfolio` — the export configurator.

    ``/portfolio/preview`` is the same page with the preview rendered: the
    exact output the export would produce, through the export's own
    selection, redaction and rendering pipeline, and **without writing
    anything** (spec-v3-study-day §11.7).
    """
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
    track = _track_value(query)
    fmt = _format_value(view, query)
    eligible = _eligible_nodes(view, query)
    can_export = bool(eligible) and _has_explicit_selection(query)

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + '<h2 class="section-title">What to include</h2>\n'
        + '<p class="section-meta">Choose finished skills, or use a track '
        "preset. Nothing is shared unless you enable it: the default share "
        "profile keeps every redaction on.</p>\n"
        + "</div>\n"
        + _selection_form(view, query, track, fmt)
        + "</section>\n"
        + _redaction_outcome(query)
        + _export_section(query, track, fmt, can_export=can_export)
        + _preview_section(root, query, view)
    )
    return "Portfolio", body, 200
