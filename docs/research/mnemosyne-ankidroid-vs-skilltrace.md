# Research note: Mnemosyne and AnkiDroid compared with SkillTrace

**Research date:** 2026-09-03  
**Scope:** `mnemosyne-proj/mnemosyne` at `ff4f61e84bea0d6928c29b7798f0f88b90938a0a`
and `ankidroid/Anki-Android` at
`789816b6e4119dc601486f37cc9b42f879f550a1`. SkillTrace comparisons cite
repository `HEAD` at `61f54164a50ed76b2481f270cb6abc2841e26265`.

- [mnemosyne-proj/mnemosyne@ff4f61e](https://github.com/mnemosyne-proj/mnemosyne/tree/ff4f61e84bea0d6928c29b7798f0f88b90938a0a)
- [ankidroid/Anki-Android@789816b6](https://github.com/ankidroid/Anki-Android/tree/789816b6e4119dc601486f37cc9b42f879f550a1)

**Method:** Primary source code and tests were read from the pinned upstream
commits. SkillTrace's glossary, roadmap, ADRs, implementation, and tests were
used for the baseline. Upstream citations are commit-pinned GitHub source
links; local citations use repository paths and exact line ranges.

This is a source comparison, not a proposal to import a card scheduler into
SkillTrace. Existing uncommitted changes were left untouched.

## Executive findings

1. **The queue contracts solve different problems.** Mnemosyne owns a mutable,
   staged card queue with explicit invalidation, prefetch, sibling-card
   suppression, grading, and counts. AnkiDroid's Kotlin layer exposes a
   backend-owned queued-card state and constructs answers for that backend.
   SkillTrace has no review queue: `next` is a pure, deterministic ranking of
   `available` and `active` skill nodes, while `sync` recomputes only derived
   readiness.
2. **SkillTrace deliberately keeps the scheduler seam shallow.** The upstream
   systems need a card-review controller and rendering contract. SkillTrace
   separates command handlers, guarded progress writes, execution records,
   pure recommendation/analytics functions, and one dispatcher. That matches
   the five-layer architecture and ADR 0002's removal of a speculative
   interface registry.
3. **Statistics are different in kind.** Mnemosyne and AnkiDroid report card,
   repetition, deck, and schedule data. SkillTrace derives velocity, blockers,
   retention reviews, and evidence coverage from local YAML-backed records,
   returning typed view models shared by CLI and web surfaces.
4. **Sync is the largest boundary difference.** Both upstream projects have
   network synchronization, session/conflict or full-upload/download semantics,
   media handling, backups/locking, and queue refresh. SkillTrace's `sync` is a
   local readiness recomputation and its event log is audit-only.
5. **Instrumentation follows product boundaries.** Mnemosyne can persist
   science logs and upload them; AnkiDroid combines crash reporting, logging,
   analytics, and backend change observers. SkillTrace records local command
   audit events and automation refusals, not telemetry.
6. **Tests protect the respective seams.** Upstream suites exercise detailed
   scheduling transitions, UI/controller behavior, sync, and instrumentation.
   SkillTrace tests protect derived/asserted state, deterministic ranking, one
   write path, audit semantics, and web/CLI equivalence.

## Efficiency advantages and safe adoptions

“More efficient” here means better throughput or separation at the product
boundary each project actually owns, not a benchmark claim. Neither upstream
queue should replace SkillTrace's graph/evidence model.

| Project | More efficient at | Adoptable without redesign |
| --- | --- | --- |
| Mnemosyne | High-throughput review sessions: staged queues, bounded filling, sister-card suppression, prefetch safety, and explicit queue invalidation keep a card UI responsive while preserving scheduling semantics ([scheduler contract](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/scheduler.py#L65-L88), [queue stages](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L155-L319)) | If SkillTrace adds a retention/execution queue, borrow explicit invalidation, bounded candidate batches, no-sister/duplicate rules where the domain requires them, and tests for queue/count transitions. Keep recommendation pure and keep progress writes guarded. |
| AnkiDroid | Concurrent client/backend coordination: serialized collection access, coroutine-safe reviewer actions, backend-derived counts, and post-answer state refresh prevent UI races ([collection queue contract](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/anki-common/src/main/kotlin/com/ichi2/anki/CollectionManager.kt#L77-L145), [reviewer answer/refresh](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/ui/windows/reviewer/ReviewerViewModel.kt#L504-L588)) | Preserve the shared CLI/web dispatcher, but apply the same principle to any future concurrent surface: serialize mutating command execution and reload a fresh joined context after writes. Use typed result/view models, not a scheduler facade. |
| SkillTrace | Explainable graph decisions and cross-surface consistency: pure recommendation/analytics, YAML source of truth, guarded state transitions, and one command path avoid synchronization and authority duplication ([recommendation](src/skilltrace/graph/recommendation.py:44-57), [dispatcher](src/skilltrace/dispatch.py:127-154), [analytics models](src/skilltrace/analytics/models.py:33-57)) | This is the safe baseline to retain. Adopt upstream contract-testing discipline only at new seams—especially invalidation, refresh, cancellation, and count semantics—without importing card scheduling or remote sync into existing layers. |

## 1. Queue contracts and scheduling

### Mnemosyne: scheduler-owned staged queue

Mnemosyne's abstract `Scheduler` requires reset and initial grading, sister-card
avoidance, queue rebuild and membership/removal operations, `next_card`,
prefetch permission, answer grading, scheduled/non-memorised/active counts,
schedule projections, and interval formatting. Queue invalidation is explicit:
controllers can rebuild after a GUI mutation and decide whether the current card
remains queued. See the [scheduler contract](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/scheduler.py#L17-L119), especially the [queue operations](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/scheduler.py#L65-L88).

`SM2Mnemosyne` keeps card IDs and fact IDs separately: fact IDs prevent sister
cards from appearing together, while the last-card ID prevents immediate
repetition. Its queue stages due/overdue retention cards, relearning cards,
seen-but-not-yet-memorised cards, unseen cards, and explicitly requested
learn-ahead cards. It fetches bounded batches, applies a non-memorised hand
limit, and advances stages as queues fill or empty. See [reset and card/fact
state](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L63-L94), [queue stages one and two](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L155-L223), and [stages three through five](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L225-L319).

Prefetch has a safety contract rather than being unconditional: it is denied
when the next queued card is the card being graded and otherwise requires at
least three queued cards. Grading carries timing (`LATE`, `EARLY`, `ON TIME`),
acquisition/retention phases, lapse handling, interval noise, sister-card
avoidance, hooks, and repetition logging. See [prefetch](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L354-L369), [grading](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L377-L445), and [retention grading](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py#L445-L518).

### AnkiDroid: backend-owned queue facade

AnkiDroid's Kotlin `Scheduler` is a facade over the Rust/backend scheduler.
`CurrentQueueState` carries the top card, queue kind (`NEW`, `LRN`, `REV`),
scheduling states and context, new/learning/review counts, timebox status,
learn-ahead seconds, and custom scheduling JavaScript. The facade fetches
queued cards with `getQueuedCards(fetchLimit = 1, intradayLearningOnly = false)`
and creates a backend `CardAnswer` containing card ID, current/new states,
rating, timestamp, and elapsed time. See [CurrentQueueState and answer
construction](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/main/java/com/ichi2/anki/libanki/sched/Scheduler.kt#L73-L172).

Counts are backend-derived and fetching does not itself decrement them. The
tests assert new-to-learning transitions, stable counts after fetching, and
count changes after answering. See [scheduler transition tests](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/test/java/com/ichi2/anki/libanki/SchedulerTest.kt#L65-L115) and [queue-count tests](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/test/java/com/ichi2/anki/libanki/SchedulerTest.kt#L932-L1004). Collection configuration selects scheduler version 1 (`DummyScheduler`) or version 2 (the normal scheduler), enables matching backend configuration, and reloads after full sync. See [scheduler loading](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/main/java/com/ichi2/anki/libanki/Collection.kt#L194-L247).

### SkillTrace: pure recommendation, not a queue

SkillTrace's nearest analogue is `recommend`: it accepts loaded nodes, edges,
progress, policy weights, session minutes, and optional remediation/blocker
facts, then considers only `available` and `active` nodes. It calculates a score
from track priority, downstream leverage, session fit, active continuation,
remediation pressure, and blocker penalty; ties break by node ID. It returns
ranked value objects and does not consume or mutate a queue. See
`src/skilltrace/graph/recommendation.py:44-57, 204-260, 272-276`.

Readiness is separate: an active hard-prerequisite edge locks a target until its
source is `passed` or `mastered`; soft and remediation edges do not lock. Sync
does one order-independent derivation pass and skips asserted states. See
`src/skilltrace/graph/readiness.py:82-115` and
`src/skilltrace/commands/sync.py:1-63`.

**Implication.** Importing upstream concepts such as `next_card`, prefetch,
answer-driven interval calculation, or a scheduler-owned mutable queue would
cross SkillTrace's graph/evidence/execution boundary. If a future retention
overlay needs a queue, it should be an explicitly scoped execution/policy
feature rather than changing `sync` or turning recommendation into a mutable
cursor.

## 2. Scheduler interfaces and client/UI boundaries

### Mnemosyne: controller plus plugin/widget contracts

`ReviewController` abstracts a review widget and owns the current card, widget,
learn-ahead mode, render-chain choice, review state, and counter contract.
`SM2Controller` resets the scheduler, selects a question, reveals an answer,
grades it, and reloads counters. Its reset path can rebuild a queue while
preserving the current card if it remains valid. See [ReviewController](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/review_controller.py#L12-L84), [SM2 controller lifecycle](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/review_controllers/SM2_controller.py#L43-L177), and [current-card preservation](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/review_controllers/SM2_controller.py#L55-L85).

The component system is a plugin/dependency boundary. Components declare type,
usage, and lifecycle; `ComponentManager` supports multiple active components
for filters/hooks and last-registered-wins selection for single-active
components such as schedulers and databases. The review widget contract
separates question/answer content, answer buttons, counters, media, and redraw.
See [component lifecycle](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/component.py#L6-L94), [component selection](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/component_manager.py#L5-L48), [component lookup](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/component_manager.py#L82-L137), and [review widget](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/ui_components/review_widget.py#L8-L103).

### AnkiDroid: serialized collection access plus ViewModel flows

AnkiDroid serializes collection access through `CollectionManager.withQueue` and
`withCol`. The queue uses an IO dispatcher and forbids suspendable blocks so
collection requests cannot interleave. The reviewer `ViewModel` exposes queue
state, counts, feedback, navigation, flags, timebox events, and card updates as
flows, and serializes user actions with a coroutine mutex. See [collection
queue contract](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/anki-common/src/main/kotlin/com/ichi2/anki/CollectionManager.kt#L77-L145) and [reviewer state/flows](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/ui/windows/reviewer/ReviewerViewModel.kt#L73-L140).

The answer path constructs a backend answer, executes it through an undoable
operation, emits feedback/leeches, and reloads current queue state. Refresh then
handles no-more-cards/timebox signals, emits the card update before showing the
question, reloads media, updates bury/suspend availability, and emits counts.
See [answer flow](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/ui/windows/reviewer/ReviewerViewModel.kt#L504-L528) and [queue refresh](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/ui/windows/reviewer/ReviewerViewModel.kt#L560-L588).

### SkillTrace: shared command seam, thin presentation

SkillTrace has no review-controller abstraction. Progress writes are guarded by
`write_readiness` and `write_asserted`; command handlers report touched records;
the dispatcher owns automation checks and audit logging. The store refuses
asserted-state demotions, while readiness sync refuses to touch asserted
progress. See `src/skilltrace/graph/state.py:110-157` and
`src/skilltrace/dispatch.py:127-154`.

The web server reloads a fresh joined context for each request and routes GET and
POST operations through server-rendered handlers. Browser mutations nest-dispatch
the same registry used by the CLI with `Context.source="web"`, preserving
command classification, refusal output, and event semantics. See
`src/skilltrace/web/handler.py:1-5, 57-151` and
`src/skilltrace/web/views.py:254-276`.

This boundary is intentionally smaller than the upstream card UI contracts.
ADR 0002 removed the speculative YAML interface layer, and ADR 0006 chose a
stdlib-only, loopback, server-rendered shell. The practical invariant is not
“the UI implements a scheduler”; it is “all writes use the same explicit
command path.” See `docs/adr/0002-cut-interface-layer-from-v1.md:15-32` and
`docs/adr/0006-stdlib-only-serve-shell.md:15-49`.

## 3. Statistics and derived views

### Mnemosyne and AnkiDroid

Mnemosyne's statistics contract is page/widget based: a statistics page computes
data for a selected variant and a separately registered widget displays it.
Schedule variants call the scheduler's scheduled-card projection per day;
retention variants call the database's retention score per day. See
[statistics page contract](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/statistics_page.py#L6-L65), [schedule statistics](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/statistics_pages/schedule.py#L9-L66), and [retention statistics](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/statistics_pages/retention_score.py#L9-L45). Its SQLite mixin derives scheduled, non-memorised, and active counts from card tables. See [SQLite statistics](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/databases/SQLite_statistics.py#L14-L43).

AnkiDroid exposes backend card statistics and review logs through `Collection`;
the statistics screen owns deck selection and renders a WebView page with a deck
search expression. See [collection statistics bridge](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/main/java/com/ichi2/anki/libanki/Collection.kt#L1121-L1136) and [statistics screen](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/pages/Statistics.kt#L27-L119).

### SkillTrace analytics

SkillTrace analytics are clock-injected derivations over sessions, session work,
blockers, reviews, evidence, nodes, and progress. Review analytics count all
scheduled reviews (including overdue), count completed reviews in the selected
window, calculate a completion rate, and sort overdue rows first. See
`src/skilltrace/analytics/derive.py:274-338`.

The typed models are the shared contract for derivation, CLI, export, and web:
`VelocityResult`, `ReviewsResult`, and `AnalyticsView` carry plain values and an
explicit `is_limited` flag when the session sample is below the configured
threshold. See `src/skilltrace/analytics/models.py:33-57, 93-112, 138-150` and
`src/skilltrace/analytics/derive.py:436-513`.

**Implication.** Upstream statistics are scheduler/database projections; the
SkillTrace equivalent should continue to report domain and operational facts,
not manufacture card-style counts. A retention overlay can add another pure
derivation without making analytics an authority over node state.

## 4. Sync and persistence boundaries

### Mnemosyne

Mnemosyne sync is a network collection protocol. The client can back up local
data, detect edited/dynamic media, authenticate and negotiate capabilities,
perform initial download/upload or incremental log transfer, synchronize media,
resolve conflicts, and restore backups after serious failures. See [client sync
sequence](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/openSM2sync/client.py#L27-L58) and [workflow](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/openSM2sync/client.py#L141-L243).

The server creates a session backup, keeps client logs for conflict resolution,
and restores the backup when a session terminates abnormally. It deliberately
uses one WSGI thread because subsequent requests must not concurrently access
SQLite, and it tracks session tokens and expiry. See [server session](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/openSM2sync/server.py#L30-L70), [serialization](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/openSM2sync/server.py#L78-L105), and [session lifecycle](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/openSM2sync/server.py#L173-L235).

SQLite sync tracks per-partner log watermarks, full-reset state, post-watermark
log entries, and an option to exclude repetition events for clients that do not
retain old repetitions. See [partner state and log selection](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/databases/SQLite_sync.py#L53-L67) and [watermarks](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/databases/SQLite_sync.py#L97-L166).

### AnkiDroid

AnkiDroid distinguishes normal sync, full download, full upload, and full
conflict resolution. Successful normal sync can reload the scheduler because
the scheduler version may change. See [sync routing](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/Sync.kt#L144-L215).

`SyncWorker` runs collection sync in a WorkManager coroutine. Collection access
is blocked during collection synchronization; media synchronization is a
separate worker. The worker monitors backend progress, supports cancellation via
backend abort calls, displays foreground notifications, handles user-input
one-way-sync cases, and reloads the scheduler after no-change completion. See
[worker contract](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/worker/SyncWorker.kt#L57-L69) and [worker execution](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/worker/SyncWorker.kt#L83-L185).

### SkillTrace

SkillTrace `sync` loads nodes, edges, and `graph/state.yaml`, calls
`sync_readiness`, saves only when derived readiness changed, and reports changed
node IDs. It does not contact a server, merge histories, handle accounts,
transfer media, maintain partner watermarks, or restore a remote-session backup.
See `src/skilltrace/commands/sync.py:1-63` and
`docs/adr/0001-separate-progress-store.md:15-33`.

The event log is also not a synchronization source. It is append-only audit
inspection: a successful mutating command gets one event with command, args, and
`records_touched`; events are never read to compute state. See
`src/skilltrace/events.py:1-13, 24-60` and
`src/skilltrace/dispatch.py:127-154`.

**Implication.** “Sync” is a false friend across these projects. SkillTrace's
name should remain attached to local derived readiness unless a future
multi-device design explicitly introduces a different protocol, source of
truth, merge model, and concurrency contract.

## 5. Instrumentation and observability

Mnemosyne's logger covers lifecycle events, database load/save counts,
card/fact/tag/media changes, repetitions, setting edits, and science-log
dumping. SQLite logging persists lifecycle and count information in a `log`
table. When enabled, a background uploader sends compressed science-log history
to a configured server endpoint. See [logger interface](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/logger.py#L11-L81), [logger operations](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/logger.py#L140-L204), [SQLite logging](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/databases/SQLite_logging.py#L17-L58), and [science-log uploader](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/log_uploader.py#L16-L94).

AnkiDroid initializes ACRA crash reporting, Timber logging, production crash
reporting, LeakCanary configuration, analytics, and throwable filtering at
application startup. Its analytics allowlist covers review preferences,
learning-ahead/timebox limits, sync and backup settings, answer commands,
reviewer controls, and study-screen preferences. Backend change notifications
refresh deck-picker and card-analysis surfaces. See [application instrumentation](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/AnkiDroidApp.kt#L120-L166), [analytics allowlist](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/analytics/AnalyticsConstants.kt#L16-L39), [review/control analytics](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/analytics/AnalyticsConstants.kt#L62-L115), and [change observer](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/main/java/com/ichi2/anki/AnkiDroidApp.kt#L470-L489).

SkillTrace's instrumentation is local audit rather than product telemetry. The
dispatcher refuses forbidden automation before handlers run; successful
mutating commands append exactly one event, while read-only, failed, and
refused commands append none. See `src/skilltrace/dispatch.py:127-154`,
`src/skilltrace/events.py:38-60`, and `src/skilltrace/automation.py:24-27, 77-113`.

## 6. Tests and verification style

Mnemosyne's scheduler tests cover queue ordering/stages, learn-ahead, grade-0
duplicate suppression, sister-card separation, interval formatting, prefetch,
stuck/filling behavior, retention, and active counts. Review-controller tests
cover reset, counters, current-card preservation, and grading. Statistics tests
assert exact schedule/retention/page variants and widget resolution. See
[scheduler tests](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/tests/test_scheduler.py#L81-L132), [prefetch and queue tests](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/tests/test_scheduler.py#L596-L649), [queue filling](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/tests/test_scheduler.py#L672-L769), [review controller](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/tests/test_review_controller.py#L28-L179), and [statistics](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/tests/test_statistics.py#L19-L175).

AnkiDroid's `SchedulerTest` covers new, learning, relearning, review, lapse,
bury/suspend, filtered-deck, preview, counts, timing, deck-tree, reorder, and
rescheduling cases. Reviewer instrumentation tests use Espresso, lifecycle
rules, permissions, retries, and custom scheduling JavaScript; they verify
custom mutations to ease/interval/data and that runtime scheduling errors do
not hide answer controls. See [scheduler test index and transitions](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/libanki/src/test/java/com/ichi2/anki/libanki/SchedulerTest.kt#L49-L115) and [reviewer instrumentation](https://github.com/ankidroid/Anki-Android/blob/789816b6e4119dc601486f37cc9b42f879f550a1/AnkiDroid/src/androidTest/java/com/ichi2/anki/ReviewerTest.kt#L42-L136).

SkillTrace tests instead protect architectural invariants: readiness derivation
and asserted-state preservation (`tests/graph/test_readiness.py:35-155`),
deterministic recommendation and locked explanations
(`tests/graph/test_recommendation.py:1-180`), one-event/no-event dispatcher
behavior (`tests/cli/test_dispatcher.py:26-121`), and browser writes through
the shared command path (`tests/web/test_writes.py:1-150`). The result is a
smaller but more explicit verification surface: pure functions, guarded state
transitions, one write path, and audit semantics rather than card-timing
behavior.

## Comparison matrix

| Concern | Mnemosyne | AnkiDroid | SkillTrace |
| --- | --- | --- | --- |
| Queue ownership | Python scheduler owns mutable staged card-ID queue | Rust/backend owns queued cards; Kotlin exposes state | No persistent review queue; pure ranked node recommendations |
| Queue invalidation | Explicit rebuild, membership, and removal methods | Re-fetch backend `CurrentQueueState` after operations | Recompute readiness from graph and progress store |
| Scheduling interface | Abstract scheduler with `next_card`, grading, counts, prefetch | Kotlin facade with backend `CardAnswer` and queued-card state | No scheduler interface; graph/evidence/execution/policy contracts |
| UI seam | Component manager, review controller, lazy widgets | Collection serialization, coroutines, ViewModel/flows, WebView | Thin CLI/web presentation over shared commands and derivations |
| Statistics | Page/widget plugins and card/database repetition statistics | Backend card stats plus WebView statistics page | Pure analytics over sessions, blockers, reviews, evidence, and progress |
| Sync | Network collection/log/media sync, backups, conflicts, serialized SQLite | WorkManager sync, backend locking, full/normal sync, separate media worker | Local readiness sync only |
| Instrumentation | SQLite log plus optional science-log upload | Timber, ACRA, analytics, change subscribers | Local audit events; no telemetry path |
| Tests | Queue timing, scheduler stages, controller, full sync scenarios | Scheduler transitions, Espresso reviewer, custom JS, sync policy/media | Pure derivation, command, web, audit, and automation invariants |

## Design conclusions for SkillTrace

- Keep recommendation pure and explainable; do not make it a scheduler cursor.
- Keep `sync` limited to derived `locked`/`available` readiness. A remote sync
  protocol would require a separate architectural decision, not an expanded
  interpretation of the current command.
- Preserve the one-write-path rule for future UI surfaces: browser actions
  should continue to dispatch the same commands and produce the same refusal
  and audit behavior as CLI actions.
- Extend analytics with pure typed projections over canonical records. Do not
  make analytics or event replay an alternative state store.
- Borrow upstream test discipline selectively: if a future retention queue is
  added, test invalidation, count semantics, and post-action refresh as explicit
  contracts; do not import card-specific semantics without a SkillTrace domain
  need.

## Scope limits

- AnkiDroid's Kotlin scheduler file establishes the facade/backend contract; the
  detailed queue algorithm lives below it and was not inferred from Kotlin alone.
- AnkiDroid's inspected statistics sources establish collection APIs and deck
  selection/WebView integration, not every backend chart computation.
- The Mnemosyne statistics, logging, and sync files are SQLite mixins; their
  behavior should not be generalized to every possible database backend.
- Scoped AnkiDroid discovery found direct tests for scheduler, metered-sync
  policy, media-worker behavior, and reviewer instrumentation; absence of a
  single end-to-end `SyncWorkerTest` file is not evidence that no indirect sync
  coverage exists.
