# Resource verification worksheet — v0.8 slice 6

**Web pass performed:** 2026-07-07 (all 26 original entries) and 2026-07-08
(replacement candidates). **Verification itself is yours to run** — click each
URL, confirm the page and its claim with your own eyes, then run the
`verify-resource` block at the bottom. The agent never runs `verify-resource`
(held in the spirit of pass/master).

**2026-07-10 — SITTING COMPLETE.** The learner eyes-on confirmed every entry
(including the Khan courses from his Algebra 1 seat, the Runestone PY4E URL,
and PyDA 3E) and personally ran the full batch: all 29 resources verified
2026-07-10, `resource-report` green, coverage 81/81, exit gate green
(pytest 1012 passed, all validators OK). Verification events committed in
`execution/events.yaml` per acceptance criterion #3. This document remains as
the sitting record.

**2026-07-08 sitting update — both DECIDE items are resolved.** Your eyes-on
finding (both sites' useful tutorial content sits behind paywalls) settled them
as *misrepresented → replaced by curriculum edit*: `real-python` and
`mode-sql-tutorial` were removed from the registry and five free replacements
added (rows 27–31 below). The registry is now 29 entries; no DECIDE items
remain. New entries carry their own web-pass flags and appear in the command
block for your verification like any other.

Every entry claims exactly `cost: free` and sets no `free_tier`, `certificate`,
or `license`. So the reconciliation below is: *does the URL still resolve, and
is "free" still honest?*

## What you must do to close slice 6 (the checklist)

The agent's half is done (web pass, this worksheet, the acceptance audit — all
green). These steps are **yours**, in order:

1. **Verify.** Click through the worksheet and run the `verify-resource` command
   block below yourself. The agent never runs it. Each run appends one audit event
   to `execution/events.yaml` and stamps `last_verified` (or a `broken` marker)
   into `graph/resources.yaml`.
2. ~~Resolve the 2 DECIDE items~~ — **done 2026-07-08**: both resolved by
   curriculum edit (retired + replaced; see the Decisions section). One residue
   for you: confirm the `runestone-py4e` URL lands on the interactive PY4E book
   you actually use — if your bookmark differs, say so and the registry URL gets
   fixed before you verify it.
3. **Confirm the exit gate still passes** on your now-modified repo:
   ```powershell
   pytest
   skilltrace validate graph; skilltrace validate evidence; skilltrace validate resources
   skilltrace resource-report          # your verified/broken entries should show
   skilltrace next --minutes 60 --limit 5 --show-locked
   ```
4. **Commit — and do NOT scrub `execution/events.yaml` this time.** The
   slice-closing commit contains exactly two kinds of change:
   - `graph/resources.yaml` — the `last_verified` dates and any `broken` markers
     your batch wrote;
   - `execution/events.yaml` — the `verify-resource` events from your commands.
     **These events are the deliverable** (acceptance criterion #3 requires them in
     the log). The standing "keep the seed log `events: []` / `git checkout HEAD --
     execution/events.yaml`" rule was only ever about `sync` pollution in slices
     1–5 — it does **not** apply to your verification events. Committing this doc
     itself is optional (it's the sitting record, not engine data).

Everything below is the reference material for step 1.

## Legend

- **OK** — URL resolves, `cost: free` confirmed against the live page.
- **READ-INCOMPLETE** — URL resolves, but the fetch couldn't read the rendered
  page (JS wall or a 403 to the bot). The provider is well-known-free; you should
  still eyeball it. Not a pass until you look.
- **DECIDE** — a real discrepancy needs your judgment (see "Decisions" below).

## Reconciliation table

| # | Resource | Claim | Web-pass result | Flag |
|---|----------|-------|-----------------|------|
| 1 | [khan-arithmetic](https://www.khanacademy.org/math/arithmetic) | free | Resolves (Khan app shell); JS-rendered body not machine-readable | READ-INCOMPLETE |
| 2 | [khan-algebra](https://www.khanacademy.org/math/algebra) | free | Resolves (app shell); "free" is background knowledge, not a page read | READ-INCOMPLETE |
| 3 | [khan-precalculus](https://www.khanacademy.org/math/precalculus) | free | Resolves (app shell); "free" is background knowledge, not a page read | READ-INCOMPLETE |
| 4 | [khan-statistics-probability](https://www.khanacademy.org/math/statistics-probability) | free | Resolves (app shell); body not machine-readable | READ-INCOMPLETE |
| 5 | [khan-linear-algebra](https://www.khanacademy.org/math/linear-algebra) | free | Resolves (app shell); body not machine-readable | READ-INCOMPLETE |
| 6 | [khan-differential-calculus](https://www.khanacademy.org/math/differential-calculus) | free | Resolves (app shell); body not machine-readable | READ-INCOMPLETE |
| 7 | [3blue1brown-essence-linear-algebra](https://www.3blue1brown.com/topics/linear-algebra) | free | Resolves; free (optional supporter membership, content not gated) | OK |
| 8 | [3blue1brown-essence-calculus](https://www.3blue1brown.com/topics/calculus) | free | Resolves; free (optional supporter) | OK |
| 9 | [seeing-theory](https://seeing-theory.brown.edu) | free | Resolves; free; site notes it is "archived for reference" (stable, not maintained) | OK |
| 10 | [openintro-statistics](https://www.openintro.org/book/os/) | free | Resolves; free PDF (pay-what-you-want, $0 option); paid print also exists — `cost: free` is honest for the free PDF | OK |
| 11 | [python-tutorial](https://docs.python.org/3/tutorial/) | free | Resolves; free (PSF License) | OK |
| 12 | [python-stdlib-reference](https://docs.python.org/3/library/) | free | Resolves; free (PSF License) | OK |
| 13 | ~~real-python~~ | — | Learner confirmed useful tutorials paywalled → **retired by curriculum edit 2026-07-08** (replaced by rows 27–29) | RESOLVED |
| 14 | [missing-semester](https://missing.csail.mit.edu/) | free | Resolves; free (CC BY-NC-SA) | OK |
| 15 | [microsoft-windows-commands](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands) | free | Resolves & readable; free | OK |
| 16 | [pro-git-book](https://git-scm.com/book/en/v2) | free | Resolves; free (CC BY-NC-SA 3.0); paid print optional | OK |
| 17 | [github-docs](https://docs.github.com/) | free | Resolves; free | OK |
| 18 | [sqlbolt](https://sqlbolt.com/) | free | Resolves; free (ad-supported) | OK |
| 19 | ~~mode-sql-tutorial~~ | — | 301 → thoughtspot.com; learner confirmed useful parts paywalled → **retired by curriculum edit 2026-07-08** (replaced by row 31) | RESOLVED |
| 20 | [sqlite-docs](https://www.sqlite.org/lang.html) | free | Resolves; free (public domain) | OK |
| 21 | [pandas-docs](https://pandas.pydata.org/docs/) | free | Resolves; free (BSD-licensed) | OK |
| 22 | [matplotlib-docs](https://matplotlib.org/stable/) | free | 403 to the bot (site is live); Matplotlib docs are well-known free (BSD-style) | READ-INCOMPLETE |
| 23 | [data-to-viz](https://www.data-to-viz.com/) | free | Resolves; free (optional paid poster, content free) | OK |
| 24 | [fundamentals-of-dataviz](https://clauswilke.com/dataviz/) | free | Resolves; free online (CC BY-NC-ND 4.0); paid print optional | OK |
| 25 | [google-tech-writing](https://developers.google.com/tech-writing) | free | Resolves; free | OK |
| 26 | [make-a-readme](https://www.makeareadme.com/) | free | Resolves; free (MIT) | OK |
| 27 | [automate-the-boring-stuff](https://automatetheboringstuff.com/) | free | Resolves & readable; free (CC BY-NC-SA), 3rd edition free online; paid Udemy course optional | OK |
| 28 | [runestone-py4e](https://runestone.academy/ns/books/published/py4e-int/index.html) | free | 403 to the bot; Runestone is free — **confirm the URL lands on the book you use** | READ-INCOMPLETE |
| 29 | [python-tutor](https://pythontutor.com/) | free | Resolves & readable; free (donation-supported), no account needed | OK |
| 30 | [python-for-data-analysis](https://wesmckinney.com/book/) | free | 403 to the bot; author documents the 3E online edition as open-access free; paid print/ebook optional | READ-INCOMPLETE |
| 31 | [select-star-sql](https://selectstarsql.com/) | free | Resolves & readable; free ("free of charge, free of ads, no registration"), CC BY-SA | OK |

**Tally (29 entries):** 20 OK · 9 READ-INCOMPLETE (Khan ×6, Matplotlib, Runestone,
PyDA 3E) · 0 DECIDE (both resolved by curriculum edit; rows 13/19 retired).
*(Corrects the earlier "18 OK · 6 READ-INCOMPLETE" tally — the table always had
6 Khan rows + Matplotlib flagged, i.e. 17 OK · 7 READ-INCOMPLETE of the 26.)*

> **Ship-unverified is honest.** Any OK or READ-INCOMPLETE entry you don't get to
> may ship *honestly unverified* — a warning in `resource-report`, never a
> blocker (the 180-day window catches them). With the two DECIDE items resolved
> by edit, nothing left in the registry is a known problem.

## Decisions — RESOLVED 2026-07-08

Both DECIDE items were settled at the sitting after the learner's eyes-on check
found that each site's genuinely useful tutorial content sits behind a paywall.
Both were **misrepresented → replaced by curriculum edit** (the issue's
alternative to a `--broken` marker); neither needs a `verify-resource` line.

### 13 · real-python — RETIRED (freemium; useful tutorials paywalled)
Removed from the registry. Its practical-tutorial role is taken over by three
new entries drawn from the learner's proven materials plus one gap-filler:
- **automate-the-boring-stuff** → the python fundamentals, CSV, and
  data-cleaning-tool nodes;
- **runestone-py4e** (interactive PY4E, already in the learner's use) → the
  core python fundamentals nodes;
- **python-tutor** → the reading-errors and errors-debugging nodes;
- **python-for-data-analysis** (Wes McKinney 3E, open access) → the pandas
  nodes, whose only tutorial-layer resource had been real-python.
Two portfolio nodes that would have dropped to a single resource were patched
with apt existing entries: `python-stdlib-reference` (the `random`/`statistics`
modules) now supports `portfolio.project.stats_simulation_01`, and
`python-tutorial` supports `portfolio.project.slope_calculator_01`.

### 19 · mode-sql-tutorial — RETIRED (URL moved to thoughtspot.com; useful parts paywalled)
Removed from the registry. Its 6 nodes were already covered by **sqlbolt** and
**sqlite-docs**; **select-star-sql** (free, interactive, no registration) was
added to the select/filtering/aggregation/joins/join-mental-models nodes to
restore the tutorial slot. `data.sql.subqueries_01` keeps sqlbolt + sqlite-docs
(Select Star SQL doesn't clearly cover subqueries, so it isn't claimed).

## The `verify-resource` command block

Run this yourself, in the repo root. The 20 OK entries are ready to fire. The 9
READ-INCOMPLETE entries are included but **you must eyeball the page first** — they
are one line each, unblock them by looking. (You've already confirmed the Khan
courses from your Algebra 1 seat, so those are just a click-and-run.) No DECIDE
entries remain.

```powershell
# --- OK: confirmed free, URL resolves ---
skilltrace verify-resource 3blue1brown-essence-linear-algebra
skilltrace verify-resource 3blue1brown-essence-calculus
skilltrace verify-resource seeing-theory
skilltrace verify-resource openintro-statistics
skilltrace verify-resource python-tutorial
skilltrace verify-resource python-stdlib-reference
skilltrace verify-resource missing-semester
skilltrace verify-resource microsoft-windows-commands
skilltrace verify-resource pro-git-book
skilltrace verify-resource github-docs
skilltrace verify-resource sqlbolt
skilltrace verify-resource sqlite-docs
skilltrace verify-resource pandas-docs
skilltrace verify-resource data-to-viz
skilltrace verify-resource fundamentals-of-dataviz
skilltrace verify-resource google-tech-writing
skilltrace verify-resource make-a-readme
skilltrace verify-resource automate-the-boring-stuff
skilltrace verify-resource python-tutor
skilltrace verify-resource select-star-sql

# --- READ-INCOMPLETE: eyeball the page, then run (well-known free) ---
skilltrace verify-resource khan-arithmetic
skilltrace verify-resource khan-algebra
skilltrace verify-resource khan-precalculus
skilltrace verify-resource khan-statistics-probability
skilltrace verify-resource khan-linear-algebra
skilltrace verify-resource khan-differential-calculus
skilltrace verify-resource matplotlib-docs
skilltrace verify-resource python-for-data-analysis
# runestone-py4e: FIRST confirm the URL opens the interactive PY4E book you use;
# if your bookmark differs, get the registry URL fixed before verifying:
skilltrace verify-resource runestone-py4e
```

After running the batch, `skilltrace resource-report` will show the verified
entries with today's date and any broken markers you set. Unreviewed entries stay
**unverified** — a warning in the report, never a blocker; the 180-day staleness
window catches them later.

> **⚠ Do NOT scrub `execution/events.yaml` when you commit.** The standing seed
> rule ("keep the audit log `events: []`, `git checkout HEAD -- execution/events.yaml`
> before committing") was for slices 1–5, where only `sync` polluted the log.
> **Slice 6 is the exception:** your `verify-resource` runs each append one audit
> event, and criterion #3 *requires* those verification events to persist in the
> log. Committing them (alongside the `last_verified` / `broken` facts in
> `resources.yaml`) is what closes the slice. Scrubbing them fails the criterion.
