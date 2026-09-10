# Spec — v2.3 Verification-hygiene hardening: polite batch sweeps

**Status:** shipped (2026-09-09) — decisions D-Bucket, D-Robots, D-Backoff,
D-Seed, D-Surface locked below; gate runs executed green on the merged
tree (affected suites + whole-repo sweep green modulo one pre-existing
`test_cli.py` registry gap fixed in the same change).
**Target:** v2.3, slot 3 of `docs/POST_V2_ROADMAP.md` — per-host rate
limiting, `robots.txt` respect, and 429 backoff over the existing
`check-resource`/registry seam. Scheduling automation stays re-deferred
with its named trigger; deep-verification stays Beyond.
**Map:** G-Hygiene
([#193](https://github.com/earledotpy/skilltrace/issues/193)).
**Standing rule:** all terms per `CONTEXT.md`; safety rules in `AGENTS.md`
are unchanged and binding — this spec never relaxes them.

---

## 0. Scope and what is explicitly out of scope

In scope for v2.3:

- A `PerHostBucket` seam in `src/skilltrace/resources/polite_sweep.py`:
  nominal per-host spacing — a host's first request proceeds immediately,
  any later same-host request waits `per_host_delay_seconds` (D-Bucket).
- A `RobotsCache` seam: one `robots.txt` fetch per host; disallowed URLs
  are never fetched and report `ok=False, reason="robots.txt disallow"`.
  Any robots fetch failure fails open (D-Robots).
- Bounded 429 backoff in `polite_batch()`: retries until
  `backoff_max_attempts` total attempts with exponential backoff
  (`Retry-After` honored when larger). Only 429 is retried (D-Backoff).
- A `polite_sweep.yaml` policy seed, registered in `POLICY_FILES` with
  value-range checks under `validate policy` (D-Seed).
---

## 1. Decisions

- **D-Bucket (nominal per-host spacing).** `PerHostBucket.reserve(host)`
  returns 0 for a host's first request (or when the delay is 0) and the
  full `per_host_delay_seconds` for any later same-host request. The
  caller sleeps the returned amount on every request via its injected
  `sleep`. Nominal — not wall-clock monotonic — so offline fixtures
  assert exact delay sequences.
- **D-Robots (respect with fail-open).** `RobotsCache` keys one parser
  per normalized hostname and calls `parser.can_fetch()`. A
  missing/unfetchable/error-status robots file allows the URL. Robots
  fetches never enter the rate-limit bucket.
- **D-Backoff (bounded, 429-only).** Backoff waits are
  `min(cap, max(base * 2**(attempt-1), Retry-After))`, slept between
  attempts, never after the final one. `backoff_max_attempts=1` is
  exact v1.8 never-retry.
- **D-Seed (ranges).** `per_host_delay_seconds` finite in [0, 600];
  `respect_robots`/`enabled` strict booleans; `backoff_max_attempts`
  integer in [1, 10]; `backoff_base_seconds` finite in (0, 60];
  `backoff_max_seconds` finite in (0, 600]; `base <= max`.
  Missing/malformed/unknown/out-of-range values fail `validate policy`.
  A disabled seed (`enabled: false`) is valid; the command degrades to
  v1.8 behavior (robots skipped, no extra delay, no 429 retries).
- **D-Surface (CLI).** `check-resources` keeps its selectors and its
  read-only contract; `--per-host-delay`/`--backoff-attempts` out of
  range fail before any fetch. The sweep User-Agent default comes from
  `policy/resource_web_verification.yaml`.

---

## 2. Safety posture (extends v1.7, unchanged)

The polite sweep is pure network reads: it never calls
`record_verification`, never sets `last_verified`, never clears or writes
`broken`, and emits no audit event. A robots disallow is a sweep-local
`ok=False` verdict, not a stored marker. Sweeps stay manual.

---

## 3. Testing architecture

- Unit: `tests/resources/test_polite_sweep.py` — bucket delays,
  robots disallow/allow/fail-open/one-fetch-per-host/never-writes, 429
  backoff/Retry-After/bounded-attempts/404-never-retried, order, empty
  input, zero writes. All offline (mocked urllib, injected sleepers).
- Policy: `tests/policy/test_validate_policy.py` — value-range, missing,
  unknown-field, and disabled-seed-valid cases.
- CLI: `tests/cli/test_resource_batch_check.py` — answered sweeps exit 0
  with registry-identical + no event; bounded 429 retries; policy
  default of 3 attempts; `--no-robots`; disabled-seed degradation;
  out-of-range flag rejection.

---

## 4. Exports

No format changes beyond one new row: `export sqlite` carries one row
per shipped policy file, so the count assertion moves 11 → 12 for
`polite_sweep.yaml`.

---

## 5. Web

Not applicable in v2.3. No Serve changes; HTTP is exercised only through
mocked standard-library seams in tests.

---

## 6. Advisory surfaces

`resource-report` is unchanged. Robots-disallow and backoff-exhausted
verdicts surface only as per-line BROKEN output — never stored markers.

---

## 7. Exit gates

```bash
pytest tests/resources/test_polite_sweep.py tests/policy/test_validate_policy.py tests/cli/test_resource_batch_check.py tests/cli/test_cli.py
skilltrace validate policy
skilltrace validate resources
```

- `check-resources` uses `polite_batch()` with the new flags
  `--per-host-delay`, `--no-robots`, `--backoff-attempts` (D-Surface).

Explicitly **out of scope**: verification-sweep scheduling automation
(re-deferred with its named trigger), resource deep-verification (Beyond),
any change to single-resource `check-resource`, `verify-resource
--check-url`, pass/mastery law, the five layers, or the event log rule.
