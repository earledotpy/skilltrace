"""
The page shell (ADR 0009): the stylesheet, chrome and nav, error/status
bodies, the one shared route preamble (:func:`_page_head`), and the
confirmation-panel shell.

The shell is **mode-neutral**: one URL-addressable shell carries both
presentation modes (spec-v3-study-day IA-1). Mode rides a URL parameter
(``?mode=guided`` / ``?mode=operations``), never a path prefix, so every
destination is deep-linkable in either presentation. Each route declares a
**default mode**, so a bare deep link always renders a sensible
presentation. Switching mode is explicit and reversible and preserves the
current destination and its query context.

View identity is the screen name (the ADR 0007 ``VIEWS`` seam), never the
path: the chrome's current-section marker reads the declared view table,
never by matching the request path.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from ...commands.health import health_report
from ...context import (
    JoinedView,
    load_context_lenient,
)
from ...graph.edges import EdgeLoadError
from ...graph.nodes import NodeLoadError
from ...graph.state import ProgressStoreError
from ._shared import (
    _degraded_banner,
    _esc,
    _flash_html,
    _normalize_pill_label,
    _slug,
    plural,
)
from .styles import STYLE as _STYLE

# The two presentation modes (spec-v3-study-day §2 PM-2). Mode is
# presentation context, never domain state: it changes the register and
# the section navigation, never a fact, a meaning or an outcome.
MODES: tuple[str, ...] = ("guided", "operations")

# The canonical guided destinations, in nav order. Read from the declared
# view seam below so the nav and the route table cannot drift.
_GUIDED_ORDER = ("today", "next", "find")

# The Operations capability destinations, in nav order. These are the six
# capabilities IA-3 names — never collapsed behind a generic "More".
_OPERATIONS_ORDER = (
    "operations",
    "graph",
    "evidence-index",
    "reviews",
    "health",
    "analytics",
    "portfolio",
)


def _mode_from(query: dict | None, default: str = "guided") -> str:
    """The requested presentation mode, falling back to the route's default.

    An unknown mode value is not an error: the route's default renders, so
    a mistyped parameter never dead-ends a deep link.
    """
    values = (query or {}).get("mode") or []
    requested = (values[0] if values else "").strip().lower()
    if requested in MODES:
        return requested
    return default if default in MODES else "guided"


def _mode_link(path: str, query: dict | None, mode: str) -> str:
    """The same destination in the other mode, keeping its query context.

    Mode switching never discards a filter, a search or a selected
    inspector context — only the ``mode`` parameter changes.
    """
    params = {
        key: values[0]
        for key, values in (query or {}).items()
        if values and key != "mode"
    }
    params["mode"] = mode
    return f"{path}?{urlencode(params)}"


def page(title: str, body: str, *, mode: str = "guided") -> str:
    """The whole served document: skip link, one style block, the page.

    The one inline ``<style>`` block is the v3 dark-first token system
    (ADR 0006: no static-file routing, styling is inline). The body class
    carries the mode so the two presentation registers differ in density
    and whitespace only — never in colour, meaning or term.
    """
    # Bodies start with a sticky <header> (via _NAV). Lift it outside the
    # main wrap so its background spans the full viewport width while its
    # inner .shell stays at the shell token width.
    header = ""
    main = body
    stripped = body.lstrip()
    if stripped.startswith("<header>"):
        end = body.find("</header>")
        if end != -1:
            header = body[: end + len("</header>")] + "\n"
            main = body[end + len("</header>"):].lstrip()
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_esc(title)} — SkillTrace</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n"
        f'<body class="mode-{_esc(mode)}">\n'
        '<a class="skip" href="#content">Skip to content</a>\n'
        f"{header}"
        f'<main class="shell" id="content">\n<h1>{_esc(title)}</h1>\n{main}\n</main>\n'
        '<footer class="shell small mut">Local only · served from your files · fresh on every load.</footer>\n'
        "</body>\n</html>\n"
    )


def _nav_links(names: tuple[str, ...], current_view: str) -> str:
    """The nav links for one section, read from the declared view seam."""
    from ..interface import VIEWS

    links = []
    for name in names:
        view = VIEWS.get(name)
        if view is None:
            continue
        current = ' aria-current="page"' if view.name == current_view else ""
        links.append(f'<a href="{_esc(view.route)}"{current}>{_esc(view.title)}</a>')
    return "".join(links)


def _nav_html(
    current_view: str = "",
    health=None,
    *,
    mode: str = "guided",
    path: str = "/",
    query: dict | None = None,
) -> str:
    """The shared chrome header: section navigation and the mode switch.

    ``current_view`` is the *view identity* (ADR 0007) — ``aria-current``
    derives from the declared interface ``VIEWS`` table (the seam), never
    from URL string-matching in the page bodies.

    The section navigation follows the current mode: Guided shows the
    task-led destinations (Today, Next, Find), Operations shows the six
    capabilities under their own home (IA-3). The mode switch is explicit,
    reversible, and preserves the destination and its query context.
    """
    if mode == "operations":
        section_label = "Operations"
        nav_class = "nav operations"
        links = _nav_links(_OPERATIONS_ORDER, current_view)
    else:
        section_label = "Guided"
        nav_class = "nav guided"
        links = _nav_links(_GUIDED_ORDER, current_view)

    other_mode = "operations" if mode == "guided" else "guided"
    switch = (
        f'<span class="nav-label">Mode</span>'
        f'<a href="{_esc(_mode_link(path, query, "guided"))}"'
        f'{" aria-current=\"true\"" if mode == "guided" else ""}>Guided</a>'
        f'<a href="{_esc(_mode_link(path, query, "operations"))}"'
        f'{" aria-current=\"true\"" if mode == "operations" else ""}>Operations</a>'
    )

    return (
        "<header>"
        '<div class="shell">'
        '<h1 class="brand"><a href="/">SkillTrace</a></h1>'
        f'<nav class="{nav_class}" aria-label="{_esc(section_label)}">'
        f'<span class="section-nav-label">{_esc(section_label)}</span>'
        f"{links}"
        f'<span class="mode-switch">{switch}</span>'
        "</nav>"
        "</div>"
        "</header>\n"
    )


def _chrome(
    root,
    current_view: str = "",
    *,
    mode: str = "guided",
    path: str = "/",
    query: dict | None = None,
) -> str:
    """The full chrome header with live health pills, fresh per request."""
    return _nav_html(
        current_view,
        health=health_report(Path(root)),
        mode=mode,
        path=path,
        query=query,
    )


def _error_body(message: str, root=None) -> str:
    """The one unified full-chrome error body: 404 and 500 share it.

    When the repo root is unavailable (or truth files are unreadable) the
    shell falls back to a chrome-less minimal page rather than faulting
    itself — the learner who typed a bad URL most needs the way back in.
    """
    header_html = (
        _chrome(root)
        if root is not None
        else "<header><div class=\"shell\"><h1 class=\"brand\">SkillTrace</h1></div></header>\n"
    )
    return (
        f'{header_html}<div class="state state-failure">\n'
        '<p class="state-title">Something went wrong</p>\n'
        f'<p class="state-body">{_esc(message)}</p>\n'
        '<p><a href="/">Back to Today</a></p>\n'
        "</div>\n"
    )


def _status_page(status: int, message: str, root=None) -> tuple[str, int]:
    if status == 404:
        return _error_body(message, root), 404
    return _error_body(message, root), status


def not_found_body(root=None) -> tuple[str, str, int]:
    """The one unified full-chrome 404 — the router's only miss body."""
    body, status = _status_page(404, "That page doesn't exist.", root)
    return "Not found", body, status


def _fresh_join(root) -> tuple[JoinedView | None, tuple[str, int] | None]:
    """One fresh lenient join per request.

    Returns ``(view, None)`` on success or ``(None, (body, status))`` when
    the strict graph/state half of the lenient seam re-raised.
    """
    try:
        return load_context_lenient(root), None
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        body = _error_body(
            f"The Skill graph or progress store failed to load: {exc}", root
        )
        return None, (body, 500)


def _page_head(
    root,
    query: dict | None = None,
    *,
    dismiss_path: str = "/",
    current_view: str = "",
    default_mode: str = "guided",
    path: str = "/",
) -> tuple[JoinedView | None, str, tuple[str, str, int] | None]:
    """The one shared route preamble — join, its failure branch, chrome, flash.

    Every GET route body and every pass/master step body builds its page
    through this helper, so the fresh-join failure contract and the single
    flash call shape exist in exactly one place. On a join failure it returns
    ``(None, "", ("Error", body, status))``; on success it returns
    ``(view, head_html, None)`` where ``head_html`` is the chrome header plus
    the one flash rendering for ``query`` (dismissed to ``dismiss_path``).
    Bodies append only their page-specific content after the head.
    """
    query = query or {}
    view, failure = _fresh_join(root)
    if view is None:
        assert failure is not None  # noqa: S101 — _fresh_join pairs them
        return None, "", ("Error", failure[0], failure[1])
    mode = _mode_from(query, default_mode)
    head = _chrome(
        root,
        current_view=current_view,
        mode=mode,
        path=path,
        query=query,
    ) + _flash_html(query, dismiss_path)
    return view, head, None


def _modal_dismiss(node_id: str, heading: str) -> str:
    """The flash-dismiss path for a pass/master panel — the panel's own URL."""
    if heading.startswith("Step 1"):
        return f"/nodes/{node_id}/master"
    if heading.startswith("Step 2"):
        return f"/nodes/{node_id}/master/confirm"
    if heading.startswith("Confirm pass"):
        return f"/nodes/{node_id}/pass"
    return f"/nodes/{node_id}"


def _modal_card(
    view: JoinedView,
    node_id: str,
    heading: str,
    inner: str,
) -> tuple[str, str]:
    """The safety panel card — title plus panel HTML, no chrome or flash."""
    node = view.node_map[node_id]
    state = view.store.state_of(node_id)
    safety_class = (
        "status-label warning"
        if heading.startswith("Step 1")
        else "status-label failure" if heading.startswith("Step 2") else "status-label info"
    )
    modal = (
        '<section class="card">\n'
        f'<p class="kicker">{_esc(heading)}</p>\n'
        f'<p class="lead">{_esc(node.title)}</p>\n'
        f'<p><span class="pill {_esc(_slug(state))}">{_esc(_normalize_pill_label(state))}</span></p>\n'
        f"{inner}"
        "</section>\n"
    )
    return node.title, modal


def _modal_shell(
    view: JoinedView,
    node_id: str,
    heading: str,
    inner: str,
    query: dict | None = None,
    root=None,
    *,
    head: str | None = None,
) -> tuple[str, str, int]:
    """The page-level safety panel enclosing a pass/master body.

    Safety color rides the panel's status label through the locked tokens:
    pass ``info``, master step 1 ``warning``, step 2 ``failure`` — panels are
    full-page routes, never overlays (tier 0, AX-2). Server-fresh per
    request; writes are 303+flash-only.
    """
    title, modal = _modal_card(view, node_id, heading, inner)
    if head is None:
        head = _chrome(root) + _flash_html(
            query or {}, _modal_dismiss(node_id, heading)
        )
    body = head + _degraded_banner(view) + modal
    return title, body, 200
