# SkillTrace User Guide

SkillTrace is your local-first study cockpit. It models your technical learning journey as a dependency graph, enforces real evidence gates before skills are checked off, and keeps track of your retention over months of practice.

No accounts, no cloud dependencies, and no magic checkboxes. Everything is driven by plain Markdown and YAML files in this repository.

---

## 1. Quickstart & Daily Rhythm

Once you have followed [INSTALL.md](INSTALL.md) and activated your virtual environment, the CLI is available as `skilltrace` or the shortcut `st`.

### The Daily CLI Workflow

Here is what a typical study session looks like:

```bash
# 1. Check your morning board (due reviews, open blockers, top recommendation)
st today

# 2. Get recommendations tailored to your available time
st next --minutes 60

# 3. Pick a skill and open your study session
st start math.linear_algebra.vectors_01

# 4. As you work through books, code, or exercises, log your time and notes
st work math.linear_algebra.vectors_01 --minutes 30 --notes "Completed practice exercises 1-15"

# 5. Submit your proof artifact against the node's evidence gate
# For objective code gates (checked by exit code / test):
st evidence submit math.linear_algebra.vectors_01 --location artifacts/vector_math.py

# For manual essay/notes gates (self-evaluated):
st submit math.linear_algebra.vectors_01 --location artifacts/notes.md --accept

# 6. Verify pass readiness
st eligibility math.linear_algebra.vectors_01

# 7. Explicitly pass the node (the engine never auto-passes for you!)
st pass math.linear_algebra.vectors_01

# 8. Close the session when you wrap up
st close
```

---

## 2. Using the Local Web Dashboard (`st ui`)

If you prefer a visual interface alongside your code editor or terminal, SkillTrace includes a built-in, stdlib-pure localhost web server:

```bash
st ui
# or explicitly:
skilltrace serve --port 8341
```

This launches your default browser at `http://127.0.0.1:8341` with a zero-JavaScript, server-rendered dashboard:

* **Today Dashboard (`/`):** View your active session strip, due retention reviews, active blockers, and top recommendations at a glance.
* **Recommendations (`/next`):** Interactive view of prerequisite-ready nodes with filters for study time and locked skills.
* **Node Detail (`/nodes/<id>`):** Full breakdown of curriculum descriptions, prerequisite links, learning resources, and evidence requirements.
* **Safe State Mutations:** Start sessions, submit work notes, and trigger explicit `pass` / `master` confirmation modals directly from your browser. Every browser write dispatches through the exact same safety engine as the CLI.

---

## 3. Evidence, Eligibility & Passing

SkillTrace treats progress as **provable claims**, not subjective checkboxes:

* **Artifacts & Gates:** Each skill node defines an `ArtifactSpec` (what you must produce) and a `ValidationGate` (how it is evaluated).
* **Objective Gates:** Checked automatically by running a command (like a unit test suite or verification script).
* **Manual Gates:** Reviewed and accepted explicitly by you (`--accept`).
* **Immutability:** Once evidence is recorded, it is never edited or deleted. If you fix an error, you submit a new record that supersedes the prior one.
* **Pass Enforcement:** `st pass <node_id>` will refuse to execute unless all required evidence gates are satisfied.

---

## 4. Retention & Spaced Review (FSRS Analytics)

Passing a skill is just the start; retaining it over months requires spaced recall. SkillTrace includes a built-in **FSRS (Free Spaced Repetition Scheduler)** retention model:

```bash
# Inspect your overall retention health and memory stability
st retention status

# See what retention reviews are due today
st reviews

# Log a review outcome (satisfactory or unsatisfactory)
st review complete rev.math.linear_algebra.vectors_01.001 --outcome satisfactory --summary "Solved recall quiz"

# Get advisory suggestions for skills whose retention confidence has decayed
st suggest reviews
```

When you pass a node, the engine automatically schedules initial retention reviews based on policy cadence. Overdue reviews generate advisory warnings on `st today` and `st next`, helping you prioritize recall before charging into advanced topics.

---

## 5. Handling Obstacles & Remediation

When you get stuck on a tricky concept:

```bash
# 1. Log a blocker describing the obstacle
st blocker create math.calculus.derivatives_01 --description "Struggling with the chain rule on composite functions"

# 2. Ask the engine for remediation suggestions (rescue nodes)
st suggest remediation

# 3. Once you overcome the hurdle, resolve the blocker
st blocker resolve blk.math.calculus.derivatives_01.001 --summary "Reviewed 3Blue1Brown visual calculus chapter 4"
```

Logging blockers applies **remediation pressure**, dynamically prioritizing foundational rescue nodes in your daily recommendations until the obstacle is cleared.

---

## 6. Reports & Analytics

Keep an eye on the big picture across your entire curriculum:

```bash
# High-level curriculum progress across all tracks
st report progress

# Active blockers, remediation actions, and rescue targets
st report blockers

# Spaced review queue, overdue reviews, and mastery candidates
st report reviews

# Full evidence audit trail and gate completion status
st report evidence

# Verification status of all external learning resources
st report resources
```

---

## 7. Data Exports, Backups & Portability

Your Markdown curriculum files and `graph/state.yaml` are the sole sources of truth. For external sharing, querying, or peace of mind, SkillTrace can generate disposable derived views:

```bash
# Generate a self-contained HTML review snapshot (written to data/export.html)
st export html

# Generate a single Markdown summary (written to data/export.md)
st export markdown

# Rebuild the SQLite mirror for SQL queries (written to data/skilltrace.db)
st export sqlite

# Create a timestamped, portable zip archive of all source files
st backup
```

Exports in `data/` and archives in `backups/` are gitignored and completely disposable—the engine never reads them back to compute state.

---

## 8. Common Troubleshooting

* **"No session open"**: Run `st start <node_id>` to open a study session.
* **"Node is locked"**: The skill has unsatisfied `hard_prerequisite` dependencies. Run `st node <node_id>` to see which prerequisites need to be passed first.
* **"Not eligible to pass"**: Run `st eligibility <node_id>` to see which evidence specs or gates are still missing.
* **`st health` reports warnings**: Review the output. Advisory warnings (e.g. overdue reviews or stale resources) do not block study actions, but highlight areas that need attention.
