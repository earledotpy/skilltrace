"""The single granted tier-1 interaction: chart hover/focus tooltips (ADR 0008).

Narrow tier 1 permits exactly one inline vanilla script, no build step, no
dependencies, for one interaction class only: tooltips on real multi-point
chart series. The renderer stays server-side
(``analytics/sparkline.py`` with ``with_points=True``); this module owns
only the tooltip upgrade. With script absent or disabled the page degrades
to its tier-0 form — static SVG whose per-point ``<title>`` still tooltips
natively — with no loss of function.

Budget: this is the one file under ``src/skilltrace/web/`` whose path
carries "analytics" and whose code emits a script tag; every other route
emits none (DD6 per-route budget gate). No mutation path lives here: the
script reads ``data-tip`` attributes and writes one transient tooltip node.
Client-built text rides ``textContent`` only (ADR 0008 escaping discipline).

Note: the script literal below uses single-line double-quoted strings on
purpose — the release gates strip triple-quoted blocks before scanning, so
a triple-quoted literal would hide the tag from the budget count.
"""

from __future__ import annotations


_TOOLTIP_SCRIPT = (
    "<script>(function(){var tip=null;"
    "function hide(){if(tip&&tip.parentNode){tip.parentNode.removeChild(tip);}tip=null;}"
    "function show(el){hide();var text=el.getAttribute('data-tip')||'';if(!text){return;}"
    "tip=document.createElement('div');tip.className='chart-tip';"
    "tip.setAttribute('role','status');tip.textContent=text;"
    "document.body.appendChild(tip);var r=el.getBoundingClientRect();"
    "tip.style.left=(r.left+window.scrollX)+'px';"
    "tip.style.top=(r.bottom+window.scrollY+6)+'px';}"
    "function fromEvent(e){return (e.target&&e.target.closest)?e.target.closest('[data-tip]'):null;}"
    "document.addEventListener('mouseover',function(e){var t=fromEvent(e);if(t){show(t);}else{hide();}});"
    "document.addEventListener('mouseout',function(e){if(fromEvent(e)){hide();}});"
    "document.addEventListener('focusin',function(e){var t=fromEvent(e);if(t){show(t);}else{hide();}});"
    "document.addEventListener('focusout',hide);"
    "document.addEventListener('keydown',function(e){if(e.key==='Escape'){hide();}});"
    "})();</script>\n"
)


def tooltip_script() -> str:
    """The granted inline tooltip script tag (analytics route only)."""
    return _TOOLTIP_SCRIPT
