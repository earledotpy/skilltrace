# R-ShellAudit — Chrome & home-shell deltas vs p25-unified

**Ticket:** [R-ShellAudit](https://github.com/earledotpy/skilltrace/issues/259), part of
[Map — Shell fidelity & study-day polish](https://github.com/earledotpy/skilltrace/issues/258).
**Sources:** `prototype/p25-unified.html` (visual contract, chrome + home shell only),
`src/skilltrace/web/views.py` (live chrome + home blocks), `src/skilltrace/web/interface/cards.py`
(VIEWS seam), `docs/spec-v2.4-interface-sublayer.md`, `docs/spec-tier1-serve.md`.
**Rendered check:** `views._nav_html('today')` output, 2026-09-15.
**Scope:** inventory only. No preference-table row is reopened; density verdicts are cited, not relitigated.

## Verdict summary

- **Defects to close** (in `T-ChromeFidelity` #261 / `T-HomeShellFidelity` #262):
  C2 (nav link register), C9 (topline spacing), H1 (hero border 4px → 5px),
  H5-shape (CTA scale), B8 (bento heading hierarchy — the one systematic defect: six cards
  with kicker but no `h2`), B1–B6 headings as instances of B8.
- **Intentional live improvements to waive** (do not "fix" toward the prototype):
  C1-structure (seam-sourced nav groups), C4 (finder Go button), C5-structure (health pill strip),
  C6 (sticky header), C7 (1040px shell), H5-behavior (state-honest CTA), H6 (no hero disclosure),
  B1-row minimalism, B3 link-rows, B5 path-free history copy, B7 (no density footer).
- **Locked-spec conflicts** (spec wins over the contract — §5): F1 (nav groups), F2 (pill colors),
  F3 (file-path copy), F4 (spine pill-chain). These are not visual-contract gaps.
- **No new literal gates proposed.** Existing tickets #261/#262 already scope the fidelity work;
  the audit graduates the map's "literal gates" fog patch with "none needed".

## 1. Chrome

| ID | Contract (`p25-unified.html`) | Live (`views.py`) | Verdict |
|----|-------------------------------|-------------------|---------|
| C1 | Single flex row: brand + Today / Next + separated Analytics group + bare input, right-aligned (100–108) | Brand on its own row (`h1.brand`); two stacked navs `daily` / `periodic` (348–359); groups rendered from the `VIEWS` seam (322–328) | **Waive structure** — F1 spec conflict (seam wins). Style within the rows is still closable (C2/C9) |
| C2 | Nav links muted 15px; current page fg-bold + terracotta underline (49–50) | Links accent, semibold; current marked `aria-current` + accent underline (184–188) | **Defect → #261.** Adopt the contract's muted/current register for chrome nav |
| C3 | Analytics group separated by left border (51, 105) | Periodic row separated by top border (185); no left separator | **Waive literal** — follows from C1. Keep row separation; do not force a left-border into stacked rows |
| C4 | Bare `<input>` 210px, "Find a skill by name…", no submit (53, 106) | GET form to `/nodes/jump`, "Jump to a skill" + **Go** button (355–358, 189–191) | **Waive — intentional improvement.** No-JS form needs the button; title-first finder is spec-locked (`spec-v2.4` §G) |
| C5 | Healthline 14px muted: "✓ Everything looks good" + accent "Full roll-up →" (54–56, 109–112) | Pill strip (`ok`/`attention`/`broken` bordered pills) + muted "Everything looks good." + muted "Full roll-up" (192–196, 329–345) | **Mixed.** Strip structure: waive (T4 §H structured `HealthReport`; intentional). Link register (accent + arrow + ✓ calm marker): **defect → #261** |
| C6 | Non-sticky header (44) | `position:sticky; top:0; z-index:10` (181) | **Waive — intentional.** Keeps nav/finder reachable on the long bento page. Not a spec conflict (no locked row either way). Clears the map's sticky-header fog patch |
| C7 | `.wrap` 1120px, padding 0 28px (45) | `--shell:1040px`, padding 0 24px; rich home overrides to 1120px via `:has(.home-rich)` (162–164, 257) | **Waive — intentional** (amended §B per G-Spec #250, noted in code 160–161) |
| C8 | Brand 19px/700 (47) | `h1.brand` 18px/800 sans (183) | Trivial — fold into #261 if touching the row, else waive |
| C9 | Topline padding 18px 0 0, gap 22px, baseline-aligned (46–48) | Brand margin 10px 0 2px; navs padded 6px 0 8px, gap .9rem, wrapping (183–184) | **Defect → #261** (spacing/density register of the topline) |
| C10 | Zero JS on the page (29–30) | No `<script>` on home (docstring 29–31) | No delta |

## 2. Hero

| ID | Contract | Live | Verdict |
|----|----------|------|---------|
| H1 | Accent left border **5px** (69) | 4px (259) | **Defect → #262** |
| H2 | Padding 28px (69) | `var(--card-pad)` = 28px (259) | Match — no work |
| H3 | Display 30px (70) | 30px override (260) | Match — no work |
| H4 | `available` pill on accent-soft (63); pill + reason line (123–126) | Pill + `_STATE_REASONS` line (780–789, 710–716) | Structure matches. **Pill fill: waive toward live** — F2 spec conflict (locked muted semantics; live `available` = ok-green, 214) |
| H5 | `.cta` 18px, 15×30px fill, "Start studying" (71, 130) | `.btn.primary` + state-honest labels; session-open handling (740–821) | **Mixed.** Button scale toward the 1.25× contract CTA: **defect → #262**. State-aware labels + omitted second start (P1.1a/b, P4.1): **waive (intentional)** |
| H6 | `details` "Why this one today" (132–137) | No hero disclosure; why-line only | **Waive — intentional** (disclosures off the primary path, views docstring 29–31) |
| H7 | "Where to learn: Hf Agents Course" slot (128) | Same slot from typed resources (795) | Match — no work |

## 3. Bento

Grid: contract `minmax(290px,1fr)`, 20px gutters (75); live `minmax(300px,1fr)`, 28/20 gaps (258).
Card padding 20px both (59; dense `--card-pad-dense`, 262). Trivial — waive or fold into #262.

**B8 — the systematic defect (all six cards):** every contract card carries `.heading`
(13.5px muted) **plus** an `h2` (19px); every live card carries `.kicker` only, no `h2`.
Verdict: **defect → #262** (ticket #262 already names "heading hierarchy" — this audit
confirms it as the single biggest home-shell gap). B1–B6 headings are instances of B8.

| ID | Contract card | Live card | Verdict (beyond B8) |
|----|---------------|-----------|---------------------|
| B1 Queue | "What comes after"; 4 bold rows with rank ordinal + opens + effort; "Rank the full 49 →" (146–168) | Kicker "Queue"; link-title rows + leverage only; "See the full ranking →" (824–858) | Row minimalism (no ordinal/effort): **waive** — ranked context without ranker internals (P2.7); full rank lives on `/next` |
| B2 Pressure | "Nothing is due" + why + mini counts + "How reviews work →" (171–177) | "Nothing is waiting — …", no link at zero (861–906) | Zero-state link question **handed to G-StudyDayHandoffs #263** — do not decide here |
| B3 Spine | Pronoun `h2` + outlined focus pill + → locked-pill chain + details + link (181–201) | Kicker + "From {title}:" locator + link rows + "And N more" (936–979) | Link-rows over pill-chain: **waive (intentional)** — F4; details omission: waive (off primary path) |
| B4 Week | Date-range `h2`; "blank"/"—" cells; "today is blank, and that's fine"; link (205–220) | Kicker; "—"/"N min" cells, today tinted; days-practiced + due lines; `/analytics` link (982–1034) | **Waive** — same honesty register, routed link. "blank" vs "—" is sub-literal |
| B5 History | `h2` + why **with engine file paths** + example line + start link (224–231) | Kicker + path-free copy; no start link at zero (1037–1096) | **Waive toward live — F3.** The contract copy violates P3.1; live is the correction. Never re-add paths (ticket #262 already forbids this) |
| B6 Browse | Counts `h2` + Track/Ready/Locked table + link (235–253) | Kicker + `p.big` counts + same table + `/nodes/jump` link (1099–1136) | Closest match — headings only (B8). Table + routed link: waive/match |
| B7 | Density-note footer (258–260) | None | **Waive permanently.** Prototype documentation, P3.1-violet on a learner page; #262 forbids re-adding |

Link treatment (contract `.plain` accent 14.5px unweighted, 80; live accent-600 + hover
underline, 264–265): trivial — waive.

## 4. Sticky-header fog patch — proposed resolution

The map's **Not yet specified** patch ("Sticky header vs prototype non-sticky — surface in
the audit; only ticket a decision if the contract and live posture conflict after the
inventory") is **cleared by this audit with no ticket**: no locked row governs header
stickiness, and stickiness is the better posture for a 7-block page with a finder.
Record: waived intentional improvement (C6).

## 5. Locked-spec conflicts (spec wins; not visual-contract gaps)

- **F1 — nav composition.** Single-row topline (contract 100–108) vs seam-sourced
  `daily`/`periodic` groups (`cards.py` `VIEWS`, 162–204; `views.py` 322–328; ADR 0007;
  `spec-v2.4` §H "health is not a nav stop"). The seam is locked direction — the contract
  composition bends, not the groups. #261 works *within* the two rows.
- **F2 — state-pill fills.** Contract `available` on accent-soft (63) vs locked muted
  semantics for the five node states (`views.py` 94–96, 212–220). Pill colors stay live.
- **F3 — file-path copy.** Contract history card names `execution/sessions.yaml +
  session_work.yaml` (227) vs P3.1. Live path-free copy stands; never re-add.
- **F4 — spine treatment.** Contract pill-chain (184–192) vs links-only bento +
  P1.1a-amended named-twice locator (live 955–979). Live link-rows stand.
- **Preference rows untouched.** Density band, health recipe, tier-1 scope, home shape —
  cited only; nothing here reopens map #208 / #243 / #252 rows.

## 6. Handoff to the fidelity tickets

- **#261 T-ChromeFidelity** closes: C2, C5-link-register, C9 (+C8 opportunistically).
  Respects: C1/C3 waivers (two rows stay), C4 (Go button stays), C6 (sticky stays), C7.
- **#262 T-HomeShellFidelity** closes: B8 (six `h2`s), H1, H5-shape, B1–B6 headings.
  Respects: F2/F3/F4 (pill fills, path-free copy, link-rows stay), B7 (no density footer).
- **#263 G-StudyDayHandoffs** receives: B2 zero-state pointer question.
- No fog graduates into new tickets: the "literal gates" and "sticky header" patches clear
  with this audit; the polish/thin-pass and walkthrough patches wait on their owners
  (#260 and handoff-copy lock respectively).
