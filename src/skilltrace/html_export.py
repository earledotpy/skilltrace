"""`skilltrace export html` — the derived, disposable, self-contained snapshot.

Third MUTATING sibling of `export markdown` / `export sqlite` (the #33
reasoning extended by G4#68): a single-page five-layer review roll-up rendered
as a self-contained `data/export.html` (one inline `<style>` block, zero JS, no
external assets). It reuses the *same* read derivations the terminal reports
print and the *same* mechanical line->HTML transform the serve pages use
(`web.views.cards_html` / `page`) — no second vocabulary (ADR 0006 / G3#67
escalation path).

Whole-file rewrite from YAML/Markdown truth on demand. A generated-at stamp and
a "snapshot, not live — run `skilltrace ui`" banner mark it as a frozen view. It
refuses to write when the strict JoinedView seam reports any load error (the
siblings' refuse-on-error from #38): a partial snapshot would misrepresent the
repository. `data/` is gitignored and excluded from `backup`, so the artifact is
disposable by construction and never read back by the engine.
"""

from __future__ import annotations

import html
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from .commands._common import now_iso
from .commands.health import health_report
from .commands.report import (
    report_blockers,
    report_evidence,
    report_progress,
    report_reviews,
)
from .commands.resource_report import resource_report
from .context import load_context_strict

HTML_EXPORT_RELPATH = Path("data") / "export.html"

# The five-layer review roll-up, in reading order, each reusing an existing
# report derivation verbatim (captured stdout -> mechanical transform).
_SECTIONS = (
    ("Progress / overview", report_progress),
    ("Blockers", report_blockers),
    ("Reviews due / overdue", report_reviews),
    ("Evidence coverage + gates", report_evidence),
    ("Resource verification", resource_report),
)


def _capture(func, ctx) -> list[str]:
    """Run a read report handler, returning its printed lines (no side effects)."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        func(ctx)
    return buffer.getvalue().splitlines()


def _banner_card(generated_at: str) -> str:
    return (
        '<div class="card">\n'
        '<div class="kicker">SNAPSHOT — NOT LIVE</div>\n'
        f"<p>Generated at {html.escape(generated_at)} (UTC). This is a frozen view "
        "of your curriculum and progress — run <code>skilltrace ui</code> for the "
        "live dashboard.</p>\n</div>\n"
    )


def _health_strip_card(root: Path) -> str:
    """The five validators plus liveness, mirroring the serve health strip."""
    from .web.views import cards_html

    report = health_report(Path(root))
    pills = "".join(
        f'<span class="pill {"verified" if layer.ok else "broken"}">'
        f"{html.escape(layer.target)}: {'OK' if layer.ok else 'FAILED'}</span>"
        for layer in report.layers
    )
    verdict_class = "ok" if report.error_count == 0 else "fail"
    body = (
        '<div class="kicker">HEALTH STRIP</div>\n'
        f"<p>{pills}</p>\n"
        + cards_html(report.liveness_lines)
        + f'<p class="banner {verdict_class}">{html.escape(report.verdict())}</p>\n'
    )
    return f'<div class="card">\n{body}</div>\n'


def render_html(ctx) -> str:
    """Build the full self-contained HTML page from the captured report lines."""
    from .web.views import cards_html, page

    snapshot = load_context_strict(ctx.root)
    if not snapshot.ok:
        raise RuntimeError("HTML export requires a complete JoinedView snapshot.")
    report_ctx = type(ctx)(
        root=ctx.root,
        args=ctx.args,
        source=ctx.source,
        joined=snapshot,
    )
    sections_html = ""
    for title, handler in _SECTIONS:
        lines = _capture(handler, report_ctx)
        inner = cards_html(lines) if lines else '<p class="mut">No data.</p>'
        sections_html += (
            f"<section>\n<h2>{html.escape(title)}</h2>\n{inner}\n</section>\n"
        )

    body = _banner_card(now_iso()) + sections_html + _health_strip_card(ctx.root)
    return page("SkillTrace export", body)
