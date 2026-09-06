# ADR 0002 — Cut the interface layer from v1

Date: 2026-07-02
Status: superseded by 0007 (2026-09-05)

## Context

The framework document and v0.1 scaffold define six layers, where layer 4
("interface") is a YAML registry of commands, views, cards, and active-view
state, with referential-integrity validation. But v1 is a CLI: the real
commands live in Python, so the registry is a parallel description that must
be kept in sync by hand — the same drift problem that led us to make
edges.yaml the sole source of truth for relationships. Views and cards model
a GUI that has no renderer before the post-v1 dashboard (backlog v1.4), yet
release validation required `layer_4_interface`, forcing dead data to ship.

## Decision

v1 has five layers: graph, evidence, execution, policy, release. The
`interface/` directory, `validate_interface`, and the layer-4 release
requirement are removed, not stubbed. The CLI is self-describing via its own
help output. The "no hidden mutation from interface cards" rule is subsumed
by the general rule: mutations happen only via explicit commands, each
appending one audit event.

## Consequences

- No YAML registry to drift from the actual CLI.
- Release validation and the smoke-test plan must drop interface checks.
- When the v1.4 dashboard arrives, its view model is designed fresh from
  real usage, with the framework document as reference — not from
  present-day guesses in cards.yaml.

## Superseded note (2026-09-05)

ADR 0007 reintroduces the interface layer as a **web-only sublayer** inside
`src/skilltrace/web/interface/`. The five-layer engine invariant from this
ADR is preserved; v1 still has five engine layers (graph, evidence,
execution, policy, release). ADR 0007's reintroduced sublayer is not an
engine layer and does not appear in release criteria.

The two anti-drift protections from this ADR's reasoning are preserved in
0007 in a tighter form: the sublayer's source of truth is the live CLI
dispatcher (`src/skilltrace/dispatch.py`'s `Registry`), not a hand-declared
YAML, and the sublayer module raises on import if any card binding cannot
resolve. The original concern about parallel hand-declared web vocabulary
drifting from real CLI commands is addressed by deriving the vocabulary
from the engine, not by removing the vocabulary.

The original Context, Decision, and Consequences sections above are kept
verbatim for historical record.
