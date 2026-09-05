# Spec — v1.7 Resource web-verification + stale-resource replacement

**Status:** locked hand-off (map [#133](https://github.com/earledotpy/skilltrace/issues/133)).
**Target:** v1.7, hygiene-only resource verification and replacement.
**Decisions:** [G-Arch #134](https://github.com/earledotpy/skilltrace/issues/134) ·
[G-CLI #135](https://github.com/earledotpy/skilltrace/issues/135) ·
[G-Replace #136](https://github.com/earledotpy/skilltrace/issues/136) ·
[G-Report #137](https://github.com/earledotpy/skilltrace/issues/137) ·
[G-Registry #138](https://github.com/earledotpy/skilltrace/issues/138) ·
[T-TestArch #139](https://github.com/earledotpy/skilltrace/issues/139) ·
[T-Exit #140](https://github.com/earledotpy/skilltrace/issues/140) ·
[G-Glossary #142](https://github.com/earledotpy/skilltrace/issues/142) ·
[G-Policy #143](https://github.com/earledotpy/skilltrace/issues/143).

The builder must not reopen product or architecture decisions. Terms follow
`CONTEXT.md`; all existing hard boundaries remain binding.

---

## 0. Scope and explicit non-goals

In scope:

- A pure standard-library URL reachability checker.
- A policy seed and per-resource enable override.
- `check-resource`, and `verify-resource --check-url`.
- Retired-resource registry metadata and `replace-resource`.
- Retired-resource rendering in `resource-report` and `report resources`.
- Tests, release safety assertions, and documentation gates.

Out of scope: scheduling, batch checks or batch replacement, rate limiting,
`robots.txt`, content or certificate validation, web UI changes, recommendation
ordering, evidence or progress transitions, live-network release gates, and
automated positive verification. No node state, graph edge, evidence record, or
`last_verified` value is changed by this work.

## 1. Data sources and source-of-truth boundaries

`graph/resources.yaml` is the authoritative LearningResource registry.
`policy/resource_web_verification.yaml` supplies web-check defaults.
`execution/events.yaml` is audit-only. Markdown/YAML sources are read and
written through existing seams; SQLite exports are disposable and never read.

Existing resource fields remain valid. Add optional `retired`, `retired_at`,
`replaced_by`, and `web_check: {enabled: bool}` fields. A retired entry must
have `retired: true`, an ISO date `retired_at`, and a valid `replaced_by`;
active entries must omit retirement metadata. The replacement pointer is
validated against the whole registry. `web_check.enabled` inherits policy when
absent and is the only per-resource override.

## 2. Architecture

Add `src/skilltrace/resources/web_check.py`:

```python
check_url(
    url: str,
    *,
    timeout_seconds: int,
    follow_redirects: bool,
    method: Literal["HEAD", "GET"],
    user_agent: str,
) -> WebCheckResult
```

`WebCheckResult` is a frozen result with `ok: bool`, `status_code: int | None`,
`final_url: str | None`, and `reason: str | None`. It uses only
`urllib.request`, explicitly applies method, timeout, redirects, and
User-Agent, and performs no registry writes. Expected HTTP and transport
failures return `ok=False`; invalid arguments raise `ValueError`. It never
calls `record_verification`, writes `last_verified`, or clears `broken`.

`verification.py` remains the sole registry writer for verification facts.
Replacement uses a separate surgical registry writer. Command handlers
validate before writing; the dispatcher owns audit events.

## 3. Policy

Create `policy/resource_web_verification.yaml`:

```yaml
resource_web_verification_policy:
  id: policy.resource_web_verification.default_v1_7
  status: active
  title: Resource web verification
  description: >
    Advisory-only automated URL reachability checks. A failed check may set
    a dated broken marker; a successful check never sets last_verified or
    clears broken.
  enabled: true
  timeout_seconds: 10
  follow_redirects: true
  check_method: HEAD
  user_agent: SkillTrace/1.7
  created_at: 2026-09-03
  updated_at: 2026-09-03
```

Register it in `POLICY_FILES` under the top-level key
`resource_web_verification_policy`. `enabled`, `follow_redirects` are strict
booleans; timeout is an integer from 1 through 120; method is `HEAD` or `GET`;
User-Agent is non-empty. Missing, malformed, unknown, or out-of-range values
fail `validate policy`. The policy is advisory and cannot authorize positive
verification.

## 4. CLI

### 4.1 `check-resource`

`skilltrace check-resource <resource_id>` accepts `--timeout 10`,
`--method HEAD|GET`, `--follow-redirects` (default true),
`--no-follow-redirects`, and `--user-agent "skilltrace/1.7 resource-check"`.
It is read-only and emits no event. It prints, for example:

```text
check-resource: OK resource_id — status 200, final_url https://example.com
check-resource: BROKEN resource_id — status 404: not found
check-resource: BROKEN resource_id — timeout after 10s
```

Both answered `OK` and answered `BROKEN` checks exit 0. Unknown resources,
missing URLs, invalid arguments, unreadable data, or inability to answer exit
1. The command never writes a marker.

### 4.2 `verify-resource --check-url`

Extend the existing command with `--check-url` (default false), the same
timeout/method/redirect flags, and default User-Agent
`skilltrace/1.7 verify-resource`. The preflight check may record only a dated
`broken` marker when it fails; it never sets `last_verified` or clears
`broken`. Without `--check-url`, the existing human path remains the sole
positive-verification path. Existing `--broken --reason` argument rules remain.

Successful command invocations exit 0 and emit exactly one existing
`verify-resource` audit event through the dispatcher. Command failures exit 1
and emit no event. Automation-boundary refusals exit 2.

### 4.3 `replace-resource`

`skilltrace replace-resource <broken_id> <candidate_id> [--dry-run]` is a
single-resource, human-initiated mutating command. Refuse with exit 1, no
writes, and no event when either ID is missing or equal, the candidate is
retired/broken/stale/unverified, the source is neither derived `broken` nor
`stale`, the resources share no node, or the candidate already covers every
source node. Load and validate all graph and registry data first.

On success, ordered-union candidate coverage (existing candidate IDs followed
by new source IDs) is written; the source receives `retired: true`,
`retired_at: YYYY-MM-DD`, and `replaced_by`. Its URL/path, claims,
`supports`, `last_verified`, and existing `broken` marker are preserved.
Nothing else changes. The dispatcher appends exactly one audit event for the `resource_replaced`
operation, represented by the established event `command` value
`replace-resource`, with args `broken_id`, `candidate_id`, `dry_run: false`,
and records `[broken_id, candidate_id]`. No new event schema is introduced.

`--dry-run` performs every validation, writes nothing, and emits no event. It
prints one deterministic JSON line:

```json
{"command":"replace-resource","broken_id":"<id>","candidate_id":"<id>","retired_at":"YYYY-MM-DD","candidate":{"supports_before":["..."],"supports_after":["..."],"supports_added":["..."]},"broken":{"retired":true,"retired_at":"YYYY-MM-DD","replaced_by":"<id>"},"writes":[]}
```

## 5. Web

Not applicable in v1.7. There is no Serve or browser integration and no live
network release requirement. HTTP transport is exercised only through mocked
standard-library seams in tests.

## 6. Advisory surfaces

`resource-report` remains read-only and has no new flags. Its total resource
count includes retired entries and it prints `summary: active=<n>, retired=<n>`.
Active entries retain existing worst-first derived status output. Retired
entries print last, in registry order, as:

```text
  [retired] <id> — retired <retired_at>; replaced by <replaced_by>
```

Retired entries do not print old status detail or candidate lines. Candidate
lists exclude the source, all retired resources, and all resources carrying a
`broken` marker; shared-node candidates remain registry-ordered and unique.
`report resources` uses the same renderer. Coverage still counts all registry
links and all graph nodes. Reporting is advisory only.

## 7. Exports

Not applicable. No export format or SQLite table changes are part of v1.7.

## 8. Testing architecture

Use three layers and no Web layer:

- Unit: `tests/resources/test_web_check.py` calls `check_url` with mocked
  `urllib.request`, asserting exact result fields for HEAD/GET, redirects,
  HTTP/transport/timeout failures, User-Agent, and invalid arguments, plus
  no-write behavior.
- CLI: `tests/cli/test_resource_web_check.py` uses disposable repositories and
  mocked HTTP. Assert exit codes, required output/statuses, marker persistence,
  positive-verification safety, and event presence without incidental formatting.
- Integration: `tests/resources/test_replace_resource.py` uses hand-built
  resource dictionaries and disposable registries. Assert exact union,
  retirement fields, pointer, broken-marker preservation, refusal rules, and
  exactly one event. No live HTTP.

Time-dependent orchestration accepts an explicit clock/date; production CLI is
the only caller resolving the current date. Use hand-built dictionaries, not a
new fixture generator or fixture directory. Exact structured assertions apply
to unit and registry tests; CLI assertions check required facts.

## 9. Exit gates

### E1 — Functional

```text
pytest tests/resources tests/policy tests/cli tests/release
skilltrace validate policy
skilltrace validate resources
skilltrace check-resource <seed-resource-id>
skilltrace verify-resource <seed-resource-id> --check-url
skilltrace replace-resource <broken-resource-id> <candidate-resource-id> --dry-run
skilltrace replace-resource <broken-resource-id> <candidate-resource-id>
skilltrace resource-report
skilltrace health
```

The command gates use deterministic local/mock fixtures; no external network
or running Serve process is required.

### E2 — Safety assertions

Implement in `tests/release/test_v17_safety_gates.py`:

- **SA1 — Event schema frozen:** compare event keys with the v1.6 snapshot;
  only the established whitelisted event shape may be added.
- **SA2 — No new SQLite reader:** only the existing SQLite export reader may
  read `data/skilltrace.db`.
- **SA3 — No automated pass/master/delete:** new paths never issue
  `pass_node`, `master_node`, or `delete_record`.
- **SA4 — Web checker read-only:** `check_url` never writes, calls
  `record_verification`, sets `last_verified`, or clears `broken`.
- **SA5 — Mutation and audit whitelist:** check/report/health are read-only;
  check-url failure can write only `broken`; replacement writes only its
  defined fields and one event; dry-run writes neither.
- **SA6 — Replacement safety:** integration proves union without duplicates,
  source marker preservation, candidate filtering, refusal rules, and no
  progress or graph-edge changes.

### E3 — Documentation

Implement in `tests/release/test_v17_doc_gates.py`:

- **DG1 — Spec gate:** this file has all required sections, E1 commands, and
  labels SA1–SA6.
- **DG2 — Glossary gate:** `CONTEXT.md` contains the finalized v1.7 terms and
  meanings for resource verification, Web check, broken marker, retired
  resource, replacement candidate, and Replacement.

## 10. Glossary

The canonical terms are in `CONTEXT.md`: **Resource verification** is the
human assertion that a resource resolves and its claims hold; a **Web check**
is automated reachability testing that may record a dated broken marker on
failure but never positive verification; a **Retired resource** remains
preserved with its replacement relationship and date but is removed from active
flows; a **Replacement candidate** is a verified alternative sharing nodes; a
**Replacement** is the human-confirmed retirement and ordered coverage
transfer. A **broken marker** records a failed observation and may coexist
with `last_verified`.

## 11. Invariants and hard boundaries

- `last_verified` is human-only; automated success never sets it or clears
  `broken`.
- Web checks, replacement, reporting, and health never pass, master, or delete.
- Asserted progress, graph edges, evidence, and immutable records are
  untouched.
- Registry source YAML is authoritative; event log is audit-only.
- Retired resources remain loadable and auditable; their original links and
  broken marker are preserved.
- Every successful mutating invocation appends exactly one event; read-only
  commands append none; dry-run appends none.
- Advisory policy and resource hygiene never block a human-initiated action.
- No hard-prerequisite override or interface-layer revival is introduced.

## 12. Acceptance

The v1.7 implementation is accepted when E1 passes, SA1–SA6 pass,
DG1–DG2 pass, existing tests remain green, and the source-of-truth and
manual-only invariants above are demonstrated. The resulting implementation
must be builder-ready without reopening any decision recorded by the linked
tickets.
