# A11Y findings — the AX-11 gate's named debt

The AX-11 gate (`docs/spec-v3-study-day.md` §9 AX-11) is automated: axe-core
and colour contrast run per slice, on real fixture data. This file records
what the gate **cannot yet clear**, so that every gap is named, measured and
visible instead of being waived silently.

Nothing here is a pass. Each entry is a debt with a specific rule id, a
measured value and the reason it is not being fixed in this change.

## 1. axe-core findings (serious/critical, WCAG 2.2 AA)

`tests/web/test_a11y_axe.py` renders every served route body from the
pinned fixture repo and runs axe-core over the served document. The
violations below are the ones axe reports today.

| Route | Rule id | Impact | Message | Why it is not fixed here |
|---|---|---|---|---|
| `node` (`GET /nodes/{id}`) | `select-name` | critical | Select element must have an accessible name | The `<select name="template">` in the session-template form has a `<label>` sibling that is not associated with it (no `for`/`id` pair). The label lives in `src/skilltrace/web/views/forms.py`, outside this change's file set. |
| `evidence-index` (`GET /evidence`) | `select-name` | critical | Select element must have an accessible name | Three filter selects (`node`, `outcome`, `standing`) have unassociated `<label>` siblings; `src/skilltrace/web/views/evidence_index.py`, outside this change's file set. |
| `analytics` (`GET /analytics`) | `select-name` | critical | Select element must have an accessible name | The date-range `<select name="days">` has an unassociated `<label>`; `src/skilltrace/web/views/analytics.py`, outside this change's file set. |
| `portfolio` (`GET /portfolio`) | `label` | critical | Form elements must have labels | The `<input type="text" name="track">` has a `<label>` sibling that is not associated with it; `src/skilltrace/web/views/portfolio.py`, outside this change's file set. |
| `portfolio` (`GET /portfolio`) | `select-name` | critical | Select element must have an accessible name | The `<select name="format">` has an unassociated `<label>`; `src/skilltrace/web/views/portfolio.py`, outside this change's file set. |

The common cause is one missing `for`/`id` association per control. The fix
is small and belongs in the view modules that render the controls; it is
recorded here rather than worked around, so the gate stays honest about
what it did and did not check.

### Routes the gate could not render at all

| Route | Error | Why it is not fixed here |
|---|---|---|
| `node-evidence` (`GET /nodes/{id}/evidence`) | `AttributeError: 'ArtifactSpec' object has no attribute 'accepted_count'` | `src/skilltrace/web/views/evidence.py` reads `spec.accepted_count` off the `ArtifactSpec` record, which does not carry that field. The record shape lives in `src/skilltrace/evidence/`, outside this change's file set. |

`tests/web/test_a11y_axe.py` reports this route as *not rendered* rather
than counting it as clean.

## 2. Colour-contrast deviations

WCAG SC 1.4.11 asks 3:1 for the visual information required to identify
user-interface components and states. The v3 token table's three border
steps are hairline separators and container edges; measured against the
canvas they sit on, they do not reach that floor in either theme.

The floor is **not** lowered. `tests/web/test_a11y_contrast.py` names each
shortfall in `KNOWN_DEVIATIONS`, holds the measured value as a ratchet (a
palette change may not make it worse), and asserts that the entry is
recorded in this file. When the border steps are corrected, the entries
are deleted and the ordinary 3:1 floor applies again.

| Theme | Role | Measured | Floor |
|---|---|---|---|
| dark | `border-subtle` on `canvas-base` | 1.24 | 3.1 |
| dark | `border-default` on `canvas-base` | 1.55 | 3.1 |
| dark | `border-strong` on `canvas-base` | 2.28 | 3.1 |
| light | `border-subtle` on `canvas-base` | 1.18 | 3.1 |
| light | `border-default` on `canvas-base` | 1.46 | 3.1 |
| light | `border-strong` on `canvas-base` | 2.37 | 3.1 |

The token table (`src/skilltrace/web/tokens.py`) is outside this change's
file set, so the values are corrected there, not here.

Everything else is at or above its floor: every text pairing is at least
4.5:1 in both themes, the focus ring and the status colours clear 3:1, and
the status inks clear 4.5:1 on their own soft fills.
