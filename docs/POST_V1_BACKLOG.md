# Post-v1 Backlog

Features and work deferred beyond v1.0.0. These do not block the stable
release. Organized by tier: Tier 1 items are nearest-term post-v1 work,
Tier 3 items are longer-horizon.

## Tier 1 -- Web UI and Dashboard

- **Local web server** (`st ui` / `skilltrace serve`) -- agile post-terminal
  daily UI reading engine models/SQLite, writing via Python domain services
  with explicit confirmation modals for pass/master. Designed from real usage
  (ADR 0002), not from the cut scaffold interface layer.
- **Static HTML report** -- optional local dashboard or exportable report for
  review outside the terminal.

## Tier 2 -- Retention Analytics

- **FSRS/Anki retention analytics** -- spaced-repetition modeling as a derived
  overlay on the existing review system. Mastery state remains permanent;
  this adds retention confidence scoring and optimal review scheduling.

## Tier 3 -- Multi-curriculum and Integrations

- **Multi-curriculum support** -- fork and operate multiple curricula from
  separate repos or branches without cross-contamination.
- **PKM integrations** -- connect with personal knowledge management tools
  (Obsidian, Logseq, etc.) for bi-directional note linking.

## Roadmap versioned items

These were identified in the original roadmap as post-v1 work:

- **v1.1** -- Resource web-verification automation and stale-resource
  replacement suggestions.
- **v1.2** -- Phase 2 ML seed graph (Google ML Crash Course, Andrew Ng, ISLR,
  Kaggle, FastAPI, Docker).
- **v1.3** -- Phase 3 LLM/agents/MCP seed graph.
- **v1.5** -- Analytics v1: study velocity, blockers by domain, review
  completion, evidence coverage (mining the event log).
- **v1.6** -- Portfolio builder and GitHub project report.
- **v2.0** -- Adaptive sequencing beyond rule-based recommendations;
  retention/confidence modeling as a derived overlay.

## Not in scope for post-v1

The framework document's advanced ideas -- diagnostic analytics, Elo/BKT-style
mastery modeling, badge issuance, generative AI tutoring -- belong after the
stable v1 engine and its near-term extensions, not in the initial post-v1
backlog.
