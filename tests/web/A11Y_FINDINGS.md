# A11Y findings — the AX-11 gate's named debt

The AX-11 gate (`docs/spec-v3-study-day.md` §9 AX-11) is automated: axe-core
and colour contrast run per slice, on real fixture data. This file records
what the gate **cannot yet clear**, so that every gap is named, measured and
visible instead of being waived silently.

**There is no outstanding debt.** Every route in the normative route table
renders, axe-core reports zero serious or critical violations against the
WCAG 2.2 AA rule sets, and every meaningful colour pairing in both themes
clears its contrast floor.

The file stays because the gates that read it must fail loudly if a gap ever
reappears: a shortfall has to be *named* to exist, never merely tolerated.
`tests/web/test_a11y_axe.py` holds two maps that are currently empty —
`UNRENDERABLE` (a route whose body does not render) and `RECORDED_FINDINGS`
(a route with blocking axe violations) — and asserts that what axe actually
reports is exactly what those maps say. An unrecorded violation fails the
gate; a stale record also fails it, so a fixed finding cannot linger.

## 1. axe-core findings (serious/critical, WCAG 2.2 AA)

None. The sweep covers thirty-one served documents — every destination in
`docs/spec-v3-study-day.md` §6, the table's node-centred graph
(`/graph/{id}`) and non-writing portfolio preview (`/portfolio/preview`),
the contextual inspector over a selected evidence record, and the one
unified error body — rendered from the pinned fixture repo and scanned with
axe-core 4.14.0 under the `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` and
`wcag22aa` rule sets.

The fixture is the product's real states, not its happiest one: an open
Session with work logged against the active node, an overdue Review, an
open Blocker, and an evidence history with a live record, a rejected record
and a correction that supersedes an earlier one. The open-Session state was
absent from an earlier revision of this fixture (a note here recorded a view
defect that has since been fixed by deriving a Session's bound node from its
logged work); it is covered now. The named Next (`next-empty`, `next-stale`)
and Find (`finder-no-results`, `finder-stale`, `finder-empty`,
`finder-source-missing`) states — the same fixtures the golden snapshot
suite pins — are covered too.

## 2. Colour-contrast deviations

None. Every meaningful pairing clears its floor in both the dark theme and
the light companion:

* text on every canvas step — 4.5:1 (WCAG SC 1.4.3);
* each status ink on its own soft fill — 4.5:1;
* the accent ink on the accent fill — 4.5:1;
* the focus ring and the status colours on every canvas step — 3:1
  (WCAG SC 1.4.11);
* the two **meaningful** border steps — the ones that bound controls and
  interactive regions — against every canvas step they may sit on — 3:1.

`border-subtle` is the one border role held below 3:1. It is a decorative
hairline: a table's row rules and a section divider. The structure it
decorates is carried by the table's own caption and header cells, so it is
not a boundary the learner needs in order to identify a control, and SC
1.4.11 does not apply to it. It is still held to a visibility floor of
1.4:1 against every canvas step, so the decoration cannot quietly become
invisible.

## 3. Deferred manual passes

The keyboard-only, screen-reader, touch, focus, reduced-motion and 320px
re-measure runs are a **named deferred effort** under §12.4 of the
specification. They were never run, so they are never a pass and never a
blocker to this contract's acceptance — and they are never grounds to
weaken the standard above.
