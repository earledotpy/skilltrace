# R-Tier3 — Tier 3 ecosystem: state of multi-curriculum tools and PKM integrations in 2026

> **Ticket:** [#96 — R-Tier3](https://github.com/earledotpy/skilltrace/issues/96) (parent map [#95](https://github.com/earledotpy/skilltrace/issues/95))
> **Branch:** `research/r-tier3-ecosystem` · **Commit:** see pointer comment on #96
> **Scope:** External-state inventory only for the two Tier 3 items in `docs/POST_V1_BACKLOG.md:23` — **multi-curriculum support** and **PKM integrations** (Obsidian, Logseq). No product scope, no SkillTrace code audit, no version-slot decision. Grounded in current (2026) primary sources.
> **Companion tickets this artifact feeds:** [G-ROI #99](https://github.com/earledotpy/skilltrace/issues/99) and [G-Slot #100](https://github.com/earledotpy/skilltrace/issues/100).
> **SkillTrace constraints weighed throughout:** files-are-truth (`docs/adr/0001-separate-progress-store.md`); single-learner by design (`CONTEXT.md` lines 1–8); event log audit-only (`CONTEXT.md` lines 318–323); "verified" is a dated human assertion, no web checks in v1 (`docs/skilltrace-application-roadmap.md` decision 17, `CONTEXT.md` lines 294–309); exports disposable, never read back (`docs/skilltrace-application-roadmap.md` decision 12, `CONTEXT.md` lines 311–316); v1 layer cut excludes a built-in interface/seam registry (`docs/adr/0002-cut-interface-layer-from-v1.md`).

## 1. How to read this document

* **Sections 2–6** answer the five numbered sub-questions from #96. Each finding cites a primary source (vendor docs, plugin repos, framework READMEs) reachable on the public web as of 2026-08-27.
* **Section 7 ("Implications for SkillTrace")** lists engine-seam candidates and ROI signals relevant to **G-ROI** and **G-Slot** — without deciding slots, only the inputs the slots will score on.
* Throughout, "SkillTrace surface" means: the v1 installable `skilltrace` CLI, the five layers (graph / evidence / execution / policy / release), and the read-only Serve surface being planned in Tier 1 (`docs/POST_V1_BACKLOG.md:9`).
* Hard boundary the artifact never crosses: Tier 3 *questions* can be answered; Tier 3 *implementation* cannot. The deliverable is this Markdown file.
* Where a citation is a plugin repo or vendor doc, the version/date is captured inline so the reader can judge staleness.

## 2. Multi-curriculum precedent — what "multiple curricula side by side" actually looks like in 2026

### 2a. Anki profiles — the "do not use it for this" baseline

Anki explicitly disrecommends profiles for content separation within a single learner.

> "Profiles are primarily intended to be used by different people, and are not recommended for splitting up your own content. … Profiles are also unsupported on AnkiDroid." — *Anki FAQ, "Synchronizing multiple profiles"* (https://faqs.ankiweb.net/synchronizing-multiple-profiles.html)

> "If you have created multiple profiles for yourself, the best option is to merge them into a single profile." — *Anki Manual, "Profiles"* (https://docs.ankiweb.net/profiles.html)

> "Without creating a new profile? No. Separate databases = separate profiles." — *Anki Forum, "Multiple language learning" (2024-08-09)* (https://forums.ankiweb.net/t/multiple-language-learning/48053)

Pattern: **one collection, subdecks for content; profiles only for separate humans**. Anki is not a precedent for SkillTrace — but it is the canonical "we tried multi-curriculum and it didn't work" datapoint. The lesson: don't use the heaviest isolation primitive (separate database + separate sync account) for what is really "different decks of the same learner".

### 2b. Obsidian vaults — file-tree isolation, the prevailing norm

Obsidian treats a "vault" as a directory of markdown files plus an `.obsidian/` config folder. The "multiple curricula" pattern is "multiple vaults on disk", one active at a time, switched via the vault picker or CLI. Plugins that span vaults do so by enumerating directories and reading files outside their own `app.vault` (e.g., the Sync Engine plugin walks configured directories separately — see §3a). Plugin lifecycle and event surface (`vault.on('create' | 'modify' | 'delete' | 'rename')`, `metadataCache.on('changed')`) are per-vault.

> "Every plugin is located in `.obsidian/plugins/<plugin-id>/` within the vault directory. The minimum required files are `manifest.json` and `main.js`." — *Obsidian Plugin Development / DeepWiki* (https://deepwiki.com/obsidianmd/obsidian-api/3-plugin-development)

> "Bi-directional / mirror remote / mirror local syncing. Startup / periodic / save-on-change syncing. Conflict resolution strategies (keep both / latest survive / keep remote / keep local / skip)." — *Sync Engine README* (https://github.com/hesprs/sync-engine/)

Pattern: **isolation = directory boundary, not engine-level multi-tenancy**. There is no built-in notion of "vault 1 vs vault 2" inside the plugin host — only "the active vault, plus a list of other vaults on disk I may be told about". This is the closest analog to SkillTrace's "clone per learner, progress store per repo".

### 2c. Logseq graphs — explicit per-graph SQLite, multi-window, partial file-mode

Logseq moved from per-graph IndexedDB (browser) to per-graph SQLite files in `~/.logseq/graphs/` (PR #3530 "Multiple windows support", 2021-12-20), with a `Graph Registry` that maps a graph URL/UUID to a physical location. Each graph is a SQLite database + an optional markdown mirror; multiple graphs can be open in separate windows. The DB-graph mode (current default since 2025) does not git-sync; only file-mode (markdown/org) graphs do.

> "The databases (transit files) are stored in `~/.logseq/graphs` instead of IndexedDB for desktop apps now." — *Logseq PR #3530* (https://github.com/logseq/logseq/pull/3530)

> "If you want to fully own your syncing between devices, especially for peer-to-peer, you should just stick to plain text files. … I recommend Git and SyncThing over any other solution." — *Logseq Discourse, "Syncing Logseq DB"* (https://discuss.logseq.com/t/syncing-logseq-db/31285)

> "Two-way Markdown Mirror — the read-only mirror from section 1 is on its way to becoming a true round-trip. Edits to the on-disk markdown will sync back into the DB graph, with ADR 0017 spelling out the model, mirror-id sparsification, mirror-property syntax, and a Logseq Sync compatibility test suite to keep the two sides honest." — *Logseq DB Changelog, 2026-05-16* (https://discuss.logseq.com/t/whats-new-with-logseq-db-may-16th-2026/35020)

Pattern: **first-class multi-graph via separate SQLite + registry**, with file-mode as a deliberate compat/peer-sync surface. The 2026 mirror work explicitly calls out the difficulty of round-trip markdown↔DB and ships a dedicated ADR for the conflict model — i.e., even the PKM tool closest to SkillTrace's files-are-truth stance is currently one-way on the mirror.

### 2d. Roam Research — one graph = one database, per-graph MCP/CLI since 2025

Roam is one graph per Roam account, but tooling has started treating graphs as routable. The official `@roam-research/roam-mcp` server (v0.4.2, 2026-02-19) supports `connect` multiple times, each connection gets a nickname, and tool calls carry the nickname as a `graph` field. Single-graph auto-selects; multi-graph must pass the nickname.

> "Run `connect` multiple times to add additional graphs. Each graph gets a nickname (a short name like 'work' or 'team acme') for easy selection." — *@roam-research/roam-mcp v0.4.2, npm registry* (https://registry.npmjs.org/%40roam-research%2Froam-mcp)

Pattern: **logical graph = Roam account; tooling layer adds cross-graph identity**. Roam itself does not natively multi-graph — the tooling layer does. Closely mirrors how a future SkillTrace "multi-curriculum" could be a thin orchestration layer over distinct repos rather than a change to the engine.

### 2e. Tana Outliner — workspaces as the isolation primitive, with explicit caution about cross-workspace moves

Tana organizes content into workspaces; the "knowledge graph" is one logical graph per workspace, and "Use separate workspaces or tags and views to keep them distinct" is the documented advice for multi-domain setups.

> "Use separate workspaces or tags and views to keep them distinct, while still linking things that overlap like your calendar, energy, or long-term goals. Your boundaries, your rules." — *Tana Outliner "Organizing workspace"* (https://outliner.tana.inc/help/organizing-workspace)

Tana's docs repeatedly warn that moving a supertag/field between workspaces can leave broken references if any of the moved content references items in the source workspace — a real-world example of the **cross-contamination** problem the SkillTrace multi-curriculum item is meant to prevent.

> "If the field you are moving is not inside supertag, you risk fragmenting information across multiple workspaces. … And even when moved properly, 'Instance from supertag' fields might still reference their source workspace's supertag." — *Tana Outliner "Organizing workspace"* (https://outliner.tana.inc/help/organizing-workspace)

Pattern: **workspaces are the container; cross-workspace moves are dangerous and must be done with reference-fixup**. Direct precedent for SkillTrace's "fork the curriculum without cross-contamination" — the SkillTrace file-tree + `state.yaml` separation is structurally simpler than Tana's supertag-with-inherited-fields but hits the same cross-reference problem if nodes reference resources that fork.

### 2f. Notion — second-brain stacks live in one workspace, separate DBs for separate domains

Notion second-brain / PARA setups use **one workspace, many databases** for separation; multi-workspace is reserved for **teams**, not personal multi-curriculum.

> "A Notion second brain for solopreneurs is built around four core databases — Notes, Projects, Resources, and Areas — connected by linked relations so information surfaces in context." — *AutoFlow Guide, "How to Build a Notion Second Brain for Solopreneurs", 2026-03-30* (https://autoflowguide.com/how-to-build-notion-second-brain-solopreneurs/)

> "The hard limit of four databases — every additional database is a decision you make at capture time about where something lives, and those micro-decisions compound into avoidance." — *AutoFlow Guide, 2026-03-30*

Pattern: **soft isolation via databases + relations, all in one workspace**. Closely matches the SkillTrace design choice of "one repo, one progress store" — Notion's second-brain equivalent is "one workspace, one set of relations".

### 2g. Git worktrees — the workhorse for "same engine, different curriculum"

Git worktrees are the dominant 2026 pattern for "operate the same code base with different content" without forking the engine. SkillTrace is git-native (its own roadmap and agent instructions assume git worktrees for the roadmap tickets — e.g., the worktree created for this artifact), so the precedent is immediate.

> "Git worktree solves this by letting you check out multiple branches at the same time in separate directories. … Each worktree directory functions like a complete Git repository." — *DataCamp, "Git Worktree Tutorial", 2025-11-27* (https://www.datacamp.com/tutorial/git-worktree-tutorial)

> "All worktrees share the same `.git` directory, so they share the same remote configuration and fetch history. You don't need to run `git fetch` in every worktree — fetching in one updates remotes for all of them." — *DataCamp, 2025-11-27*

Tooling layered on top of worktrees (e.g. `git-parsec`, 2026-05-04) automates per-ticket worktree lifecycle: create, push, PR, cleanup. Indicates a 2026 ecosystem that treats worktree-per-task as a stable primitive.

> "When AI agents run in parallel on the same repo, they collide on `.git/index.lock` — crashing mid-task, burning tokens on retries, and leaving broken state. Worktrees solve isolation, but lack the lifecycle management agents need." — *git-parsec README* (https://erishforg.github.io/git-parsec/)

Pattern: **isolation = filesystem directory + branch, not engine-level**. Direct precedent for "fork a curriculum into its own branch and work on it without cross-contamination" — and it is what the SkillTrace roadmap and AGENTS.md already use for the roadmap tickets themselves.

### 2h. Summary of multi-curriculum patterns

| Tool | Isolation primitive | Cross-contamination risk | Engine-level multi-curriculum? |
|---|---|---|---|
| Anki | Profile = separate collection + separate AnkiWeb account (discouraged for one learner) | High (no shared stats) | No — discouraged |
| Obsidian | Vault = separate directory; plugins enumerate | Low (different `.obsidian/`) | No — file-tree boundary |
| Logseq (DB mode) | Graph = separate SQLite + registry; file-mode is the git-syncable surface | Medium (mirror round-trip is in-progress 2026) | Yes — explicit per-graph DB |
| Logseq (file mode) | Graph = separate directory of `.md`/`.org` | Low | No — file-tree boundary |
| Roam | Graph = account; tooling layer adds cross-graph identity | Low at account boundary; high inside one graph | No — orchestration layer only |
| Tana | Workspace = first-class container; cross-workspace moves break refs | Medium (documented ref-loss) | Yes — but cross-workspace moves are dangerous |
| Notion | Database = logical separation; workspace = team boundary | Low | No — relation-graph within one workspace |
| Git worktree | Directory + branch on shared engine | Low (separate working tree) | No — engine unchanged |

**Signal:** no major PKM tool offers "multi-curriculum *inside one engine*" as a first-class concept. The pattern that works is *files-on-disk isolation + a thin orchestrator*. The pattern that does not work (Anki profiles) is the one closest to "separate database per curriculum" — the same shape SkillTrace would get by giving each curriculum its own `state.yaml`, but SkillTrace already does that as the default.

## 3. PKM integration shapes — what "bi-directional note linking" looks like in practice

Three reference implementations are the most-cited in 2025–2026 PKM-integration literature. All three predate the SkillTrace question and all three expose concrete data-flow choices.

### 3a. Obsidian-to-Anki (Obsidian ↔ Anki via AnkiConnect)

A canonical "learning engine ↔ PKM note store" bridge. The plugin extracts flashcards from markdown by regex (start/end tags, inline, or user-defined), pushes them to Anki via the AnkiConnect HTTP API, then writes the Anki note IDs back into the Obsidian markdown (as `<!--ID: ...-->` HTML comments) so the next run can match updates.

Data flow (per the plugin's documented data flow):
1. Scan vault (or configured subdirectory) for files matching user-defined patterns; filter by `Ignore Folders and Files` (Glob syntax) and skip files whose content hash matches the last run.
2. Per file, extract notes by configured regex → categorize into *to add*, *to edit*, *to delete*.
3. Convert markdown to Anki HTML, handle media, send to AnkiConnect in two rounds (round 1: create/update/delete + media; round 2: deck/tag ops).
4. Receive Anki note IDs, write them back into the Obsidian file at the end of the note.

Sync model: **manual/command-palette triggered** (default); a "Scan vault" command and a "Clear all" command; no continuous file-watch by default. The Obsidian → Anki direction is primary; Anki → Obsidian is not supported.

Conflict handling: none — the file is the source of truth, Anki notes are derived. "Updating notes from file — Your text files are the canonical source of the notes" (README). ID loss breaks sync ("If note IDs are accidentally removed from Obsidian files, synchronization breaks").

> "While the synchronization system is robust, it has some limitations: 1. One-way synchronization — Changes made in Anki are not reflected back in Obsidian. 2. ID dependency — If note IDs are accidentally removed from Obsidian files, synchronization breaks. 3. Full file processing — When a file changes, all notes in that file are reprocessed." — *Obsidian to Anki / Synchronization and Updates* (https://deepwiki.com/ObsidianToAnki/Obsidian_to_Anki/5.3-synchronization-and-updates)

**Direct relevance to SkillTrace:** the canonical "Markdown is source of truth, remote system is derived" pattern. The plugin's "write back an opaque ID into the markdown" trick is exactly the kind of artifact SkillTrace must avoid: it would mean changing a node's `state.yaml` and possibly its markdown frontmatter on every sync, violating the "no Sync on asserted progress" rule (`docs/skilltrace-application-roadmap.md` decision 2, `CONTEXT.md` lines 36–41).

### 3b. Logseq DB sync — first-party, server-mediated, explicit conflict protocol

Logseq's `db-sync` (the server behind Logseq Sync) is a per-graph WebSocket + HTTP API. It uses a `tx` (transaction) model: client batches datoms and sends them as Transit-encoded payloads; server returns a `tx/reject` message that includes `:missing-block-uuids` and a `/sync/:graph-id/repair/blocks` endpoint to fetch authoritative state.

> "`GET /sync/:graph-id/pull?since=<t>` — Same as WS pull. Response: `{"type":"pull/ok","t":<t>,"checksum":"<c>","txs":[{"t":<t>,"tx":"<transit>","outliner-op":"<keyword?>"}...]}`. Error response (409): `{"error":"graph not ready"}` when bootstrap upload/import has not finished." — *Logseq db-sync protocol* (https://github.com/logseq/logseq/blob/3de7c751/docs/agent-guide/db-sync/protocol.md)

> "Return missing block UUIDs when the sync server rejects a tx batch because required blocks/datoms are absent. Keep failed pending txs pending on recoverable rejects, enqueue an explicit client repair tx, and retry the upload batch." — *Logseq PR #12788, "fix: db-sync missing data repair"* (https://github.com/logseq/logseq/pull/12788)

The markdown mirror (the feature that lets Logseq graphs live as on-disk markdown for git/Syncthing workflows) is currently one-way (DB → markdown) in 2026 production, with the round-trip on a feature branch.

> "Two-way Markdown Mirror — the read-only mirror from section 1 is on its way to becoming a true round-trip. Edits to the on-disk markdown will sync back into the DB graph, with ADR 0017 spelling out the model, mirror-id sparsification, mirror-property syntax, and a Logseq Sync compatibility test suite to keep the two sides honest." — *Logseq DB Changelog, 2026-05-16* (https://discuss.logseq.com/t/whats-new-with-logseq-db-may-16th-2026/35020)

**Direct relevance to SkillTrace:** a first-party, server-mediated bi-directional sync with an explicit `tx/reject` + repair protocol. The two-way markdown mirror is the same idea as a SkillTrace↔PKM bridge and is *still in development* at Logseq, with a dedicated ADR. The "mirror-id sparsification" and "mirror-property syntax" terms suggest non-trivial embed IDs in markdown — the same anti-pattern SkillTrace would hit if it tried to write progress into the PKM's notes.

### 3c. Roam MCP / Roam-tools — graph as the addressable unit, write-visibility via buffered batches

The `@roam-research/roam-mcp` server (official, 2026-02-19 v0.4.2) exposes graph access as routable tools; the `DiscourseGraphs/dg-team-mcp` extension layers *buffered* writes — the AI proposes a batch, a Roam-side plugin renders the proposed write for human approval, then the AI can poll the batch by ID for `pending | resolved/approved | resolved/rejected`.

> "Buffered Write Visibility — multi-batch Roam-native write approval: `propose_write_batch` — Buffer a same-parent append batch. Multiple batches to different parents coexist. `propose_write` — Convenience wrapper. `get_pending_write_batch` — Poll a batch by ID. Returns `pending` while waiting, or `resolved` with `approved`/`rejected` after the user acts in Roam." — *DiscourseGraphs/dg-team-mcp README* (https://github.com/DiscourseGraphs/dg-team-mcp)

**Direct relevance to SkillTrace:** a non-trivial pattern for *bi-directional* flows where one side is human-gated. The "buffered write" model (propose, poll, human approves in the target app) is one possible shape for a PKM integration that never silently mutates the PKM's notes.

### 3d. Other notable reference implementations (one-liners)

* **SurfSense Obsidian plugin** — push-only client over HTTPS to a FastAPI backend; ships a `vaultFingerprint` (sorted-path SHA-256) to dedupe multi-device connectors; idle backoff for reconciliation.
  *Source:* DeepWiki, "Plugin Architecture and Sync Engine" (https://deepwiki.com/MODSetter/SurfSense/17.1-plugin-architecture-and-sync-engine)
* **Obsidian Sync Engine (hesprs/sync-engine)** — modular plugin platform for vault↔remote (WebDAV/S3), extensibility via modules (`registerRemoteFs`, `registerDecider`, `registerConflictResolver`); 13-case sync matrix.
  *Source:* README + docs (https://github.com/hesprs/sync-engine/, https://hesprs.github.io/projects/sync-engine)
* **Obsidian Local Sync (entire-vc/evc-local-sync-plugin)** — bidirectional vault↔local directory sync, with per-mapping conflict strategies, symlink support, dry-run preview. Use case: "AI writes `/docs`, Obsidian stays current".
  *Source:* README (https://github.com/entire-vc/evc-local-sync-plugin)
* **Vault Intelligence (Obsidian plugin)** — hybrid local (Orama/IndexedDB) + cloud (Gemini) for search; ships a "Slim-Sync" sharded cold store in the vault with `content: ""` to avoid duplication.
  *Source:* Developer guide (https://cybaea.github.io/obsidian-vault-intelligence/devs/ARCHITECTURE.html)
* **Fit (joshuakto/fit)** — bidirectional Obsidian↔GitHub sync via the Git Data API; SHA-1 blob content-addressing; `_fit/` conflict directory.
  *Source:* docs/architecture.md (https://github.com/joshuakto/fit/blob/HEAD/docs/architecture.md)

### 3e. What "bi-directional" actually means, by the integration

| Integration | Direction in practice | Sync trigger | Conflict model | What is the source of truth |
|---|---|---|---|---|
| Obsidian-to-Anki | One-way (Obsidian → Anki), with ID echo back into the file | Manual / command palette | None — last writer wins per regex match | Obsidian markdown file |
| Logseq db-sync | Bi-directional (DB ↔ Logseq Sync server); mirror is DB → markdown only in 2026 production | WebSocket (push) + HTTP pull/repair | `tx/reject` with `:missing-block-uuids` and server repair endpoint | Logseq DB (server-authoritative) |
| Roam MCP + DiscourseGraphs | Bi-directional via MCP; writes are *buffered* for human approval | Tool calls from MCP client | "propose / poll / approve in Roam" workflow | Roam graph |
| SurfSense | Push-only (Obsidian → backend) | `vault`/`metadataCache` event listeners + reconcile | Idle backoff; first-sync manifest | Backend (SurfSense SearchSpace) |
| Sync Engine (hesprs) | Bi-directional (vault ↔ remote) | Startup / periodic / save-on-change | Configurable: keep-both / latest / keep-remote / keep-local / skip | Neither — equal peers |
| Local Sync (entire-vc) | Bi-directional (vault ↔ local dir) | On-change / startup / scheduled | Configurable per mapping | Neither — equal peers |
| Vault Intelligence | Bi-directional conceptually (index ↔ vault) | Web Worker + metadata change | Slim-Sync: sharded by model hash, content stripped | Obsidian markdown file |

**The consistent signal across these seven:** *bi-directional* in 2026 PKM-integration parlance almost never means "two equal writers". It means *one authoritative store, one or more derived views, with explicit repair rules for divergence*. The two integrations that genuinely use a peer model (Sync Engine, Local Sync) ship *configurable conflict strategies*, not implicit merge.

## 4. Engine surface implications — what each Tier 3 item would touch on SkillTrace

This section enumerates the *minimum* engine surface that would change, weighed against the SkillTrace constraints. It is an inventory, not a recommendation.

### 4a. Multi-curriculum support

The current "multi-curriculum" pattern in SkillTrace is `CONTEXT.md:1-8`:

> "**Learner** — the single person whose curriculum and progress a SkillTrace repository holds. SkillTrace is single-learner by design: one clone is one learner's identity; no record carries a user field. A second learner forks the curriculum without the progress store."

That is already the multi-curriculum primitive: **a curriculum is the repo minus the progress store; a second learner forks the curriculum without `graph/state.yaml`, adds their own `state.yaml`.** This is structurally identical to the git-worktree pattern (§2g) and to Obsidian's vault-on-disk pattern (§2b).

Engine surface this item might touch:
1. **No engine change at all** if "multi-curriculum support" means "document the fork-without-state.yaml pattern" and ship `skilltrace init --from-curriculum <path>` (a copy-without-state helper). This costs near-zero and aligns with the current `single-learner by design` language.
2. **A thin orchestrator command** (e.g., `skilltrace curricula <add|list|switch|remove>`) that manages a list of curriculum checkouts, each with its own `state.yaml`. This is structurally the same as Roam's MCP multi-graph pattern (§2d) and Logseq's `Graph Registry` (§2c) but at the file-tree level. It does *not* require engine changes because the engine is already curriculum-agnostic (`docs/skilltrace-application-roadmap.md` decision 19, `CONTEXT.md` lines 58–66).
3. **A more invasive change** that adds a `curriculum_id` field to records (e.g., per-node metadata, per-evidence metadata). This would touch the node/evidence loaders, the progress store, and the export pipeline — and it would *violate* `CONTEXT.md:1-8` ("no record carries a user field") and the existing rule that no record carries a `curriculum` field. It is a structural decision and would warrant an ADR.

Constraints the item must preserve:
* **Files-are-truth** (`docs/adr/0001-separate-progress-store.md`). Multi-curriculum is a way to *honor* this rule — curriculum is a file-tree boundary, not a record field. The conservative reading says: keep it that way.
* **Single-learner by design** (`CONTEXT.md:1-8`). A second learner is a second fork, not a second field. The conservative reading says: keep it that way.
* **Event log is audit-only** (`CONTEXT.md:318-323`). No "switched curriculum" event should be in the log unless it is a learner command. If the orchestrator is a command, its event is the natural fit; if it is automatic on every CLI invocation, it pollutes the log.
* **No web checks in v1** (`docs/skilltrace-application-roadmap.md` decision 17). Any "fetch curriculum from remote" feature belongs in v1.1 (the existing `Resource web-verification` backlog item) or later, not as part of multi-curriculum.

### 4b. PKM integrations

The current SkillTrace engine is not built to be a "Sync target" for an external note store. There is no ID-echo, no hash, no bidirectional protocol. The closest the engine comes is:
* `Execution/event log` (`execution/events.yaml`) — append-only, audit-only (`CONTEXT.md:318-323`). Not a sync primitive.
* `Serve` — read-only over truth files (`CONTEXT.md:325-332`). Could be the read side of a PKM integration but not the write side.
* `Export` — disposable derived artifact (`CONTEXT.md:311-316`). Explicitly "never read back by the engine" — so it cannot be the substrate for a bi-directional sync.

Engine surface this item might touch:
1. **Read-only Serve endpoints as a PKM-facing surface** (e.g., `GET /nodes/<id>`, `GET /node/<id>/evidence`). This is already Tier 1 scope (`docs/POST_V1_BACKLOG.md:9-12`) and is the *minimum* PKM-integration surface — the PKM-side plugin polls SkillTrace Serve for state. No engine change beyond what Tier 1 ships.
2. **A "publish to file" command** (e.g., `skilltrace publish --vault <path> --since <date>`) that writes a structured summary (per-node state, evidence count, last review) into a directory the PKM can read. This is structurally identical to the SurfSense / Vault Intelligence pattern of writing into the vault without changing the engine of truth. It does not violate files-are-truth if the published file is explicitly marked as a one-way projection. It does *not* read back.
3. **A bidirectional protocol** with a sync target. This requires (a) an identity layer (node ID ↔ external note ID), (b) a hash layer (content hash to detect external edits), (c) a conflict model (the same `tx/reject + repair` Logseq shipped in 2025, or a "buffered write" Roam pattern), (d) a written-into-SkillTrace side that contradicts the "no Sync on asserted progress" rule (`docs/skilltrace-application-roadmap.md` decision 2). The current engine would need a guarded "PKM proposal" path, and that path needs an ADR.

Constraints the item must preserve:
* **Files-are-truth** (`docs/adr/0001-separate-progress-store.md`). The PKM-side notes are *another* files-are-truth store; a bridge that "imports an external edit as a state change" would need explicit learner confirmation at the SkillTrace CLI — the same guard `skilltrace pass` already requires.
* **No web checks in v1** (`docs/skilltrace-application-roadmap.md` decision 17). A PKM plugin that calls SkillTrace Serve over HTTP from the PKM side is fine — Serve is local. A SkillTrace-side plugin that *polls* the PKM is also fine if the PKM exposes a local file/CLI surface; a SkillTrace-side poll against a SaaS PKM (e.g., Notion API) introduces the same "automated web assertion" risk the resource-verification item was deferred to v1.1 to avoid.
* **Event log is audit-only** (`CONTEXT.md:318-323`). A "PKM sync applied an external edit" event is fine, *if* it is the kind of event that the audit log can record (a learner action or a command), not a side effect of a read.
* **Hard boundary: no automated pass/master/delete** (`docs/skilltrace-application-roadmap.md` decisions 6 + 7). A PKM integration that "absorbs a Notion 'pass' checkbox" would touch `asserted progress` from outside the learner command — the *hardest* boundary in the engine. The conservative reading: PKM integrations can never write `passed` or `mastered`; they can only attach *advisory annotations* (the mechanism already in `CONTEXT.md:181-187`).
* **"Verified" is a dated human assertion** (`CONTEXT.md:294-309`). A PKM integration that auto-verifies a SkillTrace `LearningResource` from a PKM note is the same shape as v1.1's web-verification work and belongs in that backlog, not in PKM-integrations.

## 5. Risks and known footguns

### 5a. The bi-directional sync data-loss pattern

A 2026-03-27 RCA of a "Catastrophic Data Loss" via Obsidian Sync is a textbook example of what a SkillTrace↔PKM bridge would have to design against.

> "Bidirectional sync is a loaded gun when operating on a partial copy of a data store. Any system that can delete data should have circuit breakers, thresholds, and pre-flight checks. Sync is not backup. Never treat a sync mechanism as a backup system. First production runs of rewritten systems need extra monitoring and manual verification. The principle of least privilege applies to data access too: automation should only have access to the specific files it manages." — *bagrounds.org RCA, 2026-03-27* (https://bagrounds.org/ai-blog/2026-03-27-9-catastrophic-vault-data-loss-rca)

> "The safest approach is to run 'ob sync-config —mode pull-only' for the initial sync, then switch to bidirectional only when pushing known changes. … If the warm cache sync fails, completely empty the vault directory before running 'ob sync-setup' so the fresh sync starts from a genuinely clean state." — *bagrounds.org RCA, 2026-03-27*

Implication: any SkillTrace↔PKM bridge must have an explicit "first-sync" or "cold-cache" mode that defaults to **pull-only** until the learner confirms, and an explicit "destructive push" gate that asks for a learner command. This is the *same* shape as the existing `pass`/`master` confirmation modal pattern (`docs/adr/0004-hard-boundaries-are-engine-constants.md` and `CONTEXT.md:99-105`).

### 5b. Plugin / vendor version breakage

A second pattern is the bi-monthly "this plugin broke after a minor upgrade" cycle.

> "After updating to 0.25.21 livesync isn't working anymore. There are no down- or uploads. Back to 0.25.20 (with BRAT) everything works fine." — *vrtmrz/obsidian-livesync issue #727* (https://github.com/vrtmrz/obsidian-livesync/issues/727)

> "I'm truly sorry. This was a very simple mistake on my end (I forgot to call LiveSync/OneShot separately). … This issue has been fixed at v0.25.22!" — *maintainer reply on #727*

> "Just adding myself as a +1 with this exact issue after upgrading to 0.25.11 on my Windows PC and Android Phone. I reverted my devices back to 0.25.10 for now and its working as expected." — *vrtmrz/obsidian-livesync issue #702* (https://github.com/vrtmrz/obsidian-livesync/issues/702)

Implication: any SkillTrace↔PKM integration is a *long-term* compatibility commitment, not a one-time feature. Obsidian plugins ship 0.x for years; Obsidian API breaking changes are quarterly. The 2026 Sync Engine rewrite (`v2.0.0 - 2026-04-05`) shipped two migration systems to move users forward, which is the cost a SkillTrace team would have to budget for.

### 5c. The "two engines on the same directory" failure mode

A 2026-02 issue documents a case where running two sync engines (LiveSync + Syncthing) on the same vault caused a case-sensitivity race that wiped a file.

> "I was running Syncthing (configured for two-way sync) on the exact same vault directory alongside LiveSync. The 'silent deletion' was actually a race condition triggered by a file name case-sensitivity mismatch across different operating systems. … For anyone else running a similar setup: you cannot have two different two-way sync engines actively managing the same vault directory." — *vrtmrz/obsidian-livesync issue #800* (https://github.com/vrtmrz/obsidian-livesync/issues/800)

Implication: a SkillTrace↔PKM bridge that *also* tries to be its own sync engine (e.g., a git workflow + a file-watch daemon + a PKM plugin) is the exact failure shape. The SkillTrace↔PKM integration must be the *only* writer to whichever path it owns, or it must hand off to a single-file-writer it has tested.

### 5d. The "you can have multiple profiles, but please don't" footgun

> "Profiles are primarily intended to be used by different people, and are not recommended for splitting up your own content. … Profiles are also unsupported on AnkiDroid." — *Anki FAQ* (https://faqs.ankiweb.net/synchronizing-multiple-profiles.html)

Implication: the *simplest* multi-curriculum primitive (separate database / separate sync account per curriculum) is a known footgun. SkillTrace's existing "single-learner by design" decision is the right call and any multi-curriculum item must not recreate the Anki-profile trap.

### 5e. The cross-workspace move / fork-with-references footgun

> "If the field you are moving is not inside supertag, you risk fragmenting information across multiple workspaces. … 'Instance from supertag' fields might still reference their source workspace's supertag." — *Tana Outliner "Organizing workspace"* (https://outliner.tana.inc/help/organizing-workspace)

Implication: the SkillTrace "fork the curriculum" pattern works for *new* nodes but breaks for *referenced* nodes. A learner who forks the AI foundations curriculum to remove a few ML nodes will silently break any `LearningResource` whose `node` field points to the dropped nodes, any remediation edge that points into them, and any evidence record that names them. The "no record carries a user field" rule is not enough to defend against this — *node* references are the same problem.

### 5f. The "buffered write" pattern as a counter-footgun

> "Buffered Write Visibility — multi-batch Roam-native write approval: `propose_write_batch` — Buffer a same-parent append batch. Multiple batches to different parents coexist." — *DiscourseGraphs/dg-team-mcp README* (https://github.com/DiscourseGraphs/dg-team-mcp)

Implication: the *only* bi-directional pattern in the seven surveyed that does not require trust in the source is the buffered-write + human-approval pattern. It is the only pattern that *naturally* fits the SkillTrace "no automation of pass/master/delete" hard boundary — because every external write is, by construction, a learner-confirmed action.

## 6. Tier 3 ROI signal

This is the section the wayfinder map will care about most. The following are *facts*, not a score.

### 6a. The PKM ecosystem is *less* stable in 2026 than in 2024

* Obsidian Sync is in the middle of a v2.0.0 rewrite (2026-04-05) with "many breaking changes" and a mandatory migration.
* Logseq DB has just shipped its read-only markdown mirror and is in *development* on the round-trip version (2026-05-16 changelog).
* Obsidian LiveSync had a multi-issue regression cycle in 2025 (issues #702, #727, #800) where users *reverted plugins* to recover.
* The Sync Engine plugin publishes benchmarks of being 100× faster than Remotely Save — which means the previous generation is being actively displaced.

**Implication for G-ROI:** building SkillTrace↔PKM right now means integrating with a moving target. A 2026 v1.0.0 integration has a high probability of needing a 2027 v1.x patch for upstream API changes — exactly the maintenance cost SkillTrace's no-web-checks rule is designed to avoid.

### 6b. Multi-curriculum precedent in the PKM space is *not* a hot use case

The dominant 2026 PKM multi-curriculum pattern is *not* "run two curricula in one engine" — it is "one vault/workspace/graph per context, files on disk". Even Notion, with its flexible database/relation system, prescribes *one workspace* for a personal second brain; the 2026 second-brain guides explicitly say "four databases, one workspace" because more decisions at capture time kills the system.

* "The hard limit of four databases — every additional database is a decision you make at capture time about where something lives, and those micro-decisions compound into avoidance." — *AutoFlow Guide, 2026-03-30* (https://autoflowguide.com/how-to-build-notion-second-brain-solopreneurs/)
* "Notion second brain for solopreneurs runs on four databases (Inbox, Notes, Projects, Areas) with bidirectional relations — more than four databases adds more friction than value for solo operators." — *AutoFlow Guide, 2026-03-30*

**Implication for G-ROI:** the *user demand* for "multi-curriculum inside one engine" is small even in tools that *do* support it (Tana workspaces, Logseq graphs), and the *engine cost* in SkillTrace is structurally near zero (it's already a fork-and-edit pattern). The "high" ROI story requires evidence of users actively blocked by the current `git clone` of curriculum — which the ticket body does not provide.

### 6c. PKM integrations are *high compound value, high fragility*

The 2026 PKM ecosystem shows three patterns in tension:
1. **Read-only Serve as the SkillTrace→PKM surface** is low-cost, low-fragility, and *unlocks* the next slot — the PKM-side plugin handles all the sync complexity, the SkillTrace side just exposes the same `JoinedView` Tier 1 is already planning.
2. **PKM→SkillTrace as a buffered-write proposal** is medium-cost (it requires a learner-command-shaped API), medium-fragility (the PKM side has to be built to the buffered pattern), and *unlocks* the "SkillTrace as a downstream system of PKM notes" use case — which is the most-tied-to-existing-study-workflow slot of any in the post-v1 backlog.
3. **A full bidirectional bridge** is high-cost, high-fragility, and *unlocks* the most ambitious use case (PKM and SkillTrace as equal peers) — but the precedent in 2026 is that *no one* has shipped this reliably yet. Logseq's own round-trip is on a feature branch. Obsidian Sync's v2.0.0 ships with two migration systems to recover users from the v1.x sync.

**Implication for G-ROI:** the compound-value ranking is clear: the read-only Serve surface is the highest-leverage PKM-integration investment, the buffered-write is the medium one, and the full bi-directional bridge is the *long-horizon* slot, not the near-term one.

### 6d. Multi-curriculum's *learner value* is dominated by its *current behavior*

`CONTEXT.md:1-8` already says: "A second learner forks the curriculum without the progress store." That *is* multi-curriculum. The Tier 3 backlog item's marginal value over the current behavior is the polish layer:
* A `skilltrace init --from-curriculum` helper that copies the curriculum without `state.yaml` (a five-line shell command, not a feature).
* A `skilltrace curricula` orchestrator that lists/forks/switches between forks (the Roam MCP multi-graph pattern, but for repos on disk).
* Documentation that names the pattern (currently the rule is implicit in the ubiquitous language).

The Tier 3 *learner value* — "operate multiple curricula without cross-contamination" — is the *same* learner value as the current implicit behavior, just with a discoverable entry point. The *compound value* is similarly limited: the orchestrator command becomes the surface for any future "share progress across curricula" feature, but no such feature is in any current backlog.

**Implication for G-ROI:** the multi-curriculum item is *low* ROI on the locked rubric axis (learner value × compound value), because the current behavior already delivers the same learner value and the new behavior is a documentation + small-helper delta. The PKM-read-only surface is *higher* ROI on the same axis because the current behavior delivers no PKM value and the new behavior unlocks the largest unmade use case in the post-v1 backlog.

## 7. Implications for SkillTrace

This section is the *input* to G-ROI and G-Slot, not the *output*. It names engine-seam candidates and ROI signals; it does not assign slots.

### 7a. Engine-seam candidates

For each candidate, the question is: *what is the smallest SkillTrace change that lets an external party (a user, a plugin author, another tool) deliver the value without re-architecting the engine?*

| Candidate | Engine surface touched | Constraint fit | Plugin / third-party capable? |
|---|---|---|---|
| **MC-1: `skilltrace init --from-curriculum <path>`** | New CLI subcommand on the installable `skilltrace` package; copies a curriculum dir without `state.yaml`/`events.yaml` | Honors all v1 constraints; aligns with `CONTEXT.md:1-8` | N/A — it's a SkillTrace command |
| **MC-2: `skilltrace curricula <list\|fork\|switch\|remove>`** | New CLI subcommand + a tiny `curricula.yaml` registry at the user-machine level (not in the repo) | Honors files-are-truth (`curricula.yaml` is not in the repo); no record fields change | Yes — a third-party orchestrator could be built around the existing `skilltrace sync` / `validate` commands without this command existing |
| **MC-3: per-record `curriculum_id` field** | Node loader, progress store, evidence loader, export pipeline; requires a schema-version bump and an ADR | **Violates** `CONTEXT.md:1-8` ("no record carries a user field") by analogy | Yes — but the cost is structural and would be re-litigated every time a new "scope" axis appears |
| **PKM-1: Read-only Serve endpoints as a PKM-facing surface** | The Tier 1 web UI surface, which is already in `docs/POST_V1_BACKLOG.md:9` | Honors all v1 constraints; Tier 1 already in plan | Yes — a PKM-side plugin (Obsidian, Logseq) can poll Serve without any SkillTrace change |
| **PKM-2: `skilltrace publish --vault <path> --since <date>`** | New CLI subcommand; writes a structured projection into a user-specified path; explicitly marked as one-way | Honors files-are-truth; the published file is a projection, never read back by the engine (matches `Export` in `CONTEXT.md:311-316`) | Yes — a PKM-side plugin can read the published file without any SkillTrace change |
| **PKM-3: Buffered PKM write proposal as a SkillTrace command** | A new subcommand shaped like `pass`/`master` — refuses unless eligibility holds, appends an audit event, never auto-applies | Honors hard boundary ("no automation of pass/master/delete"); introduces a new learner command | Yes — a PKM-side plugin can queue proposals and the learner can confirm in the terminal or the future Serve modal |
| **PKM-4: Full bidirectional SkillTrace↔PKM protocol** | New sync layer with a hash-based identity, a `tx/reject` repair protocol, a guarded external-write path; an ADR; a multi-version compatibility commitment | Touches the asserted-progress invariant; requires an ADR on whether the engine's hard boundary extends to "any external write to asserted progress" | Partially — SkillTrace must own the protocol; a third party can build one client but the server-side is engine code |

### 7b. ROI signal for G-ROI

If G-ROI's locked rubric is **learner value × compound value** (per map #95), the following are the inputs each Tier 3 candidate supplies:

**Multi-curriculum:**
* **MC-1 (init helper):** learner value = small (a five-line shell command is replaced by a named subcommand); compound value = small (no downstream feature unlocked). Expected ROI: **Low**.
* **MC-2 (curricula orchestrator):** learner value = medium (a discoverable "I have three curricula" workflow); compound value = medium (becomes the surface for any future cross-curriculum analytics). Expected ROI: **Medium**.
* **MC-3 (per-record `curriculum_id`):** learner value = small (no observed user demand for in-engine multi-curriculum); compound value = small (any "share progress" feature would re-litigate the constraint). Expected ROI: **Low** + structural cost. **Likely not a slot — better as a v2.0+ decision if the user-demand signal changes.**

**PKM integrations:**
* **PKM-1 (read-only Serve):** learner value = medium (lets the existing PKM notes stay in the PKM; no daily-loop change); compound value = **high** (it is the prerequisite for PKM-2 and PKM-3, and is the natural surface for an Obsidian-sidebar "SkillTrace" panel). Expected ROI: **High**.
* **PKM-2 (publish to file):** learner value = medium (one-way projection is enough for most "what's due?" PKM-side uses); compound value = medium (the published file is also a back-up shape, doubling as a soft-export). Expected ROI: **Medium**.
* **PKM-3 (buffered write):** learner value = high (lets the existing PKM drive SkillTrace actions with the same confirmation gate as a terminal command); compound value = high (turns SkillTrace into a *downstream* of an existing study workflow, which is the post-v1 "unlocks a class of use" hit). Expected ROI: **High** — but only after PKM-1 ships and only if the upstream PKM plugins are willing to implement the buffered pattern.
* **PKM-4 (full bidirectional):** learner value = high in theory; compound value = high in theory. **Fragility cost = high** (the 2026 PKM sync ecosystem is mid-rewrite; Logseq's two-way mirror is on a feature branch; Obsidian Sync v2 is shipping migrations; LiveSync had multi-issue regression cycles). Expected ROI: **High long-horizon, low near-term** — i.e., this is the slot a learner in 2027 wants, not the slot a learner in 2026 wants.

### 7c. Compound-value chain (for G-Slot)

The dependency chain that emerges:

```
PKM-1 (Serve read endpoints)        ── enables ──→  PKM-2 (publish to file)
                                              ╲
                                               ╲── enables ──→  PKM-3 (buffered write) ── enables ──→  PKM-4 (full bidirectional, long-horizon)

MC-2 (curricula orchestrator)        ── enables ──→  (future) cross-curriculum analytics
                                                                     (not in any current backlog)
```

The chain implies a natural slot ordering:
1. **PKM-1** before any other PKM slot (it is a Tier 1 dependency anyway, so it ships "for free" once Tier 1 lands).
2. **PKM-2** and **PKM-3** as a pair, after Tier 1 lands and after the PKM ecosystem stabilizes (probably not before 2027 given the rewrite cycle in §6a).
3. **PKM-4** as a long-horizon slot, with the explicit caveat that Logseq's own two-way mirror is *also* a long-horizon slot at Logseq.
4. **MC-1** as a documentation + small-helper delta that can ship *with* Tier 1 polish (v0.9.0-rc1-style).
5. **MC-2** as a slot *only if* a user-demand signal emerges in the post-v1.4 soak period; otherwise it is documentation + a `docs/HOWTO-multi-curriculum.md` and stays out of the version slots.
6. **MC-3** is a no-slot — it would re-litigate the single-learner-by-design decision and there is no current evidence the decision is wrong.

### 7d. The three facts that most drive the slot

If the G-Slot session is short on time, the three facts that most push the Tier 3 ordering are:

1. **The PKM ecosystem is mid-rewrite in 2026** (Sync Engine v2, Logseq two-way mirror on a feature branch, LiveSync regression cycles). Any SkillTrace↔PKM investment that lands before the rewrites settle has a high maintenance cost. (Cite: §6a.)
2. **SkillTrace's "multi-curriculum" is already a documented pattern** (`CONTEXT.md:1-8`). The marginal value of any Tier 3 multi-curriculum slot is the discoverability and tooling, not new learner capability. (Cite: §6d.)
3. **The buffered-write pattern is the only bi-directional pattern in 2026 PKM tooling that survives the no-automation hard boundary**, because it is *by construction* a learner-confirmed action. (Cite: §5f, §3c.)

These three together push: PKM-1 and MC-1 to near-term slots (with Tier 1 / Tier 1 polish), PKM-2/3 to mid-term slots, and MC-2 + PKM-4 to "wait for the ecosystem to settle + wait for the demand signal".

## 8. Primary sources cited

The seven PKM integration reference implementations:

* Obsidian-to-Anki plugin — https://github.com/ObsidianToAnki/Obsidian_to_Anki · https://deepwiki.com/ObsidianToAnki/Obsidian_to_Anki
* Logseq db-sync protocol — https://github.com/logseq/logseq/blob/3de7c751/docs/agent-guide/db-sync/protocol.md · https://github.com/logseq/logseq/pull/12788
* Roam MCP server (official) — https://registry.npmjs.org/%40roam-research%2Froam-mcp
* DiscourseGraphs dg-team-mcp (buffered write pattern) — https://github.com/DiscourseGraphs/dg-team-mcp
* SurfSense Obsidian plugin — https://deepwiki.com/MODSetter/SurfSense/17.1-plugin-architecture-and-sync-engine
* Obsidian Sync Engine (hesprs) — https://github.com/hesprs/sync-engine/ · https://hesprs.github.io/projects/sync-engine
* Obsidian Local Sync (entire-vc) — https://github.com/entire-vc/evc-local-sync-plugin
* Vault Intelligence (Obsidian plugin) — https://cybaea.github.io/obsidian-vault-intelligence/devs/ARCHITECTURE.html
* Fit (Obsidian↔GitHub sync) — https://github.com/joshuakto/fit/blob/HEAD/docs/architecture.md

The five multi-curriculum reference tools:

* Anki profiles — https://docs.ankiweb.net/profiles.html · https://faqs.ankiweb.net/synchronizing-multiple-profiles.html · https://forums.ankiweb.net/t/multiple-language-learning/48053
* Obsidian vault/plugin host — https://deepwiki.com/obsidianmd/obsidian-api/3-plugin-development
* Logseq graphs and registry — https://github.com/logseq/logseq/pull/3530 · https://discuss.logseq.com/t/syncing-logseq-db/31285 · https://discuss.logseq.com/t/whats-new-with-logseq-db-may-16th-2026/35020 · https://deepwiki.com/logseq/logseq/4.3-repository-and-graph-management
* Roam Research — https://roamresearch.com/ · https://registry.npmjs.org/%40roam-research%2Froam-mcp
* Tana Outliner — https://outliner.tana.inc/help/organizing-workspace · https://outliner.tana.inc/learn/features/workspaces
* Notion second-brain guides (2026) — https://autoflowguide.com/how-to-build-notion-second-brain-solopreneurs/ · https://novapixeldev.com/blog/build-second-brain-notion-ai-tools · https://notionmarkethub.com/how-to-build-second-brain-notion-para-method/
* Git worktrees — https://www.datacamp.com/tutorial/git-worktree-tutorial · https://www.boot.dev/blog/devops/git-worktree · https://blog.safia.rocks/2025/09/03/git-worktrees/ · https://erishforg.github.io/git-parsec/

The risk / footgun datapoints:

* Bi-directional sync data-loss RCA (Obsidian Sync, 2026-03-27) — https://bagrounds.org/ai-blog/2026-03-27-9-catastrophic-vault-data-loss-rca
* Remotely Save bi-directional sync bug — https://github.com/remotely-save/remotely-save/issues/991
* Obsidian LiveSync regression cycles — https://github.com/vrtmrz/obsidian-livesync/issues/702 · https://github.com/vrtmrz/obsidian-livesync/issues/727 · https://github.com/vrtmrz/obsidian-livesync/issues/800
* Sync Engine v2.0.0 rewrite (2026-04-05) — https://github.com/hesprs/obsidian-webdav-sync/blob/49a160a2c002c6175681c883d38838c232e5c365/CHANGELOG.md

Local SkillTrace documents weighed as constraints:

* `CONTEXT.md` (ubiquitous language) — Learner (1–8), asserted progress (36–41), engine/curriculum split (58–66), GraphEdge (72–76), hard boundary (90–97), evidence/supersede (159–179), advisory annotation (181–187), reviewed (240–252), Verified (294–309), Export (311–316), Event log (318–323), Serve (325–332).
* `docs/POST_V1_BACKLOG.md` — Tier 1 (9–12), Tier 2 (16–20), Tier 3 (23–27), roadmap versioned items (31–41).
* `docs/skilltrace-application-roadmap.md` — all twenty governing design decisions (35–94), RC plan (98–110), Tier 3 items in the post-v1 section (594–615).
* `docs/adr/0001-separate-progress-store.md` — progress store as the source of truth for learner state.
* `docs/adr/0002-cut-interface-layer-from-v1.md` — v1 layer cut excludes a built-in interface/seam registry.
* `docs/adr/0004-hard-boundaries-are-engine-constants.md` — hard boundaries are engine-constant behavior.
* Wayfinder map #95 and tickets #99 (G-ROI), #100 (G-Slot) — the consumers of this artifact.
