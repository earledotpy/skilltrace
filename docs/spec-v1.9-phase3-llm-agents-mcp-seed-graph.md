# Spec — v1.9 Phase 3 LLM/agents/MCP seed graph + deployment primer

**Status:** locked hand-off (map [#163](https://github.com/earledotpy/skilltrace/issues/163)).
**Target:** v1.9, Phase 3 LLM/agents/MCP seed-graph content plus the FastAPI + Docker-family deployment primer as full seed nodes, on the existing v1.8 surface.
**Map:** [#163 Map — v1.9 Phase 3 LLM/agents/MCP seed graph + deployment primer](https://github.com/earledotpy/skilltrace/issues/163)
**Decisions:** [R-Sources #164](https://github.com/earledotpy/skilltrace/issues/164) ·
[R-PrimerToolchain #165](https://github.com/earledotpy/skilltrace/issues/165) ·
[G-GraphShape #166](https://github.com/earledotpy/skilltrace/issues/166) ·
[G-Primer #167](https://github.com/earledotpy/skilltrace/issues/167) ·
[T-SeedGraph #168](https://github.com/earledotpy/skilltrace/issues/168) ·
[T-Spec #169](https://github.com/earledotpy/skilltrace/issues/169) (this spec).
**Locked inputs (operationalized, not re-debated):** the v1.9 source list from
`docs/POST_V1_ROADMAP.md` v1.9 slot row + R-Sources
[#164](https://github.com/earledotpy/skilltrace/issues/164) and R-PrimerToolchain
[#165](https://github.com/earledotpy/skilltrace/issues/165); the 6-stage
seed-provenance chain from
[#151](https://github.com/earledotpy/skilltrace/issues/151); the locked graph shape from
[G-GraphShape #166](https://github.com/earledotpy/skilltrace/issues/166) and the locked primer checklist from
[G-Primer #167](https://github.com/earledotpy/skilltrace/issues/167); the v1.8 locked spec
`docs/spec-v1.8-phase2-ml-seed-graph.md` with its T-TestArch/T-Exit pattern
(three-layer TDD, E1/E2/E3 + SA1–SA7 + DG1–DG2).

The builder must not reopen product or architecture decisions. Terms follow
`CONTEXT.md`; all existing hard boundaries remain binding. Build order: the
v1.8 built tree first (88 nodes / 136 edges / 33 resources — the tree this
spec's draft was authored against), then this spec's deltas. The T-SeedGraph draft branch predates
the v1.9 build, so merge it onto the built tree and re-run every validator.

> Hand-off gate (from map `Destination`): a builder can implement v1.9
> without reopening a product or architecture question. This doc satisfies
> that gate: every acceptance bullet is a concrete check (commands, gate
> ids, file paths).

---

## 0. Scope and explicit non-goals

In scope for v1.9:

- The Phase 3 LLM/agents/MCP seed graph from the T-SeedGraph draft branch
  (`v1.9/seed-graph-draft` @ `8adcba7`): 12 new nodes, 21 `graph/edges.yaml`
  additions, 12 `graph/resources.yaml` additions, including the ≥ 1 capstone
  integration node with ≥ 2-source citation that deploys via the primer (§2).
- The deployment primer as full seed nodes (not an appendix): 2 portfolio
  primer nodes (FastAPI minimal app + Docker Engine build/run/smoke) with the
  Engine-canonical 4-command acceptance and the Gradio + ZeroGPU hosted split (§2, §10).
- The 3-part verification bar applied to all 12 new resources (9 sources + 3 primer) (§10(b)).
- Test-count port + locked state-entry materialization + v19 safety/doc gates (§§6–7).

Explicitly **out of scope** (per map `Out of scope` + ticket verdicts):

- Phase 3 source re-debate — the 9-source list is **locked** from the slot row
  (HF Agents Course, DSPy, LangGraph, smolagents, LlamaIndex, MCP, Microsoft Agent
  Framework replacing AutoGen, OpenAI Agents SDK, PydanticAI). The spec operationalizes
  the bar; it does not re-debate the list.
- Phase 4 remainder / Phase 5 survey — HF Context Course, CrewAI, DL.AI short
  courses and the rest of `docs/roadmap/phase-4-agentic-ai.md` are strictly out for v1.9.
- Phase 2 graph reshape; v1.8 spec re-opens — v1.8 is locked; v1.9 adds content
  against the built tree (additions only — no existing edge, node, or resource touched).
- Automated positive verification — forbidden by the v1 hard boundary. A successful
  check never sets `last_verified` or clears `broken`.
- No engine seam changes: seed-data content only on the existing v1.8 surface
  (`validate graph`, `validate resources`, `check-resource(s)`, `verify-resource`,
  `replace-resource`). No new modules, policy blocks, event schemas, or
  interface-layer revival (ADR 0002).
- Docker Desktop as default — Docker Engine is the canonical acceptance target;
  Podman / Rancher Desktop / Finch / Colima appear as one advisory note, never as
  multiplied acceptance (§2, §10).
- Cloud sync / server-side engine; multi-learner — ruled elsewhere (local-first,
  single-learner by design).
- Scheduling automation of any shape; rate-limit / `robots.txt` / 429 backoff;
  deep verification (SSL / cert / content hash); Web UI changes for seed content —
  inherited deferrals/boundaries from the v1.7 and v1.8 maps.
- Capstone trio build + portfolio (v2.0) / adaptive sequencing (v2.1) — v1.9 enables
  them; building them is their own slots.

## 1. Data sources and source-of-truth boundaries

`graph/edges.yaml` is the sole relationship source: node frontmatter carries
no `state`, `prerequisites`, `unlocks`, or `node_type`, and the v1.9 nodes use
only the locked seed-provenance frontmatter keys (`source_metadata`,
`regeneration_key`, `section_provenance`, `roadmap_anchors`) plus the standard
node fields. `graph/resources.yaml` is the authoritative LearningResource
registry (loader: `src/skilltrace/resources/registry.py:39`
`_REGISTRY_RELPATH`); `execution/events.yaml` is audit-only. Markdown/YAML
sources are read and written through existing seams; SQLite exports are
disposable and never read.

The v1.9 source list is **locked** (map Notes; R-Sources #164, strictly the slot row):
HF Agents Course, DSPy, LangGraph, smolagents, LlamaIndex, MCP (spec/protocol),
Microsoft Agent Framework (AutoGen successor, maintenance mode), OpenAI Agents SDK,
PydanticAI — plus FastAPI and the Docker-family docs (Docker Engine canonical;
Podman / Rancher Desktop / Finch / Colima as alternates; Docker Desktop NOT the
default). The spec operationalizes the bar (§10); it does not re-debate the list.

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
version, sections, regeneration key, `reference_only` note, `last_verified`
pending marker), so the closed registry schema needs no change for provenance.

No policy change: v1.7's `policy/resource_web_verification.yaml` (spec §3,
`resource_web_verification_policy`) is referenced unchanged. The builder makes **no**
`POLICY_FILES` change (`src/skilltrace/policy/loading.py:18`) and ships **no** new policy file.
The v1.9 primer introduces no policy surface — Engine-canonical vs. alternates is a
seed wording distinction inside node bodies, not a policy block.

## 2. Architecture / seed-graph content

Per [T-SeedGraph #168](https://github.com/earledotpy/skilltrace/issues/168):
merge the draft branch `v1.9/seed-graph-draft` @ `8adcba7` (16 files, +1229,
additions only — zero removed lines in `graph/edges.yaml` / `graph/resources.yaml`,
no existing node/edge/resource touched) onto the built tree, then re-run
`validate graph` and `validate resources`. Post-merge expectations: 100 nodes,
157 edges (157 active), 45 resources.

### 2.1 New node files (12, all under `graph/nodes/`)

Tracks only (bands dropped per G-GraphShape; existing foundational / portfolio /
consolidation wording only — consolidation unused, v1.8 precedent). Prefix
`agents.*` mirrors the `ml.*` precedent.

| File | Track | Role |
|---|---|---|
| `agents.concepts.agent_fundamentals_01.md` | foundational | Agent/tool/action-loop vocabulary; CodeAgents vs tool-calling (HF Units 0–1) |
| `agents.frameworks.smolagents_01.md` | foundational | CodeAgent vs ToolCallingAgent, tools, sandboxes, models |
| `agents.frameworks.langgraph_01.md` | foundational | Graphs/state/reducers, persistence, prebuilt ReAct agent |
| `agents.data.llamaindex_rag_01.md` | foundational | Agentic RAG pipeline (retrievers, query engines, MCP tools package) |
| `agents.optimization.dspy_01.md` | foundational | Program-don't-prompt, signatures/modules, GEPA optimization |
| `agents.protocol.mcp_01.md` | foundational | Base protocol (JSON-RPC 2.0, lifecycle), server Tools, stdio + Streamable HTTP |
| `agents.frameworks.ms_agent_framework_01.md` | foundational | Workflows (sequential/concurrent/handoff), MCP-as-tools, migration guides |
| `agents.frameworks.openai_agents_sdk_01.md` | foundational | Agents/Runner, handoffs, guardrails, tracing |
| `agents.frameworks.pydanticai_01.md` | foundational | Typed harness, toolsets, built-in test model, pydantic-evals |
| `agents.deploy.fastapi_minimal_01.md` | portfolio | **Primer 1/2** — `app/main.py` Hello World, `fastapi dev` vs `fastapi run`, `/docs` |
| `agents.deploy.docker_engine_build_run_01.md` | portfolio | **Primer 2/2** — from-scratch Dockerfile + Engine 4-command smoke |
| `agents.capstone.deployed_agent_integration_01.md` | portfolio | **Capstone** — LangGraph + MCP agent served by FastAPI, Engine-local + ZeroGPU hosted |

Primer scope stops at the official first-steps + Docker floor per G-Primer:
canonical layout is `app/` (`app/main.py` with `FastAPI()`, `@app.get("/")`
returning `{"message": "Hello World"}`); single-file noted as one-line variant.
`--proxy-headers` and the deprecated `tiangolo/uvicorn-gunicorn` base image are
one-line warnings inside node bodies, never nodes. Max 2 FastAPI primer nodes.
All primer nodes claim no 30-min fit (`min_minutes: 60`, standing
curriculum-authoring rule enforced by `tests/seed/test_seed_acceptance.py`).

### 2.2 New edges (21, all appended to `graph/edges.yaml`)

Hard chain (11): fundamentals → each of the other 8 framework/protocol nodes
(8); `fastapi_minimal` → `docker_engine_build_run` (1, the self-contained primer
chain); LangGraph + docker-primer → capstone (2, the two-lineage capstone parents).
Soft ordering links (10): HF overview → primer pair (2); MCP → MCP-consuming
frameworks capped at 4 (smolagents, llamaindex, ms-agent-framework, openai-agents-sdk)
(4); DSPy → LangGraph ordering (1); 2 framework comparisons
(smolagents → langgraph, pydanticai → openai-agents-sdk) (2); MCP → capstone (1,
the tools-arrive-over-MCP surface — ordering, not dependency since the two hard
parents already supply an integration path). No existing edge touched; no source
dropped, added, or reordered. Hard-vs-soft doctrine carried from v1.8: hard = target
incoherent without source; all framework-to-framework links soft; short hard chains only.
Post-merge: 136 + 21 = 157 edges, all active.

Primer wiring (locked): self-contained hard chain (minimal-app → Dockerfile/build-run/smoke);
only new soft edges point into it; the single hard edge out is the Dockerfile node →
capstone. Only new soft edges point into the primer; no existing node gains an edge.

### 2.3 New resources (12, all appended to `graph/resources.yaml`)

| ID | URL | Cost claims | Supports |
|---|---|---|---|
| `hf-agents-course` | `https://huggingface.co/learn/agents-course/unit0/introduction` | free + `certificate` | fundamentals |
| `dspy-docs` | `https://dspy.ai/` | free | dspy, capstone |
| `langgraph-docs` | `https://docs.langchain.com/oss/python/langgraph/overview` | free | langgraph, capstone |
| `smolagents-docs` | `https://huggingface.co/docs/smolagents` | free | smolagents |
| `llamaindex-docs` | `https://developers.llamaindex.ai/python/framework/` | free | llamaindex-rag, capstone |
| `mcp-spec` | `https://modelcontextprotocol.io/` | free | mcp, smolagents, llamaindex, ms-framework, openai-sdk, capstone |
| `ms-agent-framework` | `https://learn.microsoft.com/en-us/agent-framework/overview` | free | ms_agent_framework |
| `openai-agents-sdk` | `https://openai.github.io/openai-agents-python/` | free | openai_agents_sdk |
| `pydanticai-docs` | `https://pydantic.dev/docs/ai/` | free | pydanticai |
| `fastapi-docs` | `https://fastapi.tiangolo.com/` | free | fastapi_minimal, docker_build_run, capstone |
| `docker-engine-docs` | `https://docs.docker.com/engine/` | free | docker_build_run, capstone |
| `hf-spaces-zerogpu` | `https://huggingface.co/docs/hub/en/spaces-zerogpu` | free | capstone |

Commercial-boundary notes (seed wording, never acceptance): LangGraph
`langgraph-api` server / Platform hosting, LlamaCloud platform, OpenAI per-token +
metered tool calls, model/sandbox/hosting costs are named as "billed separately /
never acceptance here" in the `license` free-text — the builder never pins a rate.
New resources land **unverified by design**: no human `last_verified` is
asserted by automation (hard boundary holds); the `license` free-text carries a
`last_verified pending (unverified by design, re-pin at spec time)` marker.
Human verification at build follows §10(b). Resource coverage post-merge: 100/100
nodes linked.

### 2.4 Capstone integration node

`agents.capstone.deployed_agent_integration_01` (deployed-agent folder: stateful
LangGraph agent with checkpointer on, ≥ 1 tool served by the learner's own MCP server
from the protocol node, wrapped in the primer FastAPI service, checked twice —
Engine-local via the 4-command acceptance + hosted via Gradio SDK plus `@spaces.GPU`
ZeroGPU deploy; never `docker push` to Spaces; closes with a best-model-style analysis
naming which source's technique moved the agent's behavior) is the ≥ 1 / ≥ 2-sources
capstone:

- Its two hard prerequisites span two source lineages: the LangGraph-anchored
  `agents.frameworks.langgraph_01` chain and the primer-anchored
  `agents.deploy.docker_engine_build_run_01` chain.
- Its supporting resources cite LangGraph + MCP (tools via MCP) + the primer
  (FastAPI serve, Engine-local check, ZeroGPU hosted split) directly, with DSPy and
  LlamaIndex one soft edge away as expected analysis ingredients.

The full criterion walk-through lives in the node's own `Capstone
integration identification` body section; the builder does not re-argue it.

### 2.5 Primer acceptance (from G-Primer, operationalized verbatim in §10)

Engine canonical acceptance (stock CI `ubuntu-24.04`, preinstalled Client+Server
28.0.4; `docker --version` recorded as evidence only). All exit 0, fixed mapping
`-p 80:80`:

- `docker build -t <primer-image> .` → exit 0
- `docker run -d --name <primer-container> -p 80:80 <primer-image>` → exit 0
- `curl -f http://localhost:80/` → exit 0, body `{"message": "Hello World"}`
- `curl -f http://localhost:80/docs` → exit 0 (HTTP 200, Swagger UI)

No Compose, no Buildx, no push/registry in acceptance. Alternates (Podman / Rancher
Desktop / Finch / Colima) appear as a single advisory note inside the primer node —
commands map to `podman build/run` or the alternate's Docker-compatible path; Engine
is the only checked target and the only name in §10 acceptance. Docker Desktop stays
non-default (subscription gate). Spaces deploy expectation (capstone split): local
container check = Engine per above; hosted check = Gradio SDK + `spaces.GPU` ZeroGPU
deploy (free tier: max 2 Spaces, 5 min/day) — acceptance checks the Space URL resolves
plus the ZeroGPU decorator present. Never `docker push` to Spaces (Docker Spaces need
a paid plan).

## 3. Policy

No new policy block. The primer's Engine-canonical vs. alternates distinction is seed
wording inside node bodies, not policy; verification reuses the existing staleness
window with no new config. The builder references v1.7's
`resource_web_verification_policy` unchanged: strict booleans for
`enabled`/`follow_redirects`, integer timeout 1–120, method `HEAD`/`GET`, non-empty
User-Agent; missing, malformed, unknown, or out-of-range values fail `validate policy`.
The policy stays advisory and can never authorize positive verification.

## 4. CLI

No new command ships in v1.9 — content-only slot on the v1.8 surface. The builder
reuses the v1.7/v1.8 surface unchanged:

- `skilltrace check-resource <id>` — single-URL reachability observation (zero writes).
- `skilltrace check-resources [--all | --stale-only]` — sequential batch sweep (G-Batch
  `batch()` helper, zero writes, `Kind.READ_ONLY`, emits no event).
- `skilltrace verify-resource <id> --check-url` — human `--broken --reason` path stays
  reason-text only; enriched `status_code`/`final_url` fields are observed detail written
  only by the `--check-url` preflight passthrough.
- `skilltrace resource-report`, `skilltrace health` — disposable-export smoke (§7 E1).

The primer's Engine 4-command acceptance (§2.5) is a **manual** `docker`/`curl` check
the builder runs by hand at build time — not a new `skilltrace` subcommand, not a gate
runner, not an event-emitting command. The first gate-runner consumer stays as decided
in #151 (v1.8 ML capstone first, v1.9 deployment-primer check second); no runner ships
in this slot. No scheduling primitive ships — no cron file, no serve background task,
no `today` hook.

## 5. Replacement / retire behavior

No change from v1.8. Warning-only retired handling (`validate resources`:
dangling `supports` on a retired entry → `WARN`, exit 0, with the locked v1.8 line;
duplicates and malformed retired shape stay `ERROR`; orphan warning suppressed for
retired entries) and the enriched broken-marker shape (`status_code` + `final_url`,
both optional, `None` omitted, legacy `{date, reason}` valid) are referenced unchanged
from `docs/spec-v1.8-phase2-ml-seed-graph.md` §§1, 5, 5.1. `validate graph` never reads
`graph/resources.yaml` (nodes/edges only — `src/skilltrace/commands/validate.py:50`),
so retired `supports` links are judged solely in `validate resources`.

## 6. Testing architecture

v1.9 adds **no new code surface** (content-only: 12 nodes + 21 edges + 12 resources),
so there is no new unit/CLI/integration layer to TDD. §6 ports the v1.8 count/presence
family to the v1.9 post-merge numbers and adds the v19 release gates — following the
same three-layer pattern (seed-count assertions on the real repo, CLI output presence
on disposable repos, registry integration via existing helpers). No Web layer. No live
HTTP anywhere; the primer's Engine/`curl` acceptance (§2.5) is a manual build-time check,
never a pytest fixture (no Docker daemon in unit tests).

- **Seed counts** (update in place, curated-repo guards only):
  `tests/graph/test_edges.py:130` — `len(edges) == 136` → `157`;
  `tests/graph/test_validation.py:197-199` — `node_count == 88`, `edge_count == 136`,
  `active_edge_count == 136` → `100` / `157` / `157`;
  `tests/cli/test_report_command.py:378,380` — `33 resource(s), 88 node(s)` →
  `45 resource(s), 100 node(s)` and `coverage: 88/88` → `coverage: 100/100`,
  plus the two progress strings (`:90` `0 of 88` → `0 of 100`; `:145` `2 of 88` →
  `2 of 100`).
- **Locked state-entry materialization** (mirror the v1.8 merge): at spec-merge time,
  materialize the 12 new nodes' derived-readiness entries in `graph/state.yaml`
  (sync leaves locked-floor nodes absent by design) so that
  `tests/graph/test_state.py:204` (`set(store.entries) == node_ids`) and
  `tests/seed/test_seed_acceptance.py:185-188` (`test_progress_store_covers_every_node`)
  pass on the merged tree. The draft branch carries the sync-derived available flips
  only; the locked-floor materialization is the builder's merge step, exactly as v1.8 did.
- **Release gates** (new files, same pattern as v1.8): `tests/release/test_v19_safety_gates.py`
  (SA1–SA7 ported, §7 E2) and `tests/release/test_v19_doc_gates.py` (DG1–DG2, §7 E3).
- **Fixtures:** no new fixture directory, generator, or test infrastructure. The draft's
  `min_minutes: 60` floor on primer nodes keeps `test_effort_and_session_fit_are_consistent`
  green with no exception.

### 6.1 Behavior coverage matrix

| Behaviour | Seed-count | CLI | Integration |
|---|---|---|---|
| Post-merge counts (100 nodes / 157 edges / 45 resources) | exact | presence (`resource-report`, `report progress`) | n/a |
| Locked-floor state materialization (every seed node present, derived states only) | n/a | n/a | exact (`test_state.py:204`, `test_seed_acceptance.py:185-188`) |
| Primer nodes carry no 30-min fit (`min_minutes: 60`) | n/a | n/a | exact (effort/fit consistency) |
| `check-resources --all` sweep over 12 new resources, zero writes, no event | n/a | registry-identical + event assertion | n/a |
| `--check-url` failure writes enriched marker only; success writes nothing positive | n/a | persisted safety assertion | exact |
| Manual Engine 4-command acceptance (NOT in pytest — hand-run at build, §10) | n/a | n/a | n/a |
| Empty-registry sweep, 429-as-BROKEN, retired WARN table | exact/presence | presence | exact (carried from v1.8, unchanged) |

## 7. Release exit gates (T-Exit-equivalent)

### E1 — Functional gates

```text
pytest tests/graph tests/seed tests/resources tests/policy tests/cli
skilltrace validate policy
skilltrace validate graph
skilltrace validate resources
skilltrace check-resource hf-agents-course
skilltrace check-resources --all
skilltrace check-resources --stale-only
skilltrace verify-resource hf-agents-course --check-url
skilltrace resource-report
skilltrace health
```

Plus the two manual build-time checks (hand-run, never pytest):

```text
docker build -t <primer-image> .
docker run -d --name <primer-container> -p 80:80 <primer-image>
curl -f http://localhost:80/
curl -f http://localhost:80/docs
```

(The hosted half of the primer split — Gradio + ZeroGPU Space URL resolves plus
`@spaces.GPU` decorator present — is a human eyeball check at build time, §10.)

The command gates use deterministic local/mock fixtures; no external
network or running Serve process is required. The v1.7/v1.8 gates
(`replace-resource --dry-run` / real, per v1.7 spec §9 and v1.8 spec §7) remain green —
v1.9 stacks on that surface. Post-merge `validate graph` must report 100
nodes / 157 edges and `validate resources` 45 resources before human
verification dates are asserted (§10).

### E2 — Safety assertions

Implement in `tests/release/test_v19_safety_gates.py` (SA1–SA7 ported verbatim from v18):

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
  Seed-content corollary (asserted in the same file): the 12 new nodes/edges/resources
  touch no `src/` path, add no CLI subcommand, and the manual Engine/`curl` acceptance
  emits no event and writes no registry field.

### E3 — Documentation gates

Implement in `tests/release/test_v19_doc_gates.py`:

- **DG1 — Spec gate:** this file has all required sections (§§0–10), every
  E1 command, and every assertion label SA1–SA7 as substrings.
- **DG2 — Glossary gate:** `CONTEXT.md` carries the §8 no-touch (the `Broken marker`
  line still names the optional `status_code` and `final_url` fields, and no
  agents/primer engine vocabulary has been added).

## 8. Glossary additions

No `CONTEXT.md` touch in the same change as this spec lands — the map's glossary-touch
fog patch resolves as no-ticket, exactly as v1.8's G-Glossary resolved to a single
line-touch, but here to zero lines. No other `CONTEXT.md` change, for these reasons:

- **No `Agent / Tool / MCP server` engine terms** — agent vocabulary (agent, tool,
  action loop, CodeAgent, handoff, guardrail, MCP server/client) is curriculum seed
  wording inside the 12 new node bodies, not engine vocabulary. The engine already
  covers the mechanics (SkillNode, GraphEdge, ArtifactSpec, ValidationGate); agents
  add no new state, edge type, or gate kind.
- **No `Deployment primer / Engine acceptance` term** — the primer is two portfolio
  seed nodes plus a manual 4-command checklist (§2.5), i.e. curriculum content + a
  hand-run check, not a node lifecycle or policy concept. `Verified` vs `Web check`
  already cover the human-assertion vs. automated-observation split the primer relies on.
- **No `Capstone integration node` term** — a slot acceptance construct
  defined in §2.4/§10(c), i.e. curriculum seed wording, not engine
  vocabulary (same ruling as v1.8 §8).
- **No #151 chain terms here** — `Candidate curriculum` / `Source anchor`
  remain proposed lines for the slot builder that first needs them as
  engine vocabulary; this spec uses them as seed-data conventions only (same
  ruling as v1.8 §8).

This resolves the map's glossary-touch fog patch: no separate glossary ticket.

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
  block a human-initiated action. Resources stay pure advice: primer/alternate
  standing never affects readiness, eligibility, or state.
- Node IDs immutable and never reused; new resources carry new slug IDs.
- Roadmap anchors are `reference_only` and never control locking or
  recommendation (every new node/edge carries them as such).

## 10. Acceptance

The v1.9 implementation is accepted when E1 passes, SA1–SA7 pass, DG1–DG2
pass, existing tests remain green, and the three slot-row checks below hold:

- [ ] **(a) Seed graph exports cleanly** — `validate graph` OK (100 nodes,
  157 edges, 157 active), `validate resources` OK (45 resources), and the
  disposable export smoke (`skilltrace health` + `resource-report`) runs
  exit 0 on the merged tree.
- [ ] **(b) All 9 sources + primer verified** — the bar has three distinguishable
  parts, all required, applied to each of the 12 new resources (9 source docs +
  `fastapi-docs` + `docker-engine-docs` + `hf-spaces-zerogpu`): (i) each carries a
  human-asserted `last_verified` with re-pinned versions at build (human act —
  the verdict; automation never asserts it); (ii) `check-resources --all` reports
  `OK` for the 12 canonical URLs (the objective observation — sweep success sets
  nothing); (iii) `validate resources` reports no broken markers on the 12 new
  resources. Re-pin at build (open pins from R-Sources/R-PrimerToolchain, 2026-09-05):
  every `latest` version; MCP latest-stable revision (2025-11-25 vs 2026-07-28 schema
  dir); LangGraph `langgraph-api`/Platform commercial terms; OpenAI tool-call rates;
  LlamaCloud/free-tier numbers if cited; alternate-tool versions (Rancher Desktop /
  Finch / Colima / Podman Desktop). This graduates the map's verification-bar fog patch
  with the first reading (registry-sweep clean) *plus* the human assertion that
  makes it a verification rather than a check.
- [ ] **(c) ≥ 1 capstone integration node with ≥ 2 source citations, deployed via the
  primer** — `agents.capstone.deployed_agent_integration_01` present in
  `graph/edges.yaml` with its two hard-prerequisite lineages (LangGraph chain +
  docker-primer chain) and ≥ 2 of the nine v1.9 sources in its supporting resources
  (LangGraph + MCP direct, DSPy/LlamaIndex analysis ingredients, §2.4) — **and** the
  deployment primer works on the free-first toolchain: the Engine 4-command acceptance
  (§2.5) passes by hand on stock CI (all exit 0, `-p 80:80`, Hello World payload +
  `/docs` 200; `docker --version` recorded as evidence only; no Compose/Buildx/push),
  alternates advisory-only, and the capstone hosted half resolves (Gradio + ZeroGPU
  Space URL + `@spaces.GPU` decorator present; never `docker push`).
- [ ] E1 + E2 + E3 from §7 all pass; the map's `Not yet specified` fog is
  empty (verification bar + test/exit-gate port graduated here, glossary-touch
  resolved as no-ticket in §8).

---

## References

`CONTEXT.md` (**SkillNode**, **GraphEdge**, **Track**, **Hard boundary**,
**Advisory policy**, **ArtifactSpec**, **ValidationGate**, **LearningResource**,
**Verified**, **Web check**, **Broken marker**, **Retired resource**, **Export**,
**Event log**); `AGENTS.md` (Safety rules; Current phase);
`docs/POST_V1_ROADMAP.md` (v1.9 slot row + Beyond this roadmap + phase-mapping sidebar);
`docs/roadmap/phase-4-agentic-ai.md` (out-of-scope pointer only — HF Context Course,
CrewAI, DL.AI extras stay out); `docs/spec-v1.8-phase2-ml-seed-graph.md` (§§0–10 shape
template + T-TestArch/T-Exit pattern: batch helper, marker enrichment, retired WARN,
SA1–SA7, DG1–DG2); `docs/adr/0002` (five layers);
branch `v1.9/seed-graph-draft` @ `8adcba7` (T-SeedGraph content:
12 nodes + 21 edges + 12 resources, capstone walk-through in the node's own body);
`research/v19-sources-findings.md` on branch `research/v19-sources` @ `cb42b76`
(R-Sources per-source URL/version/claims/section table, verified 2026-09-05);
`research/v19-primer-toolchain-findings.md` on branch `research/v19-primer-toolchain`
@ `d319b15` (R-PrimerToolchain Engine-canonical evidence: GH `ubuntu-24.04` Docker
Server 28.0.4, FastAPI Dockerfile floor, Gradio+ZeroGPU free-first path);
`src/skilltrace/resources/registry.py:39` (registry path),
`src/skilltrace/resources/verification.py:47` (`record_verification`),
`src/skilltrace/resources/validation.py:75` (`check_resources`),
`src/skilltrace/commands/validate.py:50` (`validate_graph` never reads resources),
`src/skilltrace/policy/loading.py:18` (`POLICY_FILES`),
`src/skilltrace/sqlite_export.py:29` (sole SQLite reader);
`tests/graph/test_edges.py:130` (136→157), `tests/graph/test_validation.py:197-199`
(88/136→100/157), `tests/cli/test_report_command.py:90,145,378,380` (88→100, 33→45),
`tests/graph/test_state.py:204` + `tests/seed/test_seed_acceptance.py:185-188`
(locked-floor materialization at merge);
`graph/edges.yaml`, `graph/resources.yaml`, `graph/state.yaml`
(post-merge: 100 nodes / 157 edges / 45 resources).
