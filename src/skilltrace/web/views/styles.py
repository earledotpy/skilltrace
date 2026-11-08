"""The served stylesheet — one inline ``<style>`` block (ADR 0006, ADR 0009).

The block is assembled from two parts:

* the **token blocks** (:func:`skilltrace.web.tokens.root_blocks`) — every
  colour, spacing step, type step, radius, motion duration and elevation,
  declared by semantic role and nowhere else;
* the **component rules** below — the normative component vocabulary of
  ``docs/spec-v3-study-day.md`` §8 VS-5: surface/section containers,
  command bars, queue items, fact and requirement rows, status labels, the
  contextual inspector, progressive disclosure, table/chart pairings,
  banners, and the purpose-built empty / limited / refusal / failure /
  recovery states.

**Cards are not the default layout primitive.** Structure comes from
sections, rows, tables and disclosures; a card is a fact container the
engine-derived Card seam renders, not the page frame.

No hex literal appears in the rules below — a colour is only ever reached
through a token, so the dark-first palette and its light companion cannot
drift apart. No rule invents a colour, meaning, term or success styling for
a mode: the two presentation registers (VS-6) are density and whitespace,
not colour.
"""

from __future__ import annotations

from ..tokens import root_blocks

__all__ = ["STYLE"]


_COMPONENT_RULES = """
  /* --- reset & base -------------------------------------------------- */
  *{box-sizing:border-box}
  html,body{width:100%; overflow-x:clip}
  body{
    margin:0;
    background:var(--canvas-base);
    color:var(--text-primary);
    font:var(--text-base)/var(--line-height) var(--font-sans);
  }
  p{max-width:var(--measure)}
  ul{padding-left:1.2rem}
  h1,h2,h3,h4{
    font-family:var(--font-sans);
    line-height:1.25;
    color:var(--text-primary);
    margin:0 0 var(--space-2);
  }
  h1{font-size:var(--text-xl)}
  h2{font-size:var(--text-lg)}
  h3{font-size:var(--text-md)}
  h4{font-size:var(--text-base)}
  a{color:var(--accent)}
  a:hover{text-decoration-thickness:2px}
  code,kbd,.mono{
    font-family:var(--font-mono);
    font-size:var(--text-sm);
  }
  table{border-collapse:collapse; width:100%}
  th,td{
    text-align:left;
    padding:var(--space-2) var(--space-3);
    border-bottom:1px solid var(--border-subtle);
    font-size:var(--text-base);
  }
  th{color:var(--text-secondary); font-weight:600}
  caption{
    text-align:left;
    color:var(--text-secondary);
    font-size:var(--text-sm);
    padding:var(--space-2) 0;
  }
  hr{border:0; border-top:1px solid var(--border-subtle); margin:var(--space-5) 0}

  /* --- focus & skip link (AX-1, AX-2) --------------------------------- */
  :focus-visible{outline:2px solid var(--status-focus); outline-offset:2px}
  .skip{
    position:absolute; left:-9999px; top:0;
    background:var(--canvas-raised); color:var(--text-primary);
    padding:var(--space-2) var(--space-4);
    z-index:20; font-weight:600;
    border:1px solid var(--accent); border-radius:var(--radius-sm);
  }
  .skip:focus{left:var(--space-2); top:var(--space-2)}

  /* --- shell & navigation --------------------------------------------- */
  .shell{max-width:var(--shell); margin:0 auto; padding:0 var(--space-5)}
  main.shell{padding:var(--space-6) var(--space-5) var(--space-7)}
  .shell-narrow{max-width:var(--shell-narrow)}
  header{
    position:sticky; top:0; z-index:10;
    background:var(--canvas-raised);
    border-bottom:1px solid var(--border-default);
  }
  .brand{
    font-size:var(--text-lg); font-weight:700; margin:var(--space-3) 0 0;
    letter-spacing:-0.01em;
  }
  .brand a{color:var(--text-primary); text-decoration:none}
  .nav{
    display:flex; gap:var(--space-4); flex-wrap:wrap;
    padding:var(--space-2) 0 var(--space-3);
    align-items:center; font-size:var(--text-base);
  }
  .nav.operations{
    border-top:1px solid var(--border-subtle);
    padding-top:var(--space-2);
  }
  .nav a{
    color:var(--text-secondary); text-decoration:none;
    padding:var(--space-1) 0; border-bottom:2px solid transparent;
  }
  .nav a:hover{color:var(--text-primary); text-decoration:underline}
  .nav a[aria-current="page"]{
    color:var(--text-primary); font-weight:600;
    border-bottom-color:var(--accent);
  }
  .nav-label{
    font-size:var(--text-xs); text-transform:none;
    color:var(--text-muted); font-weight:600; margin-right:var(--space-1);
  }
  .mode-switch{
    margin-left:auto; display:flex; gap:var(--space-2); align-items:center;
    font-size:var(--text-sm);
  }
  .mode-switch a[aria-current="true"]{
    color:var(--text-primary); font-weight:600;
    border-bottom-color:var(--accent);
  }
  .section-nav-label{
    font-weight:600; color:var(--text-secondary); font-size:var(--text-sm);
  }
  .section-nav-disclosure summary{cursor:pointer; font-weight:600}

  /* --- the page frame: sections, not cards ---------------------------- */
  .page-title{font-size:var(--text-display); margin-bottom:var(--space-2)}
  .section{
    border-top:1px solid var(--border-subtle);
    padding:var(--space-5) 0;
  }
  .section:first-of-type{border-top:0; padding-top:var(--space-2)}
  .section-head{
    display:flex; gap:var(--space-3); align-items:baseline;
    flex-wrap:wrap; margin-bottom:var(--space-3);
  }
  .section-title{font-size:var(--text-lg); margin:0}
  .section-meta{color:var(--text-muted); font-size:var(--text-sm)}
  .section-body{max-width:var(--measure)}

  /* --- rows: the fact and requirement primitives ---------------------- */
  .rows{display:flex; flex-direction:column; gap:var(--space-1)}
  .row{
    display:flex; gap:var(--space-3); flex-wrap:wrap;
    padding:var(--space-2) 0;
    border-bottom:1px solid var(--border-subtle);
  }
  .row:last-child{border-bottom:0}
  .row-label{color:var(--text-secondary); min-width:11rem; flex:0 0 11rem}
  .row-value{flex:1 1 18rem; min-width:0}
  .requirement{
    display:flex; gap:var(--space-3); align-items:baseline; flex-wrap:wrap;
    padding:var(--space-2) 0;
    border-bottom:1px solid var(--border-subtle);
  }
  .requirement:last-child{border-bottom:0}
  .requirement-name{flex:1 1 16rem; min-width:0}
  .requirement-count{color:var(--text-secondary); font-size:var(--text-sm)}

  /* --- queue items: the priority list --------------------------------- */
  .queue{display:flex; flex-direction:column; gap:var(--space-2); margin:0; padding:0; list-style:none}
  .queue-item{
    border:1px solid var(--border-subtle);
    border-left:3px solid var(--border-default);
    border-radius:var(--radius-sm);
    background:var(--canvas-raised);
    padding:var(--space-3) var(--space-4);
  }
  .queue-item.dominant{
    border-left-color:var(--accent);
    border-color:var(--border-default);
    padding:var(--space-4) var(--space-5);
  }
  .queue-item.secondary{border-left-color:var(--border-subtle)}
  .queue-title{font-weight:600; margin:0 0 var(--space-1)}
  .queue-why{color:var(--text-secondary); margin:0 0 var(--space-2)}
  .queue-actions{display:flex; gap:var(--space-2); flex-wrap:wrap; align-items:center}

  /* --- command bar ---------------------------------------------------- */
  .command-bar{
    display:flex; gap:var(--space-3); flex-wrap:wrap; align-items:center;
    padding:var(--space-3) 0;
  }
  .actions{display:flex; gap:var(--space-2); flex-wrap:wrap; align-items:center}

  /* --- buttons & controls --------------------------------------------- */
  .btn{
    display:inline-block;
    font:inherit; font-weight:600; font-size:var(--text-base);
    padding:var(--space-2) var(--space-4);
    border-radius:var(--radius-sm);
    border:1px solid var(--border-default);
    background:var(--canvas-subtle);
    color:var(--text-primary);
    text-decoration:none;
    cursor:pointer;
    min-height:2.75rem;
  }
  .btn:hover{border-color:var(--border-strong); background:var(--canvas-selected)}
  .btn.primary{
    background:var(--accent); border-color:var(--accent); color:var(--accent-ink);
  }
  .btn.primary:hover{filter:brightness(1.08)}
  .btn.secondary{background:transparent; color:var(--text-primary)}
  .btn.master{border-color:var(--mastery-ink); color:var(--mastery-ink)}
  .btn[disabled]{opacity:.55; cursor:not-allowed}
  .btn-quiet{background:none; border:none; color:var(--text-secondary); padding:var(--space-1)}
  input,select,textarea{
    font:inherit; font-size:var(--text-base);
    background:var(--canvas-subtle); color:var(--text-primary);
    border:1px solid var(--border-default);
    border-radius:var(--radius-sm);
    padding:var(--space-2);
    min-height:2.75rem;
  }
  input[type=checkbox],input[type=radio]{min-height:0; width:1rem; height:1rem}
  textarea{min-height:5rem}
  label{color:var(--text-secondary); font-size:var(--text-sm)}
  fieldset{border:1px solid var(--border-subtle); border-radius:var(--radius-sm); margin:0 0 var(--space-3)}
  legend{color:var(--text-secondary); font-size:var(--text-sm); padding:0 var(--space-2)}
  .form-row{display:flex; flex-direction:column; gap:var(--space-1); margin-bottom:var(--space-3)}
  .inline-check{display:flex; gap:var(--space-2); align-items:center; flex-wrap:wrap}
  .filters{display:flex; gap:var(--space-3); flex-wrap:wrap; align-items:flex-end}

  /* --- status labels: never colour-only (AX-1, VS-3) ------------------ */
  .status-label{
    display:inline-flex; align-items:center; gap:var(--space-1);
    font-size:var(--text-sm); font-weight:600;
    padding:2px var(--space-2);
    border-radius:var(--radius-pill);
    border:1px solid var(--border-default);
    background:var(--canvas-subtle);
    color:var(--text-primary);
  }
  .status-label::before{content:"\\2022"; color:var(--text-muted)}
  .status-label.success{border-color:var(--status-success); color:var(--status-success-ink); background:var(--status-success-soft)}
  .status-label.warning{border-color:var(--status-warning); color:var(--status-warning-ink); background:var(--status-warning-soft)}
  .status-label.failure{border-color:var(--status-failure); color:var(--status-failure-ink); background:var(--status-failure-soft)}
  .status-label.info{border-color:var(--status-info); color:var(--status-info-ink); background:var(--status-info-soft)}
  .status-label.mastery{border-color:var(--mastery-ink); color:var(--mastery-ink); background:var(--mastery-soft)}
  .status-label.neutral{color:var(--text-secondary)}

  /* --- banners -------------------------------------------------------- */
  .banner{
    padding:var(--space-3) var(--space-4);
    border:1px solid var(--border-default);
    border-left:3px solid var(--border-strong);
    border-radius:var(--radius-sm);
    background:var(--canvas-raised);
    color:var(--text-primary);
    font-size:var(--text-base);
    margin:var(--space-2) 0;
  }
  .banner.advisory,.banner.attention{border-left-color:var(--status-info); background:var(--status-info-soft)}
  .banner.ok,.banner.success{border-left-color:var(--status-success); background:var(--status-success-soft)}
  .banner.warn,.banner.warning{border-left-color:var(--status-warning); background:var(--status-warning-soft)}
  .banner.err,.banner.error{border-left-color:var(--status-failure); background:var(--status-failure-soft)}

  /* --- the five non-success states (SC-00a) --------------------------- */
  .state{
    border:1px solid var(--border-subtle);
    border-left:3px solid var(--border-default);
    border-radius:var(--radius-sm);
    padding:var(--space-4);
    background:var(--canvas-raised);
    margin:var(--space-3) 0;
  }
  .state-title{font-weight:600; margin:0 0 var(--space-1)}
  .state-body{color:var(--text-secondary); margin:0 0 var(--space-2)}
  .state-empty{border-left-color:var(--border-strong)}
  .state-limited{border-left-color:var(--status-warning)}
  .state-refusal{border-left-color:var(--status-info)}
  .state-failure{border-left-color:var(--status-failure)}
  .state-recovery{border-left-color:var(--accent)}

  /* --- disclosure ----------------------------------------------------- */
  details.disclosure{
    border:1px solid var(--border-subtle);
    border-radius:var(--radius-sm);
    padding:var(--space-2) var(--space-3);
    margin:var(--space-2) 0;
    background:var(--canvas-raised);
  }
  details.disclosure > summary{cursor:pointer; font-weight:600}
  details.disclosure[open] > summary{margin-bottom:var(--space-2)}

  /* --- the contextual inspector (RT note 2, no route of its own) ------ */
  .inspector{
    border:1px solid var(--border-default);
    border-radius:var(--radius-md);
    background:var(--canvas-raised);
    padding:var(--space-4);
    margin:var(--space-4) 0;
  }
  .inspector-title{font-size:var(--text-md); font-weight:600; margin:0 0 var(--space-2)}
  .inspector-raw{
    font-family:var(--font-mono); font-size:var(--text-sm);
    color:var(--text-muted); margin:0 0 var(--space-2);
  }

  /* --- the Card seam's fact container ---------------------------------- */
  .card{
    background:var(--canvas-raised);
    border:1px solid var(--border-subtle);
    border-radius:var(--radius-md);
    padding:var(--space-4);
    margin:var(--space-3) 0;
  }
  .card.guidance{border-left:3px solid var(--border-default)}
  .card.result.locked{border-style:dashed; border-left-style:solid}
  .card .ref{font-family:var(--font-mono); font-size:var(--text-sm); color:var(--text-muted)}
  .kicker{font-size:var(--text-sm); font-weight:600; color:var(--text-secondary); margin:0 0 var(--space-1)}
  .lead{font-weight:600; margin:var(--space-1) 0}
  .next-action{font-weight:600; margin:var(--space-2) 0}
  .mut{color:var(--text-muted)}
  .small{font-size:var(--text-sm); color:var(--text-muted)}
  .big{font-size:var(--text-md)}
  .label{font-weight:600; margin:var(--space-3) 0 var(--space-1)}

  /* --- legacy state pills (the five canonical words, text always) ----- */
  .pill{
    display:inline-block; border:1px solid var(--border-default);
    border-radius:var(--radius-pill); padding:2px var(--space-2);
    font-size:var(--text-sm); font-weight:600;
    background:var(--canvas-subtle); color:var(--text-primary);
  }
  .pill.locked{color:var(--text-secondary)}
  .pill.available{color:var(--text-primary)}
  .pill.active{color:var(--status-info-ink); background:var(--status-info-soft); border-color:var(--status-info)}
  .pill.passed{color:var(--status-success-ink); background:var(--status-success-soft); border-color:var(--status-success)}
  .pill.mastered{color:var(--mastery-ink); background:var(--mastery-soft); border-color:var(--mastery-ink)}

  /* --- utilities ------------------------------------------------------ */
  .flash-dismiss{font-size:var(--text-sm); margin:var(--space-1) 0 var(--space-3)}
  .result-count{font-size:var(--text-md); font-weight:600}
  .history-list{list-style:none; padding:0; margin:0}
  .history-item{
    padding:var(--space-2) 0;
    border-bottom:1px solid var(--border-subtle);
    display:flex; gap:var(--space-3); flex-wrap:wrap; align-items:baseline;
  }
  .history-item:last-child{border-bottom:0}
  .history-when{color:var(--text-muted); font-size:var(--text-sm)}
  .visually-hidden{
    position:absolute; width:1px; height:1px; overflow:hidden;
    clip:rect(0 0 0 0); clip-path:inset(50%); white-space:nowrap;
  }
  .chart-figure{margin:var(--space-3) 0}
  .chart-figure figcaption{color:var(--text-secondary); font-size:var(--text-sm)}
  .chart-table caption{color:var(--text-secondary)}

  /* --- the two presentation registers (VS-6) --------------------------- */
  /* Guided: calmer, more whitespace, one dominant action.
     Operations: denser facts, wider tables. Same tokens, same colours. */
  body.mode-guided main.shell{padding-top:var(--space-6)}
  body.mode-guided .section{padding:var(--space-6) 0}
  body.mode-operations main.shell{padding-top:var(--space-4)}
  body.mode-operations .section{padding:var(--space-4) 0}
  body.mode-operations table{font-size:var(--text-sm)}
  body.mode-operations th,body.mode-operations td{padding:var(--space-1) var(--space-2)}

  /* --- narrow window: mandatory degradation (AX-10) -------------------- */
  @media (max-width: 640px) {
    .shell{padding:0 var(--space-4)}
    main.shell{padding:var(--space-4) var(--space-4) var(--space-6)}
    .page-title{font-size:var(--text-xl)}
    .row,.requirement{flex-direction:column; gap:var(--space-1)}
    .row-label{flex:1 1 auto; min-width:0}
    .nav{gap:var(--space-3)}
    .mode-switch{margin-left:0; width:100%}
    .inspector{border-left:0; border-top:3px solid var(--accent)}
    .chart-table thead{display:none}
    .chart-table td,.chart-table th{display:block; padding:var(--space-1) 0}
  }

  /* --- reduced motion: no nonessential animation (AX-6, VS-9) --------- */
  @media (prefers-reduced-motion: reduce) {
    *{animation:none !important; transition:none !important}
  }
"""


STYLE: str = root_blocks() + _COMPONENT_RULES
