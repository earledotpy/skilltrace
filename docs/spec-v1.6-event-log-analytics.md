# Spec — v1.6 Event-log analytics v1

**Status:** locked hand-off (map #118) — no open product or architecture
decisions block the v1.6 build. T-TestArch and T-Exit are open; their
sections are stubs (§6, §7) to be filled verbatim once those tickets close.
**Target:** v1.6, the first event-log analytics release, shipping after
v1.5 (Tier 2 FSRS retention analytics).
**Map:** [#118 Map — v1.6 Event-log analytics v1](https://github.com/earledotpy/skilltrace/issues/118)
**Decisions:** [R1 #119](https://github.com/earledotpy/skilltrace/issues/119) · [R2 #120](https://github.com/earledotpy/skilltrace/issues/120) · [G3 #121](https://github.com/earledotpy/skilltrace/issues/121) · [G4 #122](https://github.com/earledotpy/skilltrace/issues/122) · [G5 #123](https://github.com/earledotpy/skilltrace/issues/123) · [G6 #124](https://github.com/earledotpy/skilltrace/issues/124) · [G7 #125](https://github.com/earledotpy/skilltrace/issues/125) · [T-TestArch #127](https://github.com/earledotpy/skilltrace/issues/127) · [T-Exit #132](https://github.com/earledotpy/skilltrace/issues/132).
**Standing rule:** all terms per `CONTEXT.md`; safety rules in `AGENTS.md`
are unchanged and binding — this spec never relaxes them.

> Hand-off gate (from map `Destination`): a builder can implement v1.6
> without reopening a product or architecture question. This doc satisfies
> that gate once T-TestArch and T-Exit close and their stubs are filled.

---

## 0. Scope and what is explicitly out of scope

In scope for v1.6:

- A new `src/skilltrace/analytics/` package: `derive.py`, `models.py`,
  `export.py`, `policy.py`, `sparkline.py`.
- Four analytics themes: **study velocity** (work items + forward node
  progress), **blockers by domain** (by track and node ID prefix),
  **review completion** (with prominent overdue highlighting), and
  **evidence coverage** (per-node counts, gap analysis, submission rate).
- A per-theme `skilltrace analytics` CLI command family with shared
  flags, policy-driven defaults, and a soft-data advisory prefix below
  the minimum-sessions threshold.
- A single-page analytics dashboard at `GET /analytics` in Serve, with
  a date-range preset dropdown, group-by toggle, a 2×2 theme-card grid,
  inline-SVG sparklines, and an advisory warning slot.
- `POST /analytics/export` route in Serve that delegates to the same
  export surface as the CLI.
- Three export formats: Markdown, HTML (self-contained), JSON (stable
  published contract). Exports are disposable, generated to
  `data/analytics-report-<theme>.<ext>` by default; gitignored and
  never read back by the engine.
- A new `policy/analytics.yaml` seed document and its entry in the
  `validate policy` umbrella.
- Advisory integration via a new `analytics_warnings()` function in
  `policy/advisory.py`; surfaced in `skilltrace today`, `skilltrace
  analytics`, and the Serve `#analytics-advisory` slot.
- Glossary additions to `CONTEXT.md` for any new terms introduced by
  this spec (see §8).

Explicitly **out of scope** (per map `Out of scope`):

- Diagnostic analytics (per `docs/POST_V1_ROADMAP.md` "Beyond this
  roadmap").
- Predictive or prescriptive analytics of any kind.
- Time-based study velocity — v1.6 measures work items and forward node
  progress only, not clock time spent.
- Network-dependent features (offline-first per ADR 0006).
- Sparklines in CLI output — sparklines are Web UI only.
- Changes to the event log's schema or write path — events are
  audit-only and are not read to compute state (CONTEXT.md, AGENTS.md).
  Analytics derives from the execution YAML files directly.

---

## 1. Data sources and schema adequacy (R1)

Per [R1 — Event log schema adequacy #119](https://github.com/earledotpy/skilltrace/issues/119):
the current execution YAML files are adequate. No schema changes are
needed to support the four themes.

The four themes read from these files:

| Theme               | Primary source(s)                                                    |
|---------------------|----------------------------------------------------------------------|
| Study velocity      | `execution/session_work.yaml` (work items); `graph/state.yaml` (forward node progress) |
| Blockers by domain  | `execution/blockers.yaml`; node ID prefix / track from `graph/nodes/*.md` |
| Review completion   | `execution/reviews.yaml`                                             |
| Evidence coverage   | `evidence/*.yaml` (one per node); `graph/nodes/*.md` (spec counts)   |

Analytics **never reads `execution/events.yaml`**: events are
audit-only per the engine invariant. Analytics derives from the
primary data files — the same truth files the engine reads.

---

## 2. Analytics module architecture (R2)

Per [R2 — Analytics module architecture #120](https://github.com/earledotpy/skilltrace/issues/120):
v1.6 introduces a new `src/skilltrace/analytics/` package. The CLI
commands and Serve routes call the same derivations; there is no
second vocabulary.

```
src/skilltrace/analytics/
    __init__.py
    derive.py      # pure derivation functions for all four themes
    models.py      # dataclasses / typed containers for derivation output
    export.py      # renders Markdown, HTML, JSON from derive.py output
    policy.py      # loads and validates policy/analytics.yaml
    sparkline.py   # inline-SVG sparkline renderer (≤40 lines, no JS)
```

`derive.py` functions are pure: they take loaded data and policy values
as arguments and return typed results from `models.py`. No side effects,
no file I/O, no `datetime.date.today()` calls — the CLI and Serve layers
pass `today` as a required argument.

`export.py` consumes the output of `derive.py`. It never re-reads YAML
or re-derives data. The CLI `analytics export` and the Serve
`POST /analytics/export` route both call `export.py` directly.

`sparkline.py` is self-contained (≤40 lines, no JS), used only by the
HTML export and the Serve dashboard.

---

## 3. Policy seed (G3)

Per [G3 — Policy file schema for analytics #121](https://github.com/earledotpy/skilltrace/issues/121):
a new `policy/analytics.yaml` file is introduced with the following
locked values.

### 3.1 New file: `policy/analytics.yaml`

```yaml
analytics_policy:
  id: policy.analytics.default_v1_6
  status: active
  title: Event-log analytics
  description: >
    Read-only operational analytics over the four themes: study velocity,
    blockers by domain, review completion, and evidence coverage.
    Rolling windows default from this file; per-metric advisory thresholds
    drive the analytics_warnings() surface. Advisory only — never blocks
    a human command, never alters state.
  default_window_days: 30
  default_group_by: prefix
  min_sessions_for_full_data: 3
  sparkline_bucket: weekly
  advisory_thresholds:
    velocity_below_target_per_week: 2
    review_completion_below_target: 0.80
    evidence_coverage_below_target: 0.60
    blockers_active_threshold: 3
  created_at: 2026-08-31
  updated_at: 2026-08-31
```

All values are policy *values*, not engine constants. They are readable
and editable by the learner; changes take effect at the next command
invocation.

### 3.2 `validate policy` integration

Add `analytics.yaml` to `POLICY_FILES` in
`src/skilltrace/policy/loading.py`, mapping the filename to
`analytics_policy` (its top-level key). The existing umbrella
`validate policy` command gains the file and the value-range checks
below. No new sub-target; the new file rides the umbrella per the
precedent set in Tier 2.

Value-range checks (each is a hard error on load, non-zero exit):

- `default_window_days`: `1 <= value <= 365`.
- `min_sessions_for_full_data`: `>= 1`.
- `advisory_thresholds.review_completion_below_target`: `0 < value < 1`.
- `advisory_thresholds.evidence_coverage_below_target`: `0 < value < 1`.
- `advisory_thresholds.velocity_below_target_per_week`: `>= 0`.
- `advisory_thresholds.blockers_active_threshold`: `>= 0`.

Bad values exit non-zero with a message naming the field.

---

## 4. CLI command surface (G4)

Per [G4 — CLI command surface for analytics #122](https://github.com/earledotpy/skilltrace/issues/122):
the analytics CLI surface mirrors the existing `report <target>`
family in style and registration pattern.

### 4.1 Subcommands

| Command                                      | Output                                      |
|----------------------------------------------|---------------------------------------------|
| `skilltrace analytics`                       | Summary: all four themes stacked            |
| `skilltrace analytics velocity`              | Per-theme table + Mentor frame              |
| `skilltrace analytics blockers`              | Per-theme table + Mentor frame              |
| `skilltrace analytics reviews`               | Per-theme table + Mentor frame              |
| `skilltrace analytics evidence`              | Per-theme table + Mentor frame              |
| `skilltrace analytics export --theme <X> --format <md\|html\|json>` | Disposable export file |

### 4.2 Shared flags

Every subcommand (including `export`) accepts:

- `--days <N>` — rolling window in days (default: `default_window_days`
  from `policy/analytics.yaml`).
- `--group-by <prefix|track>` — grouping dimension (default:
  `default_group_by`).
- `--state <state>` — node state filter, repeatable (OR logic). Zero
  `--state` flags means all states. Examples: `--state passed`,
  `--state passed --state mastered`.

### 4.3 Soft-data advisory

When the number of sessions in the rolling window is below
`min_sessions_for_full_data`, every subcommand prefixes its output
with:

```
[advisory] Limited data — fewer than N sessions in the last W days.
           Results may not reflect your full activity.
```

This is an advisory prefix, not an error. The command exits 0.

### 4.4 Registration

All `analytics` subcommands are registered in
`src/skilltrace/commands/analytics.py` as a new module and wired
through the existing `Registry.register(…)` pattern in
`src/skilltrace/cli.py`. Kind: `READ_ONLY` for all subcommands except
`export`, which is `MUTATING` (one `export_analytics` audit event per
call). The `today` date is passed as a required argument from the CLI
layer; `derive.py` never calls `datetime.date.today()`.

### 4.5 Export subcommand

`analytics export` writes to `data/analytics-report-<theme>.<ext>` by
default (theme segment omitted for the all-themes summary). The
`--output PATH` flag overrides the destination; `-` writes to stdout.
Exports are disposable and gitignored; the engine never reads them
back. The command appends one `export_analytics` audit event to
`execution/events.yaml`; it refuses (non-zero exit) on any data load
error.

---

## 5. Web UI analytics dashboard (G5)

Per [G5 — Web UI analytics dashboard design #123](https://github.com/earledotpy/skilltrace/issues/123):
a single-page analytics dashboard is added to Serve at `GET /analytics`.

### 5.1 Route and parameters

`GET /analytics?days=<N>&group-by=<prefix|track>`

Both query parameters are optional; omitted values fall back to
`policy/analytics.yaml` defaults. The route derives all four themes
in a single pass and renders the full dashboard.

### 5.2 Navigation

The header nav gains an `Analytics` link after `Health`. The link is
always present; the dashboard shows a graceful empty state when there
is no data.

### 5.3 Page layout

```
┌──────────────────────────────────────────────────────────┐
│  date-range preset dropdown (7d / 30d / 90d / policy)    │
│  group-by toggle (prefix / track)                        │
│                                                          │
│  [overdue-review banner — prominent, shown when any]     │
│                                                          │
│  ┌──────────────┐  ┌────────────────────────┐            │
│  │ Velocity     │  │ Blockers by domain     │            │
│  │ <details>    │  │ <details>              │            │
│  └──────────────┘  └────────────────────────┘            │
│  ┌──────────────┐  ┌────────────────────────┐            │
│  │ Reviews      │  │ Evidence coverage      │            │
│  │ <details>    │  │ <details>              │            │
│  └──────────────┘  └────────────────────────┘            │
│                                                          │
│  <div id="analytics-advisory"></div>  ← G6 advisory slot │
└──────────────────────────────────────────────────────────┘
```

Each theme card is a `<details open>` element containing the
per-theme derivation output, an inline-SVG sparkline (from
`sparkline.py`), and a per-theme export form that POSTs to
`/analytics/export`.

Mobile: the 2×2 grid collapses to a single-column layout at ≤900px
(the existing Serve breakpoint).

### 5.4 Export route

`POST /analytics/export` accepts `theme` and `format` form parameters
and delegates to `export.py` — the same code path as the CLI's
`analytics export`. The response is a file download or a redirect to
the data directory; one `export_analytics` audit event is appended.

### 5.5 Sparklines

`src/skilltrace/analytics/sparkline.py` produces inline SVG. It is
≤40 lines, contains no JavaScript, and is used by both the HTML export
and the Serve dashboard. Sparklines never appear in CLI output.

### 5.6 Empty state

When the rolling window contains no data, each theme card renders a
calm empty-state message rather than an error. The dashboard never
errors on seed (no data at all).

---

## 6. Advisory integration (G6)

Per [G6 — Advisory integration mechanism #124](https://github.com/earledotpy/skilltrace/issues/124):
advisory warnings for analytics are introduced via a new function in
the existing `policy/advisory.py`.

### 6.1 New function

```python
def analytics_warnings(root: Path, view: AnalyticsView) -> list[str]:
    ...
```

- Reads thresholds from `policy/analytics.yaml` via `policy.py`.
- Returns `[]` on `PolicyLoadError` (fail-open; never crashes a
  consumer).
- Threshold comparisons live in `advisory.py`; derivations in
  `derive.py` stay pure of policy.
- Returns a list of human-readable warning strings, one per threshold
  violation (e.g. `"velocity below target: 1.2 items/week vs. target
  2"`).

No unifying facade is introduced yet; two functions (`analytics_warnings`
and the existing retention advisory) coexist independently.

### 6.2 Surfaces

Advisory warnings appear in three places:

| Surface                        | Behavior                                                                 |
|--------------------------------|--------------------------------------------------------------------------|
| `skilltrace today`             | Extends the pressure paragraph; analytics advisory capped at 2 lines    |
| `skilltrace analytics` (any)   | Prominent warning block at the top of output, before the theme data      |
| Serve `GET /analytics`         | Fills the `#analytics-advisory` slot (§5.3)                              |

`skilltrace health` is unchanged — health checks liveness, not coaching.

### 6.3 Advisory policy constraint

Advisory warnings never block a human command. Showing or hiding them
has no effect on command exit codes (other than `analytics export`
already being `MUTATING`). They are informational output only.

---

## 7. Export formats (G7)

Per [G7 — Export format specifications #125](https://github.com/earledotpy/skilltrace/issues/125):
three export formats are supported. All are driven from `derive.py`
via `export.py`.

### 7.1 Markdown

- Compact per-theme tables + advisory banner.
- Readable as plain text.
- No images or external references.

### 7.2 HTML

- Self-contained: one inline `<style>`, zero JavaScript.
- Tables + inline-SVG sparklines (reuses `sparkline.py` from §5.5).
- Advisory banner.
- Opens in any browser with no network access required.

### 7.3 JSON

Stable published contract — not a 1:1 mirror of `derive.py` internals.
Top-level structure:

```json
{
  "generated_at": "<ISO datetime>",
  "period": { "days": 30, "start": "<ISO date>", "end": "<ISO date>" },
  "group_by": "prefix",
  "state_filter": [],
  "advisory_warnings": ["..."],
  "velocity": { ... },
  "blockers": { ... },
  "reviews": { ... },
  "evidence": { ... }
}
```

- `advisory_warnings` is always present (may be `[]`).
- Theme blocks (`velocity`, `blockers`, `reviews`, `evidence`) are
  omitted only when there is literally nothing to report for that theme.
- The schema is the contract; `derive.py` internals may change without
  breaking it.

### 7.4 Audit event

Every `analytics export` invocation (CLI or Serve) appends one
`export_analytics` event to `execution/events.yaml`. The command
refuses (non-zero exit) on any `ExportData` load error.

---

## 8. Testing

*Resolved: [T-TestArch — Lock v1.6 analytics testing architecture (4-layer) #127](https://github.com/earledotpy/skilltrace/issues/127)*

### 8.1 Clock injection (D1)

Every function in `src/skilltrace/analytics/derive.py` that produces a
time-keyed output (velocity's per-week counts, review-overdue days,
evidence submission rate) takes `today: datetime.date` as a required
keyword argument. The CLI layer (the entry point of `analytics` and its
subcommands) is the only place that calls `datetime.date.today()`; the
Web layer (`GET /analytics`) likewise injects the request's resolved
date. No module-level clock, no default-to-now, no monkeypatching of
stdlib `date`. Matches T-Clock D1.

### 8.2 Four test layers (D2)

**Unit layer** (`tests/analytics/test_derive.py`, new): calls
derivation functions directly with frozen `today` and hand-built
histories; pins exact numbers computed from `policy/analytics.yaml`.
This is where the math is verifiable — the file is the executable spec
for the four themes' derivations.

**Command-output layer** (`tests/cli/test_analytics_command.py`, new):
drives `cli.run(...)` against a disposable repo seeded with
`policy/analytics.yaml`; asserts exit 0 and that the right *sections*
appear (the four theme blocks under the `analytics` umbrella, per-theme
table under each subcommand, the `[advisory] Limited data — ...` line
below threshold, the advisory warning block). *Not* the exact rendered
text — formatting is the surface's concern. Extends the existing repo
pattern (in-process `cli.run`, disposable repo, event-log read-only
assertion); no new test infrastructure.

**Export layer** (`tests/analytics/test_export.py`, new): drives
`analytics export` and asserts shape. Markdown = compact per-theme
tables + advisory banner (presence). HTML = self-contained (one inline
`<style>`, zero JS), inline-SVG sparklines present per theme, advisory
banner present (presence). JSON = exact fields pinned: `generated_at`,
`period`, `group_by`, `state`, `advisory_warnings`, and the per-theme
blocks (`velocity` / `blockers` / `reviews` / `evidence`); empty themes
omitted only when literally nothing to report. The JSON contract is
published, not derived 1:1 from `derive.py` — pinned exactly.

**Web layer** (`tests/web/test_analytics_dashboard.py`, new):
in-process HTML parse of `GET /analytics`; asserts presence of the four
`<details open>` theme cards, presence of one inline-SVG sparkline per
card, presence of the date-range preset dropdown and group-by toggle,
presence of the overdue-review banner when any review is overdue,
presence of the per-theme export forms, presence of the
`#analytics-advisory` slot when `analytics_warnings()` returns a
non-empty list. *Not* the exact rendered text.

### 8.3 Fixture style (D3)

Hand-built dicts in test functions, written into a disposable repo via
the existing `_write_yaml` helper. No new `tests/fixtures/` directory,
no checked-in YAML, no shared generator function. The math is fully
determined by `(events, today, policy_seed, filters)`; the test cases
are short enough that a generator would obscure more than it
abbreviates, and a checked-in fixture would be a second source of truth
whose drift from the policy seed wouldn't be caught. Matches T-Clock D2.

### 8.4 Assertion granularity (D4)

Unit layer: exact values computed from `policy/analytics.yaml`
thresholds (e.g. `min_sessions_for_full_data=3` → at 2 sessions,
`is_limited=True`; at 3, `is_limited=False`). CLI layer:
presence/section only (matches T-Clock D4). Export layer: Markdown and
HTML presence only; JSON fields exact (the published contract). Web
layer: presence only.

### 8.5 Coverage matrix (D5)

| Behaviour | Unit | CLI | Export (JSON exact) | Web |
|---|---|---|---|---|
| Velocity work-item + node-progress aggregation | yes | presence | yes | presence |
| Blockers grouped by track and node-ID prefix | yes | presence | yes | presence |
| Review completion rate + overdue highlighting | yes | presence + overdue banner text | yes | presence + banner |
| Evidence coverage per node + gap analysis | yes | presence | yes | presence |
| Empty state (zero events) | yes (returns empty shape) | "no data" section | empty themes omitted | "no data" section |
| Soft threshold (`min_sessions_for_full_data=3`) | yes (`is_limited` flag) | yes (`[advisory] Limited data — ...` line verbatim) | yes (`advisory_warnings` field) | yes (banner renders) |
| State filter (`--state` repeatable, OR semantics) | yes (filter applied before grouping) | yes (flag-parsing + output section) | yes (`state` field in payload) | n/a (UI filters deferred to policy) |
| Advisory integration (`analytics_warnings()`) | n/a (lives in `policy/advisory.py`) | yes (warning block; count-capped 2 bits in `today`) | yes (`advisory_warnings` field) | yes (`#analytics-advisory` slot) |
| Inline-SVG sparklines (weekly bucket) | n/a | n/a | HTML: presence | yes (one per theme card) |
| JSON contract stability | n/a | n/a | yes (exact fields) | n/a |
| HTML self-contained (one inline `<style>`, zero JS) | n/a | n/a | HTML: yes | yes (byte-level scan for `<script>`) |
| Markdown readable as plain text | n/a | n/a | Markdown: yes (no HTML in MD) | n/a |

### 8.6 Out of scope for this ticket

- Per-test-file names and exact pytest fixtures are an implementation
  detail of the per-build tickets; the layer split and behaviour-to-layer
  mapping above are the spec.
- CI configuration (new pytest markers, separate test runs, slow-test
  splits) is out of scope unless a test proves slow.
- Removing dormant keys elsewhere in `policy/*.yaml` is out of scope
  unless surfaced by a T-Build ticket.
- Web dashboard end-to-end browser tests (Playwright/Selenium) are out
  of scope; the in-process HTML parse is sufficient per the no-JS
  constraint locked in G5.

---

## 9. Exit gates

*Resolved: [T-Exit — Lock v1.6 release exit gates (commands + safety assertions + doc gates) #132](https://github.com/earledotpy/skilltrace/issues/132)*

### 9.1 Functional gates (E1)

Eleven commands, run against the seed repo in order. All must exit 0.

```
pytest tests/analytics tests/policy tests/cli tests/web
skilltrace validate policy
skilltrace analytics
skilltrace analytics velocity
skilltrace analytics blockers
skilltrace analytics reviews
skilltrace analytics evidence
skilltrace analytics export --theme velocity --format md
skilltrace analytics export --theme velocity --format html
skilltrace analytics export --theme velocity --format json
skilltrace today
```

`skilltrace health` is not gated here — the no-new-advisory-in-health
invariant is expressed as SA4 below (a structural scan), which is a
stronger gate than running a command that must not change. `GET
/analytics` is not gated here — the web layer is authoritative under
`pytest tests/web` (T-TestArch D2); a live-server gate is outside Tier
2 precedent. Export gates use velocity as the representative theme;
per-theme variation is covered exhaustively by
`tests/analytics/test_export.py`.

### 9.2 Safety assertions (E2)

Four static scans, all in `tests/release/test_v16_safety_gates.py`:

**SA1 — Event schema frozen**
Load `execution/events.yaml` (seed); compare the set of top-level keys
and per-record keys against a snapshot stored at
`tests/release/snapshots/events_v1_5.yaml`. Diff is the failure
message. Guards the R1 invariant: events are audit-only and never read
to compute state.

**SA2 — No new SQLite reader**
`Path.glob("src/**/*.py")` scanned for `sqlite3.connect` paired with
`data/skilltrace.db` outside the single whitelist entry:
`src/skilltrace/export/sqlite_export.py`. Matches Tier 2 safety
assertion #3.

**SA3 — No automated pass/master/delete**
Scan `src/**` and `tests/**` for any code path that issues a
`pass_node`, `master_node`, or `delete_record` command without an
explicit learner-flag token (`--i-am-sure` or equivalent). Matches
Tier 2 safety assertion #4.

**SA4 — Audit-only events from analytics surfaces**
Scan `src/skilltrace/analytics/**`,
`src/skilltrace/commands/analytics.py`, and `src/skilltrace/web/**`
for audit-event emission. Permitted: exactly one `export_analytics`
event, emitted only from `src/skilltrace/commands/analytics.py` (CLI
export path) and from the Serve `POST /analytics/export` route. Any
other event type, or `export_analytics` from any other call site in
these modules, is a failure. All analytics query subcommands are
READ_ONLY and emit nothing.

The advisory-cap behavioural assertion (`today` pressure paragraph
≤ 2 analytics bits) belongs in `tests/cli/test_analytics_command.py`
per T-TestArch D5 — it requires a seeded fixture and is not a static
scan.

### 9.3 Doc gates (E3)

Two checks in `tests/release/test_v16_doc_gates.py`:

**DG1 — Spec exit-gates section is filled**
`docs/spec-v1.6-event-log-analytics.md` exists, contains a `## 9`
heading, and contains every gate command from E1 and every assertion
label from E2 (SA1, SA2, SA3, SA4) as substrings. Substring match —
not a byte-identical diff — so whitespace or minor formatting variation
does not fail the gate. Fails only on a missing command or missing
assertion label.

**DG2 — CONTEXT.md contains all six §10 terms**
`CONTEXT.md` contains each of the following strings:
- `Study velocity`
- `Blockers by domain`
- `Review completion`
- `Evidence coverage`
- `Rolling window`
- `Soft data threshold`

---

## 10. Glossary additions to CONTEXT.md

The following terms are introduced by this spec and are to be added to
`CONTEXT.md` in the same change as this file lands.

**Study velocity** — a derived operational metric counting work items
logged and forward node progress (nodes moving from a lower to a higher
asserted state) within a rolling window. Measured in work items per
week. Advisory policy warns when the rate falls below the target in
`policy/analytics.yaml`. Study velocity is read-only and advisory —
it never blocks a command or alters state.

**Blockers by domain** — a derived operational metric grouping open
and recently-resolved Blockers by track or node ID prefix, over a
rolling window. Advisory policy warns when the count of active blockers
exceeds the threshold in `policy/analytics.yaml`. Blockers by domain
is read-only and advisory — it never alters a Blocker record or state.

**Review completion** — a derived operational metric measuring the
ratio of completed reviews to scheduled-plus-overdue reviews, with
prominent overdue highlighting, over a rolling window. Advisory policy
warns when the completion ratio falls below the target in
`policy/analytics.yaml`. Review completion is read-only and advisory —
it never schedules, complete, or cancel a review.

**Evidence coverage** — a derived operational metric reporting
per-node evidence counts, gap analysis (required specs with zero
accepted records), and submission rate, over a rolling window.
Advisory policy warns when the coverage ratio falls below the target
in `policy/analytics.yaml`. Evidence coverage is read-only and
advisory — it never submits or alters an evidence record.

**Rolling window** — the time span a derivation or analytics command
covers, counted backwards from today. The default is controlled by
`default_window_days` in `policy/analytics.yaml` and may be overridden
per-invocation with `--days`. A rolling window is advisory context for
a derivation; it never affects node states, evidence records, or
progress.

**Soft data threshold** — the minimum number of sessions in the rolling
window (`min_sessions_for_full_data` in `policy/analytics.yaml`) below
which an analytics command prefixes its output with a limited-data
advisory. The threshold is a data-quality warning only; it never blocks
output or changes exit codes.

---

## 11. Invariants and constraints preserved

- Hard boundaries per `AGENTS.md` and `AGENTS.md` Safety rules are
  unchanged. `pass_node`, `master_node`, `delete_record` remain
  manual-only; asserted progress never moves backward; AI review is
  never an acceptance authority.
- The event log (`execution/events.yaml`) is never read to compute
  state; analytics derives from the primary execution YAML files only
  (R1). No event schema change.
- `derive.py` is pure: no file I/O, no wall-clock calls. The CLI and
  Serve layers are the sole `datetime.date.today()` call sites.
- Exports are disposable and gitignored; the engine never reads them
  back (per Export definition in `CONTEXT.md`).
- Advisory warnings never block a human command.
- v1's five layers (ADR 0002) are preserved. v1.6 adds code in the
  `policy` and `execution` layers only; no new layer, no revived
  `interface/` scaffold.
- `policy/automation_boundary.yaml` is unchanged; analytics introduces
  no automation.
- The `analytics export` audit event is `MUTATING`; all analytics
  query commands are `READ_ONLY`.

---

## 12. Acceptance — this map is done when

- [ ] All nine wayfinder tickets on map #118 are closed (R1, R2, G3,
      G4, G5, G6, G7, T-TestArch #127, T-Exit #132, **T-Spec #126 —
      this spec**).
- [ ] `docs/spec-v1.6-event-log-analytics.md` (this file) is
      referenced from map #118's `## Decisions so far`.
- [ ] §8 (Testing) is filled from T-TestArch #127's resolution.
- [ ] §9 (Exit gates) is filled from T-Exit #132's resolution.
- [ ] `CONTEXT.md` contains the six terms in §10.
- [ ] No product or architecture decision remains that would block
      the exit-gate commands in §9.
- [ ] Map `## Not yet specified` is empty.

---

## References

`CONTEXT.md` (especially **Event log**, **Export**, **Serve**,
**Advisory policy**, **Hard boundary**, **Session**, **SessionWork**,
**Blocker**, **Review**, **EvidenceRecord**); `AGENTS.md` (Safety
rules; Current phase); `docs/POST_V1_ROADMAP.md` (v1.6 slot);
`docs/adr/0001` … `0006`; `docs/spec-tier2-retention-analytics.md`
(Tier 2 precedent for testing split, exit-gate shape, and spec
structure); `src/skilltrace/policy/loading.py` `POLICY_FILES`;
`src/skilltrace/policy/advisory.py` (advisory integration extension
point); `src/skilltrace/web/views.py` (Serve patterns);
`src/skilltrace/commands/` (CLI registration pattern);
`policy/analytics.yaml` (seed values); `execution/session_work.yaml`,
`execution/reviews.yaml`, `execution/blockers.yaml`,
`evidence/*.yaml`, `graph/state.yaml` (data sources per R1);
`tests/release/` (safety-gate suite location per Tier 2 precedent).
