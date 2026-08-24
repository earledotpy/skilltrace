# Spec — Tier 1 Web UI and Dashboard (serve + static report)

**Status:** locked hand-off (map #62) — no open product or architecture decisions block v1.1 build.
**Target:** `v1.1` nearest post-v1 (`docs/POST_V1_BACKLOG.md:7-14`, `docs/skilltrace-application-roadmap.md:596-598`); `v1.4` reserved for polish.
**Map:** [#62 Map — Tier 1 Web UI and Dashboard (serve + static report)](https://github.com/earledotpy/skilltrace/issues/62)
**Decisions:** [R1#63](https://github.com/earledotpy/skilltrace/issues/63) · [G1#64](https://github.com/earledotpy/skilltrace/issues/64) · [P1#65](https://github.com/earledotpy/skilltrace/issues/65) · [G2#66](https://github.com/earledotpy/skilltrace/issues/66) · [G3#67](https://github.com/earledotpy/skilltrace/issues/67) · [G4#68](https://github.com/earledotpy/skilltrace/issues/68) · [G5#69](https://github.com/earledotpy/skilltrace/issues/69) + report-curation gist (joint G1/G4/G5). ADR 0002, ADR 0006 (`docs/adr/0006-stdlib-only-serve-shell.md:1`), `CONTEXT.md:296` Serve / `CONTEXT.md:274` Export.
**Prototype:** `prototype/p1-daily-home-view.html` (3 variants, `@02af61e`) + `prototype/p1-modals.html` (pass/master/start confirms).
**Build plan:** 5 `wayfinder:task` children of #62 — `T1 Engine seam → T2 Serve shell → T3 Daily views → T4 Safety modals + daily writes → T5 Export html`.

> Hand-off gate (from map `Destination`): a builder can implement Tier 1 without reopening a product or arch question. This doc + the prototype sketches + the 5 ticketed slices satisfy that gate. All terms per `CONTEXT.md`; schema frozen per `docs/SCHEMA_REFERENCE.md:1`.

---

## Checklist — what is locked

### A. MVP boundary (G1)

- [ ] **Tier 1 = live localhost serve + derived static report.** Live server is primary daily UI (`st ui` / `skilltrace serve`); static report is disposable `data/export.html` via strict seam (not a second lifecycle, not extra deps). Both `localhost` only, single-learner, files-are-truth (`docs/SAFETY_BOUNDARIES.md:1`, `CONTEXT.md:296`).
- [ ] **MVP is daily loop only.** IN: `today` + `next --minutes --limit --show-locked` + `node <id>` detail + `health` roll-up + derived eligibility display (`src/skilltrace/evidence/eligibility.py:1` / `src/skilltrace/policy/mastery.py:66` via `JoinedView` lenient) + asserted writes `pass`/`master` behind explicit confirmation modals (`src/skilltrace/evidence/passing.py:36` → `src/skilltrace/graph/state.py:118` forward-only). Hand-off targets `v1.1`; `v1.4` is polish. See `G1#64`.
- [ ] **Deferred (remain CLI-available, become immediate follow-on slices or v1.5+):** `start`/`work`/`session close` (single-open invariant), `blocker create/resolve`, `remediation create/complete`, `review schedule/complete/cancel`, `evidence submit`/`attempt record` (frozen-at-submission + supersede `docs/adr/0003-acceptance-frozen-at-submission.md:1`), drill-down `report progress/blockers/reviews/evidence/resources`, `resources --node-id` browser + `verify-resource`/`resource-report`, `export markdown/sqlite` + `backup` are **not** MVP live UI — except the 5 writes promoted to first-class browser writes in `G5#69` (see §F). Rationale: only daily loop is every-study-day.

### B. Safety & hard boundaries (G2)

- [ ] **One write path.** Browser mutations never call `src/skilltrace/graph/state.py:118` `write_asserted` directly. A confirmed action builds `Context(root, Namespace(node_id=…))` and calls `dispatch(REGISTRY.get("pass"|"master"|…), ctx)` in-process — same handlers (`src/skilltrace/commands/pass_.py`, `src/skilltrace/commands/master.py`), same guarded writer, same sole-caller invariant, same `src/skilltrace/automation.py:12` + `src/skilltrace/dispatch.py:116` boundary check, same single audit event. Handler stdout is captured/discarded; `CommandResult.exit_code` + `records_touched` is the contract. Freshness is structural: every POST re-runs `plan_pass`/`plan_master` against freshly loaded truth, so a stale modal can never assert what eligibility no longer supports.
- [ ] **Pass modal (server-rendered, per-request `JoinedView` lenient):** node title+id+current state; per-required-spec accepted/minimum counts; gate authority (objective/manual); `passed_but_not_backed` warning when present; auto-review note ("confirming schedules reviews per `policy/cadence.py`"); explicit Confirm button. No pre-disabled state — current eligibility renders as advisory text beside the button; domain refusal on click is truth (`[warning]`/`[error]` per `src/skilltrace/render.py:1`).
- [ ] **Master modal is two-step.** Step 1 shows mastery facts (passed date, satisfactory spaced review, spacing policy value `policy/mastery.py:66`); step 2 is explicit "this is permanent" confirm. Mastered never demotes (`AGENTS.md: Safety rules`, `CONTEXT.md:40`).
- [ ] **Exit-code → browser mapping:** `0` asserted → close modal, refresh view, success line + auto-scheduled review ids; `2` domain refusal (locked/ineligible/backward) → modal stays open, refusal text verbatim inline; `1` operational failure → dismiss modal, page-level banner suggesting `skilltrace validate`.
- [ ] **Locked & advisory rendering.** Locked nodes rendered, never hidden: locked pill + unsatisfied `hard_prerequisite` list wherever node appears; `Start`/`Pass` visible but domain-refused on click ("locked is the only wall"). Recommendation lists keep opt-in "show locked" toggle (`next --show-locked` parity). Advisory policies (workload, cadence, remediation pressure, track weights) are passive UI only — banners/pills/pressure strip/"Why this?" collapsibles — never disable a control or refuse a submit; refusals come only from hard checks (`CONTEXT.md:107` Advisory policy).
- [ ] **Event provenance.** Web-initiated mutations append under same canonical `_command_name` (`pass`, `master`, `start`, …) plus `source: "web"` in event args (rides in `Context`, not `argv`, so `dispatch._event_args` underscore exclusion untouched). Events remain audit-only, never read to compute state. No delete affordance at all in Tier 1 (`delete_record` moot; supersession CLI-only until G5 affordances).
- [ ] **No pending acceptance queue, no generic `PATCH /state`.** Pass/master are the only hard-boundary writes; `active` via `start` is forward-only but evidentially weightless.

### C. Serve topology & stack (G3 + ADR 0006)

- [ ] **Stdlib-only shell.** `http.server.ThreadingHTTPServer` behind thin `BaseHTTPRequestHandler` router, ~150–250 lines owned glue (routing, query/form parsing, HTML assembly). Zero new deps — `pyproject.toml: requires-python >=3.14`, `dependencies = ["PyYAML>=6.0"]` untouched. Rejected: Flask (~7 transitive), FastAPI+uvicorn (async overkill), serving disposable exports (`data/export.html`/`data/skilltrace.db` never read back per `src/skilltrace/export_data.py:1`).
- [ ] **Read seam — lenient, fresh per request.** Every `GET` calls `load_context_lenient(root)` (`src/skilltrace/context.py:260`) anew: no cache, no file-watch. CLI/editor mutations appear on next refresh. Strict entrypoint reserved for `export html` (`src/skilltrace/context.py:200`). Never read `data/*.db`/`data/export.md`.
- [ ] **Write seam — G2 constraint realized.** `serve` itself is `READ_ONLY` (appends no event); browser writes nest-dispatch through registry per §B.
- [ ] **MVP route table (6 + 4 extended via G5):**
  ```
  GET  /                              today dashboard (today brief + top rec + health strip + pressure excerpts)
  GET  /next?minutes=&limit=&locked=  recommendation list (mirrors CLI flags)
  GET  /nodes/{id}                    node detail (Mentor 7-part shape + eligibility)
  GET  /health                        health roll-up (5 validators + liveness)
  GET  /nodes/{id}/pass       → POST /nodes/{id}/pass                 pass flow (G2 modal)
  GET  /nodes/{id}/master     → GET  /nodes/{id}/master/confirm → POST /nodes/{id}/master/confirm   master two-step (G2)
  POST /nodes/{id}/start        (G5)  start — node detail + today's top pick
  POST /work                    (G5)  work — session strip + node detail (notes/minutes/blocked→notes)
  POST /session/close           (G5)  session close — optional honest-end behind "forgot to close?" reveal
  POST /nodes/{id}/blockers     (G5)  blocker create
  POST /blockers/{id}/resolve   (G5)  blocker resolve
  POST /nodes/{id}/evidence     (G5)  evidence submit (spec select auto when node has exactly one; manual-gate radios only on manual nodes)
  ```
  All server-rendered HTML, standard form POSTs, redirect-after-POST, zero JavaScript. No audit-log view, no delete affordance in Tier 1.
- [ ] **Rendering — `render.py` voice reused verbatim + mechanical transform.** Pages call `src/skilltrace/render.py:42` helpers and transform terminal lines mechanically (escape per line, `[pill]` → CSS class, indentation → structure). One voice source, drift impossible, no CLI refactor. Sanctioned escalation if crusty: refactor `render.py` into structured section data — never parallel hand-declared web vocabulary (ADR 0002 lesson).
- [ ] **Placement & traits.** Subpackage `src/skilltrace/web/` (not `interface/`/`views/`). `serve` registered READ_ONLY + `ui` alias (`src/skilltrace/cli.py:68` `REGISTRY` pattern like `close`→`session close`). Styling: one inline `<style>` block — no static-file routing. Port 8341 default, fail-fast if busy (`--port` override); browser auto-open `http://127.0.0.1:<port>` via stdlib `webbrowser` (`--no-browser` opt-out); loopback-only (no `--host`); foreground until `Ctrl+C`; `--root` global semantics resolved at startup; `data/*` never touched so gitignore interaction nil; Windows UTF-8 via `src/skilltrace/cli.py:530`.

### D. Static HTML export (G4)

- [ ] **Disposable derived artifact, third sibling.** `skilltrace export html` writes self-contained `data/export.html` (inline CSS, zero JS, no external assets) — single-page five-layer review roll-up (progress / blockers / reviews / evidence+gates / resource verification / health strip) via `load_context_strict` (`src/skilltrace/context.py:200`) reusing `report *` derivations (`src/skilltrace/commands/report.py`). Rejected: frozen replica of daily views (lies about liveness), multi-page mirror of serve, `--output PATH`, `serve --snapshot`.
- [ ] **Command — zero-arg MUTATING.** Writes `data/export.html`, accepts no args beyond subcommand (same convention `src/skilltrace/commands/export.py:5` as `markdown`/`sqlite`). Sharing is copying the one file.
- [ ] **Regeneration & environment.** Whole-file rewrite on demand, never incremental; visible generated-at stamp + "snapshot, not live — run `st ui`" banner; `refuse-on-load-error`; `.gitignore:10` already ignores `data/`; `src/skilltrace/backup.py:3` explicitly excludes `data/` — interaction nil by construction. **Ships last** in v1.1 (`engine seam → serve shell → daily views → safety modals → export html` per G1).

### E. Report curation — live vs snapshot (joint G1/G4/G5 gist, no separate ticket)

- [ ] **Live `serve` shows daily-relevant excerpts only:** health strip, pressure excerpts (overdue reviews via `execution/reviews.yaml` derived, open blockers, `45 available · 36 locked` counts), plus `today` top recommendation. Full `report progress/blockers/reviews/evidence/resources` tables are **not** live UI in Tier 1.
- [ ] **Full review is the snapshot:** curated single-page `data/export.html` (see §D) plus CLI `report *` and `resource-report`. Search/filter deferred to `v1.5` (`docs/skilltrace-application-roadmap.md:606`, `docs/POST_V1_BACKLOG.md:38`) — not Tier 1.

### F. Remaining study-loop writes → browser affordances (G5) — complete mutation inventory

Cross-cutting: every write below dispatches in-process per §B, same `source: "web"` + `0/2/1` mapping; buttons stay enabled; degraded `load_context_lenient` empty layer shows advisory banner but keeps forms enabled.

| Write | Host | Form facts (verbatim CLI parity) | Heavyweight modal? |
|---|---|---|---|
| `start` | Node detail + today's top pick | optional template picker (`micro/standard/deep`); locked reason + open-session name beside button; domain refuses second session | Lightweight single-click confirm (copy: "marks `<node>` active — progress never moves backward") |
| `work` | Session strip (home) + node detail | notes text; optional minutes; blocked checkbox requiring notes (`--blocked` ⇒ `--notes`) | Plain submit |
| `session close` | Session strip button | optional honest-end field behind reveal (`--end`, after start, not future) | Plain submit |
| `blocker create` | Node detail "I'm stuck" inline | description required | Plain submit |
| `blocker resolve` | Action on each open-blocker row | summary required | Plain submit |
| `evidence submit` | Node detail evidence section | location required; spec select (auto when node has exactly one); accept/reject radios rendered only on manual-gate nodes; supersedes flow behind advanced toggle (record id + required reason) | Plain submit; gate verdict rendered loudly (acceptance frozen at submission `docs/adr/0003-acceptance-frozen-at-submission.md`) |

**CLI-only in Tier 1 (read-only displays where useful):** `attempt record` (plus history), `remediation create/complete` (read-only `suggest remediation` hints naming CLI), `review schedule/cancel/complete` (due/overdue read-only), `verify-resource` (human-only; statuses as read-only broken/stale pills), `export markdown/sqlite` + `backup` (snapshots stay CLI; `export html` is §D). Heavyweight modals stay exclusive to `pass`/`master`; disabled forms from derived preconditions rejected.

### G. View model — JoinedView fields mapped to UI

- [ ] **Primary on every load (above fold):** `node.title` + `store.state_of(node_id)` → state pill + Mentor `section_brief` (`src/skilltrace/context.py:173` `node_map`/`titles`/`has_gate`/`specs_by_node`/`resources_by_node:189`), `resources_by_node[node_id]` → Where to learn, `specs_by_node` + `has_gate` + `live_accepted_count(records)` → How to proceed/eligibility, hard-prerequisite edges → locked reason & unlocks context, `recommend(limit)` → Also in range.
- [ ] **Collapsible/secondary:** "Why this?" — `Recommendation.reason` + track/factor weights + remediation boost — advisory only.
- [ ] **Drill-down drawer/tabs:** full spec table + gate kind, evidence records with supersede lineage, attempts, resource verification derived status (`src/skilltrace/resources/status.py:34` broken dominates, stale from `last_verified + policy`), review schedule/history + cadence, sessions/work (single-open invariant `src/skilltrace/execution/sessions.py:58`), open blockers/remediation, unlock fan-out. Events audit trail never reconstructs state.

### H. Theming / polish — past hand-off (out of scope for this map)

- [ ] Tier 1 ships one inline `<style>` block only; theming, layout system, `a11y`, mobile fidelity deferred to polish (`v1.4` / `v0.9.0-rc1` Daily-use polish `docs/skilltrace-application-roadmap.md:108` + G1#64 + G3#67 + ADR 0006). No design-system decision blocks `v1.1`.

### I. Analytics — past hand-off

- [ ] Tier 1 dashboard shows `health` strip only. Velocity, blocker breakdown, evidence coverage, review completion, and any telemetry-free counting are `v1.5`/Tier 2 (`docs/POST_V1_BACKLOG.md:38-40`) and sit beyond this map; FSRS/Tier 2 retention analytics (`docs/POST_V1_BACKLOG.md:16-20`) out of scope.

### J. Prototype sketches (linked, not built here)

- [ ] `prototype/p1-daily-home-view.html` — 3 variants (A linear / B dashboard / C split) translating real `today/next/node/health` + `render.py` Mentor via `JoinedView` lenient; partitions pressure, Why-this, node drill-down, placeholders for modals (P1#65).
- [ ] `prototype/p1-modals.html` — cheap static stub: pass modal facts, master two-step, lightweight `start` confirm; disabled buttons, no JS, same inline style.

### K. Build plan — 5 slices (engine seam → serve shell → daily views → safety modals → export html)

Tickets `T1`–`T5` are `wayfinder:task` children of #62, wired `T1 → T2 → T3 → T4 → T5` so frontier is `T1` only. Each is stdlib-only unless a new dep is explicitly decided (none in Tier 1). See child issues for per-slice acceptance.

### L. Invariants & constraints preserved

- [ ] Hard boundaries per `docs/SAFETY_BOUNDARIES.md:1` + `CONTEXT.md:90`/`CONTEXT.md:98`: no automated `pass`/`master`/`delete`, asserted progress never demotes, hard-prereq never overridden, AI review never authority; `docs/SCHEMA_REFERENCE.md:1` frozen; `ARCHIVE/scaffold-v0.1/` history preserved (`docs/adr/0005-scaffold-retirement.md:1`); `data/` disposable never read back; `v1` is five layers (`docs/adr/0002-cut-interface-layer-from-v1.md:1`), never `interface/`.

---

## Acceptance — map is done when

- [ ] This checklist + the two prototype sketches are linked from #62 `## Decisions so far` and this file.
- [ ] No product or arch decision remains that would block the 5 build slices.
- [ ] `## Not yet specified` is empty; `## Out of scope` records the three ruled-out patches (theming/polish, full drill-down+search/filter, Tier 1 analytics).
- [ ] `pytest` green, `skilltrace health` / `today` / `next --minutes 60` / `node math.arithmetic.order_operations_01` exit 0 on seed; `skilltrace validate graph|evidence|execution|policy|resources` green.

## References

`CONTEXT.md`, `docs/skilltrace-application-roadmap.md`, `docs/adr/0001-0005` + `docs/adr/0006-stdlib-only-serve-shell.md`, `docs/curriculum-authoring.md`, `docs/SCHEMA_REFERENCE.md`, `docs/POST_V1_BACKLOG.md`, `archive/scaffold-v0.1/interface/` + `archive/scaffold-v0.1/web-app-vision/reference-research-document.md` (ref-only), `src/skilltrace/context.py:146` `JoinedView`, `src/skilltrace/context.py:200` strict / `src/skilltrace/context.py:260` lenient, `src/skilltrace/render.py:42`, `src/skilltrace/cli.py:68` `REGISTRY` + `src/skilltrace/dispatch.py:116`, `src/skilltrace/export_data.py:88`, `src/skilltrace/graph/state.py:118`.
