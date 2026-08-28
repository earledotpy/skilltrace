# SkillTrace Runbook

Operational reference and command cheatsheet for SkillTrace. All commands assume the virtual environment is activated and you are in the repository root.

---

## 1. Daily Study Loop

```bash
# 1. Inspect morning agenda (open session, due reviews, active blockers, top recommendation)
st today

# 2. Get recommendations sized to your available time (e.g. 45 or 60 minutes)
st next --minutes 60
st next --minutes 45 --limit 3 --show-locked

# 3. Open a study session on a target skill node
st start <node_id>

# 4. Record work items and notes as you make progress
st work <node_id> --minutes 25 --notes "Read documentation and worked through exercises"

# 5. Submit proof of work against the node's evidence gate
st evidence submit <node_id> --location artifacts/<filename>
# For manual gates (self-assessed):
st submit <node_id> --location artifacts/<filename> --accept

# 6. Check pass eligibility (verifies all required gate constraints)
st eligibility <node_id>

# 7. Explicitly pass the node (learner-initiated command)
st pass <node_id>

# 8. Close the active session when done
st close
```

---

## 2. Web UI & Localhost Server

SkillTrace provides a built-in, zero-dependency localhost web server for visual study sessions:

```bash
# Launch localhost web server and auto-open browser (default: port 8341)
st ui
# Or canonical command:
skilltrace serve

# Custom port or headless (no auto-open) options:
skilltrace serve --port 9000 --no-browser
```

---

## 3. Node Detail & Learning Resources

```bash
# Inspect complete node detail (curriculum brief, prerequisite edges, resources, eligibility)
st node <node_id>

# Reverse index: list all resources that support a given node
st resources --node-id <node_id>

# Verify an external resource link or mark as broken
st verify-resource res.<provider>.<slug>
st verify-resource res.<provider>.<slug> --broken --note "URL 404s"

# Whole-registry resource verification report
st resource-report
```

---

## 4. Retention & FSRS Spaced Reviews

SkillTrace implements the FSRS (Free Spaced Repetition Scheduler) model for memory retention:

```bash
# Check memory stability, retention confidence, and overall retention health
st retention status

# List scheduled, due, and overdue spaced retention reviews
st reviews

# Schedule an ad-hoc retention review
st review schedule <node_id> --date 2026-09-15

# Record review outcome (satisfactory or unsatisfactory)
st review complete rev.<node>.<seq> --outcome satisfactory --summary "Passed recall quiz"
st review complete rev.<node>.<seq> --outcome unsatisfactory --summary "Needed refresher on proofs"

# Cancel a scheduled review
st review cancel rev.<node>.<seq> --reason "Superseded by capstone project"

# Get advisory suggestions for decaying retention candidates
st suggest reviews
```

---

## 5. Blockers & Remediation Workflow

```bash
# Create an obstacle record when blocked on a skill
st blocker create <node_id> --description "Unclear on loss function backpropagation"

# Resolve a blocker once cleared
st blocker resolve blk.<node>.<seq> --summary "Worked through micrograd tutorial"

# List active blockers
st blockers

# Log an ad-hoc remediation action
st remediation create <node_id> --description "Re-read linear algebra chapter 2"
st remediation complete rem.<node>.<seq> --summary "Completed matrix transformations review"

# Get remediation rescue node suggestions
st suggest remediation
```

---

## 6. Assessment Attempts & Permanent Mastery

```bash
# Record an immutable pass/fail assessment attempt
st attempt record <node_id> --outcome passed
st attempt record <node_id> --outcome failed --note "Missed edge case handling"

# Check mastery eligibility (requires passed status + valid evidence + spaced satisfactory review)
st eligibility <node_id> --mastery

# Assert permanent mastery
st master <node_id>
```

---

## 7. Reports

```bash
st report progress       # Curriculum progress and track completion breakdown
st report blockers       # Active blockers, remediation pressure, and rescue targets
st report reviews        # Retention review queue, overdue items, mastery candidates
st report evidence       # Proof trail audit, validation gates, supersession chains
st report resources      # External resource verification and staleness audit
```

---

## 8. Layer Validation & Engine Diagnostics

```bash
# Holistic health verdict rolling up all 5 layer validators + liveness warnings
st health

# Per-layer validator subcommands
st validate graph        # Node IDs, frontmatter, edges, and cycle detection
st validate evidence     # Specs, gates, records, attempts, and supersession chains
st validate execution    # Sessions, work items, blockers, reviews, and event log
st validate policy       # Hard boundary checks and advisory parameter schemas
st validate resources    # Resource registry IDs, URLs, and node links
```

---

## 9. Data Exports, Sync & Backups

```bash
# Recompute derived readiness (locked/available) for all nodes
st sync

# Generate disposable derived exports
st export html           # Self-contained HTML dashboard snapshot (data/export.html)
st export markdown       # Consolidated single-file Markdown export (data/export.md)
st export sqlite         # SQLite database mirror for SQL queries (data/skilltrace.db)

# Create a timestamped backup archive in backups/
st backup
```

---

## 10. Automation Boundary Verification

Verify that the engine's hard safety boundaries are strictly enforced:

```bash
st check-automation pass_node     # Must refuse (forbidden automation)
st check-automation master_node   # Must refuse (forbidden automation)
st check-automation delete_record # Must refuse (forbidden automation)
```

---

## 11. Command Aliases

| Alias | Canonical Subcommand | Notes |
| :--- | :--- | :--- |
| `st` | `skilltrace` | Primary entrypoint alias |
| `st ui` | `skilltrace serve` | Localhost web dashboard server |
| `st submit` | `skilltrace evidence submit` | Evidence submission shortcut |
| `st close` | `skilltrace session close` | Session close shortcut |
| `st blockers` | `skilltrace report blockers` | Quick blockers list |
| `st reviews` | `skilltrace report reviews` | Quick reviews list |
