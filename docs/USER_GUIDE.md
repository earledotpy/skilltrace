# User Guide

SkillTrace is a local-first study tool that answers "What should I study
next?" and tracks your progress through a skill graph. Everything runs
locally on your machine -- no cloud, no account, no network required after
install.

## Getting started

See [INSTALL.md](INSTALL.md) for installation. Once installed, run:

```bash
skilltrace health
```

This confirms everything is working. On first use, the seed graph is ready
with 81 nodes across math, programming, data, and tooling skills.

## Your daily study loop

### 1. See what's due

```bash
skilltrace today
```

Shows your open session (if any), due reviews, active blockers, and the top
recommendation for right now.

### 2. Get recommendations

```bash
skilltrace next --minutes 60
```

Lists nodes sized to your available time, ranked by learning impact. Each
recommendation explains why it was chosen and what passing it unlocks.

### 3. Start studying

```bash
skilltrace start <node_id>
```

Opens a session and marks the node as active. You can only have one open
session at a time.

### 4. Record your work

```bash
skilltrace work <node_id> --minutes 25 --notes "Worked through practice problems"
```

Add work items as you go. You can work on multiple nodes in one session.

### 5. Submit evidence

When your work is ready, submit it as evidence:

```bash
# For objective gates (auto-checked):
skilltrace evidence submit <node_id> --location artifacts/my-solution.py

# For manual gates (self-assessed):
skilltrace evidence submit <node_id> --location artifacts/essay.md --accept
```

### 6. Check if you can pass

```bash
skilltrace eligibility <node_id>
```

Shows whether you meet all requirements to pass, with per-spec counts.

### 7. Pass the node

```bash
skilltrace pass <node_id>
```

This is your explicit decision. No automated process can do this for you.

### 8. Close the session

```bash
skilltrace close
```

## Exploring the graph

```bash
# View a node's full detail (curriculum, progress, evidence, resources)
skilltrace node <node_id>

# See what resources support a node
skilltrace resources --node-id <node_id>
```

## Reports

```bash
skilltrace report progress       # Your progress across all tracks
skilltrace report blockers       # What's blocking you
skilltrace report reviews        # Due and overdue retention checks
skilltrace report evidence       # Your proof trail
skilltrace report resources      # Resource verification status
```

## Blockers and reviews

If you're stuck on a node:

```bash
skilltrace blocker create <node_id> --description "Can't understand X"
```

When resolved:

```bash
skilltrace blocker resolve blk.<node>.NNN --summary "Found a good explanation"
```

Retention reviews are scheduled automatically when you pass a node. Check
them with:

```bash
skilltrace reviews
```

## Data management

```bash
skilltrace export markdown   # Human-readable snapshot
skilltrace export sqlite     # SQLite mirror for querying
skilltrace export html       # Self-contained HTML snapshot (data/export.html)
skilltrace backup            # Timestamped zip of all data
```

Exports and backups are in the `data/` and `backups/` directories, which are
gitignored. They are disposable -- the source files are always the truth.

## Troubleshooting

**"No session open"** -- run `skilltrace start <node_id>` to begin.

**"Node is locked"** -- check `skilltrace next` to see what prerequisites
you need to pass first.

**"Not eligible to pass"** -- run `skilltrace eligibility <node_id>` to see
what's missing.

**Health shows warnings** -- run `skilltrace health` for details. Warnings
don't block use but indicate something to address.
