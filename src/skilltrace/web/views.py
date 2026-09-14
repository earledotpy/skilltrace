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

Information architecture: v2.4 card-stack + sublayer (spec-v2.4 §A–§H). One column of
reading-order cards; the Today focus card carries the one primary CTA, pressure
excerpts and the health strip follow instead of competing; drill-downs
are native ``<details>`` elements off the primary path, so no JavaScript anywhere. Reads go through
the lenient ``JoinedView`` fresh per request.
"""

from __future__ import annotations

import html
import re
from argparse import Namespace
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from ..commands.eligibility import passed_at_of
from ..commands.health import health_report
from ..commands.node_detail import (
    derive_node_drilldown,
    derive_node_detail,
)
from ..commands.recommend import derive_next
from ..commands.today import derive_today
from ..mentor.cards import (
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
from ..context import JoinedView, load_context_lenient
from ..dispatch import Context, dispatch
from .interface.affordances import intent_label
from .interface.cards import ActiveViewState, Affordance, Card, view_by_name
from .interface.render import render_rich_cards
from .interface.translate import rich_cards as _rich_cards_from_model
from ..analytics.derive import derive_analytics
from ..analytics.models import AnalyticsParams
from ..analytics.policy import limited_data_sentence
from ..analytics.sparkline import sparkline_svg
from ..evidence.eligibility import compute_eligibility, live_accepted_count
from ..execution.overdue import utc_today
from ..execution.records import open_session
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError
from ..graph.state import ProgressStoreError
from ..policy.mastery import compute_mastery_eligibility
from ..policy.advisory import analytics_warnings
from ..resources.status import VerificationStatus


def _esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


_STYLE = """
  /* v2.4 T1 locked §B design tokens (P5.4): every hex lives in :root; one accent.
     Muted semantics for exactly the five node states plus attention/warn/err;
     alias classes collapse to one treatment each (warn, err); no hex outside :root. */
  :root {
    /* §B locked palette (hexes live here only) */
    --bg:#fbf7f0;          /* cream */
    --fg:#2b2622;          /* primary text */
    --muted:#7a6f63;       /* secondary text */
    --border:#ece2d3;      /* hairlines */
    --accent:#b0562c;      /* one accent (terracotta) */
    --warn:#faf0d7;
    --err:#f6ded4;
    --ok:#e7f3ec;
    --advisory:#e7eef5;

    /* private supporting set */
    --card:#fffdf9;
    --pill:#f6efe4;
    --accent-ink:#ffffff;         /* ink on an accent fill (primary CTA) */
    --accent-soft:#f7e7db;        /* soft accent tint surface */

    /* treatment + node-state inks (foreground/border on the muted fills) */
    --muted-ink:#7a6f63;
    --warn-ink:#8a6a2a;
    --err-ink:#a5533a;
    --ok-ink:#33694e;
    --advisory-ink:#3d5f82;
    --locked-ink:#7a6f63;
    --available-ink:#33694e;
    --active-ink:#3d5f82;
    --passed-ink:#33694e;
    --mastered-ink:#9b4d26;

    /* §B type scale (P5.1): 16px humanist base, lh ~1.55, display ~2x, 24/14/13.5, measure 70ch */
    --base:16px;
    --lh:1.55;
    --step-display:32px;
    --step-24:24px;
    --step-14:14px;
    --step-135:13.5px;
    --measure:70ch;

    /* §B font-role split: serif for prose, sans for chrome, mono once (node detail) */
    --font-serif:Georgia, 'Times New Roman', serif;
    --font-sans:ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    --font-mono:ui-monospace, 'Cascadia Mono', 'Segoe UI Mono', Consolas, monospace;

    /* §B spacing (P5.2): card padding band 24-32px; section 40px > intra 14px */
    --space-section:40px;
    --space-intra:14px;
    --card-pad:28px;

    /* §B radius 14 / 11 / 999 px */
    --radius:14px;
    --radius-sm:11px;
    --radius-pill:999px;

    /* §B shell: 1040px with a 720px daily-loop column and one 960px breakpoint */
    --shell:1040px;
    --loop:720px;
  }
  *{box-sizing:border-box}
  html,body{width:100%; overflow-x:clip}
  body{margin:0; font:var(--base)/var(--lh) var(--font-serif); color:var(--fg); background:var(--bg);}
  .wrap{max-width:var(--shell); margin:0 auto; padding:0 24px;}
  main.wrap{padding:var(--space-section) 24px 48px}
  .daily-loop{max-width:var(--loop)}
  p{max-width:var(--measure); line-height:var(--lh)}
  ul{padding-left:1.2rem}
  h1,h2,h3,h4{font-family:var(--font-sans); line-height:1.2; color:var(--fg)}
  h1{font-size:var(--step-24); margin:0 0 .4rem}
  h2{font-size:var(--step-24); margin:var(--space-section) 0 .6rem}
  .display{font-family:var(--font-sans); font-size:var(--step-display); line-height:1.2; margin:0 0 .4rem} /* Today's opening question only */
  table{border-collapse:collapse; width:100%}
  th,td{text-align:left; padding:8px .5rem; border-bottom:1px solid var(--border); font-family:var(--font-sans); font-size:var(--step-14)}
  code{font-family:var(--font-mono); font-size:.95em}
  header{position:sticky; top:0; z-index:10; background:var(--card); border-bottom:1px solid var(--border)}
  header .wrap{max-width:var(--shell); margin:0 auto; padding:0 24px}
  header h1.brand{font-size:18px; font-weight:800; margin:10px 0 2px; line-height:1.2; font-family:var(--font-sans)}
  .nav{font-size:.9rem; display:flex; gap:.9rem; flex-wrap:wrap; padding:6px 0 8px; align-items:center; font-family:var(--font-sans)}
  .nav.periodic{border-top:1px solid var(--border); padding-top:8px}
  .nav a{color:var(--accent); text-decoration:none; font-weight:600}
  .nav a:hover{text-decoration:underline}
  .nav a[aria-current="page"]{border-bottom:2px solid var(--accent); padding-bottom:2px}
  .nav .jump{display:flex; gap:6px; align-items:center; margin-left:auto}
  .nav .jump input{border:1px solid var(--border); border-radius:var(--radius-sm); padding:4px 8px; font:inherit; font-size:var(--step-135); background:var(--card); color:var(--fg)}
  .nav .jump button{border:1px solid var(--accent); background:var(--accent); color:var(--accent-ink); border-radius:var(--radius-sm); padding:4px 10px; font-weight:600; cursor:pointer; font-size:var(--step-135)}
  .health-strip{display:flex; gap:6px; flex-wrap:wrap; padding:6px 0 8px; font-size:var(--step-135)}
  .health-strip .pill{border:1px solid var(--border); border-radius:var(--radius-pill); padding:3px 10px; background:var(--card); font-size:var(--step-135)}
  .health-strip .pill.ok{background:var(--ok); border-color:var(--ok-ink)}
  .health-strip .pill.attention{background:var(--warn); border-color:var(--warn-ink)}
  .health-strip .pill.broken{background:var(--err); border-color:var(--err-ink)}
  .card{background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:var(--card-pad); margin:var(--space-intra) 0; gap:var(--space-intra)}
  .kicker{font-family:var(--font-sans); font-size:var(--step-135); font-weight:700; color:var(--muted); margin:.6rem 0 .25rem}
  .kicker:first-child{margin-top:0}
  .title{font-family:var(--font-sans); font-size:var(--step-24); font-weight:700; line-height:1.2; margin:4px 0}
  .label{font-family:var(--font-sans); font-weight:600; margin:.4rem 0 .12rem}
  .lead{font-weight:600; font-size:var(--step-14); margin:.15rem 0; font-family:var(--font-serif)}
  .next-action{margin:.6rem 0 .1rem; font-weight:600; font-family:var(--font-sans)}
  .mut{color:var(--muted); font-size:var(--step-135)}
  .small{font-size:var(--step-135); color:var(--muted); line-height:1.45}
  .big{font-size:var(--step-14); line-height:1.5}
  .count{margin-right:.9rem}
  .count strong{font-size:var(--step-24); font-family:var(--font-sans)}
  .display{font-size:var(--step-display); font-family:var(--font-serif); font-weight:600; line-height:1.2; margin:.4rem 0 .8rem}
  .resumable .inline{display:inline-block; margin-left:.6rem}
  .pill{display:inline-block; border:1px solid var(--border); border-radius:var(--radius-pill); padding:2px 10px; font-size:var(--step-14); margin:.1rem .3rem .1rem 0; background:var(--pill); font-weight:600; font-family:var(--font-sans); color:var(--fg)}
  /* muted semantics: exactly the five node states + attention/warn/err */
  .pill.locked{background:var(--card); border-color:var(--locked-ink); color:var(--locked-ink)}
  .pill.available{background:var(--ok); border-color:var(--available-ink); color:var(--available-ink)}
  .pill.active{background:var(--advisory); border-color:var(--active-ink); color:var(--active-ink)}
  .pill.passed{background:var(--ok); border-color:var(--passed-ink); color:var(--passed-ink)}
  .pill.mastered{background:var(--accent-soft); border-color:var(--accent); color:var(--mastered-ink)}
  .pill.attention{background:var(--warn); border-color:var(--warn-ink); color:var(--warn-ink)}
  .pill.warn{background:var(--warn); border-color:var(--warn-ink); color:var(--warn-ink)}
  .pill.err{background:var(--err); border-color:var(--err-ink); color:var(--err-ink)}
  /* legacy alias classes collapse to the canonical treatments above */
  .pill.ready-to-start{background:var(--ok); border-color:var(--available-ink); color:var(--available-ink)}
  .pill.in-progress{background:var(--advisory); border-color:var(--active-ink); color:var(--active-ink)}
  .pill.verified{background:var(--ok); border-color:var(--ok-ink); color:var(--ok-ink)}
  .pill.broken{background:var(--err); border-color:var(--err-ink); color:var(--err-ink)}
  .pill.stale{background:var(--warn); border-color:var(--warn-ink); color:var(--warn-ink)}
  .banner{padding:10px 14px; border-radius:var(--radius-sm); margin:.4rem 0; font-size:var(--step-14); font-family:var(--font-sans); line-height:1.5}
  .banner.advisory, .banner.attention{background:var(--advisory); border:1px solid var(--advisory-ink)}
  .banner.ok{background:var(--ok); border:1px solid var(--ok-ink); animation:settle .6s ease-out}
  .banner.warn{background:var(--warn); border:1px solid var(--warn-ink)}
  .banner.err{background:var(--err); border:1px solid var(--err-ink)}
  /* legacy banner aliases collapse to the canonical, one treatment each */
  .banner.warning{background:var(--warn); border:1px solid var(--warn-ink)}
  .banner.error{background:var(--err); border:1px solid var(--err-ink)}
  .banner.fail{background:var(--err); border:1px solid var(--err-ink)}
  .banner.success{background:var(--ok); border:1px solid var(--ok-ink); animation:settle .6s ease-out}
  @keyframes settle{from{opacity:.35} to{opacity:1}}
  .btn{display:inline-block; border:1px solid var(--border); background:var(--card); color:var(--fg); border-radius:var(--radius); padding:8px 16px; font-weight:600; cursor:pointer; font-family:var(--font-sans); font-size:var(--step-14); text-decoration:none}
  .btn.primary{background:var(--accent); color:var(--accent-ink); border-color:var(--accent)}
  .btn.master{background:var(--err); color:var(--err-ink); border-color:var(--err-ink)}
  .btn.secondary{background:var(--bg); border-color:var(--border); color:var(--accent)}
  /* §B + §F page-level safety panel (T5): bordered panel inside the one
     nav-carrying shell — server-fresh, no overlay (no dialog, no popover,
     no backdrop). Border tokens: pass → --accent, master step 1 → --warn,
     master step 2 → --err; panel padding at the locked card band. */
  .safety{padding:var(--card-pad)}
  .safety-accent{border-left:4px solid var(--accent)}
  .safety-warn{border-left:4px solid var(--warn)}
  .safety-err{border-left:4px solid var(--err)}
  .flash-dismiss{font-size:var(--step-135); margin-left:.6rem}
  .analytics-grid{display:grid; grid-template-columns:1fr 1fr; gap:var(--space-intra)}
  /* the single locked breakpoint (desktop-only; P5.4: the 900px rules collapse to one) */
  @media(max-width:960px){.analytics-grid{grid-template-columns:1fr}}
"""


def page(title: str, body: str) -> str:
    """Wrap a body in the single shared layout (one inline style block)."""
    # Bodies start with a sticky <header> (via _NAV). Lift it outside the
    # main wrap so its background spans the full viewport width while its
    # inner .wrap stays 1040px — same shell as the locked §B tokens.
    header = ""
    main = body
    stripped = body.lstrip()
    if stripped.startswith("<header>"):
        end = body.find("</header>")
        if end != -1:
            header = body[: end + len("</header>")] + "\n"
            main = body[end + len("</header>"):].lstrip()
            # If the header carried its own _NAV, the remaining body may still
            # start with whitespace; keep it trimmed for clean markup.
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_esc(title)} — SkillTrace</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n<body>\n"
        f"{header}"
        f'<main class="wrap">\n<h1>{_esc(title)}</h1>\n{main}\n</main>\n</body>\n</html>\n'
    )




def _nav_html(current_view: str = "", health=None) -> str:
    """The shared chrome header (v2.4 S2+T4): two nav groups + health pill.

    ``current_view`` is the *view identity* (ADR 0007) — ``aria-current``
    derives from the declared interface ``VIEWS`` table (the seam), never
    from URL string-matching in the page bodies. Health is not a nav stop
    (T4 §H): the chrome carries a header pill strip plus a muted
    ``Full roll-up`` pointer to the one roll-up page. The health strip
    renders an ambient headline plus one attention pill from the structured
    ``HealthReport`` (warning counts ride the P2.4 seam).
    """
    from .interface import VIEWS

    # Both nav groups read from the declared seam in one pass: the group, the
    # route and the current-view marker all come from ``VIEWS`` — never from
    # string-matching the request path (ADR 0007 active-view).
    groups: dict[str, list[str]] = {"daily": [], "periodic": []}
    for view in VIEWS.values():
        if view.group is None or "{" in view.route:
            continue  # non-nav pages and parameterized routes carry no link
        current_attr = ' aria-current="page"' if view.name == current_view else ""
        groups[view.group].append(
            f'<a href="{_esc(view.route)}"{current_attr}>{_esc(view.title)}</a>'
        )
    pills = ""
    if health is not None:
        warnings = sum(layer.warning_count for layer in health.layers if layer.ok)
        failed = [layer for layer in health.layers if not layer.ok]
        if failed:
            pills = (
                '<span class="pill attention">Needs attention — '
                f"{len(failed)} layer{'s' if len(failed) != 1 else ''} failing</span>"
            )
        elif warnings:
            pills = (
                '<span class="pill attention">Needs attention — '
                f"{warnings} warning{'s' if warnings != 1 else ''}</span>"
            )
        else:
            pills = '<span class="mut">Everything looks good.</span>'
        pills += ' <a class="mut" href="/health">Full roll-up</a>'
    return (
        "<header>"
        '<div class="wrap">'
        '<h1 class="brand">SkillTrace</h1>'
        '<nav class="nav daily" aria-label="Daily loop">'
        + "".join(groups["daily"])
        + "</nav>"
        '<nav class="nav periodic" aria-label="Periodic">'
        + "".join(groups["periodic"])
        + '<form class="jump" method="get" action="/nodes/jump">'
        '<input type="text" name="node_id" placeholder="Jump to a skill" aria-label="jump to skill" size="32">'
        '<button type="submit">Go</button>'
        "</form>"
        "</nav>"
        f'<div class="health-strip" aria-label="health">{pills}</div>'
        "</div>"
        "</header>\n"
    )


def _chrome(root, current_view: str = "") -> str:
    """The full chrome header with live health pills, fresh per request."""
    return _nav_html(current_view, health=health_report(Path(root)))


def _error_body(message: str, root=None) -> str:
    """The one unified full-chrome error body (T4 §H): 404 and 500 share it.

    When the repo root is unavailable (or truth files are unreadable) the
    shell falls back to a chrome-less minimal page rather than faulting
    itself — the learner who typed a bad URL most needs the way back in.
    """
    header_html = (
        _chrome(root)
        if root is not None
        else "<header><div class=\"wrap\"><h1 class=\"brand\">SkillTrace</h1></div></header>\n"
    )
    return (
        f'{header_html}<div class="card">\n'
        '<div class="kicker">Something went wrong</div>\n'
        f'<p class="big">{_esc(message)}</p>\n'
        '<p><a href="/">Back to Today</a></p>\n'
        "</div>\n"
    )


def _status_page(status: int, message: str, root=None) -> tuple[str, int]:
    if status == 404:
        return _error_body(message, root), 404
    return _error_body(message, root), status


def not_found_body(root=None) -> tuple[str, str, int]:
    """The one unified full-chrome 404 (T4 §H) — the router's only miss body."""
    body, status = _status_page(404, "That page doesn't exist.", root)
    return "Not found", body, status


def _fresh_join(root) -> tuple[JoinedView | None, tuple[str, int] | None]:
    """One fresh lenient join per request.

    Returns ``(view, None)`` on success or ``(None, (body, status))`` when the
    strict graph/state half of the lenient seam re-raised.
    """
    try:
        return load_context_lenient(root), None
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        body = _error_body(
            f"The Skill graph or progress store failed to load: {exc}", root
        )
        return None, (body, 500)


# --- Browser-write plumbing (T4): one dispatch path, exit-code mapping ----------


@dataclass
class Redirect:
    """A POST outcome that sends 303 See Other — redirect-after-POST."""

    location: str


def _dispatch_web(root, command_name: str, **arg_fields) -> tuple[int, list[str]]:
    """Nest-dispatch one registry command in-process with ``source: "web"``.

    The registry is imported lazily (``cli`` imports this package at startup),
    and it is *the* process-wide ``REGISTRY`` — the same registration the CLI
    resolves, so handlers, kinds, automation labels, audit events, and refusal
    semantics cannot drift from the command line (G2#66's one-write-path rule).
    Handler stdout is captured so refusals can render verbatim; the
    ``CommandResult.exit_code`` is the whole contract.
    """
    from ..cli import REGISTRY

    command = REGISTRY.get(command_name)
    if command is None:  # pragma: no cover — every wired name is registered
        raise KeyError(f"no such command in the registry: {command_name}")
    ctx = Context(root=Path(root), args=Namespace(**arg_fields), source="web")
    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = dispatch(command, ctx)
    return exit_code, buffer.getvalue().splitlines()


def _output_banners(lines: list[str], *, default_class: str = "advisory") -> str:
    """Captured handler output as banners — through the P3.1 translation seam.

    Every line flows through the interface sublayer's forbidden-vocabulary
    translation (no surface bypasses it): CLI voice is rewritten as the
    human act, and the CLI banner kinds map onto the sublayer's semantic
    classes (the alias classes never reach a page). Escaping stays total.
    """
    from .interface import banners

    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    kind = class_map.get(default_class, "attention")
    parts: list[str] = []
    for banner_kind, banner_text in banners(lines, default_class=kind):
        css = banner_kind or kind
        parts.append(f'<p class="banner {_esc(css)}">{_esc(banner_text)}</p>')
    return "".join(parts)


def _flash_tuples(query: dict) -> list[tuple[str, str]]:
    """Flash banners carried across a redirect as (css, text) tuples."""
    from .interface import banners

    text = (query.get("notice") or [""])[0]
    if not text:
        return []
    kind = (query.get("kind") or ["ok"])[0]
    if kind not in {"ok", "warning", "error"}:
        kind = "ok"
    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    css = class_map.get(kind, "attention")
    return [
        (banner_kind or css, banner_text)
        for banner_kind, banner_text in banners(text.splitlines(), default_class=css)
    ]


def _linkify_health(escaped_text: str) -> str:
    """Point operational failures at /health (P3.5) — the one link in a flash."""
    return escaped_text.replace("/health", '<a href="/health">/health</a>')


def _flash_html(query: dict, dismiss_path: str = "/") -> str:
    """Flash banners carried across a redirect in the query string (T5 §F+P3.5).

    Every banner is translated human copy from the one translation module
    (fixed at its source, never redacted at the address bar). Dismissal is
    a plain link to the path without the query string; operational failures
    point at /health.
    """
    parts: list[str] = []
    for css, text in _flash_tuples(query):
        banner = _linkify_health(_esc(text))
        parts.append(f'<p class="banner {_esc(css)}">{banner}</p>\n')
    if parts:
        parts.append(
            f'<p class="flash-dismiss"><a href="{_esc(dismiss_path)}">Dismiss</a></p>\n'
        )
    return "".join(parts)


def _redirect_with_notice(location: str, lines: list[str], kind: str) -> Redirect:
    """PRG redirect carrying translated human copy as the flash notice (T5 P3.5+D2).

    The URL is a copy surface: copy is fixed at its source by the one
    translation module (no flags, command names, exit classes, paths,
    record ids or ADR numbers) and never redacted at the address bar.
    Banner-kind tags ride the ``kind`` param, never the notice text.
    """
    from .interface import translate_lines

    clean: list[str] = []
    for line in translate_lines(lines):
        line = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", line).strip()
        if line:
            clean.append(line)
    notice = "\n".join(clean)
    params = urlencode({"notice": notice, "kind": kind})
    separator = "&" if "?" in location else "?"
    return Redirect(location=f"{location}{separator}{params}")


def _safe_next(form: dict, fallback: str) -> str:
    """The host page a form POST returns to — local paths only."""
    target = (form.get("next") or [fallback])[0]
    if target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def _field(form: dict, key: str) -> str | None:
    values = form.get(key)
    if not values or not values[0].strip():
        return None
    return values[0]


def _int_field(form: dict, key: str) -> tuple[int | None, str | None]:
    raw = _field(form, key)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{key} must be an integer."


def _degraded_banner(view: JoinedView) -> str:
    """Advisory notice when lenient layers degraded — reads as empty only."""
    if not view.degraded:
        return ""
    names = ", ".join(sorted(set(view.degraded)))
    return (
        '<p class="banner advisory">Some supporting details failed to load and read '
        f"as empty ({_esc(names)}) — everything you can do here still works, and a "
        "refusal on click remains the truth. The health roll-up carries the detail.</p>"
    )


def _finish_write(
    next_url: str,
    lines: list[str],
    exit_code: int,
    *,
    refusal_url: str | None = None,
) -> Redirect:
    """Map a dispatched write's exit code per the locked T5 contract (§D1+S5).

    Every POST → 303 See Other + translated flash; no 4xx ever leaves a
    write. ``0`` → ok flash to ``next_url``; ``2`` (domain refusal) →
    warning flash to ``refusal_url`` (the acceptance step for pass/master,
    else ``next_url``); ``1`` (operational failure) → error flash to
    ``next_url`` pointing at /health for the detail.
    """
    if exit_code == 0:
        return _redirect_with_notice(next_url, lines, "ok")
    if exit_code == 2:
        return _redirect_with_notice(refusal_url or next_url, lines, "warning")
    lines = [*lines, "Something went wrong — see /health for the detail."]
    return _redirect_with_notice(next_url, lines, "error")


# --- Structured cards -> HTML ------------------------------------------------


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.isupper():
        lowered = text.lower()
        return lowered[0].upper() + lowered[1:]
    return text


_CANONICAL_STATE_LABELS = {
    "locked": "Locked",
    "available": "Available",
    "active": "Active",
    "passed": "Passed",
    "mastered": "Mastered",
    "ready to start": "Available",
    "in progress": "Active",
}


def _normalize_pill_label(label: str) -> str:
    lowered = label.strip().lower()
    return _CANONICAL_STATE_LABELS.get(lowered, label)


def _render_part(part) -> str:
    """One typed card part to HTML — the single card-type-to-CSS-class map."""
    if isinstance(part, Banner):
        return f'<p class="banner {_esc(part.kind)}">{_esc(part.text)}</p>'
    if isinstance(part, Pill):
        norm_label = _normalize_pill_label(part.label)
        return (
            f'<span class="pill {_esc(_slug(norm_label))}">{_esc(norm_label)}</span>'
        )
    if isinstance(part, Kicker):
        return f'<div class="kicker">{_esc(_sentence_case(part.text))}</div>'
    if isinstance(part, (Title, Lead)):
        return f'<p class="lead">{_esc(part.text)}</p>'
    if isinstance(part, Label):
        return f'<p class="label">{_esc(part.text)}</p>'
    if isinstance(part, Sub):
        return f'<div class="sub">{_esc(part.text)}</div>'
    if isinstance(part, NextAction):
        # The web affordance mapping (v2.4 S1): the fact's intent renders as
        # a human affordance — never its ``command`` string (that is the
        # CLI's presentation; P3.1 bans it from every page string).
        from .interface import intent_label

        title = None
        if part.command and part.intent == "pass" and " passed" in part.command:
            title = part.command.split(" passed")[0].removeprefix("Mark ").strip()
        label = intent_label(part.intent, title=title)
        return (
            f'<p class="next-action" data-intent="{_esc(part.intent)}">'
            f"{_esc(label)}</p>"
        )
    return f"<p>{_esc(part.text)}</p>"  # Para (and any future plain part)


def _render_card_inner(card: MentorCard) -> str:
    return "\n".join(_render_part(part) for part in card.parts)


def render_cards(cards: list[MentorCard]) -> str:
    """Deprecated-compat serializer: typed parts as one ``<div class="card">``.

    The pre-§E part-to-HTML map. Reachable only through :func:`cards_html`
    for out-of-scope line producers (health liveness, report exports);
    route bodies compose Richer Cards and render via
    ``interface.render.render_rich_cards``. A grep gate in
    ``tests/web/test_rich_seam.py`` pins this to the two definitions.
    """
    return "".join(
        f'<div class="card">\n{_render_card_inner(card)}\n</div>\n' for card in cards
    )


def cards_html(lines: list[str]) -> str:
    """Deprecated compat: legacy lines as cards (health/reports/export only).

    Parses ``lines`` via ``mentor.cards.lines_to_cards`` and renders through
    the deprecated :func:`render_cards` part map so out-of-scope line
    producers keep their HTML without a route body composing MentorCards.
    """
    return render_cards(lines_to_cards(lines))


# --- Shared cards ---------------------------------------------------------------


# --- Route bodies ---------------------------------------------------------------


def _focus_resources(model) -> list[str]:
    """The focus node's resource lines, off the derivation's typed parts."""
    resources: list[str] = []
    section = ""
    for card in model.cards:
        for part in card.parts:
            if isinstance(part, Label):
                section = part.text.strip().lower()
                continue
            if isinstance(part, Sub) and section.startswith("where to learn"):
                resources.append(part.text)
    return resources


def _focus_card(view, model) -> str:
    """Today block 1 — the focus card (§A), a Richer Card (§E).

    The page's display heading (``.display``, T4 §H) opens the page once,
    above the card — the focus title itself is never a second ``h1``.
    """
    if not model.focus_node_id or model.focus_node_id not in view.node_map:
        # No focus: the quiet empty state — one muted pointer, no backlog.
        # A status card, not a Richer Card: no skill is presented.
        return (
            '<p class="display">What is today about?</p>\n'
            '<div class="card focus">\n'
            '<div class="kicker">Today</div>\n'
            '<p class="lead">Nothing is queued for today.</p>\n'
            '<p class="mut">Sync your readiness or explore what to study '
            'from <a href="/next">Next</a>.</p>\n'
            "</div>\n"
        )
    focus = view.node_map[model.focus_node_id]
    state = view.store.state_of(focus.id)
    action = model.focus_action
    # The plain-language reason: the study-day brief's first sentence (the
    # raw factor list never renders on Today).
    reason = ""
    if model.cards:
        for part in model.cards[0].parts:
            if isinstance(part, Lead):
                reason = part.text.split(". ")[0].strip()
                if reason and not reason.endswith("."):
                    reason += "."
                break
    if action is None:
        # Absent fact = no affordance (P4.1): without the fact this is not
        # a Richer Card — fall back to the quiet status rendering.
        return (
            '<p class="display">What is today about?</p>\n'
            '<div class="card focus">\n'
            '<div class="kicker">Today</div>\n'
            f'<p class="lead"><a href="/nodes/{_esc(focus.id)}">{_esc(focus.title)}</a></p>\n'
            f'<p><span class="pill {_esc(state)}">{_esc(_normalize_pill_label(state))}</span></p>\n'
            + (f'<p class="big">{_esc(reason)}</p>\n' if reason else "")
            + "</div>\n"
        )
    affordance = Affordance.from_intent(action.intent, binding=action, title=focus.title)
    card = Card(
        state=state,
        title=focus.title,
        why=reason or state,
        resources=_focus_resources(model)
        or ["No resources are registered for this skill yet."],
        affordances=(affordance,),
        kicker="Today",
        node_id=focus.id,
    )
    affordance_html: dict[int, str] | None = None
    if action.intent == "start" and state == "available":
        # The one primary CTA: the live write path (the POST target), which
        # replaces the copy-only affordance rendering.
        affordance_html = {0: _start_confirm_form(view, focus.id)}
    return (
        '<p class="display">What is today about?</p>\n'
        + render_rich_cards(
            [card],
            state=ActiveViewState(
                view=view_by_name("today"), affordances=(affordance,)
            ),
            affordance_html=affordance_html,
            affordance_mode="link",
            classes={0: "focus"},
        )
    )


def _count_set_card(model) -> str:
    """Today block 2 — the count set: ready / reviews waiting / days practiced.

    Labeled counts plus one muted pointer; zero-count pills are dropped;
    the raw backlog never renders (§A).
    """
    counts = model.counts
    items: list[str] = []
    ready = counts.get("available", 0)
    if ready:
        items.append(f'<span class="count"><strong>{ready}</strong> ready</span>')
    waiting = len(model.overdue)
    if waiting:
        items.append(
            f'<span class="count"><strong>{waiting}</strong> review'
            f'{"s" if waiting != 1 else ""} waiting</span>'
        )
    days = model.days_practiced
    if days:
        items.append(
            f'<span class="count"><strong>{days}</strong> day'
            f'{"s" if days != 1 else ""} practiced</span>'
        )
    counts_html = (
        " ".join(items) if items else '<span class="count mut">Nothing waiting</span>'
    )
    return (
        '<div class="card counts">\n'
        f"<p>{counts_html}</p>\n"
        '<p class="mut"><a href="/next">See what to study &rarr;</a></p>\n'
        "</div>\n"
    )


def _resumable_active_line(view) -> str:
    """Today block 3 — the resumable-active line, only while a session is open."""
    current = open_session(view.sessions)
    if current is None:
        return ""
    started = _esc(str(current.started_at)[:16].replace("T", " "))
    return (
        '<div class="card resumable">\n'
        f"<p>Session open since {started}.</p>\n"
        '<form class="inline" method="post" action="/session/close">'
        '<input type="hidden" name="next" value="/">'
        '<button type="submit" class="btn secondary">Close session</button>'
        "</form>\n"
        "</div>\n"
    )


def home_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/` — Today as the P3 card-stack (v2.4 §A).

    Three card-level blocks (≤ 4): the focus card (the one primary CTA),
    the count set (ready / reviews waiting / days practiced), and the
    resumable-active line while a session is open. Queue and pressure
    recede behind the ``/next`` stop; zero tables; no ``<details>`` on the
    primary path; the raw backlog never renders.

    Returns ``(page_title, body_html, http_status)``.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_today(view, Path(root), minutes=30)

    header_html = _chrome(root, current_view="today")

    body = (
        header_html
        + _flash_html(query or {}, "/")
        + _degraded_banner(view)
        + _focus_card(view, model)
        + _count_set_card(model)
        + _resumable_active_line(view)
    )
    return "Today", body, 200


def _template_select(templates: set[str], empty_label: str) -> str:
    options = "".join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in sorted(templates))
    return (
        f'<select name="template"><option value="">{_esc(empty_label)}</option>{options}</select>'
    )


def _start_confirm_form(view: JoinedView, node_id: str) -> str:
    """The lightweight single-click start confirm (G5) — never a heavyweight modal.

    Copy states the forward-only permanence; locked reason and an already-open
    session stay visible as advisory text while the button stays enabled.
    """
    state = view.store.state_of(node_id)
    open_now = open_session(view.sessions)
    advisory = ""
    if state == "locked":
        advisory = (
            '<p class="mut">Currently locked (unsatisfied hard prerequisite) — '
            "satisfy prerequisites before starting.</p>"
        )
    elif open_now is not None:
        advisory = (
            '<p class="mut">A session is already open — '
            "close it before starting another.</p>"
        )
    button_label = "Start this session"
    return (
        '<div class="form-row"><label>Session template</label>'
        f"{_template_select(view.policy.session_templates, '(none)')}</div>"
        f"{advisory}"
        '<div class="actions">'
        f'<form method="post" action="/nodes/{_esc(node_id)}/start">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        f'<button type="submit" class="btn primary">{_esc(button_label)}</button></form>'
        '<span class="mut">marks this skill '
        "<strong>active</strong> — progress never moves backward.</span>"
        "</div>"
    )


def _work_form_fields() -> str:
    return (
        '<div class="form-row"><label>Notes</label>'
        '<textarea name="notes"></textarea></div>'
        '<div class="form-row"><label>Minutes '
        '<input type="number" name="minutes" min="1" style="max-width:7rem"></label></div>'
        '<div class="form-row inline-check">'
        '<label><input type="checkbox" name="blocked" value="1"> ended stuck '
        "(blocked requires notes)</label></div>"
    )


def _parse_int(query: dict, key: str, default: int) -> int | None:
    values = query.get(key)
    if not values:
        return default
    try:
        return int(values[0])
    except ValueError:
        return None


def next_body(root, query: dict) -> tuple[str, str, int]:
    """GET `/next` — grouped action-verb affordances, honestly controlled (T4 §H).

    Honest controls (session window, option count, and a show-locked
    disclosure) replace the CLI mirror: flag names never render. ``Why
    this?`` is one human sentence plus an optional disclosure — ranker
    internals (scores, weights, leverage counts) stay hidden. A
    ``Not ready yet — and why`` card replaces the show-locked id dump;
    candidate titles are links (via the Card seam's ``node_id``).
    """
    minutes = _parse_int(query, "minutes", 60)
    limit = _parse_int(query, "limit", 5)
    if minutes is None or limit is None:
        body, status = _status_page(400, "Minutes and options must be numbers.", root)
        return "Next", body, status

    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    # T4 §H: the locked half is the "Not ready yet — and why" card rather
    # than a flag, so the derivation always carries the locked candidates
    # (its own id-dump appendix is dropped in ``_candidate_stack``).
    model = derive_next(
        view, Path(root), minutes=minutes, limit=limit, show_locked=True
    )

    # Honest controls: the session window and option count phrased as
    # questions; the locked half is one disclosure card, never a flag name.
    filters = (
        '<div class="card">\n'
        '<form class="filters" method="get" action="/next">'
        f'<label>How much time do you have <input type="number" name="minutes" value="{minutes}" min="1" size="4"></label>'
        f'<label>How many ideas do you want <input type="number" name="limit" value="{limit}" min="1" size="3"></label>'
        '<button type="submit">Update ideas</button>'
        "</form>\n"
        "</div>\n"
    )

    locked_section = _not_ready_card(model, view)

    header_html = _chrome(root, current_view='next')

    return (
        "Next",
        header_html
        + _flash_html(query, "/next")
        + filters
        + _candidate_stack(view, model)
        + locked_section,
        200,
    )


def _not_ready_card(model, view) -> str:
    """The ``Not ready yet — and why`` card (T4 §H): titles + reasons, no ids."""
    if not model.locked:
        return (
            '<div class="card">\n'
            '<div class="kicker">Not ready yet — and why</div>\n'
            "<p>Everything in reach is already listed above.</p>\n"
            "</div>\n"
        )
    return (
        '<div class="card">\n'
        '<div class="kicker">Not ready yet — and why</div>\n'
        f"{_not_ready_list(model, view)}\n"
        "</div>\n"
    )


def _not_ready_list(model, view) -> str:
    """The locked rows: titles + states in human words, never raw ids.

    The derivation's own ``LockedCandidate.reason`` carries node ids and a
    CLI-voice hint, so the web composes the reason from the structured
    ``unsatisfied`` pairs instead (P3.1/P3.2).
    """
    rows = []
    for cand in model.locked:
        title = view.titles.get(cand.node_id) or "Another skill"
        if cand.unsatisfied:
            waiting = ", ".join(
                f"{view.titles.get(pid) or 'an earlier skill'} ({state})"
                for pid, state in cand.unsatisfied
            )
            reason = f"waiting on {waiting}"
        else:
            reason = "its readiness looks out of date — sync your readiness"
        rows.append(f"<li><strong>{_esc(title)}</strong> — {_esc(reason)}</li>")
    return f"<ul>{''.join(rows)}</ul>"


def _why_details(rec) -> str:
    """``Why this?`` — one human sentence plus an optional disclosure (T4 §H).

    Ranker internals (scores, weights, leverage counts, session-fit flags)
    never render: the candidate cards already carry the one-line why, and
    the advisory note is the only disclosure.
    """
    return (
        "<details>\n<summary>Why this?</summary>\n"
        f'<div class="sub">{_esc(rec.reason)}</div>\n'
        '<p class="mut">Advisory reasoning — policies reorder recommendations; '
        "they never block a human-initiated action.</p>\n</details>\n"
    )


def _candidate_stack(view, model) -> str:
    """Candidate Richer Cards with the per-card advisory "Why this?" attached.

    Candidates are the OPTION cards in the derivation's order; the k-th
    such card receives model.recommendations[k]'s reasoning as its
    attached facts block. Banner/appendix cards ride the banner channel —
    except the derivation's ``locked`` appendix, whose id dump is replaced
    by the page's own ``Not ready yet — and why`` card (T4 §H, P3.2).
    """
    cards, banners = _rich_cards_from_model(model.cards, titles=view.titles)
    banners = [(kind, text) for kind, text in banners if kind != "locked"]
    rec_iter = iter(model.recommendations)
    extras: dict[int, str] = {}
    for index, card in enumerate(cards):
        if (card.kicker or "").strip().upper().startswith("OPTION"):
            rec = next(rec_iter, None)
            if rec is not None:
                extras[index] = _why_details(rec)
    return render_rich_cards(
        cards,
        banners,
        state=ActiveViewState(view=view_by_name("next")),
        extras=extras,
    )


def node_body(root, node_id: str, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/nodes/{id}` — brief-first, state-aware collapse (T4 §H).

    Pass requirements are stated once; the no-op evidence form is omitted;
    the one permitted raw id renders as small muted secondary text, and the
    page carries the single mono use. Nothing is marked current on node
    pages (T4 §H): the chrome renders with no active view.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_node_detail(view, node_id)
    if model is None:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    actions = _node_actions_card(view, node_id)
    drill = _drill_down_card(node_id, view, Path(root), model)
    title = view.node_map[node_id].title
    header_html = _chrome(root)

    secondary_id = f'<p class="small mut">{_esc(node_id)}</p>\n'
    cards, banners = _rich_cards_from_model(model.cards, titles=view.titles)
    body = (
        header_html
        + _flash_html(query or {}, f"/nodes/{node_id}")
        + _degraded_banner(view)
        + secondary_id
        + render_rich_cards(
            cards,
            banners,
            state=ActiveViewState(view=view_by_name("node")),
        )
        + actions
        + drill
    )
    return title, body, 200


def _resolve_blocker_form(blocker_id: str, next_url: str = "/") -> str:
    """Resolve affordance on each open-blocker row (G5): summary required."""
    return (
        "<details><summary>Resolve</summary>"
        f'<form method="post" action="/blockers/{_esc(blocker_id)}/resolve">'
        f'<input type="hidden" name="next" value="{_esc(next_url)}">'
        '<div class="form-row"><label>Resolution summary</label>'
        '<input type="text" name="summary" required></div>'
        '<button type="submit" class="btn secondary">Clear blocker</button></form></details>'
    )


def _evidence_submit_form(view: JoinedView, node_id: str) -> str:
    """Evidence submit (G5) — the CLI's fields, judged at submission.

    The no-op form is *omitted* (v2.4 S4): a node with no artifact spec or
    no gate renders the explanation only — a form the domain would always
    refuse never renders. Spec select auto-resolves when the node has
    exactly one spec; accept/reject radios render only on manual-gate
    nodes; the supersede flow hides behind an advanced toggle.
    """
    specs = view.specs_by_node.get(node_id, [])
    gate = view.gates_by_node.get(node_id)

    if not specs:
        return (
            "<details><summary>Submit evidence</summary>"
            '<p class="mut">No artifact spec is defined for this skill — '
            "evidence cannot be recorded here.</p></details>"
        )
    if gate is None:
        return (
            "<details><summary>Submit evidence</summary>"
            '<p class="mut">No validation gate is defined for this skill — '
            "evidence cannot be recorded here.</p></details>"
        )

    if len(specs) == 1:
        spec_field = f'<input type="hidden" name="spec" value="{_esc(specs[0].id)}">'
    else:
        options = "".join(
            f'<option value="{_esc(s.id)}">{_esc(s.title or s.id)}</option>' for s in specs
        )
        spec_field = (
            '<div class="form-row"><label>Artifact spec</label>'
            f'<select name="spec">{options}</select></div>'
        )

    if gate.command:
        verdict_field = (
            '<p class="mut">Objective gate — running it decides the verdict.</p>'
        )
    else:
        verdict_field = (
            '<div class="form-row"><label>Gate verdict (manual)</label>'
            '<span class="inline-check">'
            '<label><input type="radio" name="verdict" value="accept"> accept</label> '
            '<label><input type="radio" name="verdict" value="reject"> reject</label>'
            "</span></div>"
        )

    record_ids = [r.id for r in view.records if r.artifact_spec_id in {s.id for s in specs}]
    datalist = ""
    if record_ids:
        options = "".join(f'<option value="{_esc(rid)}"></option>' for rid in record_ids)
        datalist = f'<datalist id="records-{_esc(node_id)}">{options}</datalist>'
    supersedes_field = (
        "<details><summary>Advanced: correct an earlier record</summary>"
        '<div class="form-row"><label>Supersedes</label>'
        f'<input type="text" name="supersedes" list="records-{_esc(node_id)}">{datalist}</div>'
        '<div class="form-row"><label>Reason (required with supersedes)</label>'
        '<input type="text" name="reason"></div>'
        "</details>"
    )

    return (
        "<details><summary>Submit evidence</summary>"
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/evidence">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        '<div class="form-row"><label>Location (repo-relative path or URL)</label>'
        '<input type="text" name="location" required></div>'
        f"{spec_field}"
        '<div class="form-row"><label>Note (optional)</label>'
        '<input type="text" name="note"></div>'
        f"{verdict_field}"
        f"{supersedes_field}"
        '<button type="submit" class="btn secondary">Submit evidence</button>'
        "</form>"
        '<p class="mut">Acceptance freezes at submission — the gate '
        "verdict renders loudly; records are immutable and corrected by "
        "superseding, never edited.</p></details>"
    )


def _node_actions_card(view: JoinedView, node_id: str) -> str:
    """Node-detail write surface (G5): pass/master modals + daily-write forms.

    Structural omission per ADR 0007 §Validation (Amendment 2026-09-11) +
    P4.1: pass on a ``locked`` node and master on a node that is not
    ``passed`` are *omitted* — absent markup, never rendered-then-refused
    and never pre-disabled. Judgment eligibility stays live elsewhere.
    """
    open_blockers = [
        b for b in view.blockers if b.node_id == node_id and b.status == "open"
    ]
    node_url = f"/nodes/{node_id}"
    # The resolve write path stays reachable per affordance: the blocker id
    # rides only in the form's POST action (a write path, never visible
    # copy), beside the human description.
    blocker_section = (
        "<ul>"
        + "".join(
            f"<li>{_esc(b.description)} "
            + _resolve_blocker_form(b.id, node_url)
            + "</li>"
            for b in open_blockers
        )
        + "</ul>"
        if open_blockers
        else '<p class="mut">No open blockers.</p>'
    )
    title = view.titles.get(node_id, node_id)
    state = view.store.state_of(node_id)
    actions = ""
    if state != "locked":  # structural wall: pass on locked is omitted
        actions += (
            f'<a class="btn" href="/nodes/{_esc(node_id)}/pass">'
            f"Mark {_esc(title)} passed&hellip;</a>"
        )
    if state == "passed":  # structural wall: master requires passed
        actions += (
            f'<a class="btn master" href="/nodes/{_esc(node_id)}/master">'
            f"Mark {_esc(title)} mastered&hellip;</a>"
        )
    actions_html = f'<div class="actions">{actions}</div>' if actions else ""
    start_label = "Start this session"
    return (
        '<div class="card">\n'
        '<div class="kicker">Write actions</div>\n'
        + actions_html
        + f"\n<details open><summary>{_esc(start_label)}</summary>"
        f"{_start_confirm_form(view, node_id)}\n</details>\n"
        "<details><summary>Log work</summary>"
        '<form method="post" action="/work">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        f"{_work_form_fields()}"
        '<button type="submit" class="btn secondary">Add work item</button></form></details>\n'
        "<details><summary>I'm stuck — create a blocker</summary>"
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/blockers">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        '<div class="form-row"><label>Description (the obstacle)</label>'
        '<input type="text" name="description" required></div>'
        '<button type="submit" class="btn secondary">Create blocker</button></form></details>\n'
        f"{_evidence_submit_form(view, node_id)}\n"
        "<details><summary>Open blockers on this skill</summary>"
        f"{blocker_section}</details>\n"
        "</div>\n"
    )

_STATUS_PILL_CLASSES = {
    VerificationStatus.BROKEN.value: "broken",
    VerificationStatus.STALE.value: "stale",
    VerificationStatus.VERIFIED.value: "verified",
}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def _drill_down_card(
    node_id: str,
    view: JoinedView,
    root: Path,
    model,
    *,
    clock=None,
) -> str:
    """Read-only factual drill-downs. No Mentor vocabulary here — tables only.

    Per-node facts come from ``DrilldownModel`` produced by
    ``commands.node_detail.derive_node_drilldown`` — the web layer
    no longer imports the per-handler private helpers from
    ``commands.node_detail``, and it no longer re-derives facts the
    CLI's ``derive_node_detail`` already produced.
    """
    drilldown = derive_node_drilldown(node_id, view, model, clock=clock)

    evidence_rows = [
        [_esc(title), _esc(kind), _esc(req), _esc(minimum), _esc(accepted)]
        for (title, kind, req, minimum, accepted) in drilldown.evidence_rows
    ]
    record_rows = [
        [_esc(rid), _esc(verdict), _esc(standing), _esc(loc)]
        for (rid, verdict, standing, loc) in drilldown.record_rows
    ]
    attempt_rows = [
        [_esc(aid), _esc(outcome), _esc(date)]
        for (aid, outcome, date) in drilldown.attempt_rows
    ]
    resource_rows = []
    for (rid, where, status) in drilldown.resource_rows:
        pill_class = _STATUS_PILL_CLASSES.get(status, "")
        resource_rows.append(
            [
                _esc(rid),
                f'<a href="{_esc(where)}">{_esc(where)}</a>' if where.startswith("http") else _esc(where),
                f'<span class="pill {pill_class}">{_esc(status)}</span>',
            ]
        )
    review_rows = [
        [_esc(rid), _esc(status), _esc(due), _esc(outcome)]
        for (rid, status, due, outcome) in drilldown.review_rows
    ]
    work_rows = [
        [_esc(sid), _esc(minutes if minutes is not None else "—"), _esc(notes)]
        for (sid, minutes, notes) in drilldown.work_rows
    ]
    blocker_rows = [
        [_esc(bid), _esc(status), _esc(desc)]
        for (bid, status, desc) in drilldown.blocker_rows
    ]
    remediation_rows = [
        [_esc(rid), _esc(status), _esc(desc)]
        for (rid, status, desc) in drilldown.remediation_rows
    ]
    prereq_rows = [
        [
            f'<a href="/nodes/{_esc(pid)}">{_esc(title)}</a>',
            _esc(pstate),
            "no — must pass first" if unsatisfied else "yes",
        ]
        for (pid, title, pstate, unsatisfied) in drilldown.prereq_rows
    ]
    unlock_rows = [
        [f'<a href="/nodes/{_esc(uid)}">{_esc(title)}</a>']
        for (uid, title) in drilldown.unlock_rows
    ]
    # Display newest first.
    event_rows = [
        [_esc(ts)[:19], _esc(cmd)]
        for (ts, cmd) in reversed(drilldown.event_rows)
    ][:10]

    def section(label: str, inner: str) -> str:
        return f"<details>\n<summary>{label}</summary>\n{inner}\n</details>\n"

    parts = ['<div class="card">\n<div class="kicker">Drill-down — read-only facts</div>\n']
    parts.append(
        section(
            "Evidence",
            f"<p>{_esc(drilldown.gate_line)}</p>"
            + (_table(["Spec", "Kind", "Requirement", "Minimum", "Live accepted"], evidence_rows) if evidence_rows else '<p class="mut">No artifact specs.</p>')
            + (_table(["Record", "Verdict", "Standing", "Location"], record_rows) if record_rows else "")
            + (_table(["Attempt", "Outcome", "Date"], attempt_rows) if attempt_rows else ""),
        )
    )
    parts.append(
        section(
            "Resources",
            _table(["Resource", "Where", "Verification"], resource_rows)
            if resource_rows
            else '<p class="mut">(no resources linked to this skill)</p>',
        )
    )
    if review_rows:
        parts.append(section("Reviews", _table(["Review", "Status", "Scheduled", "Outcome"], review_rows)))
    execution_inner = ""
    if work_rows:
        execution_inner += _table(["Session", "Minutes", "Notes"], work_rows)
    if blocker_rows:
        execution_inner += _table(["Blocker", "Status", "Description"], blocker_rows)
    if remediation_rows:
        execution_inner += _table(["Remediation", "Status", "Description"], remediation_rows)
    if execution_inner:
        parts.append(section("Sessions, blockers, remediation", execution_inner))
    graph_inner = ""
    if prereq_rows:
        graph_inner += _table(["Hard prerequisite", "State", "Satisfied?"], prereq_rows)
    if unlock_rows:
        graph_inner += "<p>This unlocks:</p>" + _table(["Unlocks"], unlock_rows)
    if graph_inner:
        parts.append(section("Graph edges", graph_inner))
    if event_rows:
        parts.append(
            section(
                "Events (audit log)",
                _table(["Timestamp (UTC)", "Command"], event_rows)
                + '<p class="mut">Audit-only history — never read back to compute state.</p>',
            )
        )
    parts.append("</div>\n")
    return "".join(parts)


def health_body(root) -> tuple[str, str, int]:
    """GET `/health` — the ambient roll-up (T4 §H).

    An ambient headline plus one attention pill when anything needs it;
    per-layer warning counts ride the P2.4 seam; not a nav stop (health
    reaches only through the header pill strip + ``Full roll-up``).
    """
    report = health_report(Path(root))

    warnings = sum(layer.warning_count for layer in report.layers if layer.ok)
    failed = [layer for layer in report.layers if not layer.ok]
    if failed:
        headline = (
            '<p class="big">Needs attention — '
            f"{len(failed)} layer{'s' if len(failed) != 1 else ''} failing.</p>\n"
        )
    elif warnings:
        headline = (
            '<p class="big">Needs attention — '
            f"{warnings} warning{'s' if warnings != 1 else ''}.</p>\n"
        )
    else:
        headline = '<p class="big">Everything looks good.</p>\n'

    rows = [
        [
            _esc(layer.target),
            _esc(layer.counts),
            '<span class="pill '
            + ("verified" if layer.ok else "broken")
            + '">'
            + ("OK" if layer.ok else "FAILED")
            + "</span>",
            (
                f'<span class="pill attention">{_esc(layer.warning_count)} warning'
                + ('s' if layer.warning_count != 1 else '')
                + "</span>"
                if layer.warning_count
                else '<span class="mut">-</span>'
            ),
        ]
        for layer in report.layers
    ]
    error_banners = "".join(
        f'<p class="banner error">{_esc(line[len("[error] "):])}</p>'
        for layer in report.layers
        for line in layer.error_lines
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"

    header_html = _chrome(root)

    body = (
        header_html
        + '<div class="card">\n'
        + '<div class="kicker">Health roll-up</div>\n'
        + headline
        + _table(["Layer", "Counts", "Status", "Warnings"], rows)
        + error_banners
        + cards_html(report.liveness_lines)
        + f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        + '<p class="mut">Read fresh from the truth files at request time — '
        "updates appear on refresh.</p>\n</div>\n"
    )
    return "Health", body, 200

def _analytics_view(root: Path, query: dict) -> tuple[object | None, tuple[str, str, int] | None]:
    view, failure = _fresh_join(root)
    if view is None:
        return None, ("Error", failure[0], failure[1])
    policy = view.policy.analytics_policy
    default_days = policy.default_window_days
    raw_days = (query.get("days") or [str(default_days)])[0]
    try:
        days = int(raw_days)
    except (TypeError, ValueError):
        body, status = _status_page(400, "Analytics days must be a positive integer.", root)
        return None, ("Bad request", body, status)
    if days <= 0:
        body, status = _status_page(400, "Analytics days must be a positive integer.", root)
        return None, ("Bad request", body, status)
    group_by = (query.get("group-by") or [policy.default_group_by])[0]
    if group_by not in {"prefix", "track"}:
        body, status = _status_page(400, "Analytics group-by must be prefix or track.", root)
        return None, ("Bad request", body, status)
    min_sessions = policy.min_sessions_for_full_data
    # T6: the window/group/filter bundle is one value for every theme.
    params = AnalyticsParams(
        window_days=days,
        group_by=group_by,
        state_filter=(),
        min_sessions_for_full_data=min_sessions,
    )
    return (
        derive_analytics(
            view,
            today=utc_today(),
            params=params,
        ),
        None,
    )


def _analytics_export_form(days: int, group_by: str, theme: str) -> str:
    return (
        '<form method="post" action="/analytics/export" class="actions">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        f'<input type="hidden" name="days" value="{days}">'
        f'<input type="hidden" name="group_by" value="{_esc(group_by)}">'
        '<button class="btn secondary" type="submit" name="format" value="md">Export MD</button>'
        '<button class="btn secondary" type="submit" name="format" value="html">Export HTML</button>'
        '<button class="btn secondary" type="submit" name="format" value="json">Export JSON</button>'
        "</form>"
    )


def _analytics_card(
    title: str, summary: str, derivation: str, svg: str, detail: str, view, theme: str
) -> str:
    """One theme's page (T4 §H): a plain card; tables collapsed (P2.2)."""
    return (
        f'<div class="card analytics-card"><p class="lead">{_esc(title)}</p>'
        f'<p class="big">{_esc(summary)}</p><p class="mut">{_esc(derivation)}</p>{svg}'
        f"<details><summary>Details</summary>{detail}</details>"
        f"{_analytics_export_form(view.window_days, view.group_by, theme)}"
        "</div>"
    )


def analytics_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/analytics` - one read-only analytics theme per page (v2.4 S5).

    The ``theme`` query parameter selects the visible theme (default
    ``velocity``); the others are one plain-link away - a page shows one
    theme's chart, not four stacked charts. Charts are static inline SVG
    through the ``analytics/sparkline.py`` seam, real multi-point series
    only (P2.2 bans pseudo-sparklines: a single-point series renders no
    sparkline, just the labeled summary).
    """
    query = query or {}
    model, failure = _analytics_view(Path(root), query)
    if model is None:
        return failure

    theme = (query.get("theme") or ["velocity"])[0]
    if theme not in {"velocity", "blockers", "reviews", "evidence"}:
        theme = "velocity"

    warnings = analytics_warnings(Path(root), model)
    overdue = (
        f'<p class="banner warning">Overdue reviews: {model.reviews.overdue_count} '
        "scheduled review(s) need attention.</p>"
        if model.reviews.overdue_count
        else ""
    )
    limited = ""
    if model.is_limited:
        sentence = limited_data_sentence(
            model.min_sessions_for_full_data, model.window_days
        )
        limited = f'<p class="banner advisory">{_esc(sentence)}</p>'
    days = model.window_days
    group_by = model.group_by
    options = "".join(
        f'<option value="{n}" {"selected" if n == days else ""}>{label}</option>'
        for n, label in ((7, "Last 7 days"), (30, "Last 30 days"), (90, "Last 90 days"))
    )
    controls = (
        '<div class="card analytics-controls"><form method="get" action="/analytics">'
        '<div class="form-row"><label>'
        "Date range</label>"
        f'<select name="days">{options}'
        f'<option value="{days}" {"selected" if days not in (7, 30, 90) else ""}>Policy default ({days}d)</option>'
        f'</select><input type="hidden" name="group-by" value="{_esc(group_by)}">'
        f'<input type="hidden" name="theme" value="{_esc(theme)}">'
        '<button class="btn secondary" type="submit">Apply</button></div></form>'
        '<div class="form-row"><label>Group by</label>'
        f'<a class="btn {"secondary" if group_by == "track" else ""}" href="/analytics?days={days}&amp;group-by=prefix&amp;theme={theme}">Prefix</a> '
        f'<a class="btn {"secondary" if group_by == "prefix" else ""}" href="/analytics?days={days}&amp;group-by=track&amp;theme={theme}">Track</a></div>'
        '</div>'
    )
    advisory = "".join(
        f'<p class="banner advisory">{_esc(warning)}</p>' for warning in warnings
    )

    velocity = model.velocity
    velocity_detail = _table(
        ["Group", "Sessions", "Nodes"],
        [[_esc(group), _esc(sessions), _esc(nodes)] for group, sessions, nodes in velocity.group_rows],
    ) if velocity.group_rows else '<p class="mut">No work items in this window.</p>'
    blockers = model.blockers
    blocker_detail = _table(
        ["Node", "Group", "Days open"],
        [[_esc(row.node_id), _esc(row.group), _esc(row.days_open)] for row in blockers.rows],
    ) if blockers.rows else '<p class="mut">No open blockers.</p>'
    reviews = model.reviews
    review_detail = _table(
        ["Node", "Due", "Days overdue"],
        [[_esc(row.node_id), _esc(row.scheduled_for), _esc(row.days_overdue)] for row in reviews.rows],
    ) if reviews.rows else '<p class="mut">No scheduled reviews.</p>'
    evidence = model.evidence
    evidence_detail = _table(
        ["Node", "Group", "State", "Gap"],
        [[_esc(row.node_id), _esc(row.group), _esc(row.state), "yes" if row.gap else "no"] for row in evidence.rows],
    ) if evidence.rows else '<p class="mut">No nodes with artifact specs.</p>'

    # Static charts: real multi-point series only (P2.2). A theme whose
    # series has a single point (blockers/reviews/evidence summaries)
    # renders the labeled summary without a pseudo-sparkline.
    velocity_svg = sparkline_svg(
        [(week.label, week.session_count) for week in velocity.weeks]
    )

    themes = {
        "velocity": (
            "Velocity",
            f"{velocity.sessions_in_window} sessions, {velocity.total_minutes} minutes",
            "Sessions and work items started in the selected window, bucketed by week.",
            velocity_svg,
            velocity_detail,
        ),
        "blockers": (
            "Blockers",
            f"{blockers.open_count} open, {blockers.resolved_in_window} resolved",
            "Open blockers are counted now; resolved blockers are counted when resolved in the window.",
            "",
            blocker_detail,
        ),
        "reviews": (
            "Reviews",
            f"{reviews.completed_in_window} completed, {reviews.overdue_count} overdue",
            "Completion rate is completed reviews divided by completed plus scheduled reviews.",
            "",
            review_detail,
        ),
        "evidence": (
            "Evidence",
            f"{evidence.nodes_with_gaps} nodes with gaps, {evidence.coverage_rate * 100:.0f}% coverage",
            "Coverage is the share of nodes with artifact specs that have no required-spec gap.",
            "",
            evidence_detail,
        ),
    }
    title, summary, derivation, svg, detail = themes[theme]
    theme_links = " ".join(
        '<a href="/analytics?days={d}&amp;group-by={g}&amp;theme={t}">{label}</a>'.format(
            d=days, g=group_by, t=name, label=_esc(label)
        )
        for name, (label, *_rest) in themes.items()
    )
    cards = _analytics_card(title, summary, derivation, svg, detail, model, theme)
    body = (
        _chrome(root, current_view="analytics")
        + _flash_html(query, "/analytics")
        + overdue
        + limited
        + advisory
        + controls
        + f'<nav class="nav" aria-label="Themes">{theme_links}</nav>'
        + f'<div class="analytics-grid">{cards}</div>'
    )
    return "Analytics", body, 200



# --- Confirmation modals (G2#66) — server-fresh facts, domain refusal is truth --


def _modal_shell(
    view: JoinedView,
    node_id: str,
    heading: str,
    inner: str,
    query: dict | None = None,
    root=None,
) -> tuple[str, str, int]:
    """The page-level safety panel enclosing a pass/master body (T5 §B+§F).

    Safety color rides the card's border via the locked tokens: pass
    ``--accent``, master step 1 ``--warn``, step 2 ``--err`` — the old
    unstyled ``.modal`` divergence is gone; panels render as cards with
    panel padding at the locked card band. No overlay: no dialog, no
    popover, no backdrop. Server-fresh per request; writes are 303+flash-only.
    """
    node = view.node_map[node_id]
    state = view.store.state_of(node_id)
    safety_class = (
        "safety-warn"
        if heading.startswith("Step 1")
        else "safety-err" if heading.startswith("Step 2") else "safety-accent"
    )
    dismiss_path = f"/nodes/{node_id}"
    if heading.startswith("Step 1"):
        dismiss_path = f"/nodes/{node_id}/master"
    elif heading.startswith("Step 2"):
        dismiss_path = f"/nodes/{node_id}/master/confirm"
    elif heading.startswith("Confirm pass"):
        dismiss_path = f"/nodes/{node_id}/pass"
    modal = (
        '<div class="card safety '
        f'{safety_class}">'
        f'<div class="kicker">{_esc(heading)}</div>'
        f'<p class="lead">{_esc(node.title)}</p>'
        f'<p><span class="pill {_esc(_slug(state))}">{_esc(_normalize_pill_label(state))}</span></p>'
        f"{inner}"
        "</div>"
    )
    header_html = _chrome(root)

    body = (
        header_html
        + _flash_html(query or {}, dismiss_path)
        + _degraded_banner(view)
        + modal
    )
    return node.title, body, 200


def pass_modal_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/pass` — the pass confirmation panel (T5 §B+§F).

    Every render recomputes eligibility from a fresh lenient join; nothing is
    pre-disabled. Confirming POSTs and re-runs the guarded write against
    freshly loaded truth, so a stale panel can never assert what eligibility
    no longer supports. Copy states what changes, its side effects, and no
    engine internals (specs by human title, never raw spec ids).
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    eligibility = compute_eligibility(
        node_id,
        view.specs_by_node.get(node_id, []),
        has_gate=node_id in view.has_gate,
        records=view.records,
        node_state=state,
    )

    gate = view.gates_by_node.get(node_id)
    if gate is None:
        authority_line = "No checking method is set up — evidence cannot count here yet."
    elif gate.command:
        authority_line = "Checked automatically — verification confirms your evidence."
    else:
        authority_line = "Checked by you — you state the verdict when you submit."

    titles_by_spec = {
        s.id: (s.title or s.id) for s in view.specs_by_node.get(node_id, [])
    }
    spec_rows = [
        [
            _esc(titles_by_spec.get(s.spec_id, s.spec_id)),
            _esc(s.minimum_count),
            _esc(s.accepted_count),
            "met" if s.met else "below minimum",
        ]
        for s in eligibility.specs
    ]
    spec_table = (
        _table(["What you show", "Minimum", "Live accepted", "Standing"], spec_rows)
        if spec_rows
        else '<p class="mut">No required proof is defined for this skill.</p>'
    )

    verdict_html = _output_banners(
        ["This skill is ready to mark as passed, on this fresh read."]
        if eligibility.eligible
        else list(eligibility.reasons),
        default_class="ok" if eligibility.eligible else "warning",
    )

    not_backed = ""
    if eligibility.passed_but_not_backed:
        not_backed = (
            '<p class="banner warning">Already passed but no longer backed by live '
            "proof — the pass stands regardless, never moves backward.</p>"
        )

    cadence = view.policy.cadence
    if cadence.schedule_reviews_after_pass and cadence.intervals:
        days = ", ".join(str(interval.days_after_pass) for interval in cadence.intervals)
        review_note = (
            '<p class="banner advisory">Marking as passed schedules '
            f"reviews for {days} days after the pass.</p>"
        )
    else:
        review_note = (
            '<p class="banner advisory">No reviews are scheduled automatically — '
            "reviews stay manual.</p>"
        )

    node_title = view.node_map[node_id].title
    inner = (
        f"<p>How this is checked: {authority_line}</p>"
        f"{spec_table}"
        "<p><strong>Eligibility</strong></p>"
        f"{verdict_html}"
        f"{not_backed}"
        "<p>Marking as passed records this skill as passed. "
        "Passed never moves backward.</p>"
        f"{review_note}"
        f'<form method="post" action="/nodes/{_esc(node_id)}/pass">'
        '<div class="actions">'
        f'<button type="submit" class="btn">Mark {_esc(node_title)} passed</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
        "</div></form>"
    )
    return _modal_shell(view, node_id, "Confirm pass", inner, query, root)


def _mastery_facts_html(view: JoinedView, node_id: str) -> tuple[str, str]:
    """Fresh mastery facts table + eligibility banners, shared by both steps (T5 §F).

    Recomputed from a fresh join on every render — step 2 re-renders the
    node and facts freshly rather than trusting step 1's read (P4.4).
    """
    state = view.store.state_of(node_id)
    values = view.policy.mastery
    passed_at = passed_at_of(view.store, node_id)
    mastery = compute_mastery_eligibility(
        node_id,
        current_state=state,
        passed_at=passed_at,
        specs=view.specs_by_node.get(node_id, []),
        records=view.records,
        reviews=view.reviews,
        values=values,
    )
    accepted_total = sum(
        live_accepted_count(view.records, s.id)
        for s in view.specs_by_node.get(node_id, [])
    )
    fact_rows = [
        ["Passed on", _esc(str(passed_at)[:10]) if passed_at else "—"],
        [
            "Live proof accepted",
            f"{accepted_total} of {values.min_accepted_evidence} required",
        ],
        [
            "Review spacing",
            f"a satisfactory completed review at least "
            f"{values.min_days_pass_to_review} day(s) after the pass",
        ],
    ]
    verdict_html = _output_banners(
        ["This skill is ready for the permanent confirm, on this fresh read."]
        if mastery.eligible
        else list(mastery.reasons),
        default_class="ok" if mastery.eligible else "warning",
    )
    return _table(["Fact", "Value"], fact_rows), verdict_html


def master_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master` — step 1 of 2: mastery facts (T5 §B+§F+P4.1)."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    facts_table, verdict_html = _mastery_facts_html(view, node_id)

    if state == "locked" or state != "passed":
        # P4.1 structural omission: Continue is omitted on a structural wall —
        # locked, or anything that is not passed — and the wall is shown with
        # its unmet prerequisites in plain words.
        if state == "locked":
            wall_note = (
                '<p class="mut">Continue is unavailable — this skill is locked '
                "until its prerequisites are passed.</p>"
            )
        else:
            wall_note = (
                '<p class="mut">Continue is unavailable — mastery needs '
                "a passed skill first.</p>"
            )
        actions = (
            '<div class="actions">'
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )
    else:
        # Judgment eligibility stays live with advisory text beside the action.
        wall_note = (
            '<p class="mut">Mastery needs a passed skill with accepted proof '
            "and a satisfactory spaced review.</p>"
        )
        actions = (
            '<div class="actions">'
            + f'<a class="btn master" href="/nodes/{_esc(node_id)}/master/confirm">'
            "Continue to permanent confirm &rarr;</a>"
            + f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )

    inner = (
        '<div class="kicker">Mastery facts</div>'
        + facts_table
        + "<p><strong>Eligibility</strong></p>"
        + verdict_html
        + wall_note
        + actions
    )
    return _modal_shell(view, node_id, "Step 1 — Mastery facts", inner, query, root)


def master_confirm_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master/confirm` — step 2 of 2: permanence (T5 §B+§F+P4.4)."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    node_title = view.node_map[node_id].title
    facts_table, verdict_html = _mastery_facts_html(view, node_id)
    inner = (
        '<div class="kicker">Mastery facts — checked again just now</div>'
        + facts_table
        + verdict_html
        + '<p class="banner warning"><strong>This is permanent.</strong> '
        "Mastered never moves backward — this is permanent. "
        "A later unsatisfactory review creates pressure, but the state never "
        "moves backward. Confirm only if you intend this skill to remain mastered "
        "forever.</p>"
        f'<form method="post" action="/nodes/{_esc(node_id)}/master/confirm">'
        '<div class="actions">'
        f'<button type="submit" class="btn master">Mark {_esc(node_title)} mastered</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/master">Back</a>'
        "</div></form>"
    )
    return _modal_shell(view, node_id, "Step 2 — This is permanent", inner, query, root)


# --- POST handlers — thin glue over dispatch, exit-code mapped -------------------


def post_pass(root, node_id: str, form: dict):
    """POST `/nodes/{id}/pass` — always 303 (T5 §D1): ok to the node page,
    refusal back to the pass step as a warning flash, failure with /health."""
    exit_code, lines = _dispatch_web(root, "pass", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
        lines,
        exit_code,
        refusal_url=f"/nodes/{node_id}/pass",
    )


def post_master_confirm(root, node_id: str, form: dict):
    """POST `/nodes/{id}/master/confirm` — always 303 (T5 §D1+P4.4)."""
    exit_code, lines = _dispatch_web(root, "master", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
        lines,
        exit_code,
        refusal_url=f"/nodes/{node_id}/master/confirm",
    )


def post_start(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    exit_code, lines = _dispatch_web(
        root, "start", node_id=node_id, template=_field(form, "template")
    )
    return _finish_write(next_url, lines, exit_code)


def post_work(root, form: dict):
    next_url = _safe_next(form, "/")
    node_id = _field(form, "node_id")
    minutes, minutes_error = _int_field(form, "minutes")
    if not node_id:
        return _redirect_with_notice(next_url, ["work requires a node id."], "warning")
    if minutes_error:
        return _redirect_with_notice(next_url, [minutes_error], "warning")
    exit_code, lines = _dispatch_web(
        root,
        "work",
        node_id=node_id,
        blocked=_field(form, "blocked") is not None,
        notes=_field(form, "notes"),
        minutes=minutes,
    )
    return _finish_write(next_url, lines, exit_code)


def post_session_close(root, form: dict):
    next_url = _safe_next(form, "/")
    exit_code, lines = _dispatch_web(root, "session close", end=_field(form, "end"))
    return _finish_write(next_url, lines, exit_code)


def post_blocker_create(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    exit_code, lines = _dispatch_web(
        root, "blocker create", node_id=node_id, description=_field(form, "description")
    )
    return _finish_write(next_url, lines, exit_code)


def post_blocker_resolve(root, blocker_id: str, form: dict):
    next_url = _safe_next(form, "/")
    exit_code, lines = _dispatch_web(
        root, "blocker resolve", blocker_id=blocker_id, summary=_field(form, "summary")
    )
    return _finish_write(next_url, lines, exit_code)


def post_evidence(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    location = _field(form, "location")
    if not location:
        return _redirect_with_notice(
            next_url,
            ["Recording evidence needs the artifact location."],
            "warning",
        )
    verdict = _field(form, "verdict")
    exit_code, lines = _dispatch_web(
        root,
        "evidence submit",
        node_id=node_id,
        spec=_field(form, "spec"),
        location=location,
        note=_field(form, "note"),
        accept=verdict == "accept",
        reject=verdict == "reject",
        supersedes=_field(form, "supersedes"),
        reason=_field(form, "reason"),
    )
    return _finish_write(next_url, lines, exit_code)


def post_analytics_export(root, form: dict):
    """POST `/analytics/export` — delegate export to the canonical CLI command."""
    theme = _field(form, "theme") or "all"
    fmt = _field(form, "format") or "md"
    group_by = _field(form, "group_by") or "prefix"
    raw_days = _field(form, "days")
    try:
        days = int(raw_days) if raw_days else None
    except ValueError:
        return _redirect_with_notice(
            "/analytics", ["The review window must be a number of days."], "warning"
        )
    if theme not in {"all", "velocity", "blockers", "reviews", "evidence"}:
        return _redirect_with_notice(
            "/analytics", ["That theme is not available."], "warning"
        )
    if fmt not in {"md", "html", "json"} or group_by not in {"prefix", "track"}:
        return _redirect_with_notice(
            "/analytics", ["That export shape is not available."], "warning"
        )
    exit_code, lines = _dispatch_web(
        root,
        "analytics export",
        theme=theme,
        format=fmt,
        days=days,
        group_by=group_by,
        state=[],
        output=None,
    )
    return _finish_write("/analytics", lines, exit_code)
