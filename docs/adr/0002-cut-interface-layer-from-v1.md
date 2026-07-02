# ADR 0002 — Cut the interface layer from v1

Date: 2026-07-02
Status: accepted

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
