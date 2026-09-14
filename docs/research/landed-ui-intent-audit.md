# A-Landed — landed v2.4 UI gap inventory vs. the single-page intent

**Ticket:** [A-Landed #244, map #243](https://github.com/earledotpy/skilltrace/issues/244).
**Date:** 2026-09-14.
**Source of truth:** the landed v2.4 UI served from `main` (`c097ef9`), fetched from `skilltrace serve --port 8395 --no-browser` and captured in `.svc_fetch.txt` on this branch. No placeholder invented.
**Companion:** the owner's two explicit user-friendly-surface questions (sessions stored + viewable? friendlier node view than a long flat list?) are captured as explicit card-inventory items on the unified-page prototype ticket [#246](https://github.com/earledotpy/skilltrace/issues/246) — this audit is the evidence for those items.

## 1. The single page, in owner's words

Owner intent (2026-09-14 grilling): the prototype `p24-reconsider.html` single rich page — "all the information on a single page with all relevant cards present" — with richness from reconsider's graph spine, the week-shaped plan, and the focus card, at the denser register. "Most of what was in the prototype is what I was expecting."

## 2. The landed page, in practice

What actually renders on `/`, from a live fetch (main, `c097ef9`):

```
<header>
  <div class="wrap">
    <h1 class="brand">SkillTrace</h1>
    <nav>…</nav>
    <div class="health-strip" aria-label="health">
      <span class="pill attention">Needs attention — 38 warnings</span>
      <a class="mut" href="/health">Full roll-up</a>
    </div>
  </div>
</header>

<main class="wrap">
  <h1>Today</h1>
  <p class="display">What is today about?</p>

  <div class="card focus">
    <div class="kicker">Today</div>
    <p class="lead">
      <a href="/nodes/agents.concepts.agent_fundamentals_01">Explain what an AI agent is and how tools extend an LLM</a>
    </p>
    <p><span class="pill active">Active</span></p>
    <p class="big">There's no session open — your best focus today is Explain what an AI agent is and how tools extend an LLM.</p>
    <p class="label">Where to learn</p>
    <div class="sub">Hf Agents Course -- https://huggingface.co/learn/agents-course/unit0/introduction</div>
    <div class="actions">
      <a class="btn primary" href="/nodes/agents.concepts.agent_fundamentals_01" data-intent="submit_evidence">Submit your next piece of evidence</a>
    </div>
  </div>

  <div class="card counts">
    <p><span class="count"><strong>48</strong> ready</span>
       <span class="count"><strong>1</strong> day practiced</span></p>
    <p class="mut"><a href="/next">See what to study →</a></p>
  </div>
</main>
```

The page surface: **one focus card + one count-set card**, and a pointer to `/next` for "what to study." That's it.

From the owner's words: "the summary that pulls people by the card where available" — the home shows one focus card, not the full available list; "how it should be a board of your available skill" — no board on `/`; "the summary and plan leading by the gap is hidden" — the gap is the separation, `/next` holds the queue/pressure; "a graph-view of your skills" — absent on `/`; "this is the board of cards" — not rendered. The landing reduced the single-page intent to one focus card + a pointer.

## 3. Gap inventory — what the prototype had on one page that the landed UI does not

The prototype's single rich page showed: focus card, available-node board, graph-spine/sequence context, queue/pressure, week shape, count set, health line. The landed home renders only two of those (focus card + count set). Each below names what's missing and where it went.

| # | Element (prototype's single page) | What landed did instead | Where it went (if anywhere) | Owner loss, plain |
|---|----|-----|-----|-----|
| 1 | **All available nodes as a readable board on one page** | No board; one focus card only, named as "your best focus today." | Available set not surfaced as card array on `/`. | Learner cannot see the set of what's available on one screen; prototype's "all available on one page" is unmet. |
| 2 | **Node title/identity readable on the page** | Focus is named here — focus card's lead link: "Explain what an AI agent is and how tools extend an LLM." | On the home, present as focus card's lead link. | This one landed — the node title is on the page. Other nodes are not named. |
| 3 | **Card state visible across the set** | One state shows: focus card carries `Active` pill. Count set shows aggregate counts (48 ready, 1 day practiced) but no per-card states. | Per-card states live on `/next` and `/nodes/{id}`; home shows only the focal one. | "All relevant cards present" implies states across the set — home carries only the focal card's state. |
| 4 | **Graph spine / sequence context on one page** ("where am I in the map; what unlocks what") | Not on `/`. Focus card has no spine/pathway context. | "Pathway summary + current spine" borrow deferred to node detail and `/next` (spec §A); on home it's absent. | The graph-first strand named in reconsider is invisible on home. |
## 4. The two user-friendly-surface questions, answered and routed to #246

### 4a. "Are sessions stored anywhere and viewable?"

Yes, sessions are persisted as YAML in the workspace:

- **`execution/sessions.yaml`** — session registry: each session has `id`, `status` (open/completed), `started_at`, optional `ended_at`, optional `template`.
- **`execution/session_work.yaml`** — the work items inside each session: `id`, `session_id`, `node_id`, `created_at`, optional `blocked`, `notes`, `minutes`.
- **`execution/blockers.yaml`** — blockers raised during study.
- **`execution/reviews.yaml`** — scheduled/completed reviews with outcomes.
- **`execution/remediation_actions.yaml`** — remediation actions.

So yes — your session history exists in plain YAML in your repo. You can read it directly, or via `skilltrace health` for a summary. From the live `skilltrace health` output on this repo: `execution: 1 sessions, 1 work items, 0 blockers, 0 remediation actions, 0 reviews — OK`.

But: **there is currently no web surface for viewing your session history.** The web UI shows only the *count* of sessions on `/health`, and the `/health` page itself is a roll-up with no session list. You can't browse your study sessions, see what you worked on in each, or read your notes/minutes. The data is there; the view is not. That's a real gap relative to the single-page intent — "how much did I study yesterday, and what did I do" belongs on a richer home or a dedicated history card.

### 4b. "Can graph nodes be viewed in a more user-friendly way than a long single list?"

The current web UI renders nodes in two list-shaped places only:

- **The `/next` queue** — a ranked, filterable list (by minutes + limit), but still a vertical list of cards, one per node.
- **The per-node `/nodes/{id}` detail page** — one node's full context, but reached by clicking or by knowing the ID.

There is **no** graph/tree/map visualization of how nodes relate. The relationships exist in `graph/edges.yaml` (prerequisite / unlocks relationships), the CLI `skilltrace health` reports "157 edges," but the web UI never renders the graph structure — you can't see "this node unlocks these 5 downstream skills" as a visual graph, and you can't browse by cluster/track.

This is deliberate, not missing: ADR 0006 keeps the serve layer stdlib-only (no JS framework, no graph-viz library); G-JS #225 locked the interaction posture at **tier 0 — JavaScript budget = 0**; the direction map (#208) explicitly refused "graph-viz libraries" and kept graph legibility by *abstraction* (pathway summaries + current spine, not a raw dump). The prototype `p24-reconsider.html` explored that abstraction in three variants (graph-first, plan-first, graph-dense) — throwaway, never built into the live UI.

So the long flat list isn't an accident — it's the current design boundary. The owner is right to want friendlier, and the right vehicle for that discussion is the unified-page prototype's card inventory on [#246](https://github.com/earledotpy/skilltrace/issues/246), where these become candidate cards: a **session history card** (date, duration, nodes worked on, notes) and a **spine/pathway card + a filterable/groupable available-node view** (by track prefix, by state, by readiness) — all tier-0 abstractions over the flat list, not a visual graph dump.

## 5. Resolution-ready reading

Bottom line:

- **Landed home:** one focus card + one count-set card + a pointer to `/next`. The focus card does name the node (item 2 above is satisfied at the home level), but the rest of the single-page richness — the available board, the spine, the queue/pressure, the week, the health calm line — is either absent or moved to other routes.
- **The two owner questions:** both answered with "yes, the data exists; no, the view doesn't — yet." Sessions are persisted as YAML and viewable via `skilltrace health` / direct file read, but not via a web session-history surface. Nodes live in a long flat list today (queue + per-node detail) with no graph/tree visualization; friendlier views are candidate cards.
- **The locked-row cause:** the home is rendered as the P3 card-stack (focus + count set + pointer), with queue/pressure/detail/spine deferred to other routes. That's the rows that made "all information on one page" into "one focal card + pointer."
| 5 | **Queue and pressure visible** (what's due, waiting, overdue; "the you are" of today) | Partially: count set shows "48 ready" + "1 day practiced," plus pointer "See what to study →" to `/next`. Actual queue/pressure cards live on `/next`. | On `/next` — not home. | Week-shaped plan and per-item queue/pressure expected on single page are on another route. |
| 6 | **Counts / daily state readable as a card** | Count set is a small card: "48 ready," "1 day practiced." Present. | Home. | This one landed. Daily state exists as a small card. |
| 7 | **Health / roll-up / calm-line presence on the page** | Health strip on page header: "Needs attention — 38 warnings" + link to `/health`. | Header strip, not a calm line below the fold. | Calm-line presence exists but as a header alert, not a substantive calm card on the page. |