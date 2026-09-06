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

## Clarification note (2026-09-06)

ADR 0007 describes a **web-only interface sublayer** inside
`src/skilltrace/web/interface/`. This sublayer is **documentation-only
background** for the Tier 1 web UI (ADR 0006, `docs/spec-tier1-serve.md`).
It:

- Adds **no engine seam** — the CLI dispatcher registry is unchanged.
- Adds **no new engine layer** — v1 remains five engine layers (graph, evidence,
  execution, policy, release). `release/criteria.yaml`'s `criterion.layers.present`
  stays 5.
- Adds **no read path** — the engine never reads the sublayer; the sublayer
  reads the engine (live dispatcher) at request time.

The five-layer engine invariant from this ADR stands. The sublayer is a
reflection of the engine, not a parallel source of truth. The original
anti-drift protections (Python-derived vocabulary, import-time validation)
are preserved in ADR 0007 in a tighter form.

**Any future revival of the interface layer as an engine layer** (i.e.,
promoting it to a sixth engine layer, adding it to release criteria,
or giving it an engine read path) **requires its own hard-to-reverse
decision record** (a new ADR with explicit reversal cost analysis).

The original Context, Decision, and Consequences sections above are kept
verbatim for historical record.
