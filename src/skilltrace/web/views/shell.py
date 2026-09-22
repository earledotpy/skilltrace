"""
The page shell (ADR 0009): the locked §B stylesheet, chrome and
nav, error/status bodies, the one shared route preamble
(:func:`_page_head`: fresh lenient join, its failure branch, chrome
header, the one flash rendering), and the confirmation-panel shell.

"""

from __future__ import annotations

from pathlib import Path

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
)


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

    /* §B dense diagnostics register (rich home, /health detail, /analytics
       tables, node drill-down): 20px card pad / 28px section gap /
       14px intra-card gap / 20px bento gutters; 28 > 14 preserves
       section-gap > intra-card-gap (amended P5.2, G-Spec #250). */
    --card-pad-dense:20px;
    --section-gap-dense:28px;
    --intra-gap-dense:14px;
    --bento-gutter-dense:20px;

    /* §B radius 14 / 11 / 999 px */
    --radius:14px;
    --radius-sm:11px;
    --radius-pill:999px;

    /* §B shell: 1040px with a 720px daily-loop column and one 960px breakpoint;
       the rich home uses a 1120px bento shell (amended §B, G-Spec #250) */
    --shell:1040px;
    --loop:720px;
    --shell-rich:1120px;
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
  header h1.brand{font-size:19px; font-weight:700; margin:18px 0 0; line-height:1.2; font-family:var(--font-sans)}
  .nav{font-size:15px; display:flex; gap:22px; flex-wrap:wrap; padding:6px 0 8px; align-items:center; font-family:var(--font-sans)}
  .nav.periodic{border-top:1px solid var(--border); padding-top:8px}
  .nav a{color:var(--muted); text-decoration:none; font-weight:400; font-size:15px; padding:6px 2px; border-bottom:2px solid transparent}
  .nav a:hover{text-decoration:underline}
  .nav a[aria-current="page"]{color:var(--fg); font-weight:700; border-bottom-color:var(--accent); padding-bottom:2px}
  /* P-A11yShell (map 258): one keyboard-only focus ring on the accent token
     plus the skip link's offscreen parking — :focus-visible leaves
     mouse/touch appearance untouched; the skip reveal rides plain :focus
     so this stays the single :focus-visible rule in the shell. */
  :focus-visible{outline:2px solid var(--accent); outline-offset:2px}
  .skip{position:absolute; left:-9999px; top:0; background:var(--card); color:var(--fg); padding:8px 16px; z-index:20; font-family:var(--font-sans); font-size:var(--step-14); font-weight:600; border:1px solid var(--accent); border-radius:var(--radius-sm)}
  .skip:focus{left:8px; top:8px}
  .nav .jump{display:flex; gap:6px; align-items:center; margin-left:auto}
  .nav .jump input{border:1px solid var(--border); border-radius:var(--radius-sm); padding:4px 8px; font:inherit; font-size:var(--step-135); background:var(--card); color:var(--fg)}
  .nav .jump button{border:1px solid var(--accent); background:var(--accent); color:var(--accent-ink); border-radius:var(--radius-sm); padding:4px 10px; font-weight:600; cursor:pointer; font-size:var(--step-135)}
  .health-strip{display:flex; gap:16px; flex-wrap:wrap; padding:8px 0 12px; font-size:var(--step-14); align-items:center; font-family:var(--font-sans)}
  .health-strip .calm::before{content:"✓"; color:var(--accent); margin-right:7px; font-weight:700}
  .health-strip .health-rollup{color:var(--accent); text-decoration:none; font-size:var(--step-14)}
  .health-strip .health-rollup:hover{text-decoration:underline}
  .health-strip .pill{border:1px solid var(--border); border-radius:var(--radius-pill); padding:3px 10px; background:var(--card); font-size:var(--step-135)}
  .health-strip .pill.ok{background:var(--ok); border-color:var(--ok-ink)}
  .health-strip .pill.attention{background:var(--warn); border-color:var(--warn-ink)}
  .health-strip .pill.broken{background:var(--err); border-color:var(--err-ink)}
  .card{background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:var(--card-pad); margin:var(--space-intra) 0; gap:var(--space-intra)}
  /* Discovery result cards (§C-bis): greyed locked cards + small secondary ID */
  .result.locked{opacity:.55; border-style:dashed}
  .result .ref{font-size:var(--step-135); margin:.2rem 0 0}
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
  /* Tier-1 narrow tooltip (ADR 0008): the one granted script's floating
     label. Tokens only (no hex outside :root); absent script means this
     rule never matches and the static SVG stands alone. */
  .chart-tip{position:absolute; z-index:30; background:var(--fg); color:var(--bg); padding:4px 8px; border-radius:var(--radius-sm); font-size:var(--step-135); pointer-events:none; max-width:16rem}
  /* §A unified single-page home (S3, map 252): the hero + six-card bento at
     the dense register. The rich shell is 1120px (amended §B); bento gutters
     20px; section gap 28px > intra-card gap 14px; the hero is double-weight
     (full grid span, 30px display, 28px padding, accent left border) and
     carries the page's only CTA — every bento card is links-only. */
  main.wrap:has(.home-rich){max-width:var(--shell-rich)}
  .bento{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:var(--section-gap-dense) var(--bento-gutter-dense)}
  .hero{grid-column:1/-1; background:var(--card); border:1px solid var(--border); border-left:5px solid var(--accent); border-radius:var(--radius); padding:var(--card-pad); margin:0}
  .hero .display{font-size:30px}
  .hero .actions{margin-top:var(--intra-gap-dense)}
  /* H5-shape (map 258): the hero CTA renders at the contract 1.25x scale
     (18px, 15x30px) — hero-scoped so the bento stays links-only and every
     other .btn keeps the locked §B register. Radius stays --radius. */
  .hero .btn.primary{font-size:18px; padding:15px 30px}
  .bento-card{background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:var(--card-pad-dense); margin:0}
  .bento-card .kicker{margin:0 0 var(--intra-gap-dense)}
  /* B8 (map 258): every bento card carries kicker + h2 — the contract's
     19px heading under the 13.5px muted kicker. Scoped to the bento so the
     global h2 (step-24, section margins) is untouched elsewhere. */
  .bento-card h2{font-size:19px; margin:0 0 4px}
  .bento-card a{color:var(--accent); text-decoration:none; font-weight:600}
  .bento-card a:hover{text-decoration:underline}
  .bento-card .actions{margin-top:var(--intra-gap-dense)}
  .queue-row,.spine-row{display:flex; justify-content:space-between; align-items:baseline; gap:var(--intra-gap-dense); padding:4px 0; border-bottom:1px solid var(--border); font-family:var(--font-sans); font-size:var(--step-14)}
  .weekstrip{display:grid; grid-template-columns:repeat(7,1fr); gap:var(--intra-gap-dense); font-family:var(--font-sans); font-size:var(--step-135)}
  .weekstrip .day{border:1px solid var(--border); border-radius:var(--radius-sm); padding:6px 2px; text-align:center}
  .weekstrip .day b{display:block; font-size:var(--step-135)}
  .weekstrip .day.today{border-color:var(--accent); background:var(--accent-soft)}
  .browsetable th,.browsetable td{padding:4px .5rem}
  /* P-DenseTrust (map 258): tabular counts ledger — one font-feature switch
     on the locked system stacks; no webfont, no token change. */
  .count strong,.health-strip .pill,th,td,.weekstrip,.queue-row,.spine-row{font-variant-numeric:tabular-nums}
  /* P-DenseTrust (map 258): sticky headers on dense-register tables only
     (health / analytics / node drill-down via table.dense); airy daily
     surfaces (hero, topline, bento browse) carry no dense table. */
  table.dense thead th{position:sticky; top:0; background:var(--card); z-index:1}
  /* P-DenseTrust (map 258): honor reduced motion on the one animation — the
     earned settle banner degrades to an instant state change. */
  @media(prefers-reduced-motion:reduce){.banner.ok,.banner.success{animation:none}}
  /* the single locked breakpoint (desktop-only; P5.4: the 900px rules collapse to one) */
  @media(max-width:960px){.analytics-grid{grid-template-columns:1fr}}
"""


def page(title: str, body: str) -> str:
    """Wrap a body in the single shared layout (one inline style block).

    The shared shell carries the one-line live-trust footer (P-DenseTrust,
    map 258): live pages read fresh from the truth files on every load —
    the disposable export snapshot carries its own "snapshot, not live"
    counterpart instead. Wording is P3.1-clean (no command names, flags,
    ids, or paths) and reuses the locked muted register — no new tokens.
    """
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
        '<a class="skip" href="#content">Skip to content</a>\n'
        f"{header}"
        f'<main class="wrap" id="content">\n<h1>{_esc(title)}</h1>\n{main}\n</main>\n'
        '<footer class="wrap small mut">Local only \u00b7 served from your files \u00b7 fresh on every load.</footer>\n</body>\n</html>\n'
    )


def _nav_html(current_view: str = "", health=None) -> str:
    """The shared chrome header (v2.4 S2+T4): two nav groups + health pill.

    ``current_view`` is the *view identity* (ADR 0007) — ``aria-current``
    derives from the declared interface ``VIEWS`` table (the seam), never
    from URL string-matching in the page bodies. Health is not a nav stop
    (T4 §H): the chrome carries a header pill strip plus a muted
    ``Health`` pointer to the one study-guidance roll-up page (renamed from
    "Full roll-up" by §C-ter — the "Full" name implied repository validity).
    The health strip renders an ambient headline plus one attention pill from
    the structured ``HealthReport`` (warning counts ride the P2.4 seam).
    """
    from ..interface import VIEWS

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
            pills = '<span class="mut calm">Everything looks good.</span>'
        pills += ' <a class="health-rollup" href="/health">Health →</a>'
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
        '<input type="text" name="node_id" placeholder="Jump to a skill" aria-label="jump to skill" title="Type a skill name or id to jump straight to its page" size="32">'
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


def _page_head(
    root,
    query: dict | None = None,
    *,
    dismiss_path: str = "/",
    current_view: str = "",
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
    head = _chrome(root, current_view=current_view) + _flash_html(query, dismiss_path)
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
    """The safety panel card — title plus card HTML, no chrome or flash."""
    node = view.node_map[node_id]
    state = view.store.state_of(node_id)
    safety_class = (
        "safety-warn"
        if heading.startswith("Step 1")
        else "safety-err" if heading.startswith("Step 2") else "safety-accent"
    )
    modal = (
        '<div class="card safety '
        f'{safety_class}">'
        f'<div class="kicker">{_esc(heading)}</div>'
        f'<p class="lead">{_esc(node.title)}</p>'
        f'<p><span class="pill {_esc(_slug(state))}">{_esc(_normalize_pill_label(state))}</span></p>'
        f"{inner}"
        "</div>"
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
    """The page-level safety panel enclosing a pass/master body (T5 §B+§F).

    Safety color rides the card's border via the locked tokens: pass
    ``--accent``, master step 1 ``--warn``, step 2 ``--err`` — the old
    unstyled ``.modal`` divergence is gone; panels render as cards with
    panel padding at the locked card band. No overlay: no dialog, no
    popover, no backdrop. Server-fresh per request; writes are 303+flash-only.

    Step bodies build their page through the shared preamble helper, so they
    pass the already-built ``head`` (chrome plus the one flash rendering);
    the legacy call shape without ``head`` rebuilds it for direct callers.
    """
    title, modal = _modal_card(view, node_id, heading, inner)
    if head is None:
        head = _chrome(root) + _flash_html(
            query or {}, _modal_dismiss(node_id, heading)
        )
    body = head + _degraded_banner(view) + modal
    return title, body, 200

