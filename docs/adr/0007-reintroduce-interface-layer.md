# ADR 0007 — Reintroduce interface layer as a web-only sublayer

Date: 2026-09-05
Status: accepted
Supersedes: ADR 0002

## Context

ADR 0002 (2026-07-02) cut v1 from six conceptual layers to five by removing
the `interface/` directory: a YAML registry of commands, views, cards, and
active-view state, plus `validate_interface` and the layer-4 release
requirement. The cut was driven by two reasons:

1. **Drift.** v1 is a CLI; real commands live in Python. The YAML registry
   was a parallel description kept in sync by hand — the same drift problem
   that made `edges.yaml` the sole source of truth for relationships.
2. **No renderer.** Views and cards modelled a GUI with no implementation
   before the post-v1 dashboard (backlog v1.4), yet release validation
   required `layer_4_interface`, forcing dead data to ship.

ADR 0002 also collapsed the "no hidden mutation from interface cards" rule
into the general rule that mutations happen only via explicit commands, each
appending one audit event.

Tier 1 (`docs/spec-tier1-serve.md`) is now the daily UI: a stdlib-only HTTP
serve shell (`src/skilltrace/web/`, deliberately *not* named `interface/` or
`views/` per ADR 0006) with six routes and an MVP surface of today / next /
node detail / health. In practice the Tier 1 screens carry the CLI's flavour
too visibly: command names surface as link text, the vocabulary of "view" is
borrowed from the URL, and screens are composed by hand from the CLI
dispatcher's return values. The user (single learner) finds this
CLI-shaped web UI a poor fit for a study tool that should be more visual and
less CLI-flavoured.

ADR 0002's two anti-drift protections are still load-bearing and must be
preserved; the cut itself, however, forecloses a richer UI vocabulary that
the same reasoning (Python-derived, validated) does not actually require.

## Decision

v1 keeps five **engine** layers (graph, evidence, execution, policy,
release). A sixth layer — **interface** — is reintroduced as a **web-only
sublayer** inside `src/skilltrace/web/interface/`.

### Home and boundary

The sublayer is internal to the web package. It is not an engine layer; it
does not appear in release criteria, it does not change
`release/criteria.yaml`'s `criterion.layers.present` (still 5), and it does
not change the v1.0 final acceptance audit invariants. The `web/` package
name chosen by ADR 0006 is preserved; the cut vocabulary is restored
*inside* the package ADR 0006 deliberately carved out.

### Vocabulary

The sublayer contains four objects:

- **View** — a screen in the web UI, addressed by URL. `/today`, `/next`,
  `/node/<id>`, `/health` are views.
- **Card** — a unit the user can see and act on within a view. A card has:
  title, view-binding (which view it lives on), command-binding (the CLI
  command it invokes), gating conditions (e.g. "show only when the bound
  node is `passed`"), confirmation copy ("This will mark math.foo mastered.
  Continue?"), icon class, color class, order within the view, and
  empty-state copy.
- **Command** — the CLI command a card invokes. The sublayer does not own
  command semantics; it reflects the existing dispatcher registry.
- **Active-view state** — the URL. Stateless; no server-side view-state
  file. Bookmarkable.

### Source of truth

Python-derived. No parallel hand-declared YAML. The CLI dispatcher's
existing `Registry` (`src/skilltrace/dispatch.py`) becomes the source of
truth for the bound command on every card. Sublayer metadata (the fields
listed above) is attached to command definitions via a `@register`-style
mechanism (decorator or equivalent) at the command definition site; the
sublayer walks the registry at request time.

This preserves ADR 0002's anti-drift lesson in a tighter form: there is no
hand-declared web vocabulary to drift from the engine, because the
vocabulary is generated from the engine.

### Mutation rule

Every UI action is a CLI command invocation that appends one audit event.
Click-to-pass and click-to-master are still gated by the same preconditions
the CLI enforces; the sublayer adds confirmation copy and gating
visibility, not bypass. The rule from ADR 0002 — "mutations happen only via
explicit commands, each appending one audit event" — is preserved
verbatim.

### Validation

At import time *and* at request time. The sublayer module raises on import
if any card's command-binding, view-binding, or required state cannot
resolve against the live dispatcher. The web server refuses to start if the
sublayer is inconsistent. At request time, a card whose gating conditions
fail for the current learner state is omitted (not shown disabled, not
shown failing) so the UI never offers an action that the engine would
refuse.

This restores `validate_interface`'s protection from the original cut,
without restoring its YAML.

## Consequences

- Every command definition gains sublayer metadata (touch on every module
  under `src/skilltrace/commands/`).
- The sublayer module's import-time check is a hard boot gate; the web
  serve shell cannot start against an inconsistent sublayer.
- Tier 1's daily-view screens gain a vocabulary for "card group"
  composition without hand-written per-screen HTML.
- The original ADR 0002 anti-drift lesson survives in a tighter form
  (Python-derived, import-time validated) rather than being abandoned.
- `docs/spec-tier1-serve.md` Section L is amended: the 5-layer invariant
  is restated as "v1 has five *engine* layers; the web package contains a
  sixth, internal, interface sublayer." A new section is added naming the
  sublayer, its four objects, and its source-of-truth posture.
- `docs/research/ten-repository-additive-adoption-roadmap.md`'s
  anti-reopen row ("a revived interface registry or a parallel UI
  vocabulary") becomes obsolete and is updated in the same change to
  describe the new posture (Python-derived, no parallel vocabulary).
- The four YAMLs at `archive/scaffold-v0.1/interface/` remain out of
  scope; the new sublayer is built from scratch against the live
  dispatcher, not mined from the archived YAMLs.

### Explicitly NOT in scope

- Promoting the sublayer to an engine-level sixth layer.
- Renaming `src/skilltrace/web/` to `interface/`.
- Adding a `criterion.web.interface.valid` release check.
- Expanding the Tier 1 MVP route surface beyond what
  `docs/spec-tier1-serve.md` currently lists.
- Mining or restoring any of the four archived YAMLs at
  `archive/scaffold-v0.1/interface/`.

## Reversal cost

Reversing this decision is local: revert 0007's companion edits
(`spec-tier1-serve.md`, the research roadmap row), flip 0007's status to
`superseded by 0008` (or equivalent), and either keep 0002's `superseded
by 0007` line for history or re-accept 0002. No engine code is coupled to
the sublayer's *existence* — the dispatcher registry is unchanged. The
sublayer code, once written, is a single package tree under
`src/skilltrace/web/interface/` and can be removed in one commit.

See: ADR 0002 (superseded), ADR 0005 (scaffold retirement), ADR 0006
(stdlib-only serve shell), `docs/spec-tier1-serve.md`,
`docs/research/ten-repository-additive-adoption-roadmap.md`,
`src/skilltrace/dispatch.py` (Registry + Command).
