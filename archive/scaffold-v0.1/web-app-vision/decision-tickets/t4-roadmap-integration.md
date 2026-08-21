# Decision Ticket T4: Roadmap Integration

**Title:** Integrate the 5‑Phase roadmap into skilltrace node states and interface

**Description:**
The original research documents define a 5‑Phase roadmap (Phases 0‑5: Prerequisites → Capstone projects). The current skilltrace build has roadmap anchors marked `reference_only` — they never control locking, readiness, or recommendation. Determine how (or whether) to integrate the roadmap into the engine and interface.

**Options:**

- **A) Keep as `reference_only`** — roadmap phases remain advisory metadata only; no impact on node states or progression. The existing approach; minimal change.

- **B) Bake phases into node states** — each node carries a `phase` tag (0‑5). Progression through phases gates availability of nodes (Phase‑n nodes only available after Phase‑n‑1 completion). This ties the roadmap directly to the curriculum graph.

- **C) Remove roadmap references** — delete all roadmap‑related content; the curriculum stands on its own without phased structure. Simplifies the engine but loses the structured progression.

- **D) Phase‑as‑recommendation** — roadmap phases appear as recommendations in the UI ("next natural step is Phase 3") but do not gate node availability. UI‑only concern.

**Decision Needed:** Select one roadmap integration approach. This affects:
- Node‑state design (whether nodes carry phase tags)
- Interface navigation (how the web app shows phase progression)
- Curriculum‑authoring workflow (adding nodes to phases)
- Roadmap‑related ADRs (0002, 0004 reference anchoring)

**Dependencies:**
- T1 (interface type — some roadmap integrations only make sense for certain interfaces)
- T2 (original research elements — the 5‑phase structure is core to the original vision)
- T3 (engine API surface — roadmap integration may require new API endpoints)

**Labels:** decision, roadmap, priority-high