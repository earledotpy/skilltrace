# Fixture clock

How a fixture or simulated-day run dates the records the engine writes.
Closes the fortnight hazard where a simulation could read "today" from a
frozen clock but every mutating command still stamped its records from the
wall clock (issue #308, follow-up to map #289 and P-StudyFortnight #292,
hazard H1).

## Contract

One funnel: `Context.clock`, injected through `cli.run(..., clock=...)` (and
`Context(root=..., args=..., clock=...)` for nest-dispatched commands).

- **Read side** — `execution.overdue.utc_today(clock=...)` is the single
  date source; every derived "today" (today, report, listings, suggest,
  retention, analytics, health liveness, replace-resource) threads the same
  clock.
- **Write side** — `commands._common.now_iso(clock=...)` stamps
  engine-written records, `resources.verification.today_iso(clock=...)`
  stamps the dated resource facts, and the dispatcher stamps the single
  audit event with the same clock.
- `clock=None` everywhere means the wall clock, so production behavior is
  unchanged; only an injected clock changes what gets written.

## Surfaces that honor the injected clock

| Surface | Stamped field(s) |
| --- | --- |
| `start` / `work` / `session close` | `started_at`, `ended_at`, work `created_at`, `active` transition |
| `sync` | readiness `changed_at` for flipped nodes |
| `evidence submit` | record `created_at` (and the gate receipt's frozen inputs) |
| `attempt record` | attempt `created_at` |
| `pass` / `master` | `passed`/`mastered` transition, auto-scheduled review `created_at` + `scheduled_for` |
| `review schedule/complete/cancel` | `created_at`, `completed_at`, `cancelled_at` |
| `blocker create/resolve`, `remediation create/complete` | `created_at`, `resolved_at`, `completed_at` |
| `verify-resource`, `check-resources --stale-only` | `last_verified` / broken-marker `date` |
| every mutating command | the audit event `timestamp` |
| `backup` | archive filename stamp |
| `export markdown` / `export html` / `analytics export` | snapshot `generated` stamp |
| read surfaces (`today`, `next`, `report`, `suggest`, `retention status`, `health`, `analytics`) | derived "today", overdue, staleness, retention dates |

## Not on the fixture clock

- **`skilltrace ui` (serve)** — the browser layer has no clock context, so it
  reads the wall clock. A page-visible simulated day is not supported; use
  the CLI for simulated runs.
- **`export sqlite` `retention_memory.computed_at`** — a disposable mirror
  stamp (the mirror is never read back by the engine). The derived `today`
  that feeds the retention rows *is* threaded, so the row dates follow the
  simulation.

## Safety

Simulated time never touches real learner records: a simulated run targets a
throwaway fixture root (a copy of the data layers), and no code path
redirects a write back to the live repo. `tests/cli/test_fixture_clock.py`
pins both halves — a full day-by-day simulated sequence whose records all
carry simulated timestamps, and a byte-identity check that the live repo's
progress store, sessions, events, and evidence records are unchanged after a
simulated run.
