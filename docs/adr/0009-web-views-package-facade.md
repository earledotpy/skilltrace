# ADR 0009 — Web views as a package behind a facade

Date: 2026-09-19
Status: accepted

## Context

By v2.4 the Tier 1 web surface (`src/skilltrace/web/`, ADR 0006) carried its
entire presentation in one module: `views.py`, ~2,590 lines holding the page
shell and the locked §B stylesheet, the chrome, the error/status machinery,
every GET route body, the confirmation panels, the analytics themes, ad-hoc
card renderers, form builders, query parsing, the flash/translation plumbing,
and the deprecated compat serializer. It was the largest module in the repo and
the single point of contention for the work queued behind it: #315 (the single
escape door and shared web micro-utilities), #316 (the shared route preamble),
#317–#319 (the per-surface Card-seam migrations), #320 (the compat retirement).

The split was blocked on proof that a structural change would not move the
output. The golden route-body snapshot harness (#312) supplies it: 15 byte-exact
golden HTML files — every served GET, both confirmation panels, the 404 —
rendered under a frozen clock with stable seeding. A refactor can now
demonstrate *structure changed, output didn't*.

Planning the split surfaced three constraints the ticket as written did not
anticipate:

1. **Five gates assert on `views.py` as a file and on its contents.** The
   deprecated serializer's count gate (`tests/web/test_rich_seam.py`), SA2, SA4
   and SA5 (`tests/release/test_v24_safety_gates.py`), and the
   analytics-export literal (`tests/release/test_v16_safety_gates.py`) each read
   that path and grep its text. Moving the file's contents would break or
   silently disarm all five.
2. **The import surface is wider than the public names.** Sixteen test modules
   plus two production callers (`web/handler.py`, `export/html_export.py`) reach
   into the module, including private names (`_STYLE`, `_finish_write`,
   `_status_page`, `_flash_html`) and incidental re-exports (`utc_today`,
   imported from `execution.overdue` and called directly by a test).
3. **A tree-wide gate reader must exclude the sublayer.** `web/interface/`
   (ADR 0007) contains `render_cards` twice — in a docstring and as
   `_TRANSLATE_SEAM`. Sweeping it would inflate a count-based gate from 2 to 4.

## Decision

`web/views.py` becomes the package `web/views/`, one module per view group, with
`web/views/__init__.py` as a facade re-exporting the complete pre-existing import
surface.

### Module boundaries

One module per view group, plus three cross-cutting modules:

- **`_shared.py`** — the primitives every group needs (`_esc`, `_field`,
  `_int_field`, `_parse_int`, `_table`, `_slug`, `_sentence_case`,
  `_normalize_pill_label`, `_degraded_banner`) and the GET-side flash rendering
  (`_flash_html`, `_flash_tuples`, `_linkify_health`, `_output_banners`).
- **`shell.py`** — the page shell and the machinery around it: the locked §B
  stylesheet, `page`, `_nav_html`, `_chrome`, the error/status bodies, the
  lenient-join preamble, and the confirmation-panel shell.
- **`compat.py`** — the deprecated part-to-HTML map.
- **View groups** — `today`, `next`, `node`, `finder`, `health`, `analytics`,
  `steps`, `forms`, `writes`.

### The facade is the package's public surface

`web/views/__init__.py` re-exports every name the pre-existing consumers reach:
the twenty-one names `web/handler.py` uses (twenty imported plus `not_found_body`
read as a module attribute), the `cards_html`, `page` and `render_cards` that
`export/html_export.py` imports, and the private names the test suite calls
directly (`_STYLE`, `_finish_write`, `_status_page`, `_flash_html`) plus the
incidental `utc_today` re-export. A structural test
(`tests/web/test_views_facade.py`) pins that surface, so a later module move
cannot silently drop a re-export.

Handler, export path and test imports stay byte-identical. The split is
mechanical and changes no behavior, no copy and no CSS.

### The gate reader

The five content gates read one helper (`tests/_web_source.py`) that
concatenates every `web/**/*.py` except `web/interface/`. The exclusion is
load-bearing (constraint 3). Count-based gates keep counting over the
concatenation, so their exact semantics are preserved rather than relaxed.
Pointing the gates at the tree instead of one file also means the successor
issues never repoint them again.

One errata from when the split landed: SA5's translation-seam import literal
moved one relative level deeper with the page layer (`from .interface import
banners` → `from ..interface import banners`) — the same assertion over the
same seam, not a relaxation.

### What stays where, and why

- **`writes.py` holds the only mutation path.** The nine POST handlers plus the
  plumbing around them (`Redirect`, in-process nest-dispatch, exit-code mapping,
  redirect-after-POST flash) live together because they are one contract: the
  captured handler output and exit code are mapped to a 303 and a translated
  flash, through the same process-wide `REGISTRY` the CLI resolves, so refusal
  semantics cannot drift from the command line (the one-write-path rule).
- **The flash helpers are read-side, not write-side.** Six GET route bodies call
  `_flash_html`, so placing them in `writes.py` would leave every GET module
  importing from the write module — an inverted dependency. They belong to
  `_shared`, keeping the graph one-way: every module → `_shared`.
- **`compat.py` is the named single home** of `render_cards` and
  `_render_card_inner`, which keeps the count gate at 2 and gives #320 one file
  to delete together with its gate.

## Consequences

- The five gates are repointed, not weakened: each keeps its exact assertion and
  gains coverage of whatever modules exist later.
- The 15 golden snapshots stay byte-identical. That diff — not the test suite's
  colour — is the split's evidence.
- Cross-cutting helpers each gain one home, which is what makes #315's single
  escape door a one-file change rather than a sweep.
- Per-view-group modules give #317, #318 and #319 one migration target each, and
  #320 one file to retire.
- No engine-layer change: `web/interface/` (ADR 0007) is untouched,
  `criterion.layers.present` stays 5, and no release criterion is added. ADR
  0008's JS posture is untouched; DD6's per-route `<script` file-count gate still
  matches only the analytics-path module.
- Cost: one more import hop for a reader, and private names are now re-exported
  from a facade rather than defined beside their only users.

## Explicitly NOT in scope

- Deduping the three `_esc` copies (`views.py` → `_shared.py`,
  `interface/render.py`, `web/health.py`). That is #315; this ADR only moves the
  views copy.
- Renaming the package to `interface/`. ADR 0006 keeps `web/` deliberately
  outside that word, and ADR 0007 puts the sublayer inside it.
- Any behavior, copy or CSS change. The snapshot harness is the contract.
- Promoting anything to an engine layer, or adding a release criterion.
- Deleting `compat.py` (that is #320) or migrating any surface onto the Card
  seam (that is #317–#319).

## Reversal cost

Low, and cheap in both directions. The facade preserved every entry point, so no
caller changes whether the code is one file or twelve. Reversal is inlining the
modules back into a single `views.py` and restoring the five gates' single-file
reads. Snapshot output is unaffected either way.

See: ADR 0006 (package name), ADR 0007 (sublayer, untouched), ADR 0008 (DD6
gate), #312 (snapshot harness, the unblocking proof), #314 (this work), #315,
#316, #317, #318, #319, #320 (successors), `docs/spec-tier1-serve.md`,
`docs/spec-v2.4-interface-sublayer.md`.

## Addendum — #315 follow-through

The single escape door
([#315 — Single escape door and shared web micro-utilities](https://github.com/earledotpy/skilltrace/issues/315))
landed as `web/interface/text.py`: one `esc()` that every web-side HTML
producer imports, the interface renderer and the handoff copy included (a
fourth copy the "Explicitly NOT in scope" count of three above had missed),
plus the one `plural()` agreement helper that replaced sixteen inline
agreement ternaries (the `'s' if n != 1 else ''` family, the *match/matches*
pair included). The renderer still escapes through that door; the door simply
lives in a leaf module, because the renderer imports the handoff copy and a
copy that imports the renderer back would be a cycle.

