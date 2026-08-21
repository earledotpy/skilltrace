# Runbook

Operational reference for daily SkillTrace use. All commands assume the
virtual environment is activated and you are in the repo root.

## Daily study loop

```bash
# 1. See what's due today
skilltrace today

# 2. Get session-sized recommendations
skilltrace next --minutes 60

# 3. Start studying a node
skilltrace start <node_id>

# 4. Record work as you go
skilltrace work <node_id> --minutes 25 --notes "Worked through examples"

# 5. Submit evidence when ready
skilltrace evidence submit <node_id> --location artifacts/<file> --accept

# 6. Check pass eligibility
skilltrace eligibility <node_id>

# 7. Pass the node (explicit learner command)
skilltrace pass <node_id>

# 8. Close the session when done
skilltrace close
```

## Node detail and resources

```bash
# View a node's full detail (curriculum + progress + evidence + resources)
skilltrace node <node_id>

# List resources supporting a node
skilltrace resources --node-id <node_id>
```

## Validation

```bash
skilltrace validate graph        # nodes, edges, cycles
skilltrace validate evidence     # specs, gates, records, attempts
skilltrace validate execution    # sessions, work, blockers, reviews
skilltrace validate policy       # boundary agreement, structural shape
skilltrace validate resources    # slug IDs, URL-or-path, node links
```

## Health check

```bash
# Roll up all five validate targets plus liveness warnings
skilltrace health
```

## Reports

```bash
skilltrace report progress       # curriculum progress and track completion
skilltrace report blockers       # obstacles, open remediation, rescue nodes
skilltrace report reviews        # retention checks, overdue reviews, mastery candidates
skilltrace report evidence       # proof trail audit, gates, supersession chains
skilltrace report resources      # resource verification status
```

## Blockers and reviews

```bash
# Create a blocker when stuck
skilltrace blocker create <node_id> --description "Can't understand X"

# Resolve a blocker
skilltrace blocker resolve blk.<node>.NNN --summary "Clarified via Y"

# List open blockers
skilltrace blockers

# Schedule a retention review
skilltrace review schedule <node_id> --date 2026-09-01

# Complete a review
skilltrace review complete rev.<node>.NNN --outcome satisfactory --summary "Retained"

# Cancel a review
skilltrace review cancel rev.<node>.NNN --reason "No longer relevant"

# List scheduled reviews
skilltrace reviews
```

## Remediation

```bash
# Log a corrective intervention
skilltrace remediation create <node_id> --description "Re-read chapter 3"

# Complete a remediation
skilltrace remediation complete rem.<node>.NNN --summary "Covered the gap"

# Get advisory suggestions
skilltrace suggest remediation
skilltrace suggest reviews
```

## Assessment attempts

```bash
# Record a pass/fail attempt (immutable fact)
skilltrace attempt record <node_id> --outcome passed
skilltrace attempt record <node_id> --outcome failed --note "Misread question"
```

## Mastery

```bash
# Check mastery eligibility (requires passed + accepted evidence + spaced satisfactory review)
skilltrace eligibility <node_id> --mastery

# Assert mastery (explicit learner command)
skilltrace master <node_id>
```

## Data export and backup

```bash
# Markdown snapshot (overwrites data/export.md each time)
skilltrace export markdown

# SQLite mirror (rebuilt each run at data/skilltrace.db)
skilltrace export sqlite

# Timestamped zip backup into backups/
skilltrace backup
```

## Automation boundary checks

```bash
skilltrace check-automation pass_node     # forbidden
skilltrace check-automation master_node   # forbidden
skilltrace check-automation delete_record # forbidden
```

## Sync

```bash
# Recompute derived readiness (locked/available) for every node
skilltrace sync
```

## Aliases

Two top-level aliases are available for the most-typed commands:

| Alias | Canonical command |
|-------|-------------------|
| `st`  | `skilltrace` (same entry point) |
| `submit` | `evidence submit` |
| `close` | `session close` |

The audit log records the canonical command name, not the alias.
