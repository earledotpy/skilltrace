# Spec — v1.8 Phase 2 ML seed graph + v1.7 deferred-item verdicts

**Status:** locked hand-off (map [#156](https://github.com/earledotpy/skilltrace/issues/156)).
**Target:** v1.8, Phase 2 ML seed-graph content plus the four v1.7 deferred-item verdicts, on the existing v1.7 surface.
**Map:** [#156 Map — v1.8 Phase 2 ML seed graph + v1.7 deferred-item verdicts](https://github.com/earledotpy/skilltrace/issues/156)
**Decisions:** [T-SeedGraph #157](https://github.com/earledotpy/skilltrace/issues/157) ·
[G-Batch #158](https://github.com/earledotpy/skilltrace/issues/158) ·
[G-Schedule #159](https://github.com/earledotpy/skilltrace/issues/159) ·
[G-Marker #160](https://github.com/earledotpy/skilltrace/issues/160) ·
[G-Retired #161](https://github.com/earledotpy/skilltrace/issues/161) ·
[T-Spec #162](https://github.com/earledotpy/skilltrace/issues/162) (this spec).
**Locked inputs (operationalized, not re-debated):** the v1.8 source list from
`docs/POST_V1_ROADMAP.md` v1.8 row + R-Phase2ML
[#97](https://github.com/earledotpy/skilltrace/issues/97); the 6-stage
seed-provenance chain from
[#151](https://github.com/earledotpy/skilltrace/issues/151); the v1.7 locked spec
`docs/spec-v1.7-resource-web-verification.md` with its T-TestArch
[#139](https://github.com/earledotpy/skilltrace/issues/139) and T-Exit
[#140](https://github.com/earledotpy/skilltrace/issues/140) resolutions.

The builder must not reopen product or architecture decisions. Terms follow
`CONTEXT.md`; all existing hard boundaries remain binding. Build order: the
v1.7 locked spec first (its `check-resource`, `web_check.check_url`,
`verify-resource --check-url`, `replace-resource`, and retired schema are this
spec's floor), then this spec's deltas. The T-SeedGraph draft branch predates
the v1.7 build, so merge it onto the built tree and re-run every validator.

> Hand-off gate (from map `Destination`): a builder can implement v1.8
> without reopening a product or architecture question. This doc satisfies
> that gate: every acceptance bullet is a concrete check (commands, gate
> ids, file paths).

---

## 0. Scope and explicit non-goals

In scope for v1.8:

- The Phase 2 ML seed graph from the T-SeedGraph draft branch
  (`v1.8/seed-graph-draft` @ `65e9f23`): 7 new nodes, 12 `graph/edges.yaml`
  additions, 4 `graph/resources.yaml` additions, including the ≥ 1 capstone
  integration node with ≥ 2-source citation (§2).
- The four v1.7 deferred-item verdicts, exactly as resolved:
  - G-Batch: fold the minimal batch sweep (`batch()` + `check-resources`); re-defer rate limiting, `robots.txt`, and 429 backoff (§4).
  - G-Schedule: re-defer scheduling automation past the slot table, no surface (§4).
  - G-Marker: fold the minimal broken-marker enrichment (`status_code` + `final_url` only) (§5).
  - G-Retired: fold warning-only retired handling in `validate resources` (§5).
- Tests, release safety assertions, and documentation gates (§§6–7).

Explicitly **out of scope** (per map `Out of scope` + ticket verdicts):

- Phase 3 / v1.9 content (HF Agents Course, DSPy, LangGraph, smolagents, LlamaIndex, MCP, MS Agent Framework, OpenAI Agents SDK, PydanticAI, FastAPI/Docker primer).
- Phase 2 graph reshape — dropping, adding, reordering, or re-wiring Phase 2 sources or prerequisites. v1.8 adds content against the locked Phase 2 shape.
- Automated positive verification — forbidden by v1.7 spec §2 + `CONTEXT.md` hard boundary. A successful check never sets `last_verified` or clears `broken`.
- No engine seam changes: no new modules beyond the batch helper's home in the existing `web_check.py`, no new policy block, no new event schema, no new SQLite reader, no interface-layer revival (ADR 0002).
- Scheduling automation of any shape (cron-external, serve-background, today-hook) — re-deferred past the slot table with no version commitment.
- Rate limiting, `robots.txt` respect, and 429 backoff — re-deferred past the slot table with no version commitment. A 429 observed by the folded batch is reported as `BROKEN … status 429` via the existing `reason` field.
- SSL / certificate / content-hash deep verification; Web UI changes for verification features; recommendation ordering; evidence or progress transitions.

## 1. Data sources and source-of-truth boundaries

`graph/edges.yaml` is the sole relationship source: node frontmatter carries
no `state`, `prerequisites`, `unlocks`, or `node_type`, and the v1.8 nodes use
only the locked seed-provenance frontmatter keys (`source_metadata`,
`regeneration_key`, `section_provenance`, `roadmap_anchors`) plus the standard
node fields. `graph/resources.yaml` is the authoritative LearningResource
registry (loader: `src/skilltrace/resources/registry.py:39`
`_REGISTRY_RELPATH`); `execution/events.yaml` is audit-only. Markdown/YAML
sources are read and written through existing seams; SQLite exports are
disposable and never read.

The v1.8 source list is **locked** (map Notes; R-Phase2ML #97): Google ML
Crash Course (2024 refresh), Andrew Ng **Machine Learning Specialization**
(Python edition, not legacy Octave), ISLP (Python edition), Kaggle Learn. The
spec operationalizes the bar (§10); it does not re-debate the list.

Every new node and resource respects the #151 seed-provenance chain (6 stages,
human-signed): source material cited with source metadata + regeneration key;
the draft branch is the generated candidate; promotion to canonical seed data
requires the existing node/edge/resource validators to pass and a human
curriculum editor's minor-vs-material judgment. Concretely, every new node
file carries `source_metadata` (primary source, canonical URL, source
version, supporting sources) + `regeneration_key` + `section_provenance`
frontmatter mirrored in a `Source provenance` body section, plus
`reference_only` roadmap anchors that never control locking. Every new
resource carries its provenance in the free-text `license` field (source,
version, sections, regeneration key, `reference_only` note), so the closed
registry schema needs no change for provenance.

v1.7's `policy/resource_web_verification.yaml` (spec §3,
`resource_web_verification_policy`) is extended only if a G-verdict
introduces a new policy block — none does (G-Batch reuses the existing
staleness window with no new config; G-Marker/G-Retired/G-Schedule add no
policy). The builder makes **no** `POLICY_FILES` change
(`src/skilltrace/policy/loading.py:18`) and ships **no** new policy file.

## 2. Architecture / seed-graph content

Per [T-SeedGraph #157](https://github.com/earledotpy/skilltrace/issues/157):
merge the draft branch `v1.8/seed-graph-draft` @ `65e9f23` (11 files, +738,
additions only — no existing edge, node, or resource touched) onto the built
tree, then re-run `validate graph` and `validate resources`. Post-merge
expectations: 88 nodes, 136 edges (136 active), 33 resources.

### 2.1 New node files (7, all under `graph/nodes/`)

| File | Track | Role |
|---|---|---|
| `ml.framing.ml_workflow_01.md` | foundational | Framing + leakage-audited split discipline |
| `ml.regression.linear_regression_01.md` | foundational | Linear score, loss, gradient descent |
| `ml.classification.logistic_regression_01.md` | foundational | Classifier generalizing the regression machinery |
| `ml.evaluation.validation_metrics_01.md` | foundational | Bias/variance diagnosis, validation curves |
| `ml.trees.ensembles_01.md` | foundational | Trees, depth-vs-boosting comparison |
| `ml.practice.titanic_baseline_01.md` | portfolio | Titanic baseline + submission discipline |
| `ml.capstone.house_prices_integration_01.md` | portfolio | **Capstone** — House Prices end-to-end pipeline |

Foundational track for concepts, portfolio track for the two competition
nodes, following the Phase 2 weekly shape from
`docs/roadmap/phase-2-classical-ml.md` minus the FastAPI/Docker preview
(re-slotted to v1.9).

### 2.2 New edges (12, all appended to `graph/edges.yaml`)

Hard concept chain (5): workflow → linear → logistic → validation →
ensembles, plus Titanic → capstone and ensembles → capstone. Soft ordering
links (7): `data.pandas.dataframe_basics_01` and
`math.statistics.probability_basics_01` → framing;
`math.calculus.gradient_intuition_01` → linear;
`programming.python.functions_01` → Titanic; validation → Titanic and
ensembles → Titanic (a first baseline submits before full fluency). No
existing edge touched; no source dropped, added, or reordered.

### 2.3 New resources (4, all appended to `graph/resources.yaml`)

| ID | URL | Cost claims | Supports |
|---|---|---|---|
| `mlcc-crash-course` | `https://developers.google.com/machine-learning/crash-course` | free | framing, linear, logistic, validation, ensembles, Titanic, capstone |
| `ng-ml-specialization-python` | `https://www.coursera.org/specializations/machine-learning-introduction` | paid + `free_tier` + `certificate` | framing, linear, logistic, validation, ensembles, capstone |
| `islp-python-edition` | `https://www.statlearning.com/` | free | linear, logistic, validation, ensembles, Titanic, capstone |
| `kaggle-learn-ml` | `https://www.kaggle.com/learn` | free + `certificate` | framing, validation, ensembles, Titanic, capstone |

New resources land **unverified by design**: no human `last_verified` is
asserted by automation (hard boundary holds). Human verification at build
follows §10(b).

### 2.4 Capstone integration node

`ml.capstone.house_prices_integration_01` (House Prices end-to-end pipeline:
CSV load and clean, leakage-audited split, regularized-regression baseline
vs. tree/gradient-boosting comparison with cross-validated RMSE choice, 3+
submissions with commit-message discipline, best-model analysis naming which
source's technique moved the score) is the ≥ 1 / ≥ 2-sources capstone:

- Its two hard prerequisites span two source lineages: the Kaggle-anchored
  `ml.practice.titanic_baseline_01` chain and the MLCC/Ng/ISLP-anchored
  `ml.trees.ensembles_01` chain.
- Its supporting resources cite three of the four v1.8 sources directly
  (`kaggle-learn-ml`, `islp-python-edition`, `mlcc-crash-course`), with the
  fourth (`ng-ml-specialization-python`) one hard edge away via the ensemble
  prerequisite's resources.

The full criterion walk-through lives in the node's own `Capstone
integration identification` body section; the builder does not re-argue it.

## 3. Policy

No new policy block. G-Batch folds the sweep with no new config (staleness
reuses the existing `stale_after_days` window — no new policy block, no new
modules); G-Marker, G-Retired, and G-Schedule introduce no policy surface.
The builder references v1.7's `resource_web_verification_policy` unchanged:
strict booleans for `enabled`/`follow_redirects`, integer timeout 1–120,
method `HEAD`/`GET`, non-empty User-Agent; missing, malformed, unknown, or
out-of-range values fail `validate policy`. The policy stays advisory and
can never authorize positive verification.

## 4. CLI

### 4.1 `check-resources` (new, from G-Batch — the only new command)

One primitive in the existing `src/skilltrace/resources/web_check.py`: a
`batch()` helper that reuses the v1.7 `check_url` **sequentially** (no token
bucket, no `robots.txt`, no retry loop) over a list of resource IDs:

```python
batch(
    entries: Iterable[str],
    *,
    timeout_seconds: int,
    follow_redirects: bool,
    method: Literal["HEAD", "GET"],
    user_agent: str,
) -> list[tuple[str, WebCheckResult]]
```

Driven by `skilltrace check-resources [--all | --stale-only]`, sharing v1.7's
timeout/method/redirect/User-Agent flags (default User-Agent
`skilltrace/1.8 check-resources`). `--all` is the default when no selector
is given; `--stale-only` restricts the sweep to resources whose derived
status is stale under the existing `stale_after_days` window. It prints one
line per resource plus a summary, for example:

```text
check-resources: OK mlcc-crash-course — status 200, final_url https://developers.google.com/machine-learning/crash-course
check-resources: BROKEN islp-python-edition — status 404: not found
check-resources: 4 checked, 3 OK, 1 BROKEN
```

Both answered `OK` and answered `BROKEN` sweeps exit 0 (a failure verdict is
the resource's, not the command's — same convention as v1.7 `check-resource`
§4.1). Unknown flags, unreadable data, or inability to answer exit 1. The
command is `Kind.READ_ONLY`, emits no event, and performs **zero writes**:
it never sets `last_verified` and never clears or writes `broken` (same
convention as v1.7 `check-resource`).

### 4.2 Scheduling (none, from G-Schedule)

No scheduling primitive ships in v1.8 — no cron file, no serve background
task, no `today` hook. Manual checks remain the design. When scheduling
re-opens as a separate future effort, cron-external is the only seam-clean
shape on record; serve-background and today-hook each need their own
seam-change ticket first (not filed — no commitment).

v1.7's `check-resource` surface is otherwise unchanged.

## 5. Replacement / retire behavior

Warning-only retired handling in `validate resources`, stacking on the v1.7
retired schema (`retired`, `retired_at`, `replaced_by`) and
`replace-resource` (v1.7 spec §§1, 4.3). Per
[G-Retired #161](https://github.com/earledotpy/skilltrace/issues/161):

- **Dangling `supports` on a retired entry → WARN, exit 0.** Locked line,
  with dangling-node detail appended:
  ```text
  WARN retired-resource <id> — retired <date>; replaced by <replaced_by> (supports unknown node <node> preserved as history)
  ```
  Rationale: v1.7 retire preserves `supports` + URL/path + broken marker by
  design, so drift in preserved history is not a curriculum break — and
  `CONTEXT.md` already rules resources pure advice that never affects
  readiness, eligibility, or state.
- **Still ERROR (fail, non-zero exit):** duplicate resource IDs (identity
  holds even for history); malformed retired shape (missing/bad
  `retired_at`, missing/unknown `replaced_by`, `retired: true` without the
  pair — loader closed-schema errors, same as v1.7 §1).
- **Orphan warning suppressed for retired entries** (`supports: []` on a
  retired entry is history, not a quality signal). The redundant free-tier
  warning applies as before, retired or not.
- **No new error or warning kinds** beyond the one WARN line — an additive
  delta on the existing v1.7 loader + `check_resources` surface
  (`src/skilltrace/resources/validation.py:75`), within the no-new-seam rule.
- **No `validate graph` change:** `validate graph` never reads
  `graph/resources.yaml` (nodes/edges only —
  `src/skilltrace/commands/validate.py:50`), so retired `supports` links are
  judged solely in `validate resources`.

### 5.1 Broken-marker enrichment (from G-Marker)

Stored `broken` marker shape (loader closed sub-schema `_BROKEN_FIELDS`
gains exactly two optionals; anything beyond the four still fails):

```yaml
broken: {date: <YYYY-MM-DD, required>, reason: <str, required>, status_code: <int | null, optional>, final_url: <str | null, optional>}
```

- `status_code` (`int | None` — `None` for transport/timeout failures) and
  `final_url` (`str | None` — `None` when no response/redirect was observed)
  are the values the v1.7-spec'd checker already returns; no checker change.
  The stored `final_url` is the observed redirect target frozen at failure
  time, not a live pointer and not a re-fetch. `date`/`reason` semantics are
  unchanged. Rejected: `error_type` enum (new classification seam),
  `retry_count` (constant 0/1 with no retry loop), `last_attempt_at`
  (duplicates `date`).
- **Loader:** both legacy `{date, reason}` and enriched markers pass; new
  fields optional; absent reads as `None`; wrong types fail with the
  existing clean `ResourceLoadError` shape. `BrokenMarker`
  (`src/skilltrace/resources/registry.py:88`) gains `status_code`/`final_url`
  `None`-default fields.
- **Writer:** `record_verification`
  (`src/skilltrace/resources/verification.py:47`) gains keyword-only
  `status_code: int | None = None` and `final_url: str | None = None`;
  the failure path writes the enriched marker and **omits `None` fields**
  from the YAML (no explicit nulls). No new `verify-resource` flags: the
  human `--broken --reason` path stays reason-text only; enriched fields are
  observed detail written only by the `--check-url` preflight, which passes
  the checker's `status_code`/`final_url` through.
- **No hard dependency on batch:** single `verify-resource --check-url`
  and the folded `batch()`/`check-resources` path write through the same
  writer. `validate resources` stays curriculum-integrity only (never reads
  verification dates or broken detail to pass/fail); enrichment changes
  loader shape only, never a validation verdict.

## 6. Testing architecture

TDD for the new code surface (batch helper, broken-marker enrichment,
retired WARN), following the three-layer pattern from v1.7 T-TestArch #139:
unit on the helper with mocked urllib, CLI safety/output on disposable
repos, registry integration for new schema fields. No Web layer. Exact
structured assertions for unit and registry tests; CLI assertions check
required facts. No live HTTP anywhere.

- **Unit** (`tests/resources/test_batch_check.py`, new): call `batch()`
  with mocked `urllib.request`; pin exact per-entry `(id, WebCheckResult)`
  fields for HEAD/GET, redirects, HTTP/transport/timeout failures
  (429 → `ok=False` surfaced via `reason`, no retry), User-Agent,
  sequential order, empty-input shape, and the no-write seam (never calls
  `record_verification`, never sets `last_verified`, never clears `broken`).
  Extend `tests/resources/test_web_check.py` only for the enriched writer
  inputs it already covers; the marker schema itself is pinned at the
  registry layer below.
- **CLI** (`tests/cli/test_resource_batch_check.py`, new): drive the
  in-process CLI against disposable repos with mocked HTTP. Assert exit 0
  for answered sweeps (including all-BROKEN), non-zero for usage/load
  failures, per-line `OK`/`BROKEN` presence plus the `N checked, …`
  summary, `--stale-only` selection against the existing staleness window,
  registry byte-identical after the run (zero writes), and no event appended.
- **Integration** (`tests/resources/test_broken_marker.py` and
  `tests/resources/test_retired_validate.py`, new): hand-built resource
  dictionaries through the existing disposable-registry helpers. Assert the
  exact enriched marker round-trip (legacy `{date, reason}` passes,
  `None` fields omitted, wrong types fail clean, unknown fifth field
  fails); the retired WARN-vs-ERROR table (dangling-on-retired warns exit
  0 with the locked line, duplicates and malformed retired shape error,
  orphan suppressed for retired, free-tier warning unchanged); and exactly
  the defined writes plus one event for the `--check-url` failure path.
- **Fixtures:** hand-built dicts in test functions via the existing
  disposable-repository/YAML helpers. No new fixture directory, generator,
  or test infrastructure. Time-dependent orchestration takes an explicit
  clock/date; production CLI is the only caller resolving the current date.

### 6.1 Behavior coverage matrix

| Behaviour | Unit | CLI | Integration |
|---|---|---|---|
| Sequential batch over N resources, order preserved | exact | presence | n/a |
| 429 reported as BROKEN via `reason`, no retry | exact | presence | n/a |
| Batch performs zero writes, emits no event | seam assertion | registry-identical + event assertion | n/a |
| `--stale-only` selection under existing window | n/a | presence | exact |
| Enriched marker round-trip (`status_code`/`final_url` optional, `None` omitted) | n/a | n/a | exact |
| Legacy `{date, reason}` markers stay valid, no backfill | n/a | n/a | exact |
| Retired WARN line, exit 0, no state/edge change | n/a | presence | exact |
| Duplicates + malformed retired shape still ERROR | n/a | non-zero exit | exact |
| `--check-url` failure writes enriched marker only; success writes nothing positive | n/a | persisted safety assertion | exact |
| Empty registry sweep (`0 checked`, exit 0) | exact | presence | exact |

## 7. Release exit gates (T-Exit-equivalent)

### E1 — Functional gates

```text
pytest tests/resources tests/policy tests/cli
skilltrace validate policy
skilltrace validate graph
skilltrace validate resources
skilltrace check-resource mlcc-crash-course
skilltrace check-resources --all
skilltrace check-resources --stale-only
skilltrace verify-resource mlcc-crash-course --check-url
skilltrace resource-report
skilltrace health
```

The command gates use deterministic local/mock fixtures; no external
network or running Serve process is required. The v1.7 gates
(`replace-resource --dry-run` / real, per v1.7 spec §9) remain green —
v1.8 stacks on that surface. Post-merge `validate graph` must report 88
nodes / 136 edges and `validate resources` 33 resources before human
verification dates are asserted (§10).

### E2 — Safety assertions

Implement in `tests/release/test_v18_safety_gates.py`:

- **SA1 — Event schema frozen:** compare event keys with the v1.6 snapshot;
  only the established whitelisted event shape may be added.
- **SA2 — No new SQLite reader:** only the existing SQLite export reader
  (`src/skilltrace/sqlite_export.py:29`) may read `data/skilltrace.db`.
- **SA3 — No automated pass/master/delete:** new paths never issue
  `pass_node`, `master_node`, or `delete_record`.
- **SA4 — Batch check is read-only on registry state:** `batch()` never
  writes, calls `record_verification`, sets `last_verified`, or clears
  `broken`; `check-resources` is `Kind.READ_ONLY` and emits no event.
- **SA5 — Marker enrichment is descriptive-only:** the writer adds at most
  the two optional fields on the failure path; success never sets
  `last_verified` or clears `broken`; reports render the new fields as
  advisory detail.
- **SA6 — Retired WARN is advisory-only:** the WARN line exits 0, never
  blocks a human-initiated action, and never touches asserted progress,
  edges, evidence, or `last_verified`; `validate graph` has no
  resources-aware change.
- **SA7 — Mutation and audit whitelist:** check/report/health are
  read-only; `--check-url` failure can write only the enriched `broken`
  marker; replacement writes only its v1.7-defined fields and one event;
  dry-run writes neither. No scheduler ships — assert no
  cron/serve-background/today-hook call site exists on the new paths.

### E3 — Documentation gates

Implement in `tests/release/test_v18_doc_gates.py`:

- **DG1 — Spec gate:** this file has all required sections (§§0–10), every
  E1 command, and every assertion label SA1–SA7 as substrings.
- **DG2 — Glossary gate:** `CONTEXT.md` carries the §8 term touch (the
  `Broken marker` line names the optional `status_code` and `final_url`
  fields).

## 8. Glossary additions

One line-touch to `CONTEXT.md`, in the same change as this spec lands: the
**Broken marker** term gains the two optional enrichment fields (observed
HTTP `status_code`, observed redirect-target `final_url`, each possibly
absent) — still a dated observation, still descriptive, still cleared only
by a later successful verification or human curriculum edit. No other
`CONTEXT.md` change, for these reasons:

- **No `Batch resource check` term** — batching is a calling convention
  over the existing **Web check** (N sequential reachability tests); the
  G-Batch resolution keeps `Verified` vs `Web check` as the covering terms.
- **No `Retired resource` touch** — the existing term (removed from active
  flows, preserved with replacement + date) already covers warning-only
  handling per G-Retired.
- **No `Capstone integration node` term** — a slot acceptance construct
  defined in §2.4/§10(c), i.e. curriculum seed wording, not engine
  vocabulary.
- **No #151 chain terms here** — `Candidate curriculum` / `Source anchor`
  remain proposed lines for the slot builder that first needs them as
  engine vocabulary; this spec uses them as seed-data conventions only.

This resolves the map's G-Glossary fog patch: no separate glossary ticket.

## 9. Invariants preserved

- Five layers (ADR 0002); no interface-layer revival; no new layer.
- Hard boundaries from `AGENTS.md` and `CONTEXT.md` unchanged: no automated
  positive verification, no auto pass/master/delete, no hard-prerequisite
  override, AI review never an acceptance authority.
- `edges.yaml` sole relationship source; asserted progress
  (`active`/`passed`/`mastered`) never moves backward.
- Learner state lives in the progress store, never in curriculum files;
  eligibility derived on demand, never stored.
- Event log audit-only (every mutating command appends one event; events
  never read to compute state); Markdown/YAML the only source of truth;
  exports disposable, never read back.
- Advisory policies and resource hygiene warn and reorder only; they never
  block a human-initiated action.
- Node IDs immutable and never reused; new resources carry new slug IDs.

## 10. Acceptance

The v1.8 implementation is accepted when E1 passes, SA1–SA7 pass, DG1–DG2
pass, existing tests remain green, and the three slot-row checks below hold:

- [ ] **(a) Seed graph exports cleanly** — `validate graph` OK (88 nodes,
  136 edges, 136 active), `validate resources` OK (33 resources), and the
  disposable export smoke (`skilltrace health` + `resource-report`) runs
  exit 0 on the merged tree.
- [ ] **(b) All 4 sources verified** — per G-Batch's verdict the bar has
  three distinguishable parts, all required: (i) each of the 4 new
  resources carries a human-asserted `last_verified` (human act at build —
  the verdict); (ii) `check-resources --all` reports `OK` for the 4
  canonical URLs (the objective observation — sweep success sets nothing);
  (iii) `validate resources` reports no broken markers on the 4 new
  resources. This graduates the map's verification-bar fog patch with the
  first reading (registry-sweep clean) *plus* the human assertion that
  makes it a verification rather than a check.
- [ ] **(c) ≥ 1 capstone integration node with ≥ 2 source citations** —
  `ml.capstone.house_prices_integration_01` present in `graph/edges.yaml`
  with its two hard-prerequisite lineages (Titanic chain + ensembles
  chain) and ≥ 2 of the four v1.8 sources in its supporting resources
  (three direct + the fourth one hard edge away, §2.4).
- [ ] E1 + E2 + E3 from §7 all pass; the map's `Not yet specified` fog is
  empty (verification bar graduated here, G-Glossary resolved as no-ticket
  in §8).

---

## References

`CONTEXT.md` (**LearningResource**, **Verified**, **Web check**, **Retired
resource**, **Replacement candidate**, **Replacement**, **Export**,
**Event log**, **Hard boundary**, **Advisory policy**); `AGENTS.md` (Safety
rules; Current phase); `docs/POST_V1_ROADMAP.md` (v1.8 slot row + Beyond
this roadmap); `docs/roadmap/phase-2-classical-ml.md` (Phase 2 weekly
shape); `docs/spec-v1.7-resource-web-verification.md` (§§1–4 the v1.8 floor:
registry fields, `check_url`, policy, CLI, replacement); `docs/adr/0002`
(five layers); branch `v1.8/seed-graph-draft` @ `65e9f23` (T-SeedGraph
content); `src/skilltrace/resources/registry.py:39` (registry path),
`:88` (`BrokenMarker`), `:261` (marker loader);
`src/skilltrace/resources/verification.py:47` (`record_verification`),
`:37` (dated-fact clock); `src/skilltrace/resources/validation.py:75`
(`check_resources`); `src/skilltrace/commands/validate.py:50`
(`validate_graph` never reads resources);
`src/skilltrace/commands/verify_resource.py:83` (command registration);
`src/skilltrace/policy/loading.py:18` (`POLICY_FILES`);
`src/skilltrace/sqlite_export.py:29` (sole SQLite reader);
`graph/edges.yaml`, `graph/resources.yaml`, `graph/state.yaml`
(post-merge: 88 nodes / 136 edges / 33 resources).
