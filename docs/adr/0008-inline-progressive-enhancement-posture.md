# ADR 0008 — Inline progressive-enhancement posture for the Tier 1 UI

Date: 2026-09-14
Status: accepted

## Context

G-JS #225 locked the interaction posture at tier 0 (JS budget = 0): every
adopted interaction scored tier 0 in all three prototypes, so no budget was
granted and 0008 stayed reserved-and-unused with ADR 0006 unamended. Map #243
re-opened the posture prototype-gated: a budget is only granted for
interactions the prototypes demonstrate mattering. The P-Unified (#246) and
P-GraphSpine (#245) prototypes mark four fetch-refresh wants (queue-row brief
expansion, spine-chain expansion, week-strip paging, browse live filter) plus
the carried candidates (pathway/spine fetch-refresh, week navigation, real
trend lines + deferred heatmap, flash-without-URL-carry) — every one degrading
to a plain link or anchor. The owner opened the budget wanting a seamless study
flow and, grilled over two rounds in G-JS #249, granted tier 1 narrowly: static
SVG trend lines plus hover tooltips only, everything else stays tier 0.

## Decision

**Tier 1, narrow and capped.** One inline vanilla `<script>` (no build step, no
dependencies, ADR 0006's hard parts retained: zero added deps, files-are-truth
fresh reads per request, server-validated mutations — the client is never
trusted) is permitted for exactly one interaction class:

- **Chart hover tooltips on real multi-point series only** — server-rendered
  inline SVG through the existing `analytics/sparkline.py` seam stays the
  renderer (P2.2 bans pseudo-sparklines); the script adds hover/focus tooltips
  only. No axes-at-scale, no zoom, no pan (R3's tier-2 wall stays out), no
  heatmap.

Everything else is refused at tier 0 with link degradation: queue/spine
in-place expansion → links to `/next` and pathway pages; week paging → links;
browse live filter → anchor links per track plus the grouped-count table;
flash-without-URL-carry → `notice`/`kind` URL carry kept with the P3.5 copy
rules and plain-link dismissal (no `history.replaceState`); the
days-practiced heatmap stays refused behind locked P1.7 (triple refusal:
P1.7 wording, CONTEXT.md *Days practiced* mirror-not-metronome, density grid
as streak/loss framing) and returns only as a fresh effort that re-opens the
preference table per map #208's rule.

Graceful degradation is the contract: with script absent or disabled, every
granted interaction degrades to its tier-0 form (static SVG with no tooltips;
links/anchors as above) with no loss of function. Safety-critical mutations
(pass/master, evidence) remain server-validated render-from-server; the script
may prevent accidental clicks but never enable unconfirmed writes; one uniform
in-flight guard against double-submit; fragments (where used) re-render from
server truth, never from client state; `textContent`-side escaping discipline
for any client-built text.

## Consequences

- ADR 0006 stands unamended (stdlib-only shell); this ADR claims the reserved
  0008 slot its text always pointed at.
- The v2.4 DD-gate discipline changes: DD6's grep-able no-`<script>` gate is
  amended or replaced by a per-route budget gate (G-Spec #250 owns the exact
  gate text) asserting the script appears only where the tooltip grant applies
  and stays within the capped shape above.
- Reopen trigger: any further budget needs the same evidence packet as #225 —
  an adopted-path interaction demonstrably failing at tier 0, prototyped with
  the exact JS it needs.

See: ADR 0006 (stands unamended), ADR 0007 (amendment notes the reserved slot),
G-JS #225 (tier-0 lock), R3 `docs/research/r3-interaction-ceiling.md`
(capability ladder + tier-2 wall), P-Unified #246 / P-GraphSpine #245
(JS-want comments), G-Preferences #247 (P1.7, P2.2), G-Direction #248 (unified
recipe the tooltips annotate), G-Spec #250 (gate placement).
