# Advisory AI Options for the Mentor Advisory Seam (Issue #283, G-AdvisoryAI)

**Status:** research notes for the decision ticket — no recommendation made here.
**Date of research:** late 2026. Free-tier terms are volatile; every provider
section below ends with a re-verify checklist for implementation time.

## Scope and constraint frame

SkillTrace is local-first, CLI-first, single-learner. AI review is never an
acceptance authority (AGENTS.md safety rules); the advisory seam would only
attach commentary to evidence. That means the model must be cheap or free,
low-volume (a few calls per day), tolerant of intermittent availability
(advisory must never block), and privacy-disciplined (curriculum and learner
data only leave the machine with the learner's explicit consent). Two family
shapes are viable: a free cloud-hosted LLM API, or a small local model.

---

## 1. Free-tier cloud API options

### 1.1 Google Gemini API (free tier)

- The API has an explicit **Free tier** ("Free input & output tokens",
  "Limited access to certain models") alongside Paid tiers
  ([pricing](https://ai.google.dev/gemini-api/docs/pricing)).
- **Data use: the free tier trains on your content.** The pricing page's
  comparison table shows "Content used to improve our products: Yes" for the
  free tier and "No" for Paid, consistently across models (the same table is
  repeated for every model family, e.g. Gemini 2.5 Pro, TTS, Veo sections)
  ([pricing](https://ai.google.dev/gemini-api/docs/pricing)). This is the
  single most important fact for SkillTrace: learner-derived facts sent on
  the free tier would be used to improve Google's products.
- **Rate limits** are measured in RPM / TPM (input tokens per minute) / RPD,
  evaluated per project (not per key), with RPD resetting at midnight
  Pacific; experimental/preview models are explicitly more restricted, and
  exact per-model free-tier numbers are surfaced in the AI Studio rate-limit
  page rather than fully tabulated in the docs page fetched for this research
  ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).
  ⚠ Numbers vary by model generation and change frequently — re-check the
  per-model free-tier row at implementation time.
- **Context window:** the Gemini line advertises 1M-token class input
  windows (the batch-token tables in the rate-limits page reference
  1M-token inputs; long-context limits apply per model)
  ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).
  Far beyond SkillTrace's needs (advisory prompts are a few hundred tokens).
- **Deprecation churn is real:** the docs carry a "Deprecations" section and
  a May 2026 breaking-changes migration notice; model generations turn over
  quickly (the docs index already spans Gemini 2.5 → 3.x → 3.8 Flash)
  ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).
- **Structured output:** the docs nav includes native Structured outputs
  support — JSON-schema-constrained responses are a first-class API feature
  ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).

**Fit notes:** generous quality ceiling, but free tier = training data use;
zero-training exclusion requires the paid tier. Rate limits easily absorb a
few calls/day.

### 1.2 Groq (free plan)

- Free Plan limits (published table, organization-level; dimensions RPM /
  RPD / TPM / TPD): text models such as `openai/gpt-oss-120b`,
  `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` get **30 RPM, 1,000 RPD, 8K TPM,
  200K TPD**; `groq/compound` / `compound-mini` get **30 RPM, 250 RPD, 70K
  TPM** ([rate limits](https://console.groq.com/docs/rate-limits)).
- RPD of 250–1,000/day is far above a single learner's advisory cadence.
- **Data use:** Groq's privacy policy explicitly excludes "Customer Data" of
  its Cloud Services (GroqCloud, GroqChat, APIs) from the consumer privacy
  policy — that processing is governed instead by the Groq Services
  Agreement and Data Processing Addendum ([privacy policy](https://groq.com/privacy-policy/),
  "This Policy does not apply to ... Customer Data"). The Services Agreement
  / DPA must be checked at implementation time for a training clause; the
  privacy policy itself does not state training on Customer Data.
- **Models:** open-weight reasoning-capable models (GPT-OSS 20B/120B, Qwen
  3.8 27B per the same table). **Structured outputs** are a documented core
  feature ([Groq docs nav](https://console.groq.com/docs/rate-limits)).

**Fit notes:** very generous free limits, fast inference; smaller model
roster than Gemini; training terms live in the Services Agreement — verify.

### 1.3 OpenRouter (free models)

- Model IDs ending in `:free` are free variants. Platform-level limits apply
  regardless of account state and are tiered by **lifetime credits
  purchased**: the limits doc defines a two-row table (fewer than N credits
  vs. at least N credits) selecting between a lower and higher
  requests-per-day ceiling plus a per-minute cap. The numeric cells render
  on the live page but did not extract reliably in this fetch (commonly
  documented as 50 RPM and 50 RPD for accounts that have not purchased
  credits, rising to 1,000 RPD after a small credit purchase — **verify the
  current table**). Account state is queryable via `GET /api/v1/key`
  (`free_model_daily_requests.used/limit`)
  ([limits](https://openrouter.ai/docs/api-reference/limits)).
- Buying at least a small credit amount raises the daily ceiling; the paid
  (non-`:free`) variant of a model has **no platform-level request cap**
  ([limits](https://openrouter.ai/docs/api-reference/limits)).
- **Routing/privacy caveat:** free variants are typically served by rotating
  third-party providers, and the routing layer can swap providers silently;
  data-use posture for a `:free` model is therefore less deterministic than

### 1.4 Cerebras Inference

- **No standing free tier.** The self-serve offer is a **free trial with $5
  in credits** at account creation; the paid Developer tier starts at $10
  top-up with "10x higher rate limits than Free" and higher-priority
  processing ([inference page](https://www.cerebras.ai/inference)). The
  pricing page lists Developer-tier pricing only, with no permanent free
  plan ([pricing](https://www.cerebras.ai/pricing)).
- Extremely fast inference (up to 30x GPU speed claimed), OpenAI-compatible
  API ([inference](https://www.cerebras.ai/inference)). Good for evaluation
  bursts, not a durable free option.

### 1.5 GitHub Models — retired

- **GitHub Models has been fully retired as of July 30, 2026**; the
  playground, model catalog, inference API, and BYOK are no longer available
  to any customer. GitHub redirects new work to Azure AI Foundry or Copilot
  ([docs](https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models)).
- Do not plan against it.

### 1.6 Mistral (La Plateforme)

- The current pricing page no longer advertises a free **API** tier: the
  "Free" plan is for the Vibe assistant / Studio, and the popular tier
  includes **$10/mo in API credits**; API pricing is per million tokens
  (e.g., Mistral Large $0.50 in / $1.50 out per 1M tokens), with batch −50%
  and cached-input discounts
  ([pricing](https://docs.mistral.ai/getting-started/pricing/)).
- **Model training opt-out is shown as a plan feature** (opt-out columns on
  the plans comparison) ([pricing](https://docs.mistral.ai/getting-started/pricing/)).
  ⚠ The older "La Plateforme Experiment/free API plan" docs URL 404s now;
  whether a free-API experiment tier still exists must be re-verified
  directly in the La Plateforme console at implementation time.
- Open-weight Mistral models (e.g., Mistral 7B, Apache 2.0 lineage) can be
  self-hosted, blurring the cloud/local distinction
  ([pricing FAQ](https://docs.mistral.ai/getting-started/pricing/)).

### 1.7 Others

- AWS Bedrock: not free-tier friendly for LLM inference in general;
  relevant only if the learner already has AWS credits. Not researched
  further here.

---

## 2. Small local models

### 2.1 Runtimes

- **Ollama**: one-command model pulls, an OpenAI-compatible endpoint
  (`http://localhost:11434/v1`), and **structured outputs via JSON schema**
  (grammar-constrained decoding, "more reliability and consistency than
  JSON mode"), with Pydantic/Zod schema support and temperature-0 guidance
  ([structured outputs](https://ollama.com/blog/structured-outputs)).
- **llama.cpp**: plain C/C++, no dependencies, 1.5-bit through 8-bit integer
  quantization, CPU (AVX/AVX2/AVX512) and GPU (Metal/CUDA/Vulkan) backends,
  CPU+GPU hybrid inference, GBNF grammar tooling for constrained
  generation, and an OpenAI-compatible `llama-server` REST API
  ([README](https://github.com/ggml-org/llama.cpp)).
- **LM Studio**: GUI wrapper over the same GGUF ecosystem; same model zoo,
  adds a local server. (Alternative, not separately cited here.)

### 2.2 Candidate models (2–8B class) in the Ollama library

All distributed as GGUF with quantization tags
([library](https://ollama.com/library)):

| Model | Sizes | Notes |
|---|---|---|
| `llama3.2` | 1b, 3b | Small instruction-tuned; tools support |
| `gemma3` | 270m, 1b, 4b, 12b, 27b | 4b is the sweet spot for prose |
| `gemma2` | 2b, 9b | Prior generation; 2b is very light |
| `qwen2.5` | 0.5b–72b (3b, 7b relevant) | 128K context claimed, multilingual |
| `qwen3` | 0.6b–235b (4b, 8b relevant) | Reasoning/thinking modes |
| `phi3` (Phi-3 Mini) | 3.8b, 14b | Microsoft small models |
| `phi4` | 14b | Too large for 8 GB RAM class at Q8 |
| `mistral` | 7b | Apache 2.0 lineage; solid general prose |
| `granite4.2` (IBM) | 3b, 8b, 30b | Enterprise; structured JSON output built in |
| `lfm2.5` | 8b (1b active, MoE) | "Edge model built for fast, reliable tool calling on consumer hardware" |

Source for sizes/capabilities:
[Ollama library](https://ollama.com/library).

### 2.3 Hardware fit, quantization, throughput

- **RAM footprint:** rule of thumb — a Q4_K_M of an N-billion-parameter
  model needs roughly 0.6–0.8 GB per B parameter. Llama 3.2 3B / Qwen2.5 3B
  / Gemma 3 4B Q4 run comfortably in ~2–4 GB; 7–8B Q4 fits in 8 GB;
  8 GB-RAM machines should avoid 7B+ at Q8 (~8–10 GB of weights plus KV
  cache). Quantization levels 1.5 through 8 bit are supported upstream
  ([llama.cpp README](https://github.com/ggml-org/llama.cpp)).
- **Q4 vs Q8:** Q4 cuts memory and compute roughly in half vs Q8 with
  generally small quality loss for instruction-following tasks (Q4_K_M is
  the widely used default); Q8 approximates full precision. For ~150-token

**Fit notes:** the advisory seam tolerates 30–60 s latency (it is not in the
pass/master critical path — and must never be). Main costs are setup
friction (install runtime + pull a 2–5 GB model) and a quality ceiling below
frontier models, mitigated by schema-constrained output and a tight prompt.

---

## 3. Integration shape for a CLI advisory layer

### 3.1 Context discipline / prompt injection

- **Send derived facts, not raw files.** The engine already derives state on
  demand (AGENTS.md: eligibility is derived, never stored as truth); the
  prompt should carry only a small projection of that derivation — node ID,
  state, next-action label, blocker count — never raw curriculum markdown,
  evidence text, or event logs. This (a) minimizes what leaves the machine
  on cloud options, and (b) gives the model nothing to "rewrite": it cannot
  fabricate prerequisites or unlock states that are not in the context.
- **Untrusted-content boundary:** if any evidence text or resource titles
  flow into the prompt, wrap them as data with explicit delimiters and
  instruct the model to treat them as quoted material. Advisory output must
  be labeled advisory in the UI regardless of content (AGENTS.md: AI review
  is never an acceptance authority — nothing the model says may flip a node
  state, even by appearance).
- **Output is advisory only:** attach as commentary on the evidence record;
  never write to `graph/edges.yaml`, `state.yaml`, or the event log as
  computed state. If commentary is persisted, the advisory generation
  follows the normal "every mutating command appends one event" rule.

### 3.2 Structured output reliability

- **Local (Ollama):** JSON-schema-constrained decoding is supported directly
  via the `format` parameter — grammar-constrained, not just "please return
  JSON"; recommended practice is temperature 0 and a schema-serialized
  prompt aid ([Ollama structured outputs](https://ollama.com/blog/structured-outputs)).
  llama.cpp offers the same class of control via GBNF grammars
  ([llama.cpp](https://github.com/ggml-org/llama.cpp)).
- **Cloud:** Gemini exposes native structured outputs; Groq documents
  structured outputs as a core feature; OpenRouter routes
  OpenAI-compatible requests to providers — structured-output support
  varies by upstream provider, so pin a provider or validate-and-retry on
  the client
  ([Gemini docs](https://ai.google.dev/gemini-api/docs/rate-limits),
  [Groq docs](https://console.groq.com/docs/rate-limits),
  [OpenRouter](https://openrouter.ai/docs/api-reference/limits)).
- **Client-side hardening:** always validate the model's JSON against the
  schema; on failure, retry once, then degrade to "no advisory" — advisory
  absence must never surface as an error to the learner.

### 3.3 Latency expectations

- Cloud APIs: short-advisory generation (~100–200 output tokens on a small
  prompt) typically completes in **1–5 s** on fast providers (Groq and
  Cerebras advertise sub-second-to-few-second generation; Cerebras claims
  up to 30x GPU speed) ([Cerebras](https://www.cerebras.ai/inference)).

---

## 5. Options-fit summary (for the decision ticket)

- **Gemini API free tier** gives the highest prose quality at $0 but is the
  only mainstream option that openly states free-tier content is used to
  improve products — a direct conflict with local-first privacy unless the
  learner opts in consciously or the deployment uses the paid tier.
- **Groq free plan** offers the most generous free limits among
  single-vendor APIs with documented structured outputs; its training
  posture lives in the Services Agreement/DPA and must be verified before
  implementation.
- **OpenRouter `:free`** maximizes model choice at $0 but has the weakest
  data-use determinism (rotating providers) and daily caps tiered by credit
  purchases.
- **Cerebras** and **Mistral** are not standing-free options today (trial
  credits / paid entry plan respectively); GitHub Models is retired and not
  plannable.
- **A small local model** (Gemma 3 4B or Qwen2.5/Qwen3 4B–7B Q4 via Ollama,
  with llama.cpp as a fallback) is the only option with a categorical
  privacy guarantee and no deprecation churn, at the cost of setup friction
  and CPU-only latency in the tens of seconds — acceptable for an advisory
  seam that is never on the critical path.
- **Hybrid** is a legitimate shape: local-by-default with an opt-in cloud
  provider for learners who want higher quality and accept the data egress;
  the context-discipline rule (derived facts only) keeps what leaves the
  machine minimal in all cloud cases.

## Re-verify at implementation time (volatile terms)

1. Gemini: current free-tier per-model RPM/RPD/TPM and the free-tier
   "used to improve products" clause —
   [pricing](https://ai.google.dev/gemini-api/docs/pricing),
   [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).
2. Groq: free-plan limits table and the Services Agreement/DPA data-use
   clause — [rate limits](https://console.groq.com/docs/rate-limits).
3. OpenRouter: exact free-variant RPM/RPD numbers and per-provider training
   flags — [limits](https://openrouter.ai/docs/api-reference/limits).
4. Mistral: whether a free API experiment tier still exists
   ([pricing](https://docs.mistral.ai/getting-started/pricing/)).
5. Ollama/llama.cpp: current small-model roster and structured-output
   behavior ([Ollama library](https://ollama.com/library)).

- Local CPU: see §2.3 — **~10–60 s** for 200 tokens at 3–8B Q4; this argues
  for a smaller model (3–4B), streaming output, or async generation the
  learner collects later.
- Rate-limit fit is a non-issue at a few calls/day on every free-tier option
  (Groq 250–1,000 RPD; OpenRouter daily caps; Gemini per-model RPD) — see
  §1 tables.

---

## 4. Cost / privacy comparison

| Dimension | Cloud free tier (Gemini / Groq / OpenRouter) | Small local model (Ollama / llama.cpp) |
|---|---|---|
| **Data leaves machine** | Yes: prompt facts sent to provider (Gemini free tier: used to improve products; OpenRouter rotates providers) | **No — nothing leaves the machine** |
| **Cost at a few calls/day** | $0 within free caps | $0 + one-time 2–5 GB download, own electricity |
| **Rate-limit fit** | Ample (§1); risk of policy changes | None; bounded by hardware |
| **Setup friction** | API key management (env var/secret store), signup, terms acceptance | Install Ollama/llama.cpp; pull a 2–5 GB model; ~4–8 GB RAM headroom |
| **Quality ceiling** | High (frontier-adjacent flash-class models) | Moderate: good short explanatory prose from 4B-class, weaker reasoning |
| **Latency (~200 tokens)** | ~1–5 s | ~10–60 s CPU-only; ~1–5 s with small GPU |
| **Structured output** | Native (Gemini) / documented (Groq) / per-provider (OpenRouter) | Grammar-constrained, reliable (Ollama `format`, GBNF) |
| **Availability** | Network + provider outage + rate limits can fail a call | Works offline; deterministic |
| **Deprecation churn** | High: model generations and free rosters churn | Model files pinned locally; no server-side breaking changes |
| **Training on learner data** | Gemini free: yes; Groq: per Services Agreement (verify); OpenRouter: per-provider (verify) | Never |

  advisory prose, Q4 at 3–4B is typically indistinguishable; at 8B, Q4
  remains the standard consumer choice. (Planning figure; benchmark with
  real prompts.)
- **CPU throughput:** modern desktop CPUs with AVX2 typically deliver
  ~5–20 tokens/s for 3–4B Q4 models and ~3–10 tokens/s for 7–8B Q4; Apple
  Silicon (Metal) and small GPUs are several times faster. A 200-token
  advisory generation therefore lands in the **~10–60 s range on CPU-only**,
  seconds on GPU. Treat these as order-of-magnitude planning figures —
  benchmark on actual hardware; llama.cpp publishes a
  performance-troubleshooting guide
  ([llama.cpp README/docs](https://github.com/ggml-org/llama.cpp)).
- **Privacy:** fully offline; nothing leaves the machine by construction
  (local HTTP only). The only option with an unqualified privacy guarantee.


### Cloud summary table

| Provider | Free tier? | Fit for few calls/day | Free-tier data used for training? | Structured output | Risk |
|---|---|---|---|---|---|
| Gemini API | Yes | Yes (per-model RPM/RPD) | **Yes** (paid tier: no) | Native | Free tier trains on content |
| Groq | Yes | 250–1,000 RPD | Not per privacy policy; governed by Services Agreement/DPA — verify | Yes (documented) | Model roster churn |
| OpenRouter `:free` | Yes | Yes, tiered daily cap | Per-provider, varies; routing rotates providers | OpenAI-compat | Least deterministic privacy |
| Cerebras | No (one-time $5 trial credit) | — | — | OpenAI-compat | Not a standing free option |
| GitHub Models | **Retired 2026-07-30** | — | — | — | Do not use |
| Mistral | No free API tier on current pricing page; $10/mo credits on entry plan | — | Opt-out is a plan feature | OpenAI-compat | Verify experiment tier |

  a single-vendor API. Per-provider training/data-policy flags must be
  pinned at implementation time (OpenRouter exposes per-provider data-policy
  selectors in its API surface)
  ([limits](https://openrouter.ai/docs/api-reference/limits)).
- 429 handling, `X-RateLimit-*` headers, and fallback-model routing are
  documented ([limits](https://openrouter.ai/docs/api-reference/limits)).

**Fit notes:** broad model choice at $0, but the weakest data-use
determinism of the cloud options; acceptable if the prompt contains no
sensitive content.

