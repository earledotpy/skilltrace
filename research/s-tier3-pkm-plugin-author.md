# S-Tier3-PKMPluginAuthor — Author outreach prep for #106

> **Ticket:** [#106 — S-Tier3-PKMPluginAuthor](https://github.com/earledotpy/skilltrace/issues/106) (parent map [#95](https://github.com/earledotpy/skilltrace/issues/95))
> **Branch:** `research/s-tier3-pkm-plugin-author` · **Commit:** see `git log` on the branch
> **Scope:** Primary-source research on the four plugin candidates named in #106, an honest AFK-vs-HITL split, an evidence-based pick of 1–2 authors, per-author public-source answers to the four ticket questions, and two ready-to-send outreach drafts. **This artifact is the *prep* for the calls the ticket asks for, not the calls themselves.** No SkillTrace code is touched; no code change proposed; the next step is a human sending two short messages.

## 1. TL;DR

**Call these two:** (1) the DiscourseGraphs maintainers of `dg-team-mcp` (the buffered-write + human-approval pattern *originators* — they own the protocol the ticket is asking about and have shipped two ADRs explicitly weighing approval-bridge vs. direct-validated-write); and (2) Hēsperus (`hesprs`) of the `sync-engine` Obsidian plugin (the most architecturally-fit Obsidian candidate, an exceptionally responsive maintainer — 12 issues closed in Aug 2026 alone — and the only one whose plugin already exposes a public module/SDK surface that a buffered-write conflict strategy could plug into without forking the conflict-resolution engine).

**The AFK-vs-HITL split:** an autonomous agent session cannot DM a Discord server, send an email, or post a maintainer-friendly GitHub issue with the right framing. The actual *calls* — a 20-minute Discord call with the DiscourseGraphs maintainers, a single e-mail or Discord DM to Hēsperus, or a one-liner issue on the `sync-engine` wishlist [#214](https://github.com/hesprs/sync-engine/issues/214) — must be human actions. What this artifact *can* deliver is everything the human will need to walk into those calls prepared: the exact maintainer handles, contact channels, recent public statements, the protocol's design rationale (with primary-source citations), and two short outreach messages sized to a maintainer's good will.

**Headline finding:** the buffered-write pattern is *not* a 2026 novelty — it is a 2026 *field* with one origin repo and zero adopters. The DiscourseGraphs team designed the approval bridge specifically because terminal-side approval "was disorienting" (their words, ADR-017, 2026-04-02), and they are the only maintainers in this set who have made the design trade-off (approval bridge vs. direct validated write) explicitly and in writing. Every other candidate plugin would need to add buffered-write as a new surface, with the cost varying from "one new conflict strategy" (Sync Engine) to "an entire new write direction" (SurfSense, which is *push-only by design*).

## 2. What an AFK research pass can and cannot do

The ticket is titled "Calls to 1–2 Obsidian/Logseq plugin authors". The word "calls" is the operative word, and it is the limit of what an agent session can do honestly:

**Can do, and did:** enumerate the four candidates; identify the right contact handle, repo, recent activity, and the most-recent public statement each maintainer has made on a relevant topic; surface everything publicly reachable about the four ticket questions (README, docs, ADRs, maintainer issue comments, blog posts, source code structure); assess the architectural fit by reading what the plugin actually does on the write path; draft a short outreach message per author that the human can copy-paste.

**Cannot do, and will not pretend to:** open a Discord DM, send an email, post on a public issue tracker on the maintainer's behalf, schedule a call, or record a call's content. The ticket's "1-2 calls" are the part that requires the *human* maintainer (the one named in `earledotpy/skilltrace`, not the plugin author) to actually spend the maintainer's social capital. Two short messages — one to each of the two recommended authors — is the realistic deliverable. The G-ROI / G-Slot sizing call in the ticket's Resolution comment section can only land after the *human* has either received a reply or waited the conventional maintainer-reply window (one week for a Discord ping, two weeks for an e-mail, one week for a public-issue comment).

This split is the most important sentence in this artifact. The next agent session and the human should both read §1 and §2 of this document before doing anything else.

## 3. The 1–2 recommended authors

### 3.1. #1 (must call) — `DiscourseGraphs/dg-team-mcp` — the buffered-write originators

* **Repo:** [github.com/DiscourseGraphs/dg-team-mcp](https://github.com/DiscourseGraphs/dg-team-mcp)
* **Org / maintainers:** [DiscourseGraphs](https://github.com/DiscourseGraphs) org; the two people shown on the org page are [@mdroidian](https://github.com/mdroidian) and [@trangdoan982](https://github.com/trangdoan982) — *Source: [DiscourseGraphs org → People](https://github.com/orgs/DiscourseGraphs/people)*.
* **Contact channel:** GitHub issue is the *only* public contact channel on the repo — Issues is currently disabled ("New issue / Issue creation is restricted in this repository"), the repo has 0 open issues, and 2 open PRs visible on the overview. *Source: [DiscourseGraphs/dg-team-mcp → Issues](https://github.com/DiscourseGraphs/dg-team-mcp/issues)*. There is no public e-mail on the org's profile. There is a separate companion repo [DiscourseGraphs/discourse-graph](https://github.com/DiscourseGraphs/discourse-graph) (45 stars, Apache-2.0) which is the mainline; the maintainers may prefer outreach via *that* repo's issue tracker.
* **Recent activity signal:** the dg-team-mcp repo's last commit is dated 2026-08-27 (today) per the org repositories list; it carries 22 commits total. The companion `discourse-graph` repo was updated 2026-08-27, has 20 open issues and 67 open PRs, indicating an active triage cadence. *Source: [DiscourseGraphs org repositories list](https://github.com/orgs/DiscourseGraphs/repositories)*.
* **Public statements relevant to the 4 questions (already on the public record):**
  * "The original write visibility showed pending writes in the terminal (Claude Code). Users couldn't see WHERE in their graph the write would land. Terminal approval was disorienting." — `DiscourseGraphs/dg-team-mcp/ADR.md` ADR-017, 2026-04-02. *Source: [ADR.md](https://github.com/DiscourseGraphs/dg-team-mcp/blob/main/ADR.md).*
  * "Move approval from terminal to Roam. Render virtual DOM blocks inline at the target parent. Support multiple simultaneous proposals to different parents. Track resolution (approved/rejected) so agents can poll for the outcome." — ADR-017, *same source*.
  * "Users need visual context of where blocks will land. Multi-agent workflows produce writes to different parents simultaneously. Fire-and-forget proposals break the feedback loop." — ADR-017, *same source*.
  * "Trade-offs: Requires Roam plugin installed. Plugin polls bridge every 1.2s (lightweight). Resolution tracking is in-memory (lost on server restart)." — ADR-017, *same source*.
  * "A relation record is a uid-stringed block full of opaque props — rendering it as a bullet communicates nothing, so the approval step would be theater. The honest options were a typed relation card in the Roam plugin (real work, deferred) or a validated direct write with `dry_run` (this ADR)." — ADR-018, 2026-07-26, *same source*. *This is the maintainers' own statement of where the buffered-write pattern is and isn't a fit.*
  * "A misfired call adds a block to a config page rather than corrupting user content, and is undone by deleting one block. Against that, there is no user-visible approval step, which is why the tool ships disabled and validates aggressively before writing." — ADR-018, 2026-07-26, *same source*.
  * "Two things have changed. First, disabled-by-default meant nobody ran it … a safety gate that pushes work onto an unsafer path is not a safety gate." — ADR-018 amendment, 2026-08-08, *same source*. *The maintainers have already publicly argued both sides of the "default-on vs. default-off" question that any SkillTrace↔PKM integration will have to face.*

* **Case for picking them:** the ticket literally says the buffered-write pattern "looks most like" the dg-team-mcp implementation. They own the protocol. They have the only public ADRs in the PKM space on the design rationale. They have shipped the pattern across two releases (2026-04 and 2026-07) and have recently thought about when the pattern is and is not appropriate. They are the only author who can answer the four ticket questions with the *exact* framing the ticket is asking about.
* **Case against picking them:** the pattern is Roam-only today. There is no Obsidian or Logseq port. Asking the dg-team-mcp maintainers "could you port this to Obsidian" is *not* what the ticket is asking — and might pull them into scope-creep. The honest framing of the call is "we'd like to use your protocol, here is what we'd build, here is what it costs you, here is what we want to know before we commit". They may also be a small team and the contact may take time.

### 3.2. #2 (recommended) — `hesprs/sync-engine` — the most architecturally-fit Obsidian candidate

* **Repo:** [github.com/hesprs/sync-engine](https://github.com/hesprs/sync-engine)
* **Maintainer:** [hesprs (Hēsperus)](https://github.com/hesprs) — "a high school student" per his profile README; `hesprs@outlook.com` is the public e-mail address on his profile; X handle is [@Hesprs](https://x.com/Hesprs); personal site [hesprs.github.io](https://hesprs.github.io); ORCID 0009-0008-7952-3109. *Source: [hesprs GitHub profile](https://github.com/hesprs).*
* **Contact channel:** e-mail (`hesprs@outlook.com`) is the most direct; public GitHub issue on the repo is a strong second (the repo accepts issues — confirmed: search "is:issue" returns the open wishlist [#214](https://github.com/hesprs/sync-engine/issues/214) and 12+ recently-closed issues); X DM is plausible but lower signal. *Sources: [profile](https://github.com/hesprs), [issues list](https://github.com/hesprs/sync-engine/issues?q=is%3Aissue).*
* **Recent activity signal:** 278 commits; the maintainer closed 12 issues in Aug 2026 alone, with response latency visibly in days (e.g. #233 closed 2026-08-21, #232 closed 2026-08-16, #247 closed 2026-08-24). Open wishlist issue #214 was opened 2026-08-09 by the maintainer himself and currently has 8 thumbs-up reactions — a public, lightweight way to gauge interest in a new feature. *Source: [sync-engine issues search](https://github.com/hesprs/sync-engine/issues?q=is%3Aissue).*
* **Public statements relevant to the 4 questions:**
  * "Bi-directional / mirror remote / mirror local syncing. Startup / periodic / save-on-change syncing. Conflict resolution strategies (keep both / latest survive / keep remote / keep local / skip)." — `hesprs/sync-engine/README.md`. *Source: [README](https://github.com/hesprs/sync-engine).*
  * "Core Functions: … Bidirectional / mirror remote / mirror local syncing. … Conflict resolution strategies (keep both / latest survive / keep remote / keep local / skip). … You can extend most above features by writing modules." — *same source*. **This is the load-bearing fact:** the plugin already exposes a `registerConflictResolver` module surface, which is the architectural shape a SkillTrace-driven "buffered-write" strategy would have to plug into.
  * "Sync Engine also has a wishlist of features, you can react with **thumbs up** 👍 on feature comments you would like to have. And the features with more votes will have higher priority." — *same source*. **The maintainer has explicitly invited feature requests and *given the community a public vote on priority*.**
  * "We welcome contributors that would like to help us with the development of either modules or core." — *same source*. He accepts third-party modules.
  * "v3.0: Rewrite entirely, dynamic module loading, module store, asymmetric storage, and rebrand / v3.1: Migrate settings to Obsidian v1.13 API / v3.2: Granular sync strategy selection / exclusion inclusion rule refactor based on ordered glob match rules." — *same source*. *v3.2 is exactly the kind of refactor that would make a "buffered-write" conflict strategy a clean fit.*

* **Case for picking him:** the only candidate maintainer with a public "yes, take community feature requests, here's a wishlist, please vote" pattern; the only one with a `registerConflictResolver` extension point on the write path; exceptional responsiveness (Aug 2026 issue-close latency in days, not weeks); already a public module SDK ([@hesprs/sync-engine-sdk on npm](https://www.npmjs.com/package/@hesprs/sync-engine-sdk) per the README badges). A buffered-write conflict strategy on Sync Engine would be a *new module*, not a core change, which is the cheapest possible architectural fit of the three Obsidian candidates.
* **Case against picking him:** he is a high school student. Time-zone and capacity are real. A heavy ask would burn goodwill. The ticket scope ("we are listening") fits — the ask is one short e-mail, not a partnership negotiation.

### 3.3. Considered and not recommended for this round

* **`MODSetter/SurfSense` (Obsidian, push-only HTTPS client).** Maintainer is [Rohan Verma / MODSetter](https://github.com/MODSetter) (16k stars, very active; San Jose, CA, US per profile). No public e-mail on profile; the primary contact channel is the project [Discord (discord.gg/ejRNvftDp9)](https://discord.gg/ejRNvftDp9) per the README. The Obsidian plugin is *push-only* by design — it uploads the vault to a SurfSense SearchSpace; the backend has no read-back-to-vault code path documented. The buffered-write pattern would be a *new write direction* and a new surface; it would also collide with the plugin's "fully local push client" privacy framing ("the plugin never reads cookies or other Obsidian state", per `surfsense_obsidian/README.md`). SurfSense *could* ship buffered-write as a future surface, but the cost is high and the maintainer has not signalled interest in writeback. The right call for the #106 ticket is to *not* call SurfSense and instead treat it as a follow-up only if the dg-team-mcp + sync-engine calls come back positive.
* **`entire-vc/evc-local-sync-plugin` (Obsidian, vault↔local folder).** Maintainer is the [entire-vc](https://github.com/entire-vc) org (8 followers, multi-repo product family: Local Sync, Team Relay, Spark MCP, Mesh). Public contact: `support@entire.vc` and `in@entire.vc`; Telegram [t.me/entire_vc](https://t.me/entire_vc) per the org profile. The plugin is bidirectional *vault↔folder* sync, with per-mapping conflict strategies that already include an "Always ask" mode (i.e. the *user-prompt* shape of buffered-write exists; the *AI-propose-then-user-approve-in-the-PKM* shape does not). 11 stars, 1 fork, 0 open issues, 2 open PRs — small user base, but the org has a clear "AI-native builder" positioning and ships an AI-tool skill (OpenClaw) that already lets agents read/write Obsidian via REST. *Architectural fit is moderate* (the "Always ask" strategy is the right shape, but a SkillTrace-side external engine would need the plugin to learn about SkillTrace specifically). *Not picked for this round* because: (a) the dg-team-mcp + sync-engine pair already covers the protocol-origin and the Obsidian-architectural-fit slots; (b) the team-relay+openclaw ecosystem is its own bigger conversation that deserves its own ticket, not a side-channel on this one. The right call is to *note* Local Sync in the G-ROI / G-Slot input as a possible third integration target, and not burn a call on it now.

## 4. Per-author public-source answers to the 4 ticket questions

The four questions from #106 are:

1. Is the buffered-write pattern (propose → human-approve → apply) compatible with your plugin's write path, or would it require a new surface?
2. What is the maintenance cost of supporting a SkillTrace-style external engine that owns the source of truth and treats the PKM-side write as a derived view?
3. What is the failure mode you most want SkillTrace-side integrators to know about? (Vault bloat, sync drift, approval UX, version compatibility.)
4. Would you accept a one-line PR to the plugin's docs naming SkillTrace as a supported external engine, or is that a higher-friction ask?

### 4.1. DiscourseGraphs / dg-team-mcp

* **Q1 — Compatible with the write path?** **Yes, by construction — the plugin is the pattern.** The "Write Visibility" subsystem is exactly the propose→approve→apply flow. Four MCP tools expose it: `propose_write_batch` (buffer a same-parent append), `propose_write` (single-branch convenience wrapper), `get_pending_write_batch` (poll for `pending` or `resolved` with `approved`/`rejected`), `clear_pending_write_batch` (manual clear; usually the plugin handles it). The architectural diagram in `ARCHITECTURE.md` shows the bridge at `127.0.0.1:3597` and the Roam plugin polling `GET /write-visibility/current` every 1.2 seconds, with virtual DOM blocks rendered inline at each parent for approval. *Sources: [README](https://github.com/DiscourseGraphs/dg-team-mcp), [ARCHITECTURE.md](https://github.com/DiscourseGraphs/dg-team-mcp/blob/main/ARCHITECTURE.md), [ADR.md ADR-017](https://github.com/DiscourseGraphs/dg-team-mcp/blob/main/ADR.md).*
* **Q2 — Maintenance cost of a SkillTrace-style external engine?** **Not publicly stated; ADR-018 has the closest framing.** ADR-018 (2026-07-26, amended 2026-08-08) is the maintainers' own record of the *cost* of supporting an external engine: they ship `create_discourse_relation` on-by-default with a five-point safety contract ("refuse rather than guess … idempotent … one direction only … `dry_run`") and argue the cost is "one block, on a config page, undone by deleting one block". The exact maintainer-stated cost of supporting a *SkillTrace* integration is not on the public record — this is the call.
* **Q3 — Failure mode to flag?** **Two are on the public record, in their own words:**
  * **Approval UX that "communicates nothing"** (their words for relation records): "rendering it as a bullet communicates nothing, so the approval step would be theater". The implication is that the *shape* of the proposed write has to be intelligible in the PKM UI, or the approval is theatre. *Source: ADR-018, 2026-07-26.*
  * **In-memory resolution tracking across restarts:** "Resolution tracking is in-memory (lost on server restart)". For SkillTrace's "no-automation" guarantee to survive a restart, the protocol needs a durable outbox on the bridge or on the SkillTrace side. *Source: ADR-017, 2026-04-02.*
* **Q4 — One-line PR to docs naming SkillTrace?** **Not publicly stated.** There is no precedent in the repo for naming an external engine in the README (the org's other repos name their own components only). This is a call question.

### 4.2. hesprs / sync-engine

* **Q1 — Compatible with the write path?** **Plausibly yes, as a new conflict strategy.** Sync Engine ships with 5 conflict strategies (keep both / latest survive / keep remote / keep local / skip) and a public `registerConflictResolver` module surface. The README explicitly states: "You can add backends, optimizers, sync triggers, i18n resources, decision strategies, conflict strategies, setting entries, custom file processing, and invoke all possible operations in custom modules." A SkillTrace-driven "buffered-write" strategy would be a new module that registers itself as a conflict resolver, surfaces a "propose" preview, and only writes after the user confirms in the plugin's confirmation dialog. **The cost is a new module, not a core change.** *Source: [README](https://github.com/hesprs/sync-engine).*
* **Q2 — Maintenance cost?** **Not publicly stated.** The closest public framing is the README's pitch for v3.0 ("Rewrite entirely, dynamic module loading, module store, asymmetric storage, and rebrand") and v3.2 ("Granular sync strategy selection / exclusion inclusion rule refactor") — both of which suggest a future where adding a new strategy is a module-store concern, not a core-engine concern. The actual cost of supporting a SkillTrace-style external engine is a call question.
* **Q3 — Failure mode to flag?** **Two are on the public record:**
  * **Destructive operations need clearer UX.** Issue #233 "Summarise destructive operations in the confirmation dialog and do not pre-select deletions" (closed 2026-08-21, status "completed") — the maintainer agreed that destructive operations need *better* confirmation UX, not just confirmation. *Source: [issue #233](https://github.com/hesprs/sync-engine/issues/233).* This is the load-bearing datapoint for Q3: any SkillTrace↔sync-engine integration must default to "do not pre-select destructive options" and must summarise what's about to change.
  * **"You cannot have two different two-way sync engines actively managing the same vault directory."** This is the R-Tier3 §5c datapoint from vrtmrz/obsidian-livesync, not sync-engine itself, but it is the dominant 2026 PKM-sync failure mode and the one a SkillTrace↔sync-engine pair most needs to design against. *Source: [vrtmrz/obsidian-livesync issue #800](https://github.com/vrtmrz/obsidian-livesync/issues/800) (referenced in `research/r-tier3-ecosystem.md` §5c).*
* **Q4 — One-line PR to docs naming SkillTrace?** **Public precedent is favourable but not specifically stated.** The README's section "How should I manage my remote storage when using this plugin?" explicitly names the *kind* of integration (e.g. WebDAV, S3, Google Drive modules) and Sync Engine ships a `modules.json` registry. There is no precedent in the repo for naming an *external engine* (rather than a Sync Engine module) in the README. This is a call question, but a low-risk one — the wishlist issue #214 is the right lightweight way to gauge the answer.

### 4.3. MODSetter / SurfSense

* **Q1 — Compatible with the write path?** **No, not without a new surface.** SurfSense's Obsidian plugin is "a push-client over HTTPS" by design; the data flow is `vault → /api/v1/obsidian/sync → backend`, with no documented read-back-to-vault code path. The plugin's privacy section explicitly states: "The `Authorization: Bearer …` header is set per-request with the token you paste; the plugin never reads cookies or other Obsidian state" and the network surface is `requestUrl` only. *Sources: [SurfSense Obsidian plugin README](https://github.com/MODSetter/SurfSense/tree/main/surfsense_obsidian), [DeepWiki — Plugin Architecture and Sync Engine](https://deepwiki.com/MODSetter/SurfSense/17.1-plugin-architecture-and-sync-engine).*
* **Q2 — Maintenance cost?** Not publicly stated. The maintainer is shipping fast (SurfSense is the "actively developed" product with a paid tier and a Discord-driven roadmap).
* **Q3 — Failure mode to flag?** **One on the public record:** "Mobile OSes aggressively suspend background apps, so mobile sync is near-realtime rather than instant. Desktop is the source of truth for live editing." *Source: [SurfSense Obsidian plugin README — Mobile section](https://github.com/MODSetter/SurfSense/tree/main/surfsense_obsidian).* The implication for any SkillTrace↔SurfSense bridge: SurfSense assumes the *desktop Obsidian* is the live source of truth; a SkillTrace-side proposal pipeline that needs a writeback to the vault would need to design for desktop-first, mobile-best-effort.
* **Q4 — One-line PR to docs naming SkillTrace?** Not publicly stated.

### 4.4. entire-vc / evc-local-sync-plugin

* **Q1 — Compatible with the write path?** **Partially, as a new conflict strategy.** Per-mapping conflict strategies include "newer file wins / Obsidian wins / AI project wins / **always ask**". The "always ask" strategy is the user-prompt shape; an AI-propose-then-user-approve-in-the-PKM shape is a new strategy. *Source: [README](https://github.com/entire-vc/evc-local-sync-plugin).*
* **Q2 — Maintenance cost?** Not publicly stated. The org's "AI Agents" product line (Team Relay + OpenClaw skill) is the closest existing precedent for a third-party AI tool calling into the plugin, and the cost there is "skill install + REST auth".
* **Q3 — Failure mode to flag?** **One on the public record:** "File deletion sync — optional, off by default: when enabled, deleting a file in one location deletes it in the other" — i.e. a *destructive* side-channel that defaults to off and that any external engine must opt into deliberately. *Source: same README, "Key Features".*
* **Q4 — One-line PR to docs naming SkillTrace?** Not publicly stated.

## 5. The drafted outreach messages

Both messages are sized to a maintainer's good will: under 200 words, a single plain-text reading, with the "we are listening, not committing" framing the ticket explicitly asks for. The human can copy-paste as-is or edit lightly.

### 5.1. Outreach to DiscourseGraphs (dg-team-mcp)

**Channel:** GitHub issue on the companion mainline repo [DiscourseGraphs/discourse-graph](https://github.com/DiscourseGraphs/discourse-graph) (the dg-team-mcp repo has issues disabled; the mainline is where maintainer conversation happens). If the human prefers a lower-friction first touch, a single comment on the open ADR discussion is a strong second option — but ADR discussions on this repo appear to happen in PRs, not issues, so the mainline issue is the safer bet.

**Subject / title:** "Protocol-portability question on the buffered-write / write-visibility bridge"

**Body:**

> Hi — I'm reaching out on behalf of SkillTrace, a single-learner, file-based learning engine whose hard boundary is "no automation of pass / master / delete". The only 2026 PKM-side pattern we've found that survives that boundary without re-litigating it is your `dg-team-mcp` write-visibility bridge (ADR-017, ADR-018), and your recent ADRs are the most explicit cost/rationale write-up of the pattern in the ecosystem. We are explicitly *not* asking you to port the bridge to Obsidian or Logseq — that's not in scope for us and not yours to take on.
>
> Four short questions, in case you have time to answer any of them:
>
> 1. From your side, is the propose→approve→apply protocol (with the in-memory resolution map at the bridge) portable to other PKM hosts whose plugin model is a poll-and-render-DOM loop (the shape Obsidian custom extensions take)? Or did you discover something in Roam's plugin API that wouldn't generalise?
> 2. What's the maintenance cost, in your experience, of a "this external engine is the source of truth; the PKM is a derived view" architecture? Anything you'd want an integrator to know up front?
> 3. The failure mode you most want integrators to know about — vault bloat, approval UX, resolution-state durability, something else?
> 4. If we built a SkillTrace-side bridge that speaks the same propose/approve/resolve protocol, would you accept a one-line doc PR on `dg-team-mcp` naming SkillTrace as a known external engine, or is that a higher-friction ask?
>
> No rush, no commitment, no deadline. We're a small project, this is a learning-mode signal for our G-ROI / G-Slot sizing. Thank you for the ADRs — they're the reason this question has a shape at all.

### 5.2. Outreach to hesprs (sync-engine)

**Channel:** a thumbs-up on the existing public wishlist issue [#214](https://github.com/hesprs/sync-engine/issues/214) plus a short comment, *or* an e-mail to `hesprs@outlook.com`. The wishlist comment is the lowest-friction, most discoverable option; the e-mail is the right channel if the human wants a private first contact. The recommended sequence is: wishlist comment first, e-mail only if no reply within a week.

**Subject / title (e-mail version):** "Module-shape question: SkillTrace as a new conflict strategy on sync-engine"

**Body (e-mail version; trim ~30% for the wishlist comment):**

> Hi Hēsperus — I'm the maintainer of SkillTrace, a small file-based learning engine with a hard "no automation of pass / master / delete" boundary. Our natural PKM-integration shape is a *propose → human-approve → apply* write, and your `registerConflictResolver` module surface looks like the cleanest place it could live as a new strategy.
>
> Three short questions, in case you have time:
>
> 1. Would a SkillTrace-style "propose before write" conflict strategy fit as a *new module* (not a core change), or would it have to live in core because of how the confirmation dialog is wired?
> 2. What's the maintenance cost, in your experience, of supporting an external engine that treats the Obsidian vault as a derived view of its own state? Anything you'd flag up front?
> 3. The failure mode you most want external-engine integrators to know about — version compatibility (Obsidian API churn), confirmation-dialog UX (your #233 work is the cleanest public datapoint on this), something else?
>
> If the answer is "interesting, but not now", that's a complete answer for us. A thumbs-up on the wishlist is also a complete answer. No PR is implied by this message.
>
> Thank you for the SDK and the module docs — they're why this is even a reasonable question to ask.

## 6. What the next agent / human should do

1. Read §1 and §2 of this artifact before doing anything else. The realistic deliverable is two short messages, not two calls.
2. Decide on the channel for DiscourseGraphs (mainline repo issue recommended). Send the §5.1 message. If the human prefers to wait for a public channel, leave the message and re-check in a week.
3. Decide on the channel for hesprs (wishlist #214 comment recommended as the lowest-friction first touch; e-mail as fallback). Send the §5.2 message. Wait one week for a public-channel reply before escalating to e-mail.
4. Record the maintainer's reply (or non-reply) on issue #106 as a "sizing implication" comment per the ticket's "Outputs" section, even if the answer is "no response yet" — that is a sizing input too (the *absence* of a reply after the conventional maintainer-response window is data, specifically a "the ecosystem is small / not yet engaged" signal that the G-ROI / G-Slot sessions need to weigh).
5. **Do not** post a "SkillTrace↔SurfSense" or "SkillTrace↔Local Sync" outreach in this round. Those are the §3.3 considered-and-not-recommended candidates and the right call is to defer them to a follow-up ticket.

## 7. Sources

**DiscourseGraphs / dg-team-mcp (primary):**
* Repo — [github.com/DiscourseGraphs/dg-team-mcp](https://github.com/DiscourseGraphs/dg-team-mcp)
* Companion mainline — [github.com/DiscourseGraphs/discourse-graph](https://github.com/DiscourseGraphs/discourse-graph)
* Org page (people, repositories) — [github.com/DiscourseGraphs](https://github.com/DiscourseGraphs)
* ADR.md (ADR-017 "Roam-Native Multi-Batch Write Approval", ADR-018 "Discourse Tools May Write Relations", ADR-019, ADR-020) — [ADR.md](https://github.com/DiscourseGraphs/dg-team-mcp/blob/main/ADR.md)
* ARCHITECTURE.md (write-visibility subsystem, file structure, bridge endpoints) — [ARCHITECTURE.md](https://github.com/DiscourseGraphs/dg-team-mcp/blob/main/ARCHITECTURE.md)
* README (tool listing, tool groups, env vars) — [README.md](https://github.com/DiscourseGraphs/dg-team-mcp)

**hesprs / sync-engine (primary):**
* Repo — [github.com/hesprs/sync-engine](https://github.com/hesprs/sync-engine)
* Maintainer profile (e-mail, X, ORCID, bio) — [github.com/hesprs](https://github.com/hesprs)
* README (feature set, module system, roadmap v3.0/v3.1/v3.2, wishlist pointer) — [README.md](https://github.com/hesprs/sync-engine)
* Issue list (responsiveness signal, wishlist #214, #233 destructive-ops UX, #247 close Aug 24) — [sync-engine issues](https://github.com/hesprs/sync-engine/issues?q=is%3Aissue)
* SDK on npm — [npmjs.com/package/@hesprs/sync-engine-sdk](https://www.npmjs.com/package/@hesprs/sync-engine-sdk)
* Documentation site — [sync.consensia.cc](https://sync.consensia.cc)

**MODSetter / SurfSense (primary):**
* Repo — [github.com/MODSetter/SurfSense](https://github.com/MODSetter/SurfSense)
* Maintainer profile — [github.com/MODSetter](https://github.com/MODSetter)
* Obsidian plugin README (push-only architecture, mobile caveats, privacy section) — [surfsense_obsidian/README.md](https://github.com/MODSetter/SurfSense/tree/main/surfsense_obsidian)
* DeepWiki third-party walkthrough of the plugin sync engine — [deepwiki.com/MODSetter/SurfSense/17.1](https://deepwiki.com/MODSetter/SurfSense/17.1-plugin-architecture-and-sync-engine)
* Discord contact — [discord.gg/ejRNvftDp9](https://discord.gg/ejRNvftDp9)

**entire-vc / evc-local-sync-plugin (primary):**
* Repo — [github.com/entire-vc/evc-local-sync-plugin](https://github.com/entire-vc/evc-local-sync-plugin)
* Org profile (people, repositories, contact channels) — [github.com/entire-vc](https://github.com/entire-vc)
* README (per-mapping conflict strategies, "always ask", file-deletion-sync off by default) — [README.md](https://github.com/entire-vc/evc-local-sync-plugin)
* Public contact e-mails — `support@entire.vc`, `in@entire.vc`; Telegram [t.me/entire_vc](https://t.me/entire_vc) (per the org profile)

**Local SkillTrace documents weighed as constraints:**
* Wayfinder ticket #106 (this ticket) — [github.com/earledotpy/skilltrace/issues/106](https://github.com/earledotpy/skilltrace/issues/106)
* Wayfinder map #95 (consolidated post-v1 roadmap) — [github.com/earledotpy/skilltrace/issues/95](https://github.com/earledotpy/skilltrace/issues/95)
* R-Tier3 ecosystem research (predecessor artifact, on `research/r-tier3-ecosystem` branch) — `research/r-tier3-ecosystem.md`
* `CONTEXT.md` — Learner (1–8), asserted progress (36–41), engine/curriculum split (58–66), hard boundary (90–97), advisory annotation (181–187), Event log (318–323), Serve (325–332)
* `docs/POST_V1_BACKLOG.md` — Tier 3 (23–27)
* `docs/skilltrace-application-roadmap.md` — twenty governing design decisions (35–94), RC plan (98–110)

**Negative finding (no public mention):**
* A web search for `"SkillTrace" site:github.com OR site:obsidian.md OR site:discuss.logseq.com` returns no mention of *this* SkillTrace (the only two `SkillTrace` repositories on GitHub are `handcraftedbygod/SkillTrace` — a Claude-skill malware scanner — and `hideya/skilltrace` — an AI-agent skill observability tool. Both are unrelated to the SkillTrace that is the subject of this ticket). Verified 2026-08-27.
