# SkillTrace

> **A local-first, CLI-first, single-learner learning engine: skill graphs with evidence-gated progression.**

SkillTrace is built for developers tackling deep, multi-year technical curricula (like AI engineering, systems, or math foundations) who want real progress tracking without the bloat of traditional LMS platforms.

Everything lives locally on disk in plain Markdown and YAML files. No cloud sync, no accounts, no telemetry, and no magical auto-grading. The engine answers four core questions every day:
1. **What should I study next?** (`st next`)
2. **Why that specific node?** (prerequisite chains + policy weights)
3. **What concrete evidence proves I know this?** (`st evidence submit`)
4. **Is my retention holding up over time?** (`st retention status`)

Designed for disciplined solo study and pairs cleanly with agentic AI coding assistants—where AI provides research, feedback, and advisory reviews, but **you** hold the final acceptance authority.

---

## Quickstart

### Prerequisites
- Python ≥ 3.14
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/earledotpy/skilltrace.git
cd skilltrace

# Set up and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install in editable mode (pure stdlib + PyYAML)
pip install -e .
```

Installation gives you the `skilltrace` CLI and its handy alias `st`.

### Verify & Launch

```bash
# 1. Run engine health checks across all five layers
st health

# 2. Check your daily dashboard in the terminal
st today

# 3. Spin up the local browser dashboard
st ui   # or: skilltrace serve
```

---

## The Daily Study Loop

SkillTrace models learning as an active, evidence-backed workflow:

```text
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │   st today   │ ───► │   st next    │ ───► │   st start   │
 │ (due/reviews)│      │(recs & time) │      │ (open session)│
 └──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
 ┌──────────────┐      ┌──────────────┐      ┌──────▼───────┐
 │   st pass    │ ◄─── │st eligibility│ ◄─── │   st work    │
 │(manual assert│      │ (gate checks)│      │(log progress)│
 └──────┬───────┘      └──────────────┘      └──────┬───────┘
        │                                           │
 ┌──────▼───────┐                            ┌──────▼───────┐
 │  st master   │ ◄── (spaced retention) ──  │st submit ev. │
 │  (permanent) │                            │(code/artifact)│
 └──────────────┘                            └──────────────┘
```

1. **Check your agenda:** `st today` shows active blockers, due retention reviews, and top picks.
2. **Get recommendations:** `st next --minutes 60` ranks prerequisite-safe nodes sized for your study window.
3. **Start studying:** `st start <node_id>` marks the skill active and opens your work session.
4. **Log your work:** `st work <node_id> --minutes 25 --notes "Solved exercise problems"` tracks time against skills.
5. **Submit evidence:** `st evidence submit <node_id> --location artifacts/solution.py` links your code or notes to the gate.
6. **Check pass readiness:** `st eligibility <node_id>` validates all evidence requirements.
7. **Pass the node:** `st pass <node_id>` asserts completion. *(This is an explicit human command; the engine never auto-passes.)*
8. **Wrap up:** `st close` ends your session.

---

## Core Command Surface

| Category | Command | Description |
| :--- | :--- | :--- |
| **Daily Routine** | `st today` | Morning brief: open session, due reviews, active blockers, top pick. |
| | `st next [--minutes M] [--limit N]` | Prerequisite-aware recommendations with Mentor explanations. |
| | `st node <node_id>` | Detailed inspection of curriculum, evidence gates, and resources for a node. |
| **Study Sessions** | `st start <node_id>` | Open a study session on a target skill node. |
| | `st work <node_id> --minutes M` | Append timestamped work notes to the current session. |
| | `st close` / `st session close` | Close the active session cleanly. |
| **Evidence & Gates** | `st evidence submit <id> --location <path>` | Submit an artifact against a node's validation gate. |
| | `st attempt record <id> --outcome <p/f>` | Record an immutable assessment outcome. |
| | `st eligibility <id> [--mastery]` | Inspect exact pass or mastery eligibility facts on demand. |
| | `st pass <node_id>` | Explicit learner assertion: mark a skill as passed. |
| | `st master <node_id>` | Permanent mastery assertion (requires spaced satisfactory reviews). |
| **Retention & Reviews** | `st retention status` | FSRS-based retention analytics, stability, and recall confidence. |
| | `st reviews` | List scheduled, due, and overdue spaced retention checks. |
| | `st review complete <rev_id> --outcome <o>` | Log review results (`satisfactory` or `unsatisfactory`). |
| | `st suggest reviews` | Get advisory review candidates based on retention decay. |
| **Blockers & Fixes** | `st blocker create <id> --description "..."` | Log an obstacle (applies advisory remediation pressure). |
| | `st blocker resolve <blk_id> --summary "..."` | Clear a blocker once resolved. |
| | `st suggest remediation` | List recommended rescue nodes for active blockers. |
| **Web UI & Reports** | `st ui` / `skilltrace serve` | Launch localhost browser dashboard (port 8341). |
| | `st report progress` | Track completion breakdown across all curriculum tracks. |
| | `st report [blockers\|reviews\|evidence]` | Audit reports for obstacles, retention queues, and evidence chains. |
| **Data & Diagnostics** | `st health` | Holistic engine diagnostic rolling up all layer validators. |
| | `st sync` | Recompute derived readiness (`locked` / `available`). |
| | `st export [html\|markdown\|sqlite]` | Generate disposable, derived views (`data/export.html`, etc.). |
| | `st backup` | Create a timestamped, portable zip archive in `backups/`. |

---

## Non-Negotiable Architectural Rules

SkillTrace is engineered with strict guardrails to keep data trustworthy over years of use:

- **No automated pass or mastery:** Passing and mastering are explicit learner commands. AI, scripts, and tests can advise, but they never flip progress states.
- **AI is never an acceptance authority:** AI feedback is strictly advisory commentary attached to evidence. Acceptance requires objective gate checks or learner sign-off.
- **Asserted progress never demotes:** Once a skill is marked `active`, `passed`, or `mastered`, engine syncs and policy recalculations will never move it backward.
- **Files are the single source of truth:** All truth lives in `graph/`, `evidence/`, `execution/`, and `policy/`. Exports (SQLite, HTML, Markdown) are disposable and never read back into the engine.
- **Immutable evidence trail:** Evidence records are never edited or deleted in place. Corrections use an explicit `supersedes` chain with documented rationale.
- **Single learner by design:** One repo is one learner's environment. To share a curriculum with another learner, fork the repo without the `graph/state.yaml` progress store.

---

## Repository Layout

```text
skilltrace/
├── graph/                  # Skill nodes (curriculum markdown), edges.yaml, resources.yaml, state.yaml
├── evidence/               # Artifact specs, validation gates, assessment attempts, evidence records
├── execution/              # Work sessions, blockers, remediation actions, reviews, audit event log
├── policy/                 # Hard safety boundaries and advisory policy parameters (YAML)
├── release/                # Release manifests, test results, and release criteria
├── src/skilltrace/         # Installable Python package (CLI commands, web server, domain models)
│   ├── commands/           # CLI subcommand implementations
│   ├── graph/              # Graph loader, cycle detection, state machine, recommendation engine
│   ├── evidence/           # Gate validation, eligibility evaluators, passing logic
│   ├── execution/          # Session management, blocker workflows, audit logger
│   ├── policy/             # Advisory weights, FSRS retention model, cadence policies
│   ├── web/                # Stdlib-pure localhost web server & UI dashboard
│   └── render.py           # Clean, stdlib terminal rendering
├── tests/                  # Per-layer pytest test suite (1,200+ unit & integration tests)
└── docs/                   # User guide, runbook, schemas, architecture records (ADRs), post-v1 roadmap
```

---

## Documentation Index

- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — Comprehensive user manual with everyday study workflows and Web UI tips.
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — Fast operational reference and CLI command cheatsheet.
- [`docs/INSTALL.md`](docs/INSTALL.md) — Installation, environment setup, and troubleshooting guide.
- [`docs/POST_V1_ROADMAP.md`](docs/POST_V1_ROADMAP.md) — Post-v1 release slot sequence (`v1.6` through `v2.1`) and learner-value ROI rubric.
- [`docs/SAFETY_BOUNDARIES.md`](docs/SAFETY_BOUNDARIES.md) — Deep dive into engine invariants and safety guardrails.
- [`docs/SCHEMA_REFERENCE.md`](docs/SCHEMA_REFERENCE.md) — Frozen schema reference for node frontmatter, edges, and state.
- [`CONTEXT.md`](CONTEXT.md) — Ubiquitous domain language and terminology glossary.
- [`docs/adr/`](docs/adr/) — Architectural Decision Records explaining key structural choices.

---

## License

Built for focused, disciplined, and lifelong learning. Distributed under the MIT License.
