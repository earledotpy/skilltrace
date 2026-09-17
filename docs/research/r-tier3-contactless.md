# R-Tier3Contactless — Tier 3 sized from public sources, no outreach

> **Ticket:** [#284 — R-Tier3Contactless](https://github.com/earledotpy/skilltrace/issues/284) (parent map [#275](https://github.com/earledotpy/skilltrace/issues/275))
> **Branch:** `research/r-tier3-contactless` · **Commit:** see the pointer comment on #284
> **Built on:** R-Tier3 ([#96](https://github.com/earledotpy/skilltrace/issues/96)) `research/r-tier3-ecosystem.md`; the S-Tier3-PKMPluginAuthor prep artifact ([#106](https://github.com/earledotpy/skilltrace/issues/106), `c0513e0`, branch `research/s-tier3-pkm-plugin-author`); the locked G-ROI rubric ([#99](https://github.com/earledotpy/skilltrace/issues/99)) and its worked Tier 3 table.
> **Scope:** Tier 3 items **MC-1, MC-2, MC-3, PKM-2, PKM-3, PKM-4** sized from public sources only, contactless. Four questions, per the ticket: (i) what each item demands of the three holding contracts — single-writer CLI/Serve write path, default-deny share profile, sync conflict matrix; (ii) the SkillTrace-side design of the buffered-write + human-approval pattern (propose → human-approve → apply) against those contracts; (iii) public-doc-only cost/ROI sizing carrying the fragility risks R-Tier3 named; (iv) a go/no-go pre-read for the human outreach calls, #106's four questions unchanged.
> **Contact posture:** no maintainer was contacted; no message, issue, e-mail, or DM was sent to any upstream project. Nothing here commits SkillTrace to any plugin or protocol.
> **Verification posture:** every external claim is a primary source read on **2026-09-16** (repo READMEs, ADRs, changelogs, developer docs, GitHub code search); every local claim cites the current tree (`main` = `58756d2`) or a named research branch. Claims public sources cannot settle are marked **human-only**.

## 1. TL;DR

| Item | Locked-rubric ROI (#99) | Contract demand found here | Contactless verdict |
|---|---|---|---|
| **MC-1** `init --from-curriculum` | **M** (L=M, C=H) | none — a new CLI subcommand that copies curriculum files without the progress store | Eligible, unchanged; no outreach warranted (no maintainer in the loop) |
| **MC-2** `curricula` registry | **L** (L=L, C=M) | a user-machine registry file; SkillTrace is its only writer | Eligible, unchanged; no outreach warranted |
| **MC-3** per-record `curriculum_id` | not scored (#99's resolution ruled the analysis out of scope) | a scope axis on the node loader, progress store, evidence loader and export pipeline + schema version bump + ADR | **No-go by construction** — it contradicts the single-learner glossary ruling (`CONTEXT.md:1-8`). A glossary question if ever revisited; never a PKM question |
| **PKM-2** `publish --vault` | **L** (L=L, C=M) | **all three**: single-writer (one writer per path), share profile (the published file is an *outbound* surface), conflict matrix (the target directory sits inside a foreign tool's sync domain) | Sized low-cost, but carries the sharpest *new* footgun found here (see §7): the vault's own sync engine is a second writer to that directory |
| **PKM-3** buffered write | **L** (L=L, C=M), *"provisional — awaits maintainer reply"* | single-writer (a proposal must not become a write path), share profile (inbound text must not leak outbound), plus a validation path for untrusted input | **The provisional flag discharges contactlessly.** An engine-owned approval surface (variant A/A′, §5) needs no upstream plugin, so the maintainer dependency is not load-bearing for PKM-3-as-an-engine-feature |
| **PKM-4** full bidirectional | **L** (L=L, C=M); long-horizon; pre-ADR on the hard-boundary extension | identity + hash + conflict protocol, an ADR extending the hard boundary to external writes to asserted progress, and a poll/watch surface the engine does not currently have | **No-go now.** The ecosystem moved *away* from two-way (Logseq's landed mirror ADR rules bidirectionality out in its own Non-goals) |

### 1.1 The five findings that change the picture

1. **The contract that bites first is not the sync conflict matrix — it is "one writer per path", applied inside a vault.** A published projection lands in a directory whose sync engine (Obsidian Sync, Sync Engine, Logseq's mirror, Syncthing) is a *second writer* that mirrors, propagates deletions, and occasionally loses data. Verified live: Sync Engine **v3.1.7 (2026-09-14)** lists *"Fixed critical data loss caused by running the migration on devices with 'Sync strategy' set to 'Mirror remote'"* (`CHANGELOG.md`).
2. **The reference implementation's own rationale does not transfer — and that is good news for the engine.** dg-team-mcp moved approval out of the terminal because *"Users couldn't see WHERE in their graph the write would land. Terminal approval was disorienting"* (ADR-017, 2026-04-02) — a *placement* problem about block position. SkillTrace state changes have no target parent; they are whole-record assertions with derived eligibility. A SkillTrace-owned approval surface therefore does **not** inherit the disorientation that motivated approval-in-target-app, and PKM-3 does not require upstream cooperation to exist.
3. **The originators themselves supply the counter-case.** ADR-018 (2026-07-26) declined to route a write through the ADR-017 approval bridge because rendering an opaque payload *"communicates nothing, so the approval step would be theater"* — and shipped a validated, idempotent, `dry_run`-able direct write instead. Criterion for SkillTrace: an approval surface must show *what the proposal changes and why it is eligible*, or drop the ceremony for refuse-rather-than-guess plus a preview.
4. **The reference protocol is not durable.** ADR-017's trade-offs state *"Resolution tracking is in-memory (lost on server restart)"*. Any SkillTrace port must state its proposal durability explicitly; the engine's files-are-truth posture points at a disposable, file-based inbound inbox rather than an in-memory registry (§5).
5. **The named re-open trigger has not tripped, and the movement is asymmetric** (§7): the only buffered-write implementation is still a self-declared proof of concept with **zero adopters** (code search for `propose_write_batch`: 4 hits, all in the origin repo); Logseq landed an explicitly **one-way** derived mirror; Obsidian's plugin API is mid-migration with breaking changes; and the most architecturally-fit Obsidian sync plugin shipped a critical-data-loss fix two days before this reading.

## 2. Method and limits

**What public sources settle.** The exact text of the three holding contracts (they are written down in this repo); the protocols and trade-offs of the reference implementations (READMEs, ADRs, changelogs, API docs); the ecosystem's current churn rate (release dates, breaking-change notes, code-search adopter counts); and the *shape* of the cost on each side of the boundary (what a plugin must implement vs. what the engine must implement).

**What they cannot settle.** (a) Whether a maintainer would accept a given change — that is precisely #106's four questions and stays human-only. (b) **Whether the learner uses a PKM at all, and which one.** No Obsidian, Logseq, or vault reference exists anywhere in `graph/`, `policy/`, or `docs/USER_GUIDE.md`; every mention in the tree lives inside `docs/research/` comparisons. This is the cheapest first gate for any go decision and it is **human-only**. (c) Whether a given plugin's *source* tolerates a foreign ignored subtree — readable from public code, but not verifiable without running it against a live vault.

**What this artifact is not.** It does not graduate Tier 3, does not edit `docs/POST_V2_ROADMAP.md` (that is [G-RoadmapWrite #282](https://github.com/earledotpy/skilltrace/issues/282)), and proposes no code change. It is the contactless sizing input #280 named when it amended the Tier 3 re-open trigger.

## 3. The holding contracts, as they exist today

Four contracts, not three. Three are named in the ticket; the fourth — plugin capabilities — is the one a Tier 3 integration trips first, and skipping it would under-size every PKM item.

### 3a. Single-writer CLI/Serve write path

- The dispatcher is *"the single chokepoint for the two cross-cutting rules (roadmap decision 13)"* — audit (one event per successful mutating command, none for read-only) and the automation boundary, which refuses a forbidden automation action *before* the handler runs and without logging an event (`src/skilltrace/dispatch.py:1-16`). Read-only vs mutating is declarative on the `Command`, not inferred.
- Serve is explicitly not a second path: *"its writes are the same explicit, confirmed learner commands as the CLI's, never a second path. Serve shows truth but is never a source of it, and nothing it renders is ever read back by the engine"* (`CONTEXT.md:384-391`).
- The hard boundary is defined in terms that decide a proposal channel's fate: a policy *"the engine enforces by refusing the action (non-zero exit)… *Automation* means an action firing as a side effect of another command"* (`CONTEXT.md:124-128`). A proposal that applies itself is exactly such a side effect.
- The *written* single-writer contract is not yet specified. The operational-contracts research states the precondition for any concurrent writer: *"Before a concurrent writer ships, specify repository-scoped serialization, reload-after-success, and stale-write refusal/diagnostic behavior. All asserted-progress writes still route through core dispatch"* (`docs/research/evidence-provenance-and-operational-contracts.md:57`).
- `POST_V2_ROADMAP.md:214-217` lists it as a holding contract: *"every UI action is a dispatcher-mediated command appending one audit event; re-opens only if a surface ever needs a second write path — an ADR-gated change, never a slot."*

### 3b. Default-deny share profile

`CONTEXT.md:442-452`: no paths, notes, blocker text, review text, free text, or URLs appear in outbound surfaces unless an explicit `--include-*` override is passed; the profile is *"enforced by a single redaction module; no format may bypass it"* (`src/skilltrace/portfolio/redaction.py`), with a redaction-bypass static scan as a release gate (SA5, `docs/spec-v2.0-portfolio-builder.md:521-523, 607`); overrides are never persisted.

Two consequences the ticket's phrasing only hints at:

1. **A file written into a vault is an outbound surface.** It leaves the repo, and a vault is normally shared, published, or synced. Node titles and derived state are fine; paths, resource URLs, note text, and blocker text are not, unless the learner passes an override for that one invocation.
2. **Redaction must hold on the way *in*, too.** Proposal text copied into an engine record becomes outbound the moment a portfolio export renders it. An inbound channel is therefore a share-profile surface, not just a validation surface.

### 3c. Sync conflict matrix (transport's gate)

The written precondition: *"Require a written matrix for immutable records, supersession heads, learner assertions, graph/policy edits, artifacts, and missing plugins before accepting any transport prototype. `sync` remains readiness-only"* (`evidence-provenance-and-operational-contracts.md:58`), listed as a holding contract at `POST_V2_ROADMAP.md:218-220` — *"re-opens when cloud sync re-opens — it is transport's gate."*

Note the scope of that gate: it is written for **cloud sync**. The contactless finding in §7 is that PKM-2/PKM-3 reach the same class of problem *without* cloud sync, because the target directory is already inside somebody else's sync engine.

### 3d. Plugin capabilities (the fourth contract)

The proposed safe capability set: *"declarative/versioned importer, renderer, advisory analyzer, artifact producer, and objective-gate adapter capabilities. Require core validation/dispatch for writes; prohibit direct asserted-progress writes, edge mutation, or authority registration. Pin relied-on plugin identity/version in a future receipt"* (`evidence-provenance-and-operational-contracts.md:59`). `POST_V2_ROADMAP.md:221-222` is blunt about the price of entry: *"no third-party capability surface in the engine; re-opens with Tier 3 integrations."*

So the honest summary of the four contracts in one line each:

| Contract | What it forbids that Tier 3 wants | Status |
|---|---|---|
| Single-writer | any second write path; any write that fires as a side effect | Written, ADR-gated to change |
| Share profile | any outbound field without an explicit per-invocation override | Written, release-tested |
| Sync conflict matrix | any transport before a written conflict matrix exists | Written as the gate; matrix itself unwritten |
| Plugin capabilities | direct asserted-progress writes, edge mutation, authority registration | Written; no capability surface exists yet |

## 4. Per-item demand, item by item

### 4a. MC-1 — `init --from-curriculum <path>`: touches nothing

Demand on the four contracts: **none**. It is a local CLI subcommand that copies a curriculum directory while deliberately omitting the progress store, and nothing it writes is read by a different component than today. No schema change, no ADR, no capability surface. Cost: one subcommand plus documentation. ROI stays **M** (L=M, C=H) and the R-Tier3 coherence-vs-reach caveat stands (`r-tier3-ecosystem.md:327, 340`). **No outreach warranted** — no maintainer is in the loop for a SkillTrace-side file copy.

### 4b. MC-2 — `curricula <list|fork|switch|remove>`: a registry outside the repo

Demand: a `curricula.yaml` locator at the user-machine level, never inside a repo, so files-are-truth is preserved (the registry is a *locator*, not learner state). The one new discipline: every command resolves its root first and never writes across repos. The three named contracts are untouched. R-Tier3 already notes a third-party orchestrator could be built around existing `sync`/`validate` commands without this command existing at all (`r-tier3-ecosystem.md:328`) — that is exactly the "compound value only" shape that scored **L** in #99. **No outreach warranted.**

### 4c. MC-3 — per-record `curriculum_id`: no-go by construction

Demand: a new scope axis threaded through the node loader, progress store, evidence loader, and export pipeline, plus a schema-version bump and an ADR (`r-tier3-ecosystem.md:329`). Its direct contradiction is the glossary, not a contract: single-learner by design, *"one clone is one learner's identity; no record carries a user field"* (`CONTEXT.md:1-8`). `curriculum_id` is the same shape of field, one axis over. #99's resolution already ruled the analysis out of scope. **Verdict: no-go by construction.** If multi-curriculum *records* ever become a real requirement, the honest primitive is already documented — clone the curriculum without the progress store — and the question belongs to a glossary change plus an ADR, never to a PKM integration. It is listed here only because the ticket names it; it is not sized, because sizing it would imply it is available.

### 4d. PKM-2 — `publish --vault`: all three contracts, zero upstream cost

Demand on **single-writer**: the published file is written only by SkillTrace; the engine never reads it back, and it must be declared as a one-way projection in the same terms the portfolio bundle already uses (*disposable, gitignored, never read back* — `CONTEXT.md:460-466`, `docs/spec-v2.0-portfolio-builder.md:607-609`).
Demand on the **share profile**: the published file is outbound, so it must pass through the single redaction module rather than being assembled field-by-field by a new renderer. The cheapest contract-safe shape is a projection that renders *redacted* content by default — node id, state, title only — with the existing `--include-*` overrides as the only way to add paths, notes, or URLs.
Demand on the **conflict matrix**: PKM-2 is the item that makes this contract relevant *without* cloud sync, because the vault directory is already replicated by another process (§7). Four verified behaviours matter: mirror-remote strategies that propagate deletions; conflict strategies that create divergent copies; duplicate-producing strategies inside the tree; and migration-time data loss.
Upstream cost: **zero** — nothing has to change in a plugin to read a file in a vault.
Footguns carried from R-Tier3 plus one new one: vault bloat from regenerated projections; the published snapshot read as truth by a *human* (the engine never reads it back, but nothing stops the learner mistaking a stale projection for current state — an honesty-banner-shaped problem, and v2.0 already has that precedent for superseded/stale content).

### 4e. PKM-3 — buffered write: two contracts plus a new validation obligation

Demand on **single-writer**: a proposal must never be a write path. The proposal arrives, the *learner* confirms, the confirmation nests the ordinary command through the dispatcher, the event lands, and the record is written once. Any design where the proposal file itself flips state fails this contract outright — and trips the hard boundary, because that is an action firing as a side effect (`CONTEXT.md:124-128`).
Demand on the **share profile**: see §3b(2). Proposal text entering an engine record is a redaction dimension, not free text.
New obligation: an **untrusted-input validation path**. This is genuinely new for the engine — every current inbound write path is a learner typing a command. The proposal must be parsed, bounded, and validated against the same eligibility rules the command re-derives anyway, and it must be *provably non-authoritative* (§5c, contract statement 5).
Demand on the **plugin capabilities** contract: none, *provided* SkillTrace owns the approval surface (variant A/A′). The moment an upstream plugin renders approvals or holds proposal state (variant B), that contract re-opens and the plugin-identity/version receipt question with it.
Cost: depends entirely on variant (§5b). Upstream cost: **zero** for A and A′.

### 4f. PKM-4 — full bidirectional: an ADR, a protocol, and a surface the engine does not have

Demand: (i) an identity + hash + conflict protocol; (ii) an **ADR**, because the honest reading of the hard boundary is a question about whether it extends to *any* external write to asserted progress (`r-tier3-ecosystem.md:333`); (iii) a **durable poll/watch surface**, which the engine does not currently have — `serve` is request-driven and renders from truth at each request (`CONTEXT.md:384-391`), so there is no background process to poll a vault; (iv) a multi-version compatibility commitment, priced against an upstream ecosystem whose plugin API and sync modules are mid-migration (§7).
Verdict: **no-go now**, unchanged from R-Tier3's *"High long-horizon, low near-term"* — but for a new reason: in 2026 the ecosystem moved *toward* one-way derived projections and *away* from round-tripping (§7).

## 5. The buffered-write + human-approval pattern, from the public record

### 5a. What the four public implementations actually specify

**dg-team-mcp (Roam / DiscourseGraphs) — the pattern's origin.** Four tools, quoted from the README: `propose_write_batch` (*"Buffer a same-parent append batch. Multiple batches to different parents coexist"*), `propose_write` (a one-branch convenience wrapper), `get_pending_write_batch` (*"Poll a batch by ID. Returns `pending` while waiting, or `resolved` with `approved`/`rejected` after the user acts in Roam"*), and `clear_pending_write_batch` (*"the Roam plugin handles this normally"*). The architecture is a chain of three surfaces: MCP client → server → *"Write-visibility bridge (127.0.0.1:3597)"* → *"Roam Desktop (Local API) / Roam Plugin (apps/roam/) → Your Roam Graph **polls bridge, renders virtual blocks, approve/reject per batch**"*. Known limitation: *"Roam Desktop must be running."*

ADR-017 (*"Roam-Native Multi-Batch Write Approval"*, 2026-04-02, Accepted) gives the rationale and the price: rationale — *"The original write visibility showed pending writes in the terminal (Claude Code). Users couldn't see WHERE in their graph the write would land. Terminal approval was disorienting"*; price — *"Requires Roam plugin installed. Plugin polls bridge every 1.2s (lightweight). **Resolution tracking is in-memory (lost on server restart)**."*

ADR-018 (2026-07-26) documents the originators declining the pattern for one write: *"**Why not route through the ADR-017 approval bridge:** that bridge renders proposed writes as virtual blocks at a target parent so the user can see where content lands. A relation record is a uid-stringed block full of opaque props — rendering it as a bullet communicates nothing, so **the approval step would be theater**."* What it shipped instead is the interesting half: a write that is validated (*"refuses rather than guesses"*), idempotent (*"an identical directed triple returns the existing `relation_uid`"*), directionally honest (*"It writes one direction only"*), previewable (*"`dry_run` resolves and validates without mutating"*), and whose safety property is stated as behaviour rather than as a gate (*"points 3–7 … are the actual safety property and are unconditional"*). The 2026-08-08 amendment flipped its default to on, reasoning: *"A safety gate that pushes work onto an unsafer path is not a safety gate."* Its trade-off is explicit: *"The idempotency check is check-then-write, so two concurrent identical calls can still race in a duplicate record."*

**Obsidian Sync Engine (`hesprs/sync-engine`) — where an approval strategy would have to plug in.** Conflict strategies now read *"smart merge / keep both / latest survive / keep remote / keep local / skip"* (note `smart merge`, which R-Tier3's reading of the same README did not list). The module surface is a list of extension *types*: *"You can add backends, optimizers, sync triggers, i18n resources, **decision strategies, conflict strategies**, setting entries, custom file processing, and invoke all possible operations in custom modules"*, and *"Repo accepts any module contribution as long as it respects contribution guide"*, with module verification and a module-management UI. Its own documented flow already contains a human confirmation step for *sync tasks*: *"Review the sync tasks that will be performed. Click 'Confirm', and your files will arrive the configured backend."* The roadmap still names v3.0 (*"Rewrite entirely, dynamic module loading, module store, asymmetric storage, and rebrand"*), v3.1 (settings migration to the Obsidian v1.13 API) and v3.2 (*"Granular sync strategy selection / exclusion inclusion rule refactor"*).

**Obsidian's own API — the cost of a plugin-side approval UI.** `Vault.process(file, fn, options)` is documented as *"Atomically read, modify, and save the contents of a note"*; `Vault.create`, `modify`, `append`, `delete`, `trash` and the `create`/`modify`/`delete`/`rename` events are the rest of the write surface. For approval UI, `Modal` + `Setting` + a submit button is the documented pattern (*"The result is passed into the `onSubmit` callback when the user clicks Submit"*), with `SuggestModal`/`FuzzySuggestModal` for lists. New in **1.14.2 (2026-09-15)**, per the changelog's Developers section: *"Added a new **ConfirmationModal** component"* — a first-party approval primitive, which measurably lowers the plugin-side cost of variant B if it is ever wanted.

**Logseq — the derived-subtree contract, written down.** `docs/adr/0016-markdown-mirror.md` (*"Electron Markdown Mirror"*, 2026-05-05, Accepted) is the closest public precedent for how a *foreign* projection should behave inside somebody else's directory: *"Logseq writes derived Markdown files under the current graph directory: … `mirror/markdown/pages/<page-file-name>.md`"*; *"Markdown Mirror is derived output. **The DB remains the source of truth**"*; *"Files under `mirror/markdown/**` **must be ignored by graph import, file watchers, and graph parsing so the mirror never feeds back into the graph**"*; and, decisively, its Non-goals open with *"1. Markdown Mirror is not bidirectional sync. 2. Editing files in `mirror/markdown/` does not update the graph. 3. The mirror is not a backup format with guaranteed import fidelity."* Trade-offs it accepts: *"External edits to mirror files are overwritten by later Logseq edits"*, a per-graph index is needed *"for reliable rename and delete cleanup"*, and the feature is Electron-desktop-only. The write-side protocol (pinned `3de7c751`) is a token-authenticated WebSocket to `/sync/:graph-id` with a transaction model: `tx/batch` uploads, `tx/reject` with `:missing-block-uuids`, and `GET /sync/:graph-id/repair/blocks` returning server-authoritative datoms; its own header says *"keep this document in sync with the current implementation."*

### 5b. Three transferable rules, then the SkillTrace-side design

1. **Each side must be the only writer of the paths it owns**, and a derived subtree must be namespaced and excluded from the other side's watchers, import, and parsing. Logseq writes this into an ADR; dg-team-mcp lives it via a loopback bridge; sync-engine warns that *"it's generally not recommended to manually manage your remote storage"*. This is the R-Tier3 §5c failure mode (*"two engines on the same directory"*) stated as a rule.
2. **The approval surface must carry information the learner needs, or be skipped.** ADR-018's *"theater"* test is the sharpest form available: show the target and the effect, or use validated direct writes with a dry run.
3. **Identity and durability must be stated, not inherited.** The origin's resolution tracking is in-memory and lost on restart; Logseq needs a per-graph index for rename/delete cleanup; dg-team-mcp needs batch IDs because *"fire-and-forget proposals break the feedback loop"*.

### 5c. Three variants of "propose → human-approve → apply" on the SkillTrace side

All three keep the same spine: **the proposal is inert, the human approves, and the ordinary command does the writing through the dispatcher.** They differ only in *where the proposal arrives* and *where the learner approves* — and that difference is exactly where the maintainer dependency lives.

**Variant A — SkillTrace-owned inbox, file-based (recommended first).**
The PKM side writes a proposal file into a SkillTrace-owned, ignored directory (e.g. `proposals/inbox/<id>.yaml`). Nothing else changes on the PKM side: a template note, a macro, a small plugin, or a shell one-liner can produce it — so **any** PKM can participate, including one with no plugin at all, and a learner can hand-write a proposal. The learner then runs `skilltrace propose list`, `propose show <id>`, `propose approve <id>` / `propose refuse <id>`; approve nests the real command through the dispatcher, with `source` recorded in the audit event exactly as Serve does today.
- Engine cost: one inbound read path, one command family, a bounded proposal schema, validation + refusal copy, tests. No scheduler, no daemon, no plugin, no schema-version bump (if the inbox is disposable — §5d).
- Upstream cost: **zero.**
- Weakness: the approval UX is the terminal — precisely what ADR-017 rejected for *its* case. But §1.1(2) applies: SkillTrace's approval surface shows derived eligibility and node context, not a spatial drop target, so the disorientation that motivated ADR-017 does not carry over.
- This is the variant that **discharges the #106 dependency** for PKM-3-as-an-engine-feature.

**Variant A′ — Serve proposal endpoint (recommended second, when Serve is next touched).**
The PKM side (or a Shortcuts action, or a `curl` in a template) POSTs the proposal to the local Serve process with a per-invocation token; Serve renders it *with the eligibility it derives* and a confirm affordance; confirm nest-dispatches with `source="web"`, exactly the existing browser-write path (`src/skilltrace/dispatch.py:38-58`).
- Engine cost: one route, a token/consent story, and the same validation as A. **No second write path** — Serve already writes only through dispatch (`CONTEXT.md:384-391`).
- Upstream cost: zero-to-small (the PKM needs *something* able to make an HTTP request).
- Strength: the approval screen can carry the theater-test information (which node, current state, what changes, why it is eligible) in v2.4's card vocabulary rather than a terminal transcript.

**Variant B — PKM-native approval (the thing #106 was actually asking about).**
Proposals are rendered inside the vault (virtual blocks or a card) and the engine polls for a resolution — a direct port of dg-team-mcp.
- Upstream cost: a per-PKM plugin surface; every PKM needs its own implementation, and the capability/identity-receipt contract (§3d) re-opens.
- Engine cost is the *larger* one: a poll/watch loop, which the engine has no home for (Serve is request-driven), plus proposal state that must survive processes, plus the availability coupling dg-team-mcp documents (*"Roam Desktop must be running"*).
- Verdict: **defer behind a maintainer reply and a learner demand signal.** It buys ergonomics, not capability — variant A already reaches every PKM; variant B is the only one that needs somebody else's cooperation, and the only one whose original rationale (§1.1(2)) does not transfer. ADR-018 reached the same conclusion from the other side: its authors declined their own bridge when the approval screen would have communicated nothing.

**Sequencing recommendation:** A first (smallest blast radius, zero dependency, fully testable against today's contracts); A′ when the Serve surface is being changed anyway; B only on evidence. None of the three requires the sync conflict matrix to be written, because none of them replicates SkillTrace state — a useful scoping result: **PKM-3 is not a transport.**

### 5d. The six contract statements, and the tests that hold them

1. **A proposal is input, not truth.** An unapproved proposal changes nothing; deleting the inbox changes nothing; the inbox is never read to compute state. (Portfolio-bundle precedent: disposable, gitignored, never read back — with one explicit exception: a proposal is read *once*, at approval, as untrusted input.)
2. **Apply is always a learner command.** No timer, no watcher, no auto-approve; approval names exactly one proposal; the audit event records the source.
3. **Eligibility is re-derived at apply time.** The proposal carries no verdict, no authority, and no accepted record — it carries a request.
4. **The proposal is bounded and disposable.** Field and size limits, a parse failure that refuses with a named fix, and no new record type, which avoids an immutability/supersession burden the pattern does not need.
5. **It is provably non-authoritative.** A hostile or tampered proposal cannot pass, master, delete, or override a prerequisite; the only path to those states is the existing command path, unchanged.
6. **It obeys the share profile in both directions.** Inbound: proposal text copied into a record stays redacted on outbound render unless an override is passed. Outbound: anything SkillTrace writes into a vault is redacted by default.

Tests that make those statements checkable (each mirroring an existing suite's style):

- **Poisoned proposal** — a proposal claiming `pass` on a locked node: approve refuses, exits non-zero, writes no record, appends no event, leaves state unchanged.
- **Non-authority / equivalence** — approving a valid proposal produces the same record, and exactly one event, as running the underlying command directly.
- **Read-only** — `propose list` / `propose show` append no events (mirrors `analytics` and `portfolio preview`).
- **Inbox absent or malformed** — every existing command behaves exactly as today; nothing degrades.
- **Redaction** — proposal-supplied text does not appear in a default-redacted export.
- **Idempotency** — approving the same proposal twice applies once and refuses the second with a named reason (ADR-018's check-then-write race is the precedent for testing this explicitly instead of assuming it).

## 6. Cost / ROI sizing per item, from public docs only

Scored on the locked rubric (L × C, H=3/M=2/L=1, combined = mean rounded down; hard-to-reversibility lives in the risk note, not the letter — [#99](https://github.com/earledotpy/skilltrace/issues/99)).

| Item | Engine-side cost | Upstream-side cost | Risk note (carried / new) | ROI |
|---|---|---|---|---|
| MC-1 | one subcommand + docs + tests; no schema, no record, no contract touched | none | coherence-vs-reach caveat carried; the fork footgun below | **M** unchanged |
| MC-2 | one command family + a machine-level registry file + tests | none | registry is a locator outside the repo, never truth; the fork footgun below | **L** unchanged |
| MC-3 | node loader + progress store + evidence loader + export pipeline + schema-version bump + ADR | none | contradicts the single-learner glossary ruling | **no-go** (not scored) |
| PKM-2 | one command + a projection renderer routed through the redaction module + an ignore/namespace policy + tests | **zero** | vault sync engine: mirror-remote deletion, keep-both duplicates, migration data loss; stale projection read as truth by the human; vault bloat | **L** unchanged (L=L, C=M) |
| PKM-3 | variant A: one inbound path + one command family + bounded schema + validation + the six tests in §5d. Variant A′: plus one route and a token story. Variant B: plus a poll/watch surface and per-PKM plugins | A/A′: **zero**. B: a plugin per PKM | proposal-hygiene (untrusted input) is new but bounded; B's availability coupling and upstream breakage carried | **L** unchanged (L=L, C=M), **provisional flag discharged** |
| PKM-4 | identity + hash + conflict protocol, an ADR, a durable poll/watch surface, a compatibility commitment | a client per PKM; SkillTrace owns the server side | the whole 2026 churn list in §7 | **L**, long-horizon, unchanged |

### 6.1 The two fragility risks R-Tier3 named, re-checked against today's shape

*(Citation note: the ticket cites "R-Tier3 §4" for these risks; in that artifact §4 is "Engine surface implications" — the footguns are §5c "two engines on the same directory", §5d "you can have multiple profiles, but please don't", and §5e "the cross-workspace move / fork-with-references footgun". Recorded here so a later reader can find them.)*

- **"Multiple profiles, please don't" (Anki, R-Tier3 §5d).** The recommended shapes actively avoid it: MC-1 copies a curriculum *without* the progress store, and MC-2 adds a locator file — both the lightest possible isolation primitive, versus Anki's heaviest (separate database + separate sync account). The risk is not re-created by anything recommended here. It is one more reason MC-3 is a no-go: a per-record scope field is the same error one level down.
- **Cross-workspace move / fork-with-references (Tana, R-Tier3 §5e).** This one *is* inherited by MC-1 and MC-2, and it is engine-local rather than PKM-shaped: a forked curriculum that drops nodes silently breaks `LearningResource.node` references, remediation edges pointing into the dropped nodes, and evidence records naming them. Two mitigations already exist in the tree: the fork is a *copy* (the original's history stays true), and v2.2's read-only `graph impact` advisory reports dangling references before a curriculum release. Practical consequence for sizing: MC-1/MC-2 should ship *with* a "references removed" warning in the init/fork path, and that is the cheapest available mitigation — worth noting when either slot is written.
- **New risk this artifact adds (not in R-Tier3): "one writer per path" inside a foreign directory** (§4d, §5b rule 1, §7). It is not a score change, but it is the risk a PKM-2 slot must carry in its acceptance criteria, and it is the reason R-Tier3's §5c rule should be restated as a contract when either PKM-2 or PKM-3 is written.

## 7. The named re-open trigger, checked: "PKM-ecosystem rewrite settling"

All readings below are dated primary sources read on **2026-09-16**. The point of this section is that the deferral trigger can now be *read* rather than guessed at — which is what a contactless pass can uniquely contribute.

| Signal | Reading | Direction |
|---|---|---|
| **Obsidian Sync Engine releases** | 3.1.2 (2026-08-24) → **3.1.7 (2026-09-14)**, six releases in three weeks, commits through 2026-09-16. v3.1.7: *"Fixed critical data loss caused by running the migration on devices with 'Sync strategy' set to 'Mirror remote'."* Earlier entries: *"Many breaking changes are present although auto migration is provided. Strongly recommended to backup before upgrade"*; *"Fixed asymmetric storage occasionally drops uploaded directories undiscoverable"*; *"Fixed deleted files / folders come back due to asymmetric record update"* | **Not settled** — active churn, recent data-loss class |
| **Its roadmap** | v3.0 *"Rewrite entirely, dynamic module loading, module store, asymmetric storage, and rebrand"*; v3.1 settings migration to the Obsidian v1.13 API; v3.2 *"Granular sync strategy selection / exclusion inclusion rule refactor"* | Not settled (mid-v3) |
| **Obsidian itself** | 1.14.2 desktop + mobile (2026-09-15). Developers section: *"Added a new ConfirmationModal component"*, *"Added documentation and a migration guide for the new Settings API"*, a breaking change (`--callout-color` now OKLCH), installer moved to Electron v43.1.1 | Plugin API mid-migration (but a new approval primitive ships) |
| **Logseq** | `docs/adr/0016-markdown-mirror.md` Accepted **2026-05-05**: mirror is derived, `mirror/markdown/**` must be ignored by import/watchers/parsing, and Non-goal 1 is *"Markdown Mirror is not bidirectional sync."* Default-branch code search for `two-way`: **0 hits**. The db-sync protocol doc still says *"keep this document in sync with the current implementation"* | **Settled — in the one-way direction.** This is the sharpest new datum of the whole pass |
| **The buffered-write pattern** | Code search `propose_write_batch`: **4 hits, all in the origin repo.** The origin repo self-declares *"⚠️ Proof of Concept"*, 3 stars, **0 forks**, 27 commits, and its most recent commits (2026-09-15) add canvas features — the write-visibility protocol has not been extended or ported since 2026-04 | **Dormant, not settling.** Zero adoption |
| **SurfSense / evc-local-sync** | Unchanged in kind from the S-Tier3 prep reading: SurfSense push-only by design; evc-local-sync small (11 stars) with an "always ask" strategy already shipping | No settling signal |

**Verdict on the trigger.** The "rewrite settling" branch is **untripped**, and the movement is asymmetric in a way that matters more than the unsettled-ness:

- The ecosystem is settling **toward one-way derived projections**, and a major PKM has now written that contract into an Accepted ADR with an explicit ignore rule (`mirror/markdown/**`). That is *exactly* the shape PKM-2 wants, and it is now a documented norm rather than a SkillTrace invention.
- The ecosystem is settling **away from round-tripping** — which is precisely PKM-4, the item whose trigger needs the settling.
- The one pattern PKM-3 was shaped after has **zero adopters** and a self-declared proof-of-concept status, and its originators published a second ADR narrowing where the pattern is even applicable.

So a roadmap reader should see three different verdicts where the deferral line currently shows one trigger: PKM-2's precondition is *improving*, PKM-3's maintainer dependency is *dischargeable*, and PKM-4's precondition is *worsening*.

## 8. Go / no-go pre-read for the human outreach calls

This is the named trigger branch #280 created for the contactless pass: *"a go signal there trips the re-open discussion without contacting anyone."* The pre-read has to answer two things — which items would be worth the calls, and what each call would then need to answer.

### 8.1 Gate 0 — the gate no public source can open

**Does the learner use a PKM at all, and which one?** Nothing in `graph/`, `policy/`, or `docs/USER_GUIDE.md` mentions Obsidian, Logseq, or a vault; every mention in the tree lives in `docs/research/`. **human-only.** If the answer is "no PKM", then every PKM item here is moot, all four outreach calls would be social capital spent on a hypothesis, and the only live branch of the Tier 3 trigger is *fresh user-demand evidence*. This gate costs one question and should be asked before anything else.

### 8.2 Which items warrant calls, and what each must answer

**Go — `hesprs/sync-engine`** (the most architecturally-fit Obsidian candidate; module surface admits conflict/decision strategies; "review the tasks, click Confirm" already ships; responsiveness signal strong). The four #106 questions stand unchanged (§8.3), but two carry the weight now: **Q1** (does an externally-written, *ignored* subtree survive your strategies — specifically `mirror remote`, `smart merge`, `keep both`, and asymmetric storage?) and **Q3** (the failure mode you most want an external engine to know about). Framing caveat for the human: the plugin is mid-v3 with a documented policy refactor aimed at exactly this (*v3.2: granular sync strategy selection / exclusion inclusion rule refactor*), so the question is best asked about that direction rather than today's settings. Value of the call: it is the one item where an upstream answer changes a *contract* (the ignore/one-writer rule), not just a comfort level.

**Go, with tempered expectations — `DiscourseGraphs/dg-team-mcp`.** They own the pattern and wrote the only public ADRs about when it does and does not apply. But temper it: the repo is a self-declared proof of concept, 0 forks, ~3 stars, and its own ADR-018 narrowed the pattern's applicability for opaque payloads. The honest ask is design counsel on variant B (Q1/Q2), not adoption. Value: cheap (Discord), and their ADR-018 reasoning is a genuine second opinion on §5c's sequencing.

**No-go — `MODSetter/SurfSense`** (push-only by design; the pattern would be a new write direction, and the prep artifact already recommended against it), **`entire-vc/evc-local-sync`** (small base with an "always ask" strategy already shipping — worth *noting* as a third target in any slot's sizing, not worth a call now), and **`logseq/logseq`** (ADR 0016 already answers the two-way question publicly; there is nothing left to ask).

**Defer — PKM-4's protocol questions** until a learner demand signal exists. Asking a maintainer to co-design a round-trip protocol while the ecosystem moves away from round-tripping spends goodwill on the item with the worst precondition.

### 8.3 The four questions, unchanged (#106 verbatim)

1. Is the buffered-write pattern (propose → human-approve → apply) compatible with your plugin's write path, or would it require a new surface?
2. What is the maintenance cost of supporting a SkillTrace-style external engine that owns the source of truth and treats the PKM-side write as a derived view?
3. What is the failure mode you most want SkillTrace-side integrators to know about?
4. Would you accept a one-line PR to the plugin's docs naming SkillTrace as a supported external engine, or is that a higher-friction ask?

**One proposed reframing for the human to consider** (flagged, not decided here): #106's questions were written before variant A existed, so they assume SkillTrace needs the *plugin* to implement the pattern. Variant A means the engine can own approval outright. Reframed, Q1 becomes *"would you object to, or would you document, an external engine that writes a one-way projection into a namespaced, watcher-ignored subtree and never reads your files back?"* — a smaller ask that does not require the maintainer to build anything. Leave the four questions intact if the reframing is unwanted; do not mix the two framings in one message.

### 8.4 What a go signal would and would not do

A go signal from any call **does not graduate Tier 3**. It trips *the re-open discussion* — the same discussion #280 defined — and its most likely outcome is a *PKM-2-first* slot with the one-writer/ignore contract written into its acceptance criteria, with PKM-3 variant A sized behind it. PKM-4 stays deferred under its own trigger either way.

## 9. What this artifact does not do

- **It does not graduate Tier 3.** The slot trigger stands as #280 amended it; this pass adds a reading of that trigger, not a decision on it.
- **It does not edit `docs/POST_V2_ROADMAP.md`.** That is [G-RoadmapWrite #282](https://github.com/earledotpy/skilltrace/issues/282). Two concrete corrections are handed to it: (a) the Tier 3 line's *"PKM-3 is additionally provisional pending maintainer replies"* clause, which this pass discharges for the engine-owned variants; (b) the single-trigger phrasing, which §7 replaces with three differently-directed verdicts.
- **It proposes no ADR.** Nothing here is hard-to-reverse, surprising, and a genuine trade-off at once. The ADR the record does contemplate (extending the hard boundary to external writes to asserted progress) belongs to PKM-4 if that item ever moves.
- **It makes no glossary change.** If a proposal surface ever ships, `Proposal` will need a `CONTEXT.md` entry (a non-authoritative, disposable inbound artifact) — and per `AGENTS.md` that lands *in the same change*, not before it.
- **It stays inside the six named items.** No slot ordering, no acceptance criteria, and no commitment to any upstream project.

## 10. Sources

**External — all read 2026-09-16, dates as printed by the source.**

- `DiscourseGraphs/dg-team-mcp` — README (*"⚠️ Proof of Concept"*, buffered-write tool table, bridge at `127.0.0.1:3597`, *"Roam Desktop must be running"*) and `ADR.md` (ADR-017 *"Roam-Native Multi-Batch Write Approval"*, 2026-04-02; ADR-018, 2026-07-26 + 2026-08-08 amendment) — https://github.com/DiscourseGraphs/dg-team-mcp
- GitHub code search, `propose_write_batch` — 4 hits, all in the origin repo (2026-09-16)
- `hesprs/sync-engine` — README (module types, conflict strategies, *"Review the sync tasks … Click 'Confirm'"*, roadmap v3.0–v3.2), `CHANGELOG.md` (v3.1.7, 2026-09-14, migration data loss under Mirror remote), releases 3.1.2–3.1.7, issue #214 (🗳️ Wishlist, open since 2026-08-09) — https://github.com/hesprs/sync-engine
- Obsidian developer documentation — `Vault` (`process` = *"Atomically read, modify, and save"*, `create`/`modify`/`append`/`delete`/`trash`, file events) and Modals (`Modal` + `Setting` + submit) — https://docs.obsidian.md/Reference/TypeScript+API/Vault · https://docs.obsidian.md/Plugins/User+interface/Modals
- Obsidian changelog — 1.14.2 desktop and mobile, 2026-09-15 (Developers: *ConfirmationModal*, Settings-API migration guide, `--callout-color` breaking change, Electron v43.1.1) — https://obsidian.md/changelog/
- `logseq/logseq` — `docs/adr/0016-markdown-mirror.md` (*"Electron Markdown Mirror"*, 2026-05-05, Accepted) — https://github.com/logseq/logseq/blob/master/docs/adr/0016-markdown-mirror.md
- `logseq/logseq` — db-sync client-server protocol, pinned `3de7c751` — https://github.com/logseq/logseq/blob/3de7c751/docs/agent-guide/db-sync/protocol.md

**Local.**

- `CONTEXT.md` — Learner and single-learner-by-design (1-8); node states and asserted progress (30-51); hard boundary (124-128); advisory annotation (215-219); Event log (377-381); Serve (384-391); Portfolio export (436); Share profile (442-447); Redaction override (448-452); portfolio bundle, disposable and never read back (460-466); headline/glossary terms as cited inline
- `AGENTS.md` — safety rules and invariants
- `src/skilltrace/dispatch.py:1-16` (single chokepoint), `:38-58` (`Context.source`, write provenance)
- `src/skilltrace/portfolio/redaction.py` — the single redaction module
- `docs/spec-v2.0-portfolio-builder.md:521-523` (SA5 redaction-bypass scan), `:607-609` (single module, never bypassed)
- `docs/POST_V2_ROADMAP.md:181-187` (Tier 3 line in Beyond), `:212-222` (holding contracts)
- `docs/research/evidence-provenance-and-operational-contracts.md:56-62` (rows 1-4, 7: receipts, single-writer, sync conflict matrix, plugin capabilities, share profile)
- [G-ROI #99](https://github.com/earledotpy/skilltrace/issues/99) resolution — the locked rubric and its worked Tier 3 table
- [G-Beyond verdicts #280](https://github.com/earledotpy/skilltrace/issues/280) resolution — the Tier 3 deferral and this ticket's trigger branch
- [S-Tier3-PKMPluginAuthor #106](https://github.com/earledotpy/skilltrace/issues/106) — the four questions; prep artifact `research/s-tier3-pkm-plugin-author` (`c0513e0`)
- R-Tier3 `research/r-tier3-ecosystem.md` ([#96](https://github.com/earledotpy/skilltrace/issues/96)) — §3c/§3e integration shapes, §4a/§4b surface implications, §5c–§5e footguns, §7a–§7d ROI signals
- `docs/research/what-can-skilltrace-learn-from-comparable-open-sourced.md:107-121, 265` — prior in-tree reading of Logseq's mirror ADR

## 11. Open questions (human-only)

1. **Does the learner use a PKM, and which?** (§8.1) — the cheapest gate; unanswerable from the tree.
2. **Is terminal approval acceptable for PKM-3 variant A?** ADR-017's *"disorienting"* finding is a warning; §1.1(2) argues its rationale does not transfer, but only the learner can confirm that for their own workflow.
3. **The four maintainer questions** (§8.3) — unchanged, and unanswered by construction in this pass.
4. **Is a projection wanted at all?** PKM-2's value proposition is "what's due?" outside the CLI, when `today` / `next` / `serve` already answer it inside the repo. Whether that is a real gap or a solved need is a learner answer, not a research finding.
5. **Should "one writer per path" be promoted from an R-Tier3 rule to a written contract before PKM-2 is ever slot-picked?** This artifact argues yes (§4d, §6.1); the decision belongs with the slot.