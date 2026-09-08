# Spec — v2.2 Provenance & graph-impact diagnostics

**Status:** designed (2026-09-08) — decisions D-Receipt, D-Capture, D-Exit,
D-Normalize, D-Schema, D-Baseline, D-Flip, D-RecDiff, D-Dangling, D-Noop,
D-Surface locked below; §7 gate runs not yet executed (pre-implementation).
**Target:** v2.2, slot 2 of `docs/POST_V2_ROADMAP.md` — bounded gate-run
receipts (immutable, optional fields: normalized command identity,
root-relative inputs, tool/version, exit class, output hashes;
secrets/unbounded logs excluded) + read-only pre-release graph-impact
diagnostic (derived lock/unlock flips, recommendation changes, dangling
refs, no-op edges).
**Map:** decisions trail R-Provenance
([#194](https://github.com/earledotpy/skilltrace/issues/194)) and G-Slots
([#196](https://github.com/earledotpy/skilltrace/issues/196)).
**Standing rule:** all terms per `CONTEXT.md`; safety rules in `AGENTS.md`
are unchanged and binding — this spec never relaxes them.

> Hand-off gate: a builder can implement v2.2 without reopening a product
> or architecture question. Every decision below is filled; §7 lists the
> gate runs the slot must pass.

---

## 0. Scope and what is explicitly out of scope

In scope for v2.2:

- An optional `gate_run` provenance block on objective-gate
  `EvidenceRecord`s, written by `evidence submit` at judgment time
  (D-Receipt).
- A captured-and-echoed gate run — the loud run preserved, output
  hashed (not stored) for the receipt (D-Capture).
- `validate evidence` shape checks for the new optional field:
  present ⇒ well-typed; absent ⇒ valid (pre-v2.2 records stay valid)
  (D-Schema).
- Portfolio share-profile classification of receipt fields under the
  existing **paths** dimension (default-deny, `--include-paths` to
  override).
- A read-only `graph impact` command with a pure core in
  `src/skilltrace/graph/impact.py`: readiness flips, recommendation
  diffs, dangling evidence/spec references, no-op edges (D-Surface).
- Baseline loading via a git ref (default `HEAD`) with a `--baseline
  <path>` escape hatch reading a second checkout (D-Baseline).

Explicitly **out of scope**:

- A full gate-runner / scheduler-queue (POST_V2 Beyond list; re-opens
  when a Phase 4/5 seed artifact needs automated gate runs — these
  receipts are the precondition, not the runner).
- Populating `tool`/`version` receipt fields in the engine (schema
  only — populating them means probing subprocesses; left for the
  future gate-runner) (D-Normalize).
- A gate timeout or any new subprocess control; `GateUnrunnable`
  semantics unchanged.
- Any change to manual-gate submits (they get no receipt), pass/mastery
  law, the five layers, or the event log's one-event-per-mutation rule.
- Streaming/incremental output hashing via `Popen` pump loops — the
  rejected alternative for v2.2 (D-Capture).

---

## 1. Gate-run receipts (D-Receipt, D-Capture, D-Exit, D-Normalize)

Locked:

- **Shape.** An `EvidenceRecord` may carry one optional mapping,
  `gate_run`, written only when the submit was judged by an *objective*
  gate. Manual-gate records never carry one. Fields (all bounded,
  secrets and unbounded logs excluded by construction — only hashes and
  argv/paths cross the boundary, never raw gate output):

```yaml
gate_run:
  command_argv: [python, evidence/checks/sql_select_check.py]
  inputs: [evidence/artifacts/data/sql/select_basics_solution.py]
  exit_class: failed   # passed (rc 0) | failed (rc != 0) — exactly two values
  exit_code: 2         # int, optional
  stdout_hash: sha256:<hex>   # hash of the captured stream (empty → absent)
  stderr_hash: sha256:<hex>
  tool: null           # optional; NEVER populated in v2.2 (absent or null)
  version: null        # optional; NEVER populated in v2.2
```

- **Immutability.** Receipts ride the append-only
  `evidence_records.yaml` write (`_append_record` re-dumps raw, never
  round-trips existing rows), so a written receipt is immutable the
  same way every record field is. The closed record schema learns
  exactly these new key names; unknown keys still fail.
- **Optional.** Absent `gate_run` is valid — seed records (manual
  gates) and pre-v2.2 records load unchanged. The seed ships only
  manual gates, so seed `evidence_records.yaml` gains nothing.
- **Never an authority.** A receipt is provenance, not a verdict input:
  pass-eligibility math, supersede warnings, and readiness derivation
  read only the fields they read today. Pinned test: a record with a
  receipt never changes eligibility math.
- **Unrunnable gate = no record** (already true, pinned again under the
  widened seam): `GateUnrunnable` still exits 1, writes no record, no
  receipt, no event.
- **Capture mechanics (D-Capture).** The handler's `_run_gate` changes
  from uncaptured to `capture_output=True`; captured stdout/stderr are
  hashed and then echoed to the terminal (stdout, then stderr) so the
  "loud run" is preserved in content and order, at the cost of the
  interleaving. Shipped checkers are short deterministic scripts; the
  streaming alternative (`Popen` + incremental hashing) is explicitly
  rejected for v2.2 and re-opens with a gate-runner slot.
- **Exit class (D-Exit).** Exactly `passed` (returncode 0) and `failed`
  (non-zero). No timeout/other class — there is no timeout today.
- **Normalization (D-Normalize).**
  - `command_argv` is the exact argv executed (`shlex.split` of the
    gate's `command`, the same parsing the seed-acceptance test
    mirrors). No cwd override, no substitution — the
    `docs/curriculum-authoring.md` contract unchanged.
  - `inputs` is the submitted artifact's root-relative `location` plus
    every argv token that resolves to an existing file under the repo
    root, deduplicated, root-relative, forward slashes.
  - `tool`/`version`: schema keys exist, values stay unpopulated in
    v2.2. Populating them means probing subprocesses or guessing; the
    future gate-runner owns that.
  - Hashes: `sha256:<hex>` over the captured stream bytes; an empty
    stream contributes no key.

Seam change (pre-agreed TDD seam): `GateRunner` widens from
`Callable[[str], int]` to a callable returning `(exit_code, stdout,
stderr)` and still raising `GateUnrunnable` on spawn failure. The
planner stays pure — it receives the run result; it never spawns. The
existing fakes in `tests/evidence/test_submission.py` and
`tests/evidence/test_submit_command.py` change first.

---

## 2. Graph-impact diagnostic (D-Baseline, D-Flip, D-RecDiff, D-Dangling, D-Noop)

Locked:

- **Command.** `graph impact [--from <git-ref>] [--baseline <path>]
  [--minutes <n>]` — `Kind.READ_ONLY`, appends no event, **exit 0
  always**: impact findings are advisory words, never a gate. (Contrast
  `validate graph`, which exits 1 on errors; impact is not validation.)
  Naming follows the two-word read-only convention (`retention
  status`).
- **Pure core.** `src/skilltrace/graph/impact.py`:
  `compute_impact(baseline_nodes, baseline_edges, current_nodes,
  current_edges, store, ...)` over already-loaded data — the TDD seam,
  mirroring the `check_graph` / `recommend` / `plan_submit` house
  style. The command shell loads both sides and calls it.
- **Baseline (D-Baseline).** Default `--from HEAD`: the engine reads
  baseline files through one read-only fetch seam (`git show <ref>:path`
  / `git ls-tree <ref>` — a file fetch, not a write path; no boundary
  touched). `--baseline <path>` instead reads a second repo root (a
  pristine clone/worktree) and requires no git. When both are given,
  `--baseline` wins and `--from` is ignored. Non-git directories fail
  cleanly (exit 1, "not a git repository" style message) — the one case
  where the diagnostic exits non-zero, because it cannot compute at all
  (same convention as a loader failure in a read-only command).
- **Flip semantics (D-Flip).** Derived readiness (`locked`/`available`)
  is computed on both sides from that side's `edges.yaml` + the *same*
  current progress store. Only readiness flips on **non-asserted**
  nodes are reported as flips. A node with asserted
  `active`/`passed`/`mastered` that a new hard prerequisite would
  "re-lock" is reported as *"asserted progress stands — not revoked"*,
  never as a flip. This is the slot's asserted-states-immutability
  acceptance clause made concrete.
- **Recommendation changes (D-RecDiff).** `recommend()` runs under
  baseline edges and current edges with identical store, policy
  weights, and session params. Boost inputs (remediation, open
  blockers, prereq-review pressure, agent signals) are derived once
  from files unchanged between the sides and applied to both — the
  diff isolates the *graph edit's* effect. Output: nodes that entered,
  left, or moved in the ranked list.
- **Dangling references (D-Dangling).** Working-tree nodes deleted
  while artifact specs, gates, records, or attempts still name them.
  `validate graph`/`validate evidence` already *error* on these; the
  diagnostic *lists* them as release impact without blocking.
- **No-op edge (D-Noop).** An active hard-prerequisite edge is a no-op
  iff removing it flips no derived readiness **and** changes no
  recommendation (leverage counts feed scores, so readiness-only is
  too weak). Counterfactual removal over all active hard edges, two
  `recommend()` passes each — cheap at seed scale (100 nodes / 157
  edges).
- **Never blocks.** Findings reorder nothing, write nothing, gate
  nothing: the diagnostic never blocks a human action, never asserts
  progress, and reads relationships only from `edges.yaml` (plus the
  same derived-readiness code `sync` uses) — never node frontmatter.

---

## 3. Schema, validation, redaction (D-Schema)

- The evidence record loader's closed schema gains the optional
  `gate_run` mapping with exactly the keys in §1; unknown keys inside
  `gate_run` fail like unknown record keys (hint naming the key).
- `exit_class` must be `passed` or `failed`; `exit_code` must be an
  int if present; `command_argv`/`inputs` must be lists of strings;
  hash fields must match `sha256:<hex>`.
- `validate evidence` gains these shape checks. A receipt referencing
  nothing (empty argv) fails; a *missing* `gate_run` never does.
- Portfolio redaction classifies `gate_run.command_argv` and
  `gate_run.inputs` under the existing **paths** dimension of the
  share profile — default-deny, `--include-paths` overrides per
  export. Hashes and `exit_class` are shareable.

---

## 4. CONTEXT.md terms (same change, glossary only)

- **Gate-run receipt** — optional immutable provenance fields frozen
  onto an objective-gate evidence record at judgment time: the
  executed command identity, root-relative inputs, exit class, and
  output hashes. A receipt records how a gate ran; it never judges,
  never gates eligibility, and never asserts progress. Gate output
  itself is never stored — only hashes.
- **Exit class** — the bounded classification of an objective gate
  run: `passed` (exit zero) or `failed` (non-zero). Inability to run
  is not an exit class and produces no record.
- **Graph-impact diagnostic** — a read-only advisory report of what a
  curriculum edit would change: derived readiness flips among
  non-asserted nodes, recommendation changes, dangling references,
  and no-op edges. It never blocks a human action, never writes, and
  never revokes asserted progress.
- **No-op edge** — an edge whose removal changes no derived readiness
  and no recommendation; reported by the graph-impact diagnostic as
  advisory.

---

## 5. Tests (TDD order)

- Pure planner: widened `GateRunner` seam; receipt construction;
  `GateUnrunnable` writes nothing; manual gates never carry a receipt;
  eligibility math ignores receipts
  (`tests/evidence/test_submission.py`).
- Handler: capture-and-echo run, receipt fields on the appended
  record, unrunnable-still-writes-nothing, byte-stable append
  (`tests/evidence/test_submit_command.py`).
- Schema: optional presence, unknown-key rejection, type checks, seed
  loads clean (`tests/evidence/test_records.py`,
  `tests/evidence/test_evidence_validation.py`).
- Redaction: receipt paths classified under the paths dimension
  (`tests/portfolio/`).
- Impact core: flips with and without asserted nodes, rec diffs,
  dangling refs, no-op detection, determinism
  (`tests/graph/test_impact.py`).
- Command: read-only-no-event, exit-0-always, `--from`/`--baseline`
  resolution, non-git failure (`tests/cli/test_graph_impact_command.py`).
- Safety: `tests/release/test_v22_safety_gates.py` — no automated
  pass/master/delete path; asserted-progress immutability under
  flips; receipt fields never influence state.

---

## 6. Docs & release

- `CONTEXT.md` §4 terms in the same change.
- `POST_V2_ROADMAP.md`: append v2.2.0 to Shipped with verification
  note.
- Version bump v2.2.0; `RELEASE_NOTES` entry; issues per
  `docs/agents/issue-tracker.md`.
- Note: the research note pins `evidence/records.py`, retired since —
  cite the current tree in references, not the research doc's line
  pins.

---

## 7. Exit gates

Functional:

```bash
pytest tests/evidence tests/graph tests/cli tests/release
skilltrace validate evidence
skilltrace graph impact              # seed: no edits since HEAD → "no changes"
skilltrace graph impact --from HEAD  # same, explicit
skilltrace validate graph
skilltrace health
```

Safety (mirroring the Tier 2 shape):

1. Unrunnable objective gate still writes no record, no receipt, no
   event.
2. A record carrying `gate_run` never changes pass-eligibility or
   readiness.
3. Manual-gate records carry no receipt.
4. `graph impact` appends no event; asserted states never flip in its
   output.
5. `gate_run` never carries raw gate output (hashes only).
6. Doc gate: this spec exists; §7 command list matches verbatim.
7. Doc gate: `CONTEXT.md` carries Gate-run receipt / Exit class /
   Graph-impact diagnostic (/ No-op edge if touched).

---

## 8. Invariants and constraints preserved

- Hard boundaries (`AGENTS.md`): receipts and diagnostics never flip
  `pass_node`/`master_node`/`delete_record`; asserted progress never
  moves backward; AI review never an acceptance authority.
- Markdown/YAML truth; `edges.yaml` sole relationship source; the
  event log stays audit-only; export/redaction contracts untouched
  except §3's classification.
- The engine's git use is confined to one read-only file-fetch seam
  for baseline loading — no write path, no state.

---

## 9. Acceptance — this spec is done when

- [ ] All D-* decisions above filled (done in this doc).
- [ ] No product or architecture decision remains blocking the §7
      gate.
- [ ] Fresh-clone run of the §7 functional gates exits 0 on seed;
      safety + doc gates green.

---

## References

`CONTEXT.md` (Node states, Progress record, Evidence record,
Acceptance authority, Event log, Share profile, Redaction override);
`docs/POST_V2_ROADMAP.md:65` (v2.2 slot row + Beyond "Full
gate-runner/scheduler-queue");
`docs/research/evidence-provenance-and-operational-contracts.md`
(ranked questions 1 + 5 — line pins predate the `evidence.py` merge;
cite current tree);
`docs/research/ten-repository-additive-adoption-roadmap.md` §3
(receipt schema from vimhjkl's observable-final-state grader);
`src/skilltrace/evidence/submission.py`,
`src/skilltrace/commands/submit.py`,
`src/skilltrace/graph/validation.py`,
`src/skilltrace/graph/recommendation.py`,
`src/skilltrace/commands/validate.py`,
`src/skilltrace/portfolio/redaction.py`;
`docs/spec-v2.1-adaptive-sequencing.md` (this spec's template);
R-Provenance #194, G-Slots #196.




