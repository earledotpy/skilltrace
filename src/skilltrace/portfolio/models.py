"""Portfolio builder data model (v2.0 spec §2–§5).

Typed shapes shared by selection, redaction, rendering, and bundling. The
JSON contract in ``export.py`` is the stable published surface; these
dataclasses are the internal pipeline vocabulary and may change without
breaking it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelectionOptions:
    """Per-invocation portfolio selection + share-profile overrides (spec §2, §3).

    ``track`` of ``None`` means no track restriction (used when ``--node``
    is supplied without an explicit ``--track``). All ``include_*`` flags
    default to deny-all per the share profile.
    """

    nodes: tuple[str, ...] = ()
    track: str | None = "portfolio"
    include_active: bool = False
    include_rejected: bool = False
    include_superseded: bool = False
    include_paths: bool = False
    include_notes: bool = False
    include_blockers: bool = False
    include_reviews: bool = False
    include_free_text: bool = False
    include_urls: bool = False


@dataclass
class SelectedEvidence:
    """One evidence record as selected for the portfolio."""

    record_id: str
    spec_id: str
    accepted: bool
    superseded: bool
    artifact_path: str | None = None
    note: str | None = None


@dataclass
class SelectedNode:
    """One portfolio node with its selected evidence and linked context."""

    node_id: str
    title: str
    track: str
    state: str
    evidence: list[SelectedEvidence] = field(default_factory=list)
    has_superseded: bool = False
    has_unverified_claim: bool = False
    blockers: list[dict] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    free_text: list[str] = field(default_factory=list)


@dataclass
class PortfolioView:
    """The derived portfolio snapshot: selection metadata + node blocks."""

    selection: SelectionOptions
    nodes: list[SelectedNode] = field(default_factory=list)
    honesty_banners: list[str] = field(default_factory=list)
    generated_at: str = ""

    @property
    def summary(self) -> dict[str, int]:
        evidence_count = sum(len(n.evidence) for n in self.nodes)
        return {
            "node_count": len(self.nodes),
            "evidence_count": evidence_count,
            "artifact_count": evidence_count,
        }
