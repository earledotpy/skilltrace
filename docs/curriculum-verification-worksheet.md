# Resource verification worksheet — v0.8 slice 6

**Web pass performed:** 2026-07-07 (agent fetched every registry URL, confirmed it
resolves, read the provider's current terms, reconciled the drafted `cost: free`
claim). **Verification itself is yours to run** — click each URL, confirm the
page and its claim with your own eyes, then run the `verify-resource` block at the
bottom. The agent never runs `verify-resource` (held in the spirit of
pass/master).

Every entry currently claims exactly `cost: free` and sets no `free_tier`,
`certificate`, or `license`. So the reconciliation below is: *does the URL still
resolve, and is "free" still honest?* Loud flags are called out; two entries need
a **judgment call from you** before (or instead of) verifying.

## What you must do to close slice 6 (the checklist)

The agent's half is done (web pass, this worksheet, the acceptance audit — all
green). These steps are **yours**, in order:

1. **Verify.** Click through the worksheet and run the `verify-resource` command
   block below yourself. The agent never runs it. Each run appends one audit event
   to `execution/events.yaml` and stamps `last_verified` (or a `broken` marker)
   into `graph/resources.yaml`.
2. **Resolve the 2 DECIDE items** (`real-python`, `mode-sql-tutorial`). These are
   *known* problems — unlike the OK / READ-INCOMPLETE entries they may **not** ship
   as silent "unverified". Pick verify, `--broken`, or a curriculum edit for each.
   (A `--broken` marker fails no test.)
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
| 13 | [real-python](https://realpython.com/) | free | 403 to the bot (site is live); Real Python is **freemium** — free articles, but courses/learning paths are paid membership | **DECIDE** |
| 14 | [missing-semester](https://missing.csail.mit.edu/) | free | Resolves; free (CC BY-NC-SA) | OK |
| 15 | [microsoft-windows-commands](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands) | free | Resolves & readable; free | OK |
| 16 | [pro-git-book](https://git-scm.com/book/en/v2) | free | Resolves; free (CC BY-NC-SA 3.0); paid print optional | OK |
| 17 | [github-docs](https://docs.github.com/) | free | Resolves; free | OK |
| 18 | [sqlbolt](https://sqlbolt.com/) | free | Resolves; free (ad-supported) | OK |
| 19 | [mode-sql-tutorial](https://mode.com/sql-tutorial/) | free | **301 → thoughtspot.com/sql-tutorial** — Mode was acquired by ThoughtSpot; the stable root URL has moved and the destination is now a marketing-wrapped page | **DECIDE** |
| 20 | [sqlite-docs](https://www.sqlite.org/lang.html) | free | Resolves; free (public domain) | OK |
| 21 | [pandas-docs](https://pandas.pydata.org/docs/) | free | Resolves; free (BSD-licensed) | OK |
| 22 | [matplotlib-docs](https://matplotlib.org/stable/) | free | 403 to the bot (site is live); Matplotlib docs are well-known free (BSD-style) | READ-INCOMPLETE |
| 23 | [data-to-viz](https://www.data-to-viz.com/) | free | Resolves; free (optional paid poster, content free) | OK |
| 24 | [fundamentals-of-dataviz](https://clauswilke.com/dataviz/) | free | Resolves; free online (CC BY-NC-ND 4.0); paid print optional | OK |
| 25 | [google-tech-writing](https://developers.google.com/tech-writing) | free | Resolves; free | OK |
| 26 | [make-a-readme](https://www.makeareadme.com/) | free | Resolves; free (MIT) | OK |

**Tally:** 18 OK · 6 READ-INCOMPLETE (Khan ×5, Matplotlib) · 2 DECIDE.

> **Ship-unverified vs. must-resolve.** The 18 OK and 6 READ-INCOMPLETE entries may
> ship *honestly unverified* if you don't get to them — a warning in
> `resource-report`, never a blocker (the 180-day window catches them). The **2
> DECIDE entries are different**: they are *known* problems, so leaving them as
> silent "unverified" does **not** satisfy the slice — each needs a decision
> (verify, mark broken, or edit) before seeding is called done. A `--broken`
> marker fails no test: coverage counts linkage, not health, and both DECIDE
> resources' nodes keep other resources.

## Decisions (yours — not the agent's to resolve)

### 13 · real-python — freemium vs. free-first doctrine
`cost: free` is defensible *only* for Real Python's free articles; its courses and
learning paths sit behind paid membership. `docs/curriculum-authoring.md` says
"every primary resource is free. No paid materials." Real Python is a secondary
resource on all 26 of its nodes (each also has python.org / a free primary), so it
isn't anyone's only path. Your call:
- **Keep + verify** if you're treating it as "the free-article slice of Real
  Python" and are comfortable that `cost: free` reads that way; or
- **Mark broken** (`--reason "freemium; courses paywalled — conflicts with
  free-first"`) to surface it for later replacement; or
- **Curriculum edit** to drop it / swap the link to a specific free article root.

Recommendation: keep and verify — it's never a sole path and its free tutorials are
genuinely free — but that's a doctrine judgment I shouldn't make for you.

### 19 · mode-sql-tutorial — root URL moved (Mode acquired by ThoughtSpot)
The registered root `https://mode.com/sql-tutorial/` now 301-redirects to
`https://www.thoughtspot.com/sql-tutorial`. The tutorial content still appears to
exist under the new host but is now marketing-wrapped. This is exactly the
"provider URL-stability" case the doctrine warns about. Its 6 nodes are all also
covered by **sqlbolt** and/or **sqlite-docs**, so nothing is orphaned if it goes.
Your call:
- **Mark broken** (`--reason "mode.com/sql-tutorial 301s to thoughtspot.com;
  root URL moved after acquisition"`); or
- **Curriculum edit** the `url` to the ThoughtSpot destination and then verify; or
- **Curriculum edit** to retire it (sqlbolt + sqlite-docs already cover its nodes).

Recommendation: mark broken now (honest, reversible), decide replacement later —
the staleness/broken report will keep reminding you.

## The `verify-resource` command block

Run this yourself, in the repo root. The 20 OK entries are ready to fire. The 4
READ-INCOMPLETE entries are included but **you must eyeball the page first** — they
are one line each, unblock them by looking. The 2 DECIDE entries are left
**commented out** with their broken-form pre-filled; uncomment the line matching
your decision.

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

# --- READ-INCOMPLETE: eyeball the page, then run (well-known free) ---
skilltrace verify-resource khan-arithmetic
skilltrace verify-resource khan-algebra
skilltrace verify-resource khan-precalculus
skilltrace verify-resource khan-statistics-probability
skilltrace verify-resource khan-linear-algebra
skilltrace verify-resource khan-differential-calculus
skilltrace verify-resource matplotlib-docs

# --- DECIDE: uncomment ONE line per resource after you choose ---
# real-python (13): keep+verify, OR mark broken:
# skilltrace verify-resource real-python
# skilltrace verify-resource real-python --broken --reason "freemium; courses paywalled — conflicts with free-first"

# mode-sql-tutorial (19): mark broken, OR verify after a URL edit:
# skilltrace verify-resource mode-sql-tutorial --broken --reason "mode.com/sql-tutorial 301s to thoughtspot.com; root URL moved after acquisition"
# skilltrace verify-resource mode-sql-tutorial
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
