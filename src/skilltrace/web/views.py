"""Daily pages — reads (T3) and browser writes (T4) over structured cards.

The GET routes (`/`, `/next`, `/nodes/{id}`, `/health`) translate the CLI
derivations into browser cards. The translation consumes the structured
``MentorCard`` model the derivations produce (``mentor.cards``) — banners
carry a ``kind`` field, pills carry a ``label`` field, kickers, titles,
leads, labels, paragraphs, and sub-lines are typed parts, and each card is
already a discrete unit. No Mentor prose is re-declared here, so CLI and
serve cannot disagree; the legacy line grammar (``[tag]`` prefixes, ``---``
separators, indentation, uppercase kickers) survives only as the terminal
serializer ``render.cards_to_lines`` and the deprecated-compat parser
``mentor.cards.lines_to_cards`` for out-of-scope line producers.

The write routes (T4, G2#66 + G5#69) are thin glue over the *same* registry the

The write routes (T4, G2#66 + G5#69) are thin glue over the *same* registry the
CLI dispatches through: a confirmed action builds ``Context(root, args,
source="web")`` and calls ``dispatch(REGISTRY.get(name), ctx)`` in-process —
no second write path, sole-caller invariant intact. Handler stdout is captured
and rendered verbatim (escaped); ``CommandResult.exit_code`` is the contract:
``0`` redirects after POST with an ok flash, ``2`` re-renders the modal (or
flashes back to the host page) with the refusal verbatim, ``1`` redirects with
a banner suggesting ``skilltrace validate``. Heavyweight confirmation stays
exclusive to ``pass``/``master``; every other daily write is a plain form.
Buttons are never pre-disabled by derived preconditions — the domain's refusal
on click is the truth (G2), so a stale modal can never assert what eligibility
no longer supports.

Information architecture: P1 variant **A — Mentor-first linear** (decision on
issue #72). One column of reading-order cards; pressure excerpts and the
health strip follow the focus card instead of competing with it; drill-downs
are native ``<details>`` elements, so no JavaScript anywhere. Reads go through
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
  /* v2.4 S2 design tokens (P5.4): every hex lives in :root; one accent.
     Two density registers (comfort = page chrome, compact = data
     tables/pills) and the font-role split (display / body / data). */
  :root {
    --bg:#fafaf9; --fg:#1c1917; --muted:#57534e; --border:#e7e5e4; --pill:#f5f5f4;
    --accent:#0c4a6e; --warn:#fef3c7; --err:#fee2e2; --advisory:#e0f2fe; --ok:#dcfce7;
    --card:#ffffff;
    --radius:12px; --radius-sm:8px;
    --density-pad:14px; --density-gap:10px; --density-pad-compact:6px; --density-gap-compact:4px;
    --font-display:ui-sans, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial;
    --font-body:ui-sans, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial;
    --font-data:ui-monospace, 'Cascadia Mono', Consolas, monospace;
  }
  *{box-sizing:border-box}
  html,body{width:100%; overflow-x:clip}
  body{margin:0; font:14px/1.5 var(--font-body); color:var(--fg); background:var(--bg);}
  .wrap{max-width:1100px; margin:0 auto; padding:0 18px;}
  main.wrap{padding:10px 18px 24px}
  h1 { font-size: 1.4rem; font-family:var(--font-display); } h2 { font-size: 1.1rem; margin-top: 1.2rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: var(--density-pad-compact) 0.5rem; border-bottom: 1px solid var(--border); }
  .mut { color: var(--muted); font-size: 0.85rem; }
  .small{font-size:12px; color:var(--muted); line-height:1.35}
  .big{font-size:15px; line-height:1.45}
  ul { padding-left: 1.2rem; }
  header{position:sticky; top:0; z-index:10; background:var(--card); border-bottom:1px solid var(--border);}
  header .wrap{max-width:1100px; margin:0 auto; padding:0 18px;}
  header h1.brand{font-size:18px; font-weight:800; margin:10px 0 2px; line-height:1.2; font-family:var(--font-display)}
  .nav { font-size: 0.9rem; display:flex; gap:0.9rem; flex-wrap:wrap; padding:6px 0 8px; align-items:center}
  .nav a { color:var(--accent); text-decoration:none; font-weight:600}
  .nav a:hover{text-decoration:underline}
  .nav a[aria-current="page"]{border-bottom:2px solid var(--accent); padding-bottom:2px}
  .nav .jump{display:flex; gap:6px; align-items:center; margin-left:auto}
  .nav .jump input{border:1px solid var(--border); border-radius:var(--radius-sm); padding:4px 8px; font:inherit; font-size:13px; background:var(--card); color:var(--fg)}
  .nav .jump button{border:1px solid var(--accent); background:var(--accent); color:#fff; border-radius:var(--radius-sm); padding:4px 10px; font-weight:600; cursor:pointer; font-size:12px}
  .health-strip{display:flex; gap:6px; flex-wrap:wrap; padding:6px 0 8px; font-size:12px}
  .health-strip .pill{border:1px solid var(--border); border-radius:999px; padding:3px 10px; background:var(--card); font-size:12px}
  .health-strip .pill.ok{background:var(--ok); border-color:#86efac}
  .health-strip .pill.attention{background:var(--warn); border-color:#fde68a}
  .health-strip .pill.broken{background:var(--err); border-color:#fca5a5}
  .card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:var(--density-pad); margin:var(--density-gap) 0; }
  .kicker { font-size:11px; letter-spacing:.08em; font-weight:700; color:var(--muted); text-transform:uppercase; margin:0.5rem 0 0.2rem; }
  .kicker:first-child{margin-top:0}
  .title{font-size:20px; font-weight:700; line-height:1.2; margin:4px 0 4px; font-family:var(--font-display)}
  .label { font-weight: 600; margin: 0.4rem 0 0.12rem; }
  .lead { font-weight: 600; font-size: 1.05rem; margin: 0.15rem 0; font-family:var(--font-display)}
  .sub { margin: 0.12rem 0 0.12rem 0.9rem; }
  .next-action{margin:0.6rem 0 0.1rem; font-weight:600}
  .count{margin-right:0.9rem}
  .count strong{font-size:1.15rem; font-family:var(--font-display)}
  .resumable .inline{display:inline-block; margin-left:0.6rem}
  .theme-nav{margin:0.6rem 0}
  .pill { display: inline-block; border: 1px solid var(--border); border-radius: 999px;
          padding: 2px 8px; font-size: 11px; margin: 0.1rem 0.3rem 0.1rem 0; background:var(--pill); font-weight:600}
  .pill.locked, .pill.broken { border-color: #fca5a5; background: var(--err); }
  .pill.available, .pill.ready-to-start, .pill.verified { border-color: #86efac; background: var(--ok); }
  .pill.active, .pill.in-progress, .pill.attention { border-color: #7dd3fc; background: var(--advisory); }
  .pill.passed { border-color: #c4b5fd; background: #ede9fe; }
  .pill.mastered { border-color: #facc15; background: #fef9c3; }
  .pill.stale { border-color: #fde68a; background: var(--warn); }
  .banner { padding: 7px 10px; border-radius: var(--radius-sm); margin: 0.35rem 0; font-size:13px}
  .banner.advisory, .banner.attention { background: var(--advisory); border:1px solid #bae6fd; }
  .banner.warn, .banner.warning { background: var(--warn); border:1px solid #fde68a; }
  .banner.err, .banner.error, .banner.fail { background: var(--err); border:1px solid #fca5a5; }
  .banner.ok, .banner.success { background: var(--ok); border:1px solid #86efac; animation: settle .6s ease-out; }
  @keyframes settle { from { opacity:.35; } to { opacity:1; } }
  .btn.primary{background:var(--accent); color:#fff; border-color:var(--accent)}
  .analytics-grid{display:grid; grid-template-columns:1fr 1fr; gap:var(--density-gap)}
  /* the one breakpoint (P5.4: the four 900px rules collapse to one) */
  @media(max-width:900px){.analytics-grid{grid-template-columns:1fr}}
"""


def page(title: str, body: str) -> str:
    """Wrap a body in the single shared layout (one inline style block)."""
    # Bodies start with a sticky <header> (via _NAV). Lift it outside the
    # main wrap so its background spans the full viewport width while its
    # inner .wrap stays 1100px — same shell as prototype/p1b-polish.html.
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
    """The shared chrome header (v2.4 S2): two nav groups + health strip.

    ``current_view`` is the *view identity* (ADR 0007) — ``aria-current``
    derives from the declared interface ``VIEWS`` table (the seam), never
    from URL string-matching in the page bodies. The health strip renders
    per-layer pills with an attention state from the structured
    ``HealthReport`` (warning counts ride the P2.4 seam).
    """
    from .interface import VIEWS

    links: list[str] = []
    for group in ("daily", "diagnostics"):
        for view in VIEWS.values():
            if view.group != group or "{" in view.route:
                continue  # parameterized routes are not nav links
            current_attr = ' aria-current="page"' if view.name == current_view else ""
            links.append(
                f'<a href="{_esc(view.route)}"{current_attr}>{_esc(view.title)}</a>'
            )
    pills = ""
    if health is not None:
        pills = "".join(
            '<span class="pill '
            + ("broken" if not layer.ok else ("attention" if layer.warning_count else "ok"))
            + '">'
            + _esc(layer.target)
            + (
                f": {_esc(layer.warning_count)} warn"
                if layer.ok and layer.warning_count
                else ": OK" if layer.ok else ": FAILED"
            )
            + "</span>"
            for layer in health.layers
        )
    return (
        "<header>"
        '<div class="wrap">'
        '<h1 class="brand">SkillTrace</h1>'
        '<nav class="nav" aria-label="primary">'
        + "".join(links)
        + '<form class="jump" method="get" action="/nodes/jump">'
        '<input type="text" name="node_id" placeholder="jump to a skill - title or id" aria-label="jump to skill" size="32">'
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
    """The shared error body (v2.4 §B): full chrome when the context loads.

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
        f'{header_html}<p class="banner error">{_esc(message)}</p>'
        '<p><a href="/">Back to Today</a></p>'
    )


def _status_page(status: int, message: str, root=None) -> tuple[str, int]:
    if status == 404:
        return _error_body(message, root), 404
    return _error_body(message, root), status


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

def _flash_html(query: dict) -> str:
    """Flash banners carried across a redirect in the query string."""
    text = (query.get("notice") or [""])[0]
    if not text:
        return ""
    kind = (query.get("kind") or ["ok"])[0]
    if kind not in {"ok", "warning", "error"}:
        kind = "ok"
    return _output_banners(text.splitlines(), default_class=kind)


def _redirect_with_notice(location: str, lines: list[str], kind: str) -> Redirect:
    """PRG redirect carrying the captured output as a flash notice."""
    notice = "\n".join(line for line in lines if line.strip())
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
    """Advisory notice when lenient layers degraded — forms stay enabled."""
    if not view.degraded:
        return ""
    names = ", ".join(sorted(set(view.degraded)))
    return (
        '<p class="banner advisory">Optional layer(s) failed to load and read '
        f"as empty ({_esc(names)}) — forms stay enabled and a refusal on "
        "click remains the truth. The validation roll-up and the health "
        "page carry the detail.</p>"
    )


def _finish_write(
    next_url: str,
    lines: list[str],
    exit_code: int,
    *,
    stay_renderer=None,
) -> Redirect | tuple[str, str, int]:
    """Map a dispatched write's exit code per G2#66.

    ``0`` → redirect-after-POST with an ok flash; ``2`` → the modal re-renders
    with the refusal verbatim inline when a ``stay_renderer`` is given, else a
    warning flash back on the host page; ``1`` → dismiss with an error flash
    suggesting ``skilltrace validate``.
    """
    if exit_code == 0:
        return _redirect_with_notice(next_url, lines, "ok")
    if exit_code == 2 and stay_renderer is not None:
        return stay_renderer(_output_banners(lines))
    if exit_code == 2:
        return _redirect_with_notice(next_url, lines, "warning")
    lines = [*lines, "Operational failure — the validation roll-up carries the detail."]
    return _redirect_with_notice(next_url, lines, "error")


# --- Structured cards -> HTML ------------------------------------------------


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _render_part(part) -> str:
    """One typed card part to HTML — the single card-type-to-CSS-class map."""
    if isinstance(part, Banner):
        return f'<p class="banner {_esc(part.kind)}">{_esc(part.text)}</p>'
    if isinstance(part, Pill):
        return (
            f'<span class="pill {_esc(_slug(part.label))}">{_esc(part.label)}</span>'
        )
    if isinstance(part, Kicker):
        return f'<div class="kicker">{_esc(part.text)}</div>'
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

        label = intent_label(part.intent)
        return (
            f'<p class="next-action" data-intent="{_esc(part.intent)}">'
            f"{_esc(label)}</p>"
        )
    return f"<p>{_esc(part.text)}</p>"  # Para (and any future plain part)


def _render_card_inner(card: MentorCard) -> str:
    return "\n".join(_render_part(part) for part in card.parts)


def render_cards(cards: list[MentorCard]) -> str:
    """The structured cards as one ``<div class="card">`` per card."""
    return "".join(
        f'<div class="card">\n{_render_card_inner(card)}\n</div>\n' for card in cards
    )


def cards_html(lines: list[str]) -> str:
    """Deprecated compat: legacy lines as cards (health/reports/export only).

    Parses ``lines`` via ``mentor.cards.lines_to_cards`` and renders through
    :func:`render_cards` so out-of-scope line producers share the one HTML
    pipeline. New code must pass ``MentorCard`` lists to ``render_cards``.
    """
    return render_cards(lines_to_cards(lines))


# --- Shared cards ---------------------------------------------------------------


# --- Route bodies ---------------------------------------------------------------


def _focus_card(view, root, model) -> str:
    """Today block 1 — the focus card (§A): title, state + reason, one CTA."""
    from .interface import intent_label

    if not model.focus_node_id or model.focus_node_id not in view.node_map:
        # No focus: the quiet empty state — one muted pointer, no backlog.
        return (
            '<div class="card focus">\n'
            '<div class="kicker">TODAY</div>\n'
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
    # The single primary CTA, from the NextAction fact's intent.
    if action is not None and action.intent == "start" and state == "available":
        cta = _start_confirm_form(view, root, focus.id)
    elif action is not None and action.node_id:
        label = intent_label(action.intent)
        href = f"/nodes/{_esc(action.node_id)}"
        cta = (
            '<div class="actions"><a class="btn primary" href="'
            + href
            + '">'
            + _esc(label)
            + "</a></div>"
        )
    else:
        cta = ""
    pill_label = {
        "locked": "Locked",
        "available": "Ready to start",
        "active": "In progress",
        "passed": "Passed",
        "mastered": "Mastered",
    }.get(state, state)
    return (
        '<div class="card focus">\n'
        '<div class="kicker">TODAY</div>\n'
        f'<p class="lead"><a href="/nodes/{_esc(focus.id)}">{_esc(focus.title)}</a></p>\n'
        f'<p><span class="pill {_esc(_slug(pill_label))}">{_esc(pill_label)}</span></p>\n'
        + (f'<p class="big">{_esc(reason)}</p>\n' if reason else "")
        + cta
        + "</div>\n"
    )


def _count_set_card(view, model) -> str:
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


def _resumable_active_line(view, root) -> str:
    """Today block 3 — the resumable-active line, only while a session is open."""
    del root
    current = open_session(view.sessions)
    if current is None:
        return ""
    started = _esc(str(current.started_at)[:16].replace("T", " "))
    return (
        '<div class="card resumable">\n'
        f"<p>Session <code>{_esc(current.id)}</code> open since {started}.</p>\n"
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
        + _flash_html(query or {})
        + _degraded_banner(view)
        + _focus_card(view, root, model)
        + _count_set_card(view, model)
        + _resumable_active_line(view, root)
    )
    return "Today", body, 200

def _template_select(templates: set[str], empty_label: str) -> str:
    options = "".join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in sorted(templates))
    return (
        f'<select name="template"><option value="">{_esc(empty_label)}</option>{options}</select>'
    )


def _start_confirm_form(view: JoinedView, root, node_id: str) -> str:
    """The lightweight single-click start confirm (G5) — never a heavyweight modal.

    Copy states the forward-only permanence; locked reason and an already-open
    session stay visible as advisory text while the button stays enabled — the
    domain refuses a second session or a locked node verbatim on click.
    """
    title = view.titles.get(node_id, node_id)
    state = view.store.state_of(node_id)
    open_now = open_session(view.sessions)
    advisory = ""
    if state == "locked":
        advisory = (
            '<p class="mut">Currently locked (unsatisfied hard prerequisite) — '
            "the domain refuses until it unlocks.</p>"
        )
    elif open_now is not None:
        advisory = (
            f'<p class="mut">Session <code>{_esc(open_now.id)}</code> is open — '
            "the domain refuses a second; close it first.</p>"
        )
    return (
        '<div class="form-row"><label>Session template</label>'
        f"{_template_select(view.policy.session_templates, '(none)')}</div>"
        f"{advisory}"
        '<div class="actions">'
        f'<form method="post" action="/nodes/{_esc(node_id)}/start">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        '<button type="submit" class="btn">Start studying</button></form>'
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
    """GET `/next?minutes=&limit=&locked=` — mirrors the CLI flags."""
    minutes = _parse_int(query, "minutes", 60)
    limit = _parse_int(query, "limit", 5)
    if minutes is None or limit is None:
        body, status = _status_page(400, "minutes and limit must be integers.", root)
        return "Next", body, status
    locked_values = query.get("locked", [""])
    show_locked = locked_values[0].lower() in {"1", "true", "on", "yes"} if locked_values else False

    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_next(
        view, Path(root), minutes=minutes, limit=limit, show_locked=show_locked
    )

    checked = " checked" if show_locked else ""
    toggle_params = f"minutes={minutes}&amp;limit={limit}" + ("" if show_locked else "&amp;locked=1")
    toggle_label = "Hide locked" if show_locked else "Show locked"
    # Human controls (v2.4 S4): the session window and option count phrased
    # as questions, with the CLI mirror noted once, muted.
    filters = (
        '<div class="card">\n'
        '<form class="filters" method="get" action="/next">'
        f'<label>Minutes you have <input type="number" name="minutes" value="{minutes}" min="1" size="4"></label>'
        f'<label>How many options <input type="number" name="limit" value="{limit}" min="1" size="3"></label>'
        f'<label><input type="checkbox" name="locked" value="1"{checked}> show locked</label>'
        '<button type="submit">Apply</button>'
        "</form>\n"
        f'<p class="mut"><a href="/next?{toggle_params}">{toggle_label}</a></p>\n'
        "</div>\n"
    )

    header_html = _chrome(root, current_view='next')

    breadcrumb = '<div class="breadcrumb"><a href="/">Today</a> &middot; <a href="/next">Next</a></div>\n'
    return "Next", header_html + breadcrumb + filters + _candidate_cards(model), 200


def _why_details(rec) -> str:
    facts = "".join(
        f"<li>{_esc(label)}: {_esc(value)}</li>"
        for label, value in (
            ("score", rec.score),
            ("track weight", f"{rec.track} = {rec.track_weight:g}"),
            ("downstream leverage", f"{rec.leverage} unlock(s)"),
            ("fits session", "yes" if rec.fits_session else "no"),
            ("already active", "yes" if rec.is_active else "no"),
            ("remediation boost", "active" if rec.remediation_boosted else "none"),
            ("open blocker penalty", "applied" if rec.open_blocked else "none"),
        )
    )
    return (
        "<details>\n<summary>Why this?</summary>\n"
        f'<div class="sub">{_esc(rec.reason)}</div>\n'
        f"<ul>{facts}</ul>\n"
        '<p class="mut">Advisory reasoning — policies reorder recommendations; '
        "they never block a human-initiated action.</p>\n</details>\n"
    )


def _candidate_cards(model) -> str:
    """Candidate cards with a per-card collapsible "Why this?" attached.

    Candidate cards are recognized by their ``OPTION`` kicker; the k-th
    such card receives model.recommendations[k]'s reasoning. Other cards
    (warning banners, remediation advisories, the locked appendix) pass
    through untouched.
    """
    rec_iter = iter(model.recommendations)
    html_out = []
    for card in model.cards:
        kicker = next(
            (part.text for part in card.parts if isinstance(part, Kicker)), ""
        )
        inner = _render_card_inner(card)
        if kicker.startswith("OPTION "):
            rec = next(rec_iter, None)
            if rec is not None:
                inner += _why_details(rec)
        html_out.append(f'<div class="card">\n{inner}\n</div>\n')
    return "".join(html_out)


def node_body(root, node_id: str, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/nodes/{id}` — primary Mentor card, write actions, drill-downs."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_node_detail(view, node_id)
    if model is None:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    actions = _node_actions_card(root, view, node_id)
    drill = _drill_down_card(node_id, view, Path(root), model)
    title = view.node_map[node_id].title
    header_html = _chrome(root, current_view='node')

    breadcrumb = (
        f'<div class="breadcrumb"><a href="/">Today</a> &middot; '
        f'<a href="/nodes/{_esc(node_id)}">{_esc(node_id)}</a></div>\n'
    )
    body = (
        header_html
        + _flash_html(query or {})
        + _degraded_banner(view)
        + breadcrumb
        + render_cards(model.cards)
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
        '<button type="submit" class="btn secondary">Resolve '
        f"{_esc(blocker_id)}</button></form></details>"
    )


def _evidence_submit_form(root, view: JoinedView, node_id: str) -> str:
    """Evidence submit (G5) — verbatim CLI fields, judged at submission.

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
            f'<option value="{_esc(s.id)}">{_esc(s.id)}</option>' for s in specs
        )
        spec_field = (
            '<div class="form-row"><label>Artifact spec</label>'
            f'<select name="spec">{options}</select></div>'
        )

    if gate.command:
        verdict_field = (
            f'<p class="mut">Objective gate — running it decides the verdict '
            f"({_esc(gate.command)}).</p>"
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
        '<div class="form-row"><label>Supersedes (record id)</label>'
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
        '<p class="mut">Acceptance freezes at submission (ADR 0003) — the gate '
        "verdict renders loudly; records are immutable and corrected by "
        "superseding, never edited.</p></details>"
    )

def _node_actions_card(root, view: JoinedView, node_id: str) -> str:
    """Node-detail write surface (G5): pass/master modals + daily-write forms.

    Structural omission per ADR 0007 §Validation (Amendment 2026-09-11) +
    P4.1: pass on a ``locked`` node and master on a node that is not
    ``passed`` are *omitted* — absent markup, never rendered-then-refused
    and never pre-disabled. Judgment eligibility stays live elsewhere.
    """
    blockers = [
        b for b in view.blockers if b.node_id == node_id and b.status == "open"
    ]
    node_url = f"/nodes/{node_id}"
    blocker_forms = "".join(
        f"<li><code>{_esc(b.id)}</code> — {_esc(b.description)} "
        + _resolve_blocker_form(b.id, node_url)
        + "</li>"
        for b in blockers
    )
    blocker_section = (
        f'<ul>{blocker_forms}</ul>'
        if blocker_forms
        else '<p class="mut">No open blockers.</p>'
    )
    state = view.store.state_of(node_id)
    actions = ""
    if state != "locked":  # structural wall: pass on locked is omitted
        actions += (
            f'<a class="btn" href="/nodes/{_esc(node_id)}/pass">Pass&hellip;</a>'
        )
    if state == "passed":  # structural wall: master requires passed
        actions += (
            f'<a class="btn master" href="/nodes/{_esc(node_id)}/master">'
            "Master&hellip;</a>"
        )
    actions_html = f'<div class="actions">{actions}</div>' if actions else ""
    return (
        '<div class="card">\n'
        '<div class="kicker">WRITE ACTIONS</div>\n'
        + actions_html
        + "\n<details open><summary>Start studying</summary>"
        f"{_start_confirm_form(view, root, node_id)}\n</details>\n"
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
        f"{_evidence_submit_form(root, view, node_id)}\n"
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

    parts = ['<div class="card">\n<div class="kicker">DRILL-DOWN — READ-ONLY FACTS</div>\n']
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
    """GET `/health` - the five validators plus liveness, read-only.

    The roll-up carries the per-layer warning counts as a column (v2.4
    P2.4 - the structured facts the health seam now reports), so a layer
    that is OK *with attention* is visible without opening the validator.
    """
    report = health_report(Path(root))

    rows = [
        [
            _esc(layer.target),
            _esc(layer.counts),
            '<span class="pill '
            + ("verified" if layer.ok else "broken")
            + ">"
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

    header_html = _chrome(root, current_view="health")

    breadcrumb = (
        "<div class=\"breadcrumb\"><a href=\"/\">Today</a> &middot; "
        "<a href=\"/health\">Health</a></div>\n"
    )
    body = (
        header_html
        + breadcrumb
        + '<div class="card">\n'
        + '<div class="kicker">HEALTH ROLL-UP</div>\n'
        + _table(["Layer", "Counts", "Status", "Warnings"], rows)
        + error_banners
        + cards_html(report.liveness_lines)
        + f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        + '<p class="mut">Read fresh from the truth files at request time - '
        "CLI edits appear on refresh.</p>\n</div>\n"
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
    return (
        f'<details open class="card analytics-card"><summary>{_esc(title)}</summary>'
        f'<p class="big">{_esc(summary)}</p><p class="mut">{_esc(derivation)}</p>{svg}{detail}'
        f"{_analytics_export_form(view.window_days, view.group_by, theme)}"
        "</details>"
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
        '<a class="btn ' + ('' if name == theme else 'secondary') + '" '
        + 'href="/analytics?days={d}&amp;group-by={g}&amp;theme={t}">{label}</a>'.format(
            d=days, g=group_by, t=name, label=_esc(label)
        )
        for name, (label, *_rest) in themes.items()
    )
    cards = _analytics_card(title, summary, derivation, svg, detail, model, theme)
    body = (
        _chrome(root, current_view="analytics")
        + _flash_html(query)
        + overdue
        + limited
        + advisory
        + controls
        + f'<div class="theme-nav">{theme_links}</div>'
        + f'<div class="analytics-grid">{cards}</div>'
    )
    return "Analytics", body, 200



# --- Confirmation modals (G2#66) — server-fresh facts, domain refusal is truth --


def _modal_shell(
    view: JoinedView,
    node_id: str,
    heading: str,
    inner: str,
    extra_html: str = "",
    root=None,
) -> tuple[str, str, int]:
    node = view.node_map[node_id]
    state = view.store.state_of(node_id)
    modal = (
        f'<div class="modal">'
        f"<h2>{heading}</h2>"
        f'<p class="mut">{_esc(node_id)} &middot; '
        f'state <span class="pill {_esc(state)}">{_esc(state)}</span></p>'
        f"{inner}"
        "</div>"
    )
    header_html = _chrome(root)

    body = header_html + _degraded_banner(view) + extra_html + modal
    return node.title, body, 200


def pass_modal_body(root, node_id: str, extra_html: str = "") -> tuple[str, str, int]:
    """GET/POST `/nodes/{id}/pass` — the pass confirmation modal (G2).

    Every render recomputes eligibility from a fresh lenient join; nothing is
    pre-disabled. Confirming POSTs and re-runs ``plan_pass`` inside the
    handler against freshly loaded truth, so a stale modal can never assert
    what eligibility no longer supports.
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
        authority_line = "No validation gate — no authority can accept its evidence."
    elif gate.command:
        authority_line = (
            "objective — runs "
            f"<code>{_esc(gate.command)}</code>; its exit code was the verdict."
        )
    else:
        authority_line = f"{_esc(gate.authority)} — learner-stated verdict at submission."

    spec_rows = [
        [
            _esc(s.spec_id),
            _esc(s.minimum_count),
            _esc(s.accepted_count),
            "met" if s.met else "below minimum",
        ]
        for s in eligibility.specs
    ]
    spec_table = (
        _table(["Required spec", "Minimum", "Live accepted", "Standing"], spec_rows)
        if spec_rows
        else '<p class="mut">No required artifact spec.</p>'
    )

    verdict_html = _output_banners(
        ["Pass eligibility currently holds on this fresh read."]
        if eligibility.eligible
        else list(eligibility.reasons),
        default_class="ok" if eligibility.eligible else "warning",
    )

    not_backed = ""
    if eligibility.passed_but_not_backed:
        not_backed = (
            '<p class="banner warning">passed_but_not_backed — this asserted pass is no '
            "longer backed by live evidence; it stands regardless, never demotes.</p>"
        )

    cadence = view.policy.cadence
    if cadence.schedule_reviews_after_pass and cadence.intervals:
        schedule = ", ".join(
            f"{interval.label} (+{interval.days_after_pass}d)"
            for interval in cadence.intervals
        )
        review_note = (
            f'<p class="banner advisory">Confirming schedules {len(cadence.intervals)} review(s) '
            f"per cadence policy: {_esc(schedule)}.</p>"
        )
    else:
        review_note = (
            '<p class="banner advisory">No auto-schedule configured — reviews stay manual '
            "(<code>review schedule</code>).</p>"
        )

    inner = (
        f"<p>Gate: {authority_line}</p>"
        f"{spec_table}"
        "<p><strong>Eligibility</strong></p>"
        f"{verdict_html}"
        f"{not_backed}"
        '<p class="mut">Confirming asserts <code>passed</code> forward-only through the '
        "same guarded writer as the CLI (one audit event, source web).</p>"
        f"{review_note}"
        f'<form method="post" action="/nodes/{_esc(node_id)}/pass">'
        '<div class="actions">'
        '<button type="submit" class="btn">Confirm pass — explicit learner command</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
        "</div></form>"
        '<p class="mut">Buttons stay enabled by design — if these facts are stale, the '
        "domain refuses on click and that refusal is the truth.</p>"
    )
    return _modal_shell(view, node_id, "Confirm pass", inner, extra_html, root)


def master_body(root, node_id: str, extra_html: str = "") -> tuple[str, str, int]:
    """GET `/nodes/{id}/master` — step 1 of 2: mastery facts."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

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
            "Accepted live evidence",
            f"{accepted_total} of {values.min_accepted_evidence} required",
        ],
        [
            "Review spacing policy",
            f"a satisfactory completed review at least "
            f"{values.min_days_pass_to_review} day(s) after the pass",
        ],
    ]
    verdict_html = _output_banners(
        ["Mastery eligibility holds — proceed to the permanent confirm."]
        if mastery.eligible
        else list(mastery.reasons),
        default_class="ok" if mastery.eligible else "warning",
    )

    inner = (
        "<div class=\"kicker\">MASTERY FACTS</div>"
        + _table(["Fact", "Value"], fact_rows)
        + "<p><strong>Eligibility</strong></p>"
        + verdict_html
        + '<p class="mut">Mastery requires a passed node with accepted evidence and '
        "satisfactory spaced review (<code>policy/mastery_promotion.yaml</code>).</p>"
        + '<div class="actions">'
        + f'<a class="btn master" href="/nodes/{_esc(node_id)}/master/confirm">'
        "Continue to permanent confirm &rarr;</a>"
        + f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
        "</div>"
    )
    return _modal_shell(view, node_id, "Step 1 — Mastery facts", inner, extra_html, root)


def master_confirm_body(root, node_id: str, extra_html: str = "") -> tuple[str, str, int]:
    """GET/POST `/nodes/{id}/master/confirm` — step 2 of 2: permanence."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    inner = (
        '<p class="banner warning"><strong>This is permanent.</strong> Mastered never '
        "demotes — a later unsatisfactory review creates pressure, but the state never "
        "moves backward. Confirm only if you intend this skill to remain mastered "
        "forever.</p>"
        '<p class="mut">Same registry nest-dispatch as the CLI '
        "(one audit event, source web).</p>"
        f'<form method="post" action="/nodes/{_esc(node_id)}/master/confirm">'
        '<div class="actions">'
        '<button type="submit" class="btn master">Confirm master — permanent</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/master">Back</a>'
        "</div></form>"
    )
    return _modal_shell(view, node_id, "Step 2 — This is permanent", inner, extra_html, root)


# --- POST handlers — thin glue over dispatch, exit-code mapped -------------------


def post_pass(root, node_id: str, form: dict):
    exit_code, lines = _dispatch_web(root, "pass", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
        lines,
        exit_code,
        stay_renderer=lambda extra: pass_modal_body(root, node_id, extra_html=extra),
    )


def post_master_confirm(root, node_id: str, form: dict):
    exit_code, lines = _dispatch_web(root, "master", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
        lines,
        exit_code,
        stay_renderer=lambda extra: master_confirm_body(root, node_id, extra_html=extra),
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
            ["evidence submit: an artifact location is required."],
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
            "/analytics", ["analytics export: days must be an integer."], "warning"
        )
    if theme not in {"all", "velocity", "blockers", "reviews", "evidence"}:
        return _redirect_with_notice(
            "/analytics", ["analytics export: unknown theme."], "warning"
        )
    if fmt not in {"md", "html", "json"} or group_by not in {"prefix", "track"}:
        return _redirect_with_notice(
            "/analytics", ["analytics export: invalid format or grouping."], "warning"
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
