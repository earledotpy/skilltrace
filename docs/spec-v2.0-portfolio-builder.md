# Spec — v2.0 Portfolio Builder

**Status:** locked hand-off (map #174) — no open product or architecture
decisions block the v2.0 build. All wayfinder tickets on map #174 are
closed; testing and exit-gate sections are filled from T-TestArch #180 and
T-Exit #181.
**Target:** v2.0, the portfolio builder and report release, shipping after
v1.7 (Tier 2 LearningResource verification).
**Map:** [#174 Map — v2.0 Portfolio builder + GitHub project report](https://github.com/earledotpy/skilltrace/issues/174)
**Decisions:** [G-Selection #175](https://github.com/earledotpy/skilltrace/issues/175) · [G-Redaction #176](https://github.com/earledotpy/skilltrace/issues/176) · [G-Bundle #177](https://github.com/earledotpy/skilltrace/issues/177) · [G-Formats #178](https://github.com/earledotpy/skilltrace/issues/178) · [G-CLI #179](https://github.com/earledotpy/skilltrace/issues/179) · [T-TestArch #180](https://github.com/earledotpy/skilltrace/issues/180) · [T-Exit #181](https://github.com/earledotpy/skilltrace/issues/181).
**Standing rule:** all terms per `CONTEXT.md`; safety rules in `AGENTS.md`
are unchanged and binding — this spec never relaxes them.

> Hand-off gate (from map `Destination`): a builder can implement v2.0
> without reopening a product or architecture question. This doc is the
> locked hand-off once T-TestArch and T-Exit closed and their sections
> were filled.

---

## 0. Scope and what is explicitly out of scope

In scope for v2.0:

- A new `src/skilltrace/portfolio/` package: `selection.py`, `redaction.py`,
  `bundle.py`, `export.py`, `models.py`.
- A new `src/skilltrace/commands/portfolio.py` module registering the
  portfolio CLI family.
- Three export formats: **Markdown** (README-ready, plain-text readable),
  **HTML** (self-contained, one inline `<style>`, zero JavaScript), **JSON**
  (stable published contract).
- A disposable **portfolio bundle** written to `data/portfolio-<date>/` with
  rewritten relative links and an honesty banner for supersession and
  staleness.
- A new `policy/portfolio.yaml` seed document and its entry in the
  `validate policy` umbrella.
- Glossary additions to `CONTEXT.md` for new terms introduced by this spec
  (see §8).

Explicitly **out of scope** (per map `Out of scope`):

- Web/Serve surface for portfolio (v2.0 is CLI-first per roadmap).
- Automated `pass_node`, `master_node`, or `delete_record` (hard boundary —
  never).
- AI review as acceptance authority (hard boundary — never).
- Asserted progress moving backward (hard boundary — never).
- Network-dependent features (offline-first per ADR 0006).

---

## 1. Data sources and schema adequacy

The portfolio builder derives from the engine's existing truth files. No
schema changes are needed.

| Source | Role |
|--------|------|
| `graph/nodes/*.md` | Node metadata (track, title, state, artifact specs, resources) |
| `graph/state.yaml` | Asserted progress (locked/available/active/passed/mastered) |
| `graph/edges.yaml` | Prerequisite and unlock relationships |
| `evidence/*.yaml` | Evidence records (accepted, superseded, rejected chains) |
| `execution/sessions.yaml` | Session timestamps (for rolling windows) |
| `execution/session_work.yaml` | Work items (node touch, minutes) |
| `execution/blockers.yaml` | Open and resolved blockers |
| `execution/reviews.yaml` | Scheduled, completed, cancelled reviews |
| `execution/resources.yaml` | LearningResource registry (URLs, verification status) |

The portfolio builder **never reads `execution/events.yaml`**: events are
audit-only per the engine invariant.

---

## 2. Portfolio selection flags and defaults (G-Selection)

Per [G-Selection — Lock portfolio selection flags and defaults #175](https://github.com/earledotpy/skilltrace/issues/175):

### 2.1 Default selection

The default export selects:
- Nodes in state `passed` or `mastered` on the **portfolio** track only.
- Evidence records that are accepted, non-superseded (live-head), and tied
  to those selected nodes.

No persisted selection file exists. Every export derives from live truth at
generation time (per `Export` in `CONTEXT.md`).

### 2.2 Flag set and semantics

All selection flags are per-invocation only. AND/OR semantics: flags within
a dimension are ORed; dimensions are ANDed.

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `--node <ID>` | repeatable | none | Restrict to named node(s) |
| `--track <NAME>` | single | `portfolio` | Restrict to track (AND with `--node`) |
| `--include-active` | boolean | false | Add `active` nodes to selection |
| `--include-rejected` | boolean | false | Add superseded/rejected evidence (with redaction banner) |
| `--include-superseded` | boolean | false | Add superseded evidence (with redaction banner) |

When `--node` is supplied without `--track`, the track filter is omitted
(no implicit track restriction).

### 2.3 Consolidation/remediation tracks

Consolidation and remediation tracks are treated like any other track:
included only if explicitly selected via `--track` or if a node on that
track is named via `--node`. They do not appear in the portfolio-track-only
default.

### 2.4 Supersession-mismatch

When a node is `passed` or `mastered` but its evidence has later been
superseded, the portfolio surfaces an **honesty banner** (see §4) rather
than silently omitting the superseded record or failing.

---

## 3. Redaction enforcement and include overrides (G-Redaction)

Per [G-Redaction — Enforce share-profile allowlists and include overrides #176](https://github.com/earledotpy/skilltrace/issues/176):

### 3.1 Default-deny share profile

The default share profile is **deny-all**: no paths, notes, blocker text,
review text, free text, or URLs appear in outbound surfaces unless an
explicit `--include-*` override flag is passed. This is the locked privacy
contract from issue #150.

### 3.2 Redaction module

A single `src/skilltrace/portfolio/redaction.py` module enforces redaction
for all formats. Every outbound surface (Markdown, HTML, JSON, bundle file
list) passes through this module. No format may bypass it.

### 3.3 What is redacted by default

| Surface | Redacted fields |
|---------|-----------------|
| Markdown/HTML report | Local artifact paths, learner notes, blocker descriptions, review notes, free-text fields, URLs |
| JSON contract | Same fields stripped or replaced with `[redacted]` |
| Bundle file list | Paths rewritten to bundle-relative; no absolute host paths |

Artifact bytes the learner explicitly selected for inclusion are **not**
touched; redaction strips paths, notes, blocker and review text from the
surrounding report only.

### 3.4 Override flags

| Flag | Effect |
|------|--------|
| `--include-paths` | Retain local artifact paths |
| `--include-notes` | Retain learner notes |
| `--include-blockers` | Retain blocker descriptions |
| `--include-reviews` | Retain review notes |
| `--include-free-text` | Retain free-text fields |
| `--include-urls` | Retain URLs |

Each flag is independent. A single flag overrides redaction for its
dimension only; the rest remain denied.

### 3.5 Backup local-only

The backup (if any) is local-only and never included in the export bundle.

---

## 4. Bundle layout, link rewriting, and honesty banner (G-Bundle)

Per [G-Bundle — Lock bundle layout, link rewriting, and honesty banner #177](https://github.com/earledotpy/skilltrace/issues/177):

### 4.1 Bundle layout

The bundle is written to `data/portfolio-<date>/` where `<date>` is the
generation date (UTC, ISO 8601).

```
data/portfolio-<date>/
    portfolio.md          # Markdown index (always present)
    portfolio.html        # Self-contained HTML preview
    portfolio.json        # JSON contract
    artifacts/            # Flat directory of accepted artifact files
        <artifact-filename-1>
        <artifact-filename-2>
        ...
    nodes/                # Per-node detail pages (Markdown)
        <node-id-1>.md
        <node-id-2>.md
        ...
    portfolio.json        # Manifest (node → artifact mapping, selection metadata)
```

The bundle is **disposable**: regenerated whole on each export, gitignored,
and never read back by the engine.

### 4.2 Link rewriting

Links from local `location` paths in artifact metadata are rewritten to
bundle-relative paths (e.g., `artifacts/<filename>`). External URLs remain
as-is unless redacted by `--include-urls` being absent.

### 4.3 Honesty banner triggers

The bundle carries an honesty banner when any of the following are true:

1. **Superseded evidence** — a node's accepted evidence has been superseded
   by a later record.
2. **Stale resources** — a linked LearningResource's `last_verified` date
   exceeds the policy staleness window.
3. **Unverified claims** — an artifact's verification gate has never been
   run or was last run before a policy-configured window.

The banner is **informational only**: it never blocks export, never alters
node state, and never changes eligibility. Its wording is:

```
[honesty] This portfolio contains [superseded evidence / stale resources /
unverified claims]. Review before sharing.
```

The specific trigger is named in the banner text.

---

## 5. Export format shapes and v2.1 contract (G-Formats)

Per [G-Formats — Lock Markdown, HTML, and JSON shapes and the v2.1 contract #178](https://github.com/earledotpy/skilltrace/issues/178):

### 5.1 Markdown

- Compact per-project sections with tables.
- Honesty banner at the top when triggered.
- Advisory/redaction banners as needed.
- Readable as plain text.
- No images or external references.

### 5.2 HTML

- **Self-contained**: one inline `<style>`, zero JavaScript.
- Tables + advisory banners.
- Opens in any browser with no network access required.
- Preview-only elements are marked as such.

### 5.3 JSON

Stable published contract — not a 1:1 mirror of `portfolio.py` internals.
Top-level structure:

```json
{
  "generated_at": "<ISO datetime>",
  "selection": {
    "track": "portfolio",
    "include_active": false,
    "include_rejected": false,
    "include_superseded": false,
    "nodes": [],
    "include_paths": false,
    "include_notes": false,
    "include_blockers": false,
    "include_reviews": false,
    "include_free_text": false,
    "include_urls": false
  },
  "honesty_banners": ["..."],
  "nodes": [
    {
      "node_id": "...",
      "state": "passed",
      "title": "...",
      "evidence": [...],
      "artifacts": [...]
    }
  ],
  "summary": {
    "node_count": 0,
    "evidence_count": 0,
    "artifact_count": 0
  }
}
```

- `honesty_banners` is always present (may be `[]`).
- `nodes` is the per-node block; empty only when no nodes match the
  selection.
- The schema is the contract; `portfolio.py` internals may change without
  breaking it. v2.1 may consume this contract.

### 5.4 Audit event

Every `portfolio export` invocation appends one `portfolio_export` audit
event to `execution/events.yaml`. The command refuses (non-zero exit) on
any data load error.

---

## 6. CLI surface, kinds, and audit event (G-CLI)

Per [G-CLI — Lock portfolio CLI surface, kinds, and audit event #179](https://github.com/earledotpy/skilltrace/issues/179):

### 6.1 Subcommands

| Command | Output | Kind |
|---------|--------|------|
| `skilltrace portfolio preview --track portfolio --format <md\|html\|json>` | Stdout | `READ_ONLY` |
| `skilltrace portfolio export --track portfolio --format <md\|html\|json>` | Bundle on disk | `MUTATING` |

`preview` renders to stdout only. `export` writes the bundle to
`data/portfolio-<date>/` and appends one `portfolio_export` audit event.

### 6.2 Shared flags

Every subcommand accepts:

| Flag | Default | Effect |
|------|---------|--------|
| `--node <ID>` | none | Repeatable node filter |
| `--track <NAME>` | `portfolio` | Track filter |
| `--include-active` | false | Include active nodes |
| `--include-rejected` | false | Include rejected evidence |
| `--include-superseded` | false | Include superseded evidence |
| `--include-paths` | false | Retain artifact paths |
| `--include-notes` | false | Retain learner notes |
| `--include-blockers` | false | Retain blocker text |
| `--include-reviews` | false | Retain review notes |
| `--include-free-text` | false | Retain free-text fields |
| `--include-urls` | false | Retain URLs |
| `--format <md\|html\|json>` | `md` | Output format |
| `--output <PATH>` | `data/portfolio-<date>.<ext>` for preview; `data/portfolio-<date>/` bundle for export | Destination. `-` writes to stdout. |

### 6.3 Registration

All portfolio subcommands are registered in
`src/skilltrace/commands/portfolio.py` as a new module and wired through
the existing `Registry.register(…)` pattern in `src/skilltrace/cli.py`.

### 6.4 Refusal behavior

The command refuses (non-zero exit) on any data load error. No partial
output is written.

---

## 7. Policy seed

A new `policy/portfolio.yaml` file is introduced with the following locked
values.

### 7.1 New file: `policy/portfolio.yaml`

```yaml
portfolio_policy:
  id: policy.portfolio.default_v2_0
  status: active
  title: Portfolio builder
  description: >
    Controls portfolio export defaults: selection track, honesty-banner
    staleness window, and redaction override defaults. All values are
    policy values, not engine constants — readable and editable by the
    learner; changes take effect at the next invocation.
  default_track: portfolio
  default_format: md
  resource_staleness_days: 90
  created_at: 2026-09-06
  updated_at: 2026-09-06
```

### 7.2 `validate policy` integration

Add `portfolio.yaml` to `POLICY_FILES` in
`src/skilltrace/policy/loading.py`, mapping the filename to
`portfolio_policy` (its top-level key). The existing umbrella
`validate policy` command gains the file and the value-range checks below.

Value-range checks (each is a hard error on load, non-zero exit):

- `default_track`: non-empty string.
- `default_format`: one of `md`, `html`, `json`.
- `resource_staleness_days`: `>= 1`.

Bad values exit non-zero with a message naming the field.

---

## 8. Testing

*Resolved: [T-TestArch — Lock v2.0 portfolio testing architecture #180](https://github.com/earledotpy/skilltrace/issues/180)*

### 8.1 Clock injection

Every function in `src/skilltrace/portfolio/` that produces a time-keyed
output takes `today: datetime.date` as a required keyword argument. The CLI
layer is the only place that calls `datetime.date.today()`; the export
layer likewise injects the request's resolved date. No module-level clock,
no default-to-now, no monkeypatching of stdlib `date`.

### 8.2 Four test layers

**Unit layer** (`tests/portfolio/test_selection.py`, `test_redaction.py`,
`test_bundle.py`, new): calls selection, redaction, and bundle functions
directly with hand-built histories; pins exact values computed from
`policy/portfolio.yaml` defaults and flag combinations.

**Command-output layer** (`tests/cli/test_portfolio_command.py`, new):
drives `cli.run(...)` against a disposable repo seeded with
`policy/portfolio.yaml`; asserts exit 0 and that the right *sections*
appear (the four node-state blocks, honesty banner when triggered,
redaction banners when overrides are absent, advisory warning block).
*Not* the exact rendered text — formatting is the surface's concern.

**Export layer** (`tests/portfolio/test_export.py`, new): drives
`portfolio export` and asserts shape. Markdown = compact per-node tables
+ advisory/honesty banners (presence). HTML = self-contained (one inline
`<style>`, zero JS), inline-SVG sparklines absent (not required for
portfolio). JSON = exact fields pinned: `generated_at`, `selection`,
`honesty_banners`, `nodes`, `summary`; empty nodes array only when no
nodes match selection.

**Bundle layer** (`tests/portfolio/test_bundle_layout.py`, new): asserts
`data/portfolio-<date>/` directory structure, `portfolio.json` manifest
presence, artifact files present with rewritten relative links, no
absolute host paths in output.

### 8.3 Fixture style

Hand-built dicts in test functions, written into a disposable repo via the
existing `_write_yaml` helper. No new `tests/fixtures/` directory, no
checked-in YAML, no shared generator function.

### 8.4 Assertion granularity

Unit layer: exact values computed from `policy/portfolio.yaml` defaults.
CLI layer: presence/section only. Export layer: Markdown and HTML presence
only; JSON fields exact (the published contract). Bundle layer: structure
exact (directory listing, manifest keys, link rewriting).

### 8.5 Coverage matrix

| Behaviour | Unit | CLI | Export (JSON exact) | Bundle |
|---|---|---|---|---|
| Default portfolio-track selection | yes | presence | yes | presence |
| --node / --track filters | yes | presence | yes | presence |
| --include-active flag | yes | presence | yes | presence |
| --include-rejected / --include-superseded | yes | presence | yes | presence |
| Redaction module enforcement | yes | presence | yes | presence |
| --include-* override flags | yes | presence | yes | presence |
| Honesty banner triggers (3 types) | yes | presence + banner text | yes | presence |
| Bundle layout (data/portfolio-<date>/) | n/a | n/a | n/a | exact |
| Link rewriting to bundle-relative | n/a | n/a | n/a | exact |
| portfolio.json manifest | n/a | n/a | n/a | exact |
| JSON contract stability | n/a | n/a | yes (exact fields) | n/a |
| HTML self-contained (one inline `<style>`, zero JS) | n/a | n/a | HTML: yes | n/a |
| Markdown readable as plain text | n/a | n/a | Markdown: yes (no HTML in MD) | n/a |

### 8.6 Redaction-bypass safety scan

A static scan in `tests/release/test_v20_safety_gates.py` (SA5) scans
`src/skilltrace/portfolio/**` and `src/skilltrace/commands/portfolio.py`
for direct artifact path access bypassing the redaction module.

---

## 9. Exit gates

*Resolved: [T-Exit — Lock v2.0 release exit gates #181](https://github.com/earledotpy/skilltrace/issues/181)*

### 9.1 Functional gates (E1)

Ten commands, run against the seed repo in order. All must exit 0.

```
pytest tests/portfolio tests/policy tests/cli tests/release
skilltrace validate policy
skilltrace validate graph
skilltrace validate evidence
skilltrace portfolio preview --track portfolio --format markdown
skilltrace portfolio preview --track portfolio --format html
skilltrace portfolio preview --track portfolio --format json
skilltrace portfolio export --track portfolio --format markdown
skilltrace portfolio export --track portfolio --format html
skilltrace portfolio export --track portfolio --format json
skilltrace portfolio export --track portfolio --include-active --include-rejected --include-superseded --include-paths --include-notes --include-blockers --include-reviews --include-free-text --include-urls --format json
skilltrace portfolio export --track portfolio --node portfolio.project.slope_calculator_01 --format json
skilltrace today
skilltrace health
```

`skilltrace health` is not gated here — the no-new-advisory-in-health
invariant is expressed as SA4 below (a structural scan), which is a
stronger gate than running a command that must not change. Export gates
use markdown as the representative format; per-format variation is covered
exhaustively by `tests/portfolio/test_export.py`. The last two export
commands test: all redaction overrides ON, and single-node selection.

### 9.2 Safety assertions (E2)

Seven static scans, all in `tests/release/test_v20_safety_gates.py`:

**SA1 — Event schema frozen**
Load `execution/events.yaml` (seed); compare the set of top-level keys
and per-record keys against a snapshot stored at
`tests/release/snapshots/events_v1_7.yaml`. Diff is the failure
message. Guards the invariant: events are audit-only and never read to
compute state.

**SA2 — No new SQLite reader**
`Path.glob("src/**/*.py")` scanned for `sqlite3.connect` paired with
`data/skilltrace.db` outside the single whitelist entry:
`src/skilltrace/export/sqlite_export.py`.

**SA3 — No automated pass/master/delete**
Scan `src/**` and `tests/**` for any code path that issues a
`pass_node`, `master_node`, or `delete_record` command without an
explicit learner-flag token.

**SA4 — No network calls in portfolio code**
Scan `src/skilltrace/portfolio/**` and `src/skilltrace/commands/portfolio.py`
for network imports/calls (`urllib`, `requests`, `http`, `aiohttp`,
`httpx`, `socket`).

**SA5 — Redaction-bypass static scan**
Scan portfolio code for direct artifact path access bypassing redaction
module (per T-TestArch).

**SA6 — Audit-event allowlist**
Scan `src/skilltrace/portfolio/**` and `src/skilltrace/commands/portfolio.py`
for event emission — only `portfolio export` event permitted from
`commands/portfolio.py`.

**SA7 — Export-never-read-back**
Scan `src/**` for any read of `data/portfolio-*/` directories or
`portfolio.json`/`portfolio.md`/`portfolio.html` as input.

### 9.3 Doc gates (E3)

Two checks in `tests/release/test_v20_doc_gates.py`:

**DG1 — Spec exit-gates section is filled**
`docs/spec-v2.0-portfolio-builder.md` exists, contains a `## Exit gates`
heading, and contains every gate command from E1 and every assertion
label from E2 (SA1, SA2, SA3, SA4, SA5, SA6, SA7) as substrings.
Substring match — not a byte-identical diff — so whitespace or minor
formatting variation does not fail the gate. Fails only on a missing
command or missing assertion label.

**DG2 — CONTEXT.md glossary gate**
`CONTEXT.md` contains each of the following strings:
- `Portfolio export`
- `Share profile`
- `Redaction override`
- `Honesty banner`
- `Portfolio bundle`
- `Portfolio preview`

---

## 10. Glossary additions to CONTEXT.md

The following terms are introduced by this spec and are to be added to
`CONTEXT.md` in the same change as this file lands.

**Portfolio export** — a derived artifact (Markdown, HTML, JSON, or bundle)
regenerated whole from the engine's truth files on demand. Portfolio
exports are disposable, never hand-edited, and never read back by the
engine. The Markdown/YAML files are the only source of truth. A portfolio
export is a review snapshot, not a daily view.

**Share profile** — the default-deny privacy contract for portfolio
exports: no paths, notes, blocker text, review text, free text, or URLs
appear in outbound surfaces unless an explicit `--include-*` override flag
is passed. The share profile is enforced by a single redaction module; no
format may bypass it.

**Redaction override** — a per-invocation `--include-*` flag that
supersedes the default-deny share profile for one dimension only
(paths, notes, blockers, reviews, free text, or URLs). Redaction overrides
are never persisted; they apply only to the single export invocation that
carries them.

**Honesty banner** — an informational banner surfaced at the top of a
portfolio export when superseded evidence, stale resources, or unverified
claims are detected. The banner names the trigger and warns the learner to
review before sharing. Honesty banners never block export, never alter
node state, and never change eligibility.

**Portfolio bundle** — the on-disk export layout written to
`data/portfolio-<date>/`, containing the Markdown index, self-contained
HTML preview, JSON contract, flat `artifacts/` directory of accepted
artifact files, and per-node `nodes/` detail pages. The bundle is
disposable, gitignored, and never read back by the engine.

**Portfolio preview** — a read-only portfolio export that renders to stdout
without writing to disk. Preview uses the same selection, redaction, and
rendering pipeline as export; it is `READ_ONLY` and emits no audit event.

---

## 11. Invariants and constraints preserved

- Hard boundaries per `AGENTS.md` Safety rules are unchanged.
  `pass_node`, `master_node`, `delete_record` remain manual-only; asserted
  progress never moves backward; AI review is never an acceptance
  authority.
- The event log (`execution/events.yaml`) is never read to compute state;
  the portfolio builder derives from primary truth files only.
- Redaction is enforced by a single module; no format may bypass it.
- The portfolio bundle is disposable and gitignored; the engine never reads
  it back.
- Advisory/honesty banners never block a human command.
- v1's five layers (ADR 0002) are preserved. v2.0 adds code in the
  `policy`, `execution`, and a new `portfolio` layer; no new layer, no
  revived `interface/` scaffold.
- `policy/automation_boundary.yaml` is unchanged; the portfolio introduces
  no automation.
- The `portfolio export` audit event is `MUTATING`; `portfolio preview` is
  `READ_ONLY`.

---

## 12. Acceptance — this map is done when

- [ ] All eight wayfinder tickets on map #174 are closed (G-Selection #175,
      G-Redaction #176, G-Bundle #177, G-Formats #178, G-CLI #179,
      T-TestArch #180, T-Exit #181, **T-Spec #182 — this spec**).
- [ ] `docs/spec-v2.0-portfolio-builder.md` (this file) is referenced from
      map #174's `## Decisions so far`.
- [ ] §8 (Testing) is filled from T-TestArch #180's resolution.
- [ ] §9 (Exit gates) is filled from T-Exit #181's resolution.
- [ ] `CONTEXT.md` contains the six terms in §10.
- [ ] No product or architecture decision remains that would block
      the exit-gate commands in §9.
- [ ] Map `## Not yet specified` is empty.

---

## References

`CONTEXT.md` (especially **Export**, **Share profile**, **Honesty banner**,
**Portfolio bundle**, **Portfolio preview**, **Redaction override**,
**Hard boundary**, **Node states**, **EvidenceRecord**, **ArtifactSpec**,
**LearningResource**, **Blocker**, **Review**); `AGENTS.md` (Safety
rules; Current phase; Repo layout); `docs/POST_V1_ROADMAP.md` (v2.0 slot);
`docs/adr/0001` … `0006`; `docs/spec-v1.6-event-log-analytics.md` (v1.6
precedent for testing split, exit-gate shape, and spec structure);
`src/skilltrace/policy/loading.py` `POLICY_FILES`;
`src/skilltrace/commands/analytics.py` (CLI registration pattern);
`src/skilltrace/dispatch.py` (`Command`, `Kind`, `Registry`);
`src/skilltrace/analytics/export.py` (export pattern);
`tests/cli/test_analytics_command.py` (test pattern);
`tests/release/` (safety-gate suite location).
