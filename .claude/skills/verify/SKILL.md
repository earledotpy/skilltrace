---
name: verify
description: How to verify SkillTrace CLI changes by driving the real CLI on a disposable copy of the repo.
---

# Verifying SkillTrace changes

SkillTrace is a Python CLI (`python -m skilltrace`) whose only state is the
repo's Markdown/YAML files. Never drive mutating commands against the real
repo — copy the four data dirs to a temp root and use the public `--root`
flag (this is the same override the test suite uses):

```powershell
$tmp = "$env:TEMP\st-verify"; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $tmp | Out-Null
foreach ($d in "graph","evidence","policy","execution") { Copy-Item -Recurse $d "$tmp\$d" }
python -m skilltrace --root $tmp <command...>
```

No install/build step needed — run from the repo root so `src/` layout
resolves (or `pip install -e .` once).

## Flows worth driving

- Session: `start <node> [--template deep]` → `work <node> [--blocked --notes …] [--minutes N]`
  → `session close [--end <iso>]`. Guards: second start, work w/o session,
  locked node, blocked w/o notes, future/backdated `--end`.
- Blockers/remediation: `blocker create/resolve`, `remediation create
  [--blocker id] / complete`. Completing remediation must NOT resolve the
  blocker (check `blockers` listing after).
- Reviews need a passed node. Cheapest legitimate pass:
  `math.arithmetic.order_operations_01` is available in seed with a manual
  gate and a 3-record minimum — submit three artifacts with
  `evidence submit <node> --location <file> --accept`, then `pass <node>`,
  then `review schedule/complete/cancel`, `reviews` (overdue is derived).
- `validate graph|evidence|execution` after any flow; all read-only.

## Audit check (the strongest single assertion)

`execution/events.yaml` must contain exactly one event per *successful
mutating* command, none for refusals or read-only commands. Parse with
Python/yaml, not by eye.

## Gotchas

- To fake a stale session, rewrite the open session's `started_at` in
  `execution/sessions.yaml` to >12h ago, then run any `work` — expect the
  `[warning] … stale` line.
- Windows console mangles em-dashes in CLI output (`�` under cp1252);
  cosmetic, not a bug.
- PowerShell has no `<<` heredoc — use the Bash tool for inline Python.
