## Resolution — T-TestArch: Lock v2.0 portfolio testing architecture

All questions resolved. Here's the complete decision record:

---

### **Layer Split: Four Layers (CLI-first, no Web surface)**

| Layer | File | Scope | Precedent |
|-------|------|-------|-----------|
| **1. Unit** | `tests/portfolio/test_unit.py` | Pure functions: selection filtering (flags → node set), redaction application, format builders (Markdown/HTML/JSON), honesty banner generation, link rewriting logic. All take `today: datetime.date` as required kwarg. | v1.6 Unit (`tests/analytics/test_derive.py`); v1.7 Unit (`tests/resources/test_web_check.py`) |
| **2. CLI** | `tests/cli/test_portfolio_command.py` | `portfolio preview` stdout sections (presence); `portfolio export` exit 0, bundle dir created, audit event emitted; flag parsing, defaults, validation errors; fail-fast on load errors. In-process `cli.run()`, disposable repo. | v1.6 CLI (`tests/cli/test_analytics_command.py`); v1.7 CLI (`tests/cli/test_resource_web_check.py`) |
| **3. Bundle** | `tests/portfolio/test_bundle.py` | On-disk bundle structure: `data/portfolio-<date>/` with `portfolio.md`, `portfolio.html`, `portfolio.json`, `artifacts/<node-id>/`; artifact files copied; link rewriting in Markdown/HTML (relative to bundle root); honesty banners present in Markdown/HTML; no per-node pages; single index files per format. | v1.6 Export (shape assertions) + v1.7 Integration (mutation end-to-end); new: bundle-on-disk layout |
| **4. Contract** | `tests/portfolio/test_contract.py` | Exact JSON contract (v2.1 stability promise fields, `redaction` object, `honesty_banners` aggregate); Markdown exact structure (header labels, section headings `## Honesty Banners`/`## Projects`/`## Summary`, project bullet format); HTML exact constraints (HTML5, single inline `<style>`, zero `<script>`, tables for data). | v1.6 Export JSON exact + HTML self-contained scan; v1.7 exact structured assertions |

**Rationale for four layers (not three like v1.7):**
- v1.7 had no on-disk artifact bundle; its Integration layer covered the `replace-resource` mutation. Portfolio's `export` mutation *creates the bundle*, so Bundle layer = on-disk layout + link rewriting + artifact copying (new for v2.0).
- Three format contracts (Markdown/HTML/JSON) with exact stability promises warrant a Contract layer separate from Bundle's presence/structure assertions.
- CLI-first + no Serve = no Web layer (matches v1.7 precedent).

---

### **Assertion Granularity per Layer**

| Layer | Granularity | Examples |
|-------|-------------|----------|
| **Unit** | **Exact** — computed values pinned from policy/seed | Selection filter returns exact node IDs for given flags; redaction strips exact fields; format builders produce exact strings for given inputs; honesty banner text exact; link rewriter produces exact relative paths |
| **CLI** | **Presence / Section only** — no exact formatting | `preview` stdout contains `## Honesty Banners`, `## Projects`, `## Summary`; `export` creates `data/portfolio-<date>/`; audit event emitted with correct keys; exit codes (0 success, 1 load error) |
| **Bundle** | **Presence + Structure exact** | Directory exists with exact name pattern; three index files exist; `artifacts/<node-id>/` flat per-node; artifact files copied byte-for-byte; Markdown/HTML links rewritten to `artifacts/<node-id>/<basename>`; honesty banner lines present in files |
| **Contract** | **Exact** — published contracts | JSON: every v2.1-stable field present, correct type, enum values; Markdown: header field labels exact (`Generated:`, `Period:`, `Selection:`, `Formats:`), section headings exact, project bullet syntax exact; HTML: `<!DOCTYPE html>`, single inline `<style>`, zero `<script>`, `<table>` for project data |

---

### **Coverage Matrix**

| Behaviour | Unit | CLI | Bundle | Contract |
|-----------|------|-----|--------|----------|
| Selection flags → node set (AND across categories, OR within repeatable) | exact | presence | n/a | n/a |
| Redaction default-deny + `--include-*` overrides per surface | exact | n/a | n/a | JSON `redaction` object exact |
| Honesty banner triggers (supersession, stale resources, unverified claims) | exact text | presence in stdout | present in `portfolio.md/.html` | Markdown/HTML banner text exact; JSON aggregate booleans |
| Bundle directory naming (`portfolio-YYYY-MM-DDTHH-MM-SSZ`) | n/a | created | exact pattern | n/a |
| Bundle layout: three index files + `artifacts/<node-id>/` flat | n/a | n/a | exact structure | n/a |
| Artifact copying (byte-for-byte, fail-fast on missing) | n/a | n/a | exact files | n/a |
| Link rewriting: internal → `artifacts/<node-id>/`; external unchanged | exact logic | n/a | rewritten in files | Markdown/HTML links exact |
| No per-node pages (single index per format) | n/a | n/a | absence check | n/a |
| `portfolio preview` stdout sections (all three formats by default) | n/a | presence | n/a | n/a |
| `portfolio export` audit event (`portfolio export` + args + `records_touched`) | n/a | exact event | n/a | n/a |
| Fail-fast on load errors (graph/evidence/execution/resources) | n/a | exit 1, no bundle, no event | n/a | n/a |
| JSON v2.1 stability promise fields | n/a | n/a | n/a | exact fields, types, enums |
| Markdown header labels, section headings, project bullet syntax | n/a | n/a | n/a | exact strings |
| HTML self-contained (inline style, zero JS, tables) | n/a | n/a | n/a | byte-level constraints |
| Redaction effective state recorded in JSON `redaction` object | n/a | n/a | n/a | exact boolean map |
| `--date` override normalizes to filesystem-safe dir name | exact | n/a | exact dir name | n/a |
| `--output -` for preview stdout | n/a | stdout | n/a | n/a |

---

### **Fixture Style (D3 precedent)**

- **Hand-built dicts** in test functions, written into disposable repo via existing `_write_yaml` helper (`tests/_builders.py`).
- **No checked-in fixtures**, no `tests/fixtures/`, no shared generator.
- Clock injection: every time-dependent function takes `today: datetime.date`; only CLI layer calls `datetime.date.today()`.

---

### **Redaction-Bypass Safety Scan: Static Scan (SA5)**

**Placement:** `tests/release/test_v20_safety_gates.py` (new file for v2.0 release gates)

**Scan:** `Path.glob("src/skilltrace/portfolio/**/*.py")` for direct field access on evidence/node/session/blocker/review/resource objects that bypasses the single redaction module (`src/skilltrace/portfolio/redaction.py` — to be created per G-Redaction).

**Forbidden patterns:**
- Direct attribute access on evidence record fields that should be redacted (e.g., `record.location`, `record.notes`, `record.blocker_text`, `record.review_text`, `record.session_notes`, `record.resource_url`) without going through `redaction.apply(record, overrides)`.
- Template/format code that interpolates raw fields instead of redacted views.

**Allowed:** The redaction module itself; CLI/command layer calling `redaction.apply()`; test files.

**Rationale:** Matches v1.6 SA3 (no automated pass/master/delete static scan) and v1.7 SA4 (web checker read-only static scan). A static scan is a release gate (E2 safety assertion); behavioral tests in Unit/Contract layers cover correct redaction *application*, but the bypass scan guards *enforcement* at the code-structure level.

**Behavioral fixture complement:** Unit layer tests (`test_unit.py`) include negative cases asserting redacted fields are absent/empty in rendered output when overrides are false — but the *safety gate* is the static scan.

---

### **Exit Gates (for T-Exit #181 to consume)**

**E1 — Functional:**
```bash
pytest tests/portfolio tests/cli/test_portfolio_command.py tests/release/test_v20_safety_gates.py
skilltrace validate policy
skilltrace portfolio preview --track portfolio
skilltrace portfolio export --track portfolio --format markdown,html,json
skilltrace health
```

**E2 — Safety Assertions (in `tests/release/test_v20_safety_gates.py`):**
- **SA1 — Event schema frozen:** compare `execution/events.yaml` keys with v1.6 snapshot + `portfolio export` event shape
- **SA2 — No new SQLite reader:** only `src/skilltrace/export/sqlite_export.py` reads `data/skilltrace.db`
- **SA3 — No automated pass/master/delete:** scan `src/**` and `tests/**` for unauthorized `pass_node`/`master_node`/`delete_record`
- **SA4 — Redaction enforcement single-module:** all portfolio format/render code imports `src.skilltrace.portfolio.redaction` for field access
- **SA5 — Redaction-bypass static scan:** (as defined above)
- **SA6 — Bundle writer atomicity:** `export` either writes complete bundle or nothing (no partial bundles on error)

**E3 — Doc Gates (in `tests/release/test_v20_doc_gates.py`):**
- **DG1 — Spec gate:** `docs/spec-v2.0-portfolio.md` exists with all E1 commands and SA1–SA6 labels
- **DG2 — Glossary gate:** `CONTEXT.md` contains v2.0 portfolio terms (Portfolio bundle, Portfolio export, Redaction override, Honesty banner, Link rewriting, Bundle manifest)

---

### **Consumed by Downstream Tickets**

- **T-Exit (#181)**: Consumes E1/E2/E3 gate commands and assertions above
- **T-Spec (#182)**: Absorbs layer split, coverage matrix, fixture style, and safety scans into the v2.0 hand-off spec

---

**This ticket is resolved.** The v2.0 portfolio testing architecture is fully specified with four layers, assertion granularity, coverage matrix, fixture style, redaction-bypass safety scan, and exit gates.