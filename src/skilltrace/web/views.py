"""Daily pages — reads (T3) and browser writes (T4) over one mechanical transform.

The GET routes (`/`, `/next`, `/nodes/{id}`, `/health`) translate the CLI
derivations into browser cards. The translation is deliberately mechanical
(ADR 0006 / G3#67): every page calls the same line-producers the CLI prints
(``derive_today`` / ``derive_next`` / ``derive_node_detail`` / ``health_report``)
and transforms those canonical lines — escape per line, ``[tag]`` prefixes to
banner classes, ``[pill]`` lines to pill classes, indentation to structure,
uppercase kickers to kickers, ``---`` separators to card breaks. No Mentor
prose is re-declared here, so CLI and serve cannot disagree; if the transform
outgrows line-shape text, the sanctioned escalation is refactoring
``render.py`` into structured data, never a parallel hand-written vocabulary.

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
from ..context import JoinedView, load_context_lenient
from ..dispatch import Context, dispatch
from ..analytics.derive import derive_analytics
from ..analytics.sparkline import sparkline_svg
from ..evidence.eligibility import compute_eligibility, live_accepted_count
from ..execution.overdue import utc_today
from ..execution.sessions import open_session
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
  :root {
    --bg:#fafaf9; --fg:#1c1917; --mut:#57534e; --border:#e7e5e4; --pill:#f5f5f4;
    --accent:#0c4a6e; --warn:#fef3c7; --err:#fee2e2; --advisory:#e0f2fe; --ok:#dcfce7;
  }
  *{box-sizing:border-box}
  html,body{width:100%; overflow-x:clip}
  body{margin:0; font:14px/1.5 ui-sans, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; color:var(--fg); background:var(--bg);}
  .wrap{max-width:1100px; margin:0 auto; padding:0 18px;}
  main.wrap{padding:10px 18px 24px}
  h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 1.2rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border); }
  .mut { color: var(--mut); font-size: 0.85rem; }
  .small{font-size:12px; color:var(--mut); line-height:1.35}
  .big{font-size:15px; line-height:1.45}
  ul { padding-left: 1.2rem; }
  header{position:sticky; top:0; z-index:10; background:#fff; border-bottom:1px solid var(--border);}
  header .wrap{max-width:1100px; margin:0 auto; padding:0 18px;}
  header h1{font-size:18px; font-weight:800; margin:10px 0 2px; line-height:1.2}
  header .sub{color:var(--mut); font-size:13px; margin-bottom:8px}
  .nav { font-size: 0.9rem; margin-bottom:0; display:flex; gap:0.9rem; flex-wrap:wrap; padding:6px 0 8px; align-items:center}
  .nav a { color:var(--accent); text-decoration:none; font-weight:600}
  .nav a:hover{text-decoration:underline}
  .nav .jump{display:flex; gap:6px; align-items:center; margin-left:auto}
  .nav .jump input{border:1px solid var(--border); border-radius:8px; padding:4px 8px; font:inherit; font-size:13px; background:#fff; color:var(--fg)}
  .nav .jump button{border:1px solid var(--accent); background:var(--accent); color:#fff; border-radius:8px; padding:4px 10px; font-weight:600; cursor:pointer; font-size:12px}
  .health-strip{display:flex; gap:6px; flex-wrap:wrap; padding:6px 0 8px; font-size:12px}
  .health-strip .pill{border:1px solid var(--border); border-radius:999px; padding:3px 10px; background:#fff; font-size:12px}
  .health-strip .pill.ok{background:var(--ok); border-color:#86efac}
  .health-strip .pill.broken{background:var(--err); border-color:#fca5a5}
  .card { background:#fff; border:1px solid var(--border); border-radius:12px; padding:14px; margin:10px 0; }
  .kicker { font-size:11px; letter-spacing:.08em; font-weight:700; color:var(--mut); text-transform:uppercase; margin:0.5rem 0 0.2rem; }
  .kicker:first-child{margin-top:0}
  .title{font-size:20px; font-weight:700; line-height:1.2; margin:4px 0 4px}
  .label { font-weight: 600; margin: 0.4rem 0 0.12rem; }
  .lead { font-weight: 600; font-size: 1.05rem; margin: 0.15rem 0; }
  .sub { margin: 0.12rem 0 0.12rem 0.9rem; }
  .pill { display: inline-block; border: 1px solid var(--border); border-radius: 999px;
          padding: 2px 8px; font-size: 11px; margin: 0.1rem 0.3rem 0.1rem 0; background:var(--pill); font-weight:600}
  .pill.locked, .pill.broken { border-color: #fca5a5; background: var(--err); }
  .pill.available, .pill.ready-to-start, .pill.verified { border-color: #86efac; background: var(--ok); }
  .pill.active, .pill.in-progress, .pill.advisory { border-color: #7dd3fc; background: var(--advisory); }
  .pill.passed { border-color: #c4b5fd; background: #ede9fe; }
  .pill.mastered { border-color: #facc15; background: #fef9c3; }
  .pill.stale { border-color: #fde68a; background: var(--warn); }
  .banner { padding: 7px 10px; border-radius: 8px; margin: 0.35rem 0; font-size:13px}
  .banner.advisory { background: var(--advisory); border:1px solid #bae6fd; }
  .banner.warn, .banner.warning, .banner.stale-note { background: var(--warn); border:1px solid #fde68a; }
  .banner.err, .banner.error, .banner.fail { background: var(--err); border:1px solid #fca5a5; }
  .banner.ok { background: var(--ok); border:1px solid #86efac; }
  .grid-two{display:grid; grid-template-columns:1.2fr .8fr; gap:14px; align-items:start;}
  .grid-two > *{min-width:0}
  @media(max-width:900px){.grid-two{grid-template-columns:1fr}}
  .grid-two .focus-sub{display:grid; grid-template-columns:1fr 1fr; gap:12px}
  @media(max-width:900px){.grid-two .focus-sub{grid-template-columns:1fr}}
  .analytics-grid{display:grid; grid-template-columns:1fr 1fr; gap:14px}
  @media(max-width:900px){.analytics-grid{grid-template-columns:1fr}}
  .analytics-card{margin:0}
  .analytics-card summary{font-size:1.05rem}
  .analytics-card svg{display:block; margin:8px 0}
  .analytics-controls{display:flex; gap:12px; flex-wrap:wrap; align-items:end}
  .analytics-controls .form-row{min-width:10rem}
  .rail{position:sticky; top:68px; align-self:start}
  .split{display:grid; grid-template-columns:360px 1fr; gap:14px}
  @media(max-width:900px){.split{grid-template-columns:1fr} .rail{position:static}}
  .breadcrumb{font-size:12px; color:var(--mut); margin:6px 0}
  .breadcrumb a{color:var(--accent)}
  details { margin: 0.4rem 0; }
  summary { cursor: pointer; font-weight: 600; }
  .filters label { margin-right: 0.9rem; }
  .form-row { margin: 0.38rem 0; }
  .form-row > label { display: block; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.12rem; }
  input[type="text"], input[type="number"], textarea, select {
    width: 100%; max-width: 34rem; padding: 0.35rem 0.5rem; font: inherit;
    border: 1px solid var(--border); border-radius: 6px; background: #fff; color: var(--fg);
  }
  textarea { min-height: 3.2rem; }
  .inline-check { font-weight: 400; font-size: 0.9rem; }
  .btn { display: inline-block; border: 1px solid #0c4a6e; background: #0c4a6e; color: #fff;
         border-radius: 8px; padding: 0.35rem 0.75rem; font-weight: 600; cursor: pointer;
         text-decoration: none; font-size: 0.9rem; }
  .btn.secondary { background: #fff; color: var(--fg); border-color: var(--border); }
  .btn.master, .modal.permanent { border-color: #7c3aed; }
  .btn.master { background: #7c3aed; color: #fff; }
  .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; margin: 0.4rem 0; }
  .modal { border: 2px solid #0c4a6e; border-radius: 12px; padding: 14px 16px; margin: 10px auto; background:#fff; max-width:860px; box-shadow:0 8px 32px rgba(0,0,0,.08)}
  a{color:var(--accent); text-decoration:none}
  a:hover{text-decoration:underline}
  .list{list-style:none; padding:0; margin:6px 0}
  .list li{border:1px solid var(--border); border-radius:12px; padding:10px; background:#fff; margin-bottom:6px}
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


_NAV = (
    '<header>'
    '<div class="wrap">'
    '<nav class="nav" aria-label="primary">'
    '<a href="/">Today</a>'
    '<a href="/next">Next</a>'
    '<a href="/health">Health</a>'
    '<a href="/analytics">Analytics</a>'
    '<form class="jump" method="get" action="/nodes/jump">'
    '<input type="text" name="node_id" placeholder="skill id — e.g. data.pandas.dataframe_basics_01" aria-label="jump to skill" size="32">'
    '<button type="submit">Go</button>'
    '</form>'
    '</nav>'
    '<div class="health-strip" aria-label="health" data-health-placeholder></div>'
    '</div>'
    '</header>\n'
)


def _error_body(message: str) -> str:
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        '<div class="health-strip" aria-label="health"></div>',
    )
    return (
        f'{header_html}<p class="banner error">{_esc(message)}</p>'
        '<p><a href="/">Back to Today</a></p>'
    )


def _status_page(status: int, message: str) -> tuple[str, int]:
    if status == 404:
        return _error_body(message), 404
    return _error_body(message), status


def _fresh_join(root) -> tuple[JoinedView | None, tuple[str, int] | None]:
    """One fresh lenient join per request.

    Returns ``(view, None)`` on success or ``(None, (body, status))`` when the
    strict graph/state half of the lenient seam re-raised.
    """
    try:
        return load_context_lenient(root), None
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        body = _error_body(
            f"The Skill graph or progress store failed to load: {exc}"
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
    """Captured handler output verbatim, escaped, as banners.

    ``[error]``/``[warning]`` prefixes keep their canonical banner classes;
    any other line (a refusal headline, a success note, an advisory) renders
    under ``default_class`` — nothing is rewritten, only escaped.
    """
    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[error] "):
            parts.append(
                f'<p class="banner error">{_esc(stripped[len("[error] "):])}</p>'
            )
        elif stripped.startswith("[warning] "):
            parts.append(
                f'<p class="banner warning">{_esc(stripped[len("[warning] "):])}</p>'
            )
        else:
            parts.append(f'<p class="banner {_esc(default_class)}">{_esc(stripped)}</p>')
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
        f"as empty ({_esc(names)}) — forms stay enabled and a domain refusal "
        'remains the truth. Run <code>skilltrace validate</code> / '
        "<code>skilltrace health</code> for the roll-up.</p>"
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
    lines = [*lines, "Operational failure — run `skilltrace validate` for the roll-up."]
    return _redirect_with_notice(next_url, lines, "error")


# --- Mechanical line -> HTML transform ----------------------------------------

_BANNER_PREFIXES = ("[warning] ", "[error] ", "[advisory] ")
_PILL_RE = re.compile(r"\[(.+)\]")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _is_kicker(text: str) -> bool:
    stripped = text.strip()
    return (
        bool(stripped)
        and stripped == stripped.upper()
        and any(ch.isalpha() for ch in stripped)
        and len(stripped) <= 80
    )


def lines_to_blocks(lines: list[str]) -> list[list[str]]:
    """Split canonical lines at ``---`` separators and standalone banners.

    Banners begin their own block so advisory callouts render as their own
    cards instead of gluing onto a neighbouring candidate card.
    """
    blocks: list[list[str]] = [[]]
    for raw in lines:
        stripped = raw.strip()
        if stripped == "---":
            blocks.append([])
            continue
        if any(stripped.startswith(prefix) for prefix in _BANNER_PREFIXES):
            blocks.append([raw])
            continue
        blocks[-1].append(raw)
    return [block for block in blocks if any(line.strip() for line in block)]


def _transform_block(block: list[str]) -> str:
    # Pre-strip blanks once so the label lookahead sees the real next line.
    substantive = [line for line in block if line.strip()]
    out: list[str] = []
    for index, raw in enumerate(substantive):
        stripped = raw.strip()

        banner = next(
            (p for p in _BANNER_PREFIXES if stripped.startswith(p)), None
        )
        if banner:
            kind = banner.strip("[] ")
            out.append(
                f'<p class="banner {_esc(kind)}">{_esc(stripped[len(banner):])}</p>'
            )
            continue

        if raw.startswith("  "):
            match = _PILL_RE.fullmatch(stripped)
            if match:
                label = match.group(1)
                out.append(
                    f'<span class="pill {_esc(_slug(label))}">{_esc(label)}</span>'
                )
            else:
                out.append(f'<div class="sub">{_esc(stripped)}</div>')
            continue

        if _is_kicker(stripped):
            out.append(f'<div class="kicker">{_esc(stripped)}</div>')
            continue

        css = ""
        if index:
            previous_is_sub = substantive[index - 1].startswith("  ")
            if not previous_is_sub and _is_kicker(substantive[index - 1].strip()):
                css = ' class="lead"'  # first prose under a kicker leads the card
        if (
            not css
            and index + 1 < len(substantive)
            and substantive[index + 1].startswith("  ")
            and len(stripped) <= 60
        ):
            css = ' class="label"'  # short callout heading above indented lines
        out.append(f"<p{css}>{_esc(stripped)}</p>")
    return "\n".join(out)


def cards_html(lines: list[str]) -> str:
    """The canonical lines as one card per block."""
    return "".join(
        f'<div class="card">\n{_transform_block(block)}\n</div>\n'
        for block in lines_to_blocks(lines)
    )


# --- Shared cards ---------------------------------------------------------------


def _pressure_card(model, view: JoinedView) -> str:
    """Pressure excerpts: overdue reviews, open blockers, availability counts.

    Advisory by construction — excerpts warn and link, they never gate.
    """
    counts = model.counts
    pills = [
        f'<span class="pill">{len(model.overdue)} overdue review'
        f'{"s" if len(model.overdue) != 1 else ""}</span>',
        f'<span class="pill">{len(model.open_blockers)} open blocker'
        f'{"s" if len(model.open_blockers) != 1 else ""}</span>',
        f'<span class="pill">{counts.get("available", 0)} available'
        f' &middot; {counts.get("locked", 0)} locked</span>',
    ]

    def _node_link(node_id: str) -> str:
        title = view.titles.get(node_id, node_id)
        return f'<a href="/nodes/{_esc(node_id)}">{_esc(title)}</a>'

    lists = ""
    if model.overdue:
        items = "".join(
            f"<li>{_node_link(r.node_id)} — due {_esc(str(r.scheduled_for)[:10])}</li>"
            for r in model.overdue
        )
        lists += f'<div class="kicker">OVERDUE REVIEWS</div><ul>{items}</ul>'
    if model.open_blockers:
        items = "".join(
            "<li>"
            f"{_node_link(b.node_id)} — {_esc(b.description)} "
            + _resolve_blocker_form(b.id)
            + "</li>"
            for b in model.open_blockers
        )
        lists += f'<div class="kicker">OPEN BLOCKERS</div><ul>{items}</ul>'

    return (
        '<div class="card">\n'
        '<div class="kicker">STUDY DAY PRESSURE — ADVISORY, NEVER BLOCKS</div>\n'
        f'<p>{"".join(pills)}</p>\n'
        f"{lists}\n</div>\n"
    )


def _health_strip_card(root, report=None) -> str:
    report = report or health_report(Path(root))
    pills = "".join(
        f'<span class="pill {"verified" if layer.ok else "broken"}">'
        f"{_esc(layer.target)}: {'OK' if layer.ok else 'FAILED'}</span>"
        for layer in report.layers
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"
    return (
        '<div class="card">\n'
        '<div class="kicker">HEALTH STRIP</div>\n'
        f"<p>{pills}"
        f'<a href="/health">Full roll-up &rarr;</a></p>\n'
        f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        "</div>\n"
    )


def _header_health_html(root, report=None) -> str:
    """Compact pills for the sticky header health strip (B viewport)."""
    report = report or health_report(Path(root))
    pills = "".join(
        f'<span class="pill {"ok" if layer.ok else "broken"}">'
        f"{_esc(layer.target)}: {'OK' if layer.ok else 'FAILED'}</span>"
        for layer in report.layers
    )
    # Keep the header strip compact — layers plus link, counts live in pressure card.
    return pills + '<a href="/health" style="margin-left:8px">Full roll-up &rarr;</a>'


def _queue_list_html(model, view: JoinedView) -> str:
    """Rec queue list below the grid — mirrors `derive_next` 60-min recommendations."""
    items = ""
    for rec in model.recommendations:
        node = view.node_map.get(rec.node_id)
        title = _esc(node.title if node else rec.node_id)
        state = view.store.state_of(rec.node_id)
        slug = _slug(state)
        items += (
            f'<li><a href="/nodes/{_esc(rec.node_id)}">{title}</a> '
            f'<span class="pill {slug}">{_esc(state)}</span>'
            f'<br><span class="small">{_esc(rec.reason[:140])}</span></li>'
        )
    if not items:
        items = '<li class="mut">No recommendations for 60 min — try <a href="/next">Next</a>.</li>'
    return (
        '<div class="card">\n'
        '<div class="kicker">OTHER GOOD CHOICES — 60-MINUTE QUEUE</div>\n'
        f'<ul class="list">{items}</ul>\n'
        '<p class="small">Live from <code>skilltrace next --minutes 60</code> — mirrors <code>derive_next</code>.</p>\n'
        '</div>\n'
    )


# --- Route bodies ---------------------------------------------------------------


def home_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/` — the today dashboard (B grid — 1.2fr focus + 0.8fr pressure).

    Returns ``(page_title, body_html, http_status)``.
    """
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]

    model = derive_today(view, Path(root), minutes=30)

    focus_bar = ""
    if model.focus_node_id and model.focus_node_id in view.node_map:
        focus = view.node_map[model.focus_node_id]
        focus_bar = (
            f'<p class="mut">Focus: '
            f'<a href="/nodes/{_esc(focus.id)}">{_esc(focus.title)}</a></p>'
        )

    # Sticky header health+nav — live pills, jump form, 1100px wrap.
    health = health_report(Path(root))
    header_health = _header_health_html(root, health)
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        f'<div class="health-strip" aria-label="health">{header_health}</div>',
    )

    # Grid-two: left 1.2fr focus + right 0.8fr rail pressure.
    left_html = (
        cards_html(model.lines)
        + _start_confirm_card(view, root, model.focus_node_id)
        + _session_strip_card(view, root)
    )
    right_html = (
        '<div class="rail">\n'
        + _pressure_card(model, view)
        + _health_strip_card(root, health)
        + '\n</div>\n'
    )
    grid_html = (
        '<div class="grid-two">\n'
        '<div>\n' + left_html + '\n</div>\n'
        + right_html
        + '\n</div>\n'
    )

    # Rec queue below grid — mirrors CLI `next --minutes 60`.
    queue_model = derive_next(view, Path(root), minutes=60, limit=5)
    queue_html = _queue_list_html(queue_model, view)

    breadcrumb = '<div class="breadcrumb"><a href="/">Today</a></div>\n'

    body = (
        header_html
        + _flash_html(query or {})
        + _degraded_banner(view)
        + focus_bar
        + breadcrumb
        + grid_html
        + queue_html
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


def _start_confirm_card(view: JoinedView, root, focus_node_id: str | None) -> str:
    if not focus_node_id or focus_node_id not in view.node_map:
        return ""
    title = _esc(view.titles.get(focus_node_id, focus_node_id))
    return (
        '<div class="card">\n'
        '<div class="kicker">START HERE — TODAY\'S TOP PICK (LIGHTWEIGHT CONFIRM)</div>\n'
        f"<p><a href=\"/nodes/{_esc(focus_node_id)}\">{title}</a></p>\n"
        f"{_start_confirm_form(view, root, focus_node_id)}\n</div>\n"
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


def _session_strip_card(view: JoinedView, root) -> str:
    """The home session strip (G5): work log + honest-end close for the open day."""
    current = open_session(view.sessions)
    close_form = (
        "<details><summary>Forgot to close?</summary>"
        '<form method="post" action="/session/close">'
        '<input type="hidden" name="next" value="/">'
        '<div class="form-row"><label>Honest end (ISO timestamp, optional — '
        'e.g. 2026-08-24T13:45+00:00)</label>'
        '<input type="text" name="end"></div>'
        '<button type="submit" class="btn secondary">Close session</button>'
        "</form><p class=\"mut\">Without it the session closes now.</p></details>"
    )
    if current is not None:
        template = (
            f' <span class="pill">{_esc(current.template)}</span>'
            if current.template
            else ""
        )
        header = (
            f"<p>Open session <code>{_esc(current.id)}</code> — started "
            f"<code>{_esc(str(current.started_at)[:19])}</code>{template}</p>"
        )
    else:
        header = (
            '<p class="mut">No session is open — start one below; closing '
            "without one is refused by the domain.</p>"
        )
    work_form = (
        "<details><summary>Log work</summary>"
        '<form method="post" action="/work">'
        '<input type="hidden" name="next" value="/">'
        '<div class="form-row"><label>Node id</label>'
        '<input type="text" name="node_id" required placeholder="e.g. math.algebra.variables_expressions_01"></div>'
        f"{_work_form_fields()}"
        '<button type="submit" class="btn secondary">Add work item</button>'
        "</form><p class=\"mut\">Verbatim CLI fields — "
        "<code>work &lt;node_id&gt; [--blocked] [--notes] [--minutes]</code>.</p></details>"
    )
    return (
        '<div class="card">\n'
        '<div class="kicker">SESSION STRIP</div>\n'
        f"{header}\n{work_form}\n{close_form}\n</div>\n"
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
        body, status = _status_page(400, "minutes and limit must be integers.")
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
    filters = (
        '<div class="card">\n'
        '<form class="filters" method="get" action="/next">'
        f'<label>minutes <input type="number" name="minutes" value="{minutes}" min="1" size="4"></label>'
        f'<label>limit <input type="number" name="limit" value="{limit}" min="1" size="3"></label>'
        f'<label><input type="checkbox" name="locked" value="1"{checked}> show locked</label>'
        '<button type="submit">Apply</button>'
        "</form>\n"
        f'<p class="mut"><a href="/next?{toggle_params}">{toggle_label}</a> '
        '(mirrors <code>next --minutes --limit --show-locked</code>)</p>\n'
        "</div>\n"
    )

    header_health = _header_health_html(root, health_report(Path(root)))
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        f'<div class="health-strip" aria-label="health">{header_health}</div>',
    )
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

    Candidate blocks are recognized by their canonical OPTION kickers; the k-th
    such block receives model.recommendations[k]'s reasoning. Other blocks
    (warnings, remediation advisories, the locked appendix) pass through.
    """
    rec_iter = iter(model.recommendations)
    html_out = []
    for block in lines_to_blocks(model.lines):
        first = next((line for line in block if line.strip()), "")
        inner = _transform_block(block)
        if first.strip().startswith("OPTION "):
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
        body, status = _status_page(404, f"Unknown node {node_id}.")
        return "Not found", body, status

    actions = _node_actions_card(root, view, node_id)
    drill = _drill_down_card(node_id, view, Path(root), model)
    title = view.node_map[node_id].title
    header_health = _header_health_html(root, health_report(Path(root)))
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        f'<div class="health-strip" aria-label="health">{header_health}</div>',
    )
    breadcrumb = (
        f'<div class="breadcrumb"><a href="/">Today</a> &middot; '
        f'<a href="/nodes/{_esc(node_id)}">{_esc(node_id)}</a></div>\n'
    )
    body = (
        header_html
        + _flash_html(query or {})
        + _degraded_banner(view)
        + breadcrumb
        + cards_html(model.lines)
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

    Spec select auto-resolves when the node has exactly one spec; accept/
    reject radios render only on manual-gate nodes (an objective gate's exit
    code is the verdict); the supersede flow hides behind an advanced toggle.
    """
    specs = view.specs_by_node.get(node_id, [])
    gate = view.gates_by_node.get(node_id)

    if not specs:
        spec_field = '<p class="mut">No artifact spec — the domain refuses any submission.</p>'
    elif len(specs) == 1:
        spec_field = f'<input type="hidden" name="spec" value="{_esc(specs[0].id)}">'
    else:
        options = "".join(
            f'<option value="{_esc(s.id)}">{_esc(s.id)}</option>' for s in specs
        )
        spec_field = (
            '<div class="form-row"><label>Artifact spec</label>'
            f'<select name="spec">{options}</select></div>'
        )

    if gate is None:
        verdict_field = '<p class="mut">No gate — the domain refuses any submission.</p>'
    elif gate.command:
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
    """Node-detail write surface (G5): pass/master modals + daily-write forms."""
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
        f'<ul>{blocker_forms}</ul>' if blocker_forms else '<p class="mut">No open blockers.</p>'
    )
    return (
        '<div class="card">\n'
        '<div class="kicker">WRITE ACTIONS — SAME REGISTRY, SAME EVENTS AS THE CLI</div>\n'
        '<div class="actions">'
        f'<a class="btn" href="/nodes/{_esc(node_id)}/pass">Pass&hellip;</a>'
        f'<a class="btn master" href="/nodes/{_esc(node_id)}/master">Master&hellip;</a>'
        "</div>\n"
        "<details open><summary>Start studying</summary>"
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
            f'<a href="/nodes/{_esc(title)}">{_esc(title)}</a>',
            _esc(pstate),
            "no — must pass first" if unsatisfied else "yes",
        ]
        for (title, pstate, unsatisfied) in drilldown.prereq_rows
    ]
    unlock_rows = [
        [f'<a href="/nodes/{_esc(uid)}">{_esc(uid)}</a>']
        for uid in drilldown.unlock_rows
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
    """GET `/health` — the five validators plus liveness, read-only."""
    report = health_report(Path(root))

    rows = [
        [
            _esc(layer.target),
            _esc(layer.counts),
            f'<span class="pill {"verified" if layer.ok else "broken"}">'
            f"{'OK' if layer.ok else 'FAILED'}</span>",
        ]
        for layer in report.layers
    ]
    error_banners = "".join(
        f'<p class="banner error">{_esc(line[len("[error] "):])}</p>'
        for layer in report.layers
        for line in layer.error_lines
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"

    header_health = _header_health_html(root)
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        f'<div class="health-strip" aria-label="health">{header_health}</div>',
    )
    breadcrumb = '<div class="breadcrumb"><a href="/">Today</a> &middot; <a href="/health">Health</a></div>\n'
    body = (
        header_html
        + breadcrumb
        + '<div class="card">\n'
        + '<div class="kicker">HEALTH ROLL-UP — FIVE VALIDATORS + LIVENESS</div>\n'
        + _table(["Layer", "Counts", "Status"], rows)
        + error_banners
        + _transform_block(report.liveness_lines)
        + f'<p class="banner {verdict_class}">{_esc(report.verdict())}</p>\n'
        + '<p class="mut">Read fresh from the truth files at request time — '
        "CLI edits appear on refresh.</p>\n</div>\n"
    )
    return "Health", body, 200


# --- Analytics dashboard (G5) ---------------------------------------------------


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
        body, status = _status_page(400, "Analytics days must be a positive integer.")
        return None, ("Bad request", body, status)
    if days <= 0:
        body, status = _status_page(400, "Analytics days must be a positive integer.")
        return None, ("Bad request", body, status)
    group_by = (query.get("group-by") or [policy.default_group_by])[0]
    if group_by not in {"prefix", "track"}:
        body, status = _status_page(400, "Analytics group-by must be prefix or track.")
        return None, ("Bad request", body, status)
    min_sessions = policy.min_sessions_for_full_data
    return (
        derive_analytics(
            view,
            today=utc_today(),
            window_days=days,
            group_by=group_by,
            state_filter=[],
            min_sessions_for_full_data=min_sessions,
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
    """GET `/analytics` — four read-only analytics themes."""
    query = query or {}
    model, failure = _analytics_view(Path(root), query)
    if model is None:
        return failure

    warnings = analytics_warnings(Path(root), model)
    overdue = (
        f'<p class="banner warning">Overdue reviews: {model.reviews.overdue_count} '
        "scheduled review(s) need attention.</p>"
        if model.reviews.overdue_count
        else ""
    )
    days = model.window_days
    group_by = model.group_by
    options = "".join(
        f'<option value="{n}" {"selected" if n == days else ""}>{label}</option>'
        for n, label in ((7, "Last 7 days"), (30, "Last 30 days"), (90, "Last 90 days"))
    )
    controls = (
        '<div class="card analytics-controls"><form id="analytics-filter" method="get" action="/analytics">'
        '<div class="form-row"><label for="analytics-days">'
        "Date range</label>"
        f'<select id="analytics-days" name="days">{options}'
        f'<option value="{days}" {"selected" if days not in (7, 30, 90) else ""}>Policy default ({days}d)</option>'
        f'</select><input type="hidden" name="group-by" value="{_esc(group_by)}">'
        '<button class="btn secondary" type="submit">Apply</button></div></form>'
        '<div class="form-row"><label>Group by</label>'
        f'<a class="btn {"secondary" if group_by == "track" else ""}" href="/analytics?days={days}&amp;group-by=prefix">Prefix</a> '
        f'<a class="btn {"secondary" if group_by == "prefix" else ""}" href="/analytics?days={days}&amp;group-by=track">Track</a></div>'
        '</div>'
    )
    advisory = "".join(f'<p class="banner advisory">{_esc(warning)}</p>' for warning in warnings)

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
    cards = (
        _analytics_card("Velocity", f"{velocity.sessions_in_window} sessions, "
                        f"{velocity.total_minutes} minutes",
                        "Sessions and work items started in the selected window, bucketed by week.",
                        sparkline_svg(
                            [(week.label, week.session_count) for week in velocity.weeks]
                        ), velocity_detail, model, "velocity")
        + _analytics_card("Blockers", f"{blockers.open_count} open, "
                        f"{blockers.resolved_in_window} resolved",
                        "Open blockers are counted now; resolved blockers are counted when resolved in the window.",
                        sparkline_svg(
                            [("open", blockers.open_count)]
                        ), blocker_detail, model, "blockers")
        + _analytics_card("Reviews", f"{reviews.completed_in_window} completed, "
                        f"{reviews.overdue_count} overdue",
                        "Completion rate is completed reviews divided by completed plus scheduled reviews.",
                        sparkline_svg(
                            [("completed", reviews.completed_in_window)]
                        ), review_detail, model, "reviews")
        + _analytics_card("Evidence", f"{evidence.nodes_with_gaps} nodes with gaps, "
                        f"{evidence.coverage_rate * 100:.0f}% coverage",
                        "Coverage is the share of nodes with artifact specs that have no required-spec gap.",
                        sparkline_svg(
                            [("accepted", sum(row.accepted_count for row in evidence.rows))]
                        ), evidence_detail, model, "evidence")
    )
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        '<div class="health-strip" aria-label="health"></div>',
    )
    body = (
        header_html + _flash_html(query) + overdue + controls
        + f'<div id="analytics-advisory">{advisory}</div>'
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
    header_html = _NAV.replace(
        '<div class="health-strip" aria-label="health" data-health-placeholder></div>',
        '<div class="health-strip" aria-label="health"></div>',
    )
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
        body, status = _status_page(404, f"Unknown node {node_id}.")
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
    return _modal_shell(view, node_id, "Confirm pass", inner, extra_html)


def master_body(root, node_id: str, extra_html: str = "") -> tuple[str, str, int]:
    """GET `/nodes/{id}/master` — step 1 of 2: mastery facts."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.")
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
    return _modal_shell(view, node_id, "Step 1 — Mastery facts", inner, extra_html)


def master_confirm_body(root, node_id: str, extra_html: str = "") -> tuple[str, str, int]:
    """GET/POST `/nodes/{id}/master/confirm` — step 2 of 2: permanence."""
    view, failure = _fresh_join(root)
    if view is None:
        return "Error", failure[0], failure[1]
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.")
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
    return _modal_shell(view, node_id, "Step 2 — This is permanent", inner, extra_html)


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
