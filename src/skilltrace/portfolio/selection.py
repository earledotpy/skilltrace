"""Portfolio node/evidence selection (v2.0 spec §2, G-Selection #175).

Default: nodes in state ``passed``/``mastered`` on the portfolio track, with
accepted, non-superseded (live-head) evidence tied to those nodes. Flags are
per-invocation only: within a dimension OR, across dimensions AND. When
``options.track`` is ``None`` (``--node`` without ``--track``) no track
restriction applies.
"""

from __future__ import annotations

from ..context import JoinedView
from . import redaction as _redaction
from .models import SelectedEvidence, SelectedNode, SelectionOptions

# Asserted states the default selection admits. ``active`` joins only via
# ``--include-active``; derived readiness never matches.
_PASSED_STATES = ("passed", "mastered")


def _superseded_ids(joined: JoinedView) -> set[str]:
    """Ids of records named by a later record's ``supersedes`` pointer."""
    return {
        record.supersedes
        for record in joined.records
        if record.supersedes is not None
    }


def select(joined: JoinedView, options: SelectionOptions) -> list[SelectedNode]:
    """Derive the selected node blocks from live truth at generation time."""
    superseded = _superseded_ids(joined)
    spec_to_node = {spec.id: spec.node_id for spec in joined.specs}

    # Group records by node via their spec linkage. Records whose spec is
    # unknown belong to no node and never enter a selection.
    records_by_node: dict[str, list] = {}
    for record in joined.records:
        node_id = spec_to_node.get(record.artifact_spec_id)
        if node_id is None:
            continue
        records_by_node.setdefault(node_id, []).append(record)

    selected: list[SelectedNode] = []
    wanted = set(options.nodes)
    for node in joined.nodes:
        state = joined.store.entries.get(node.id)
        node_state = state.state if state is not None else None
        if node_state in _PASSED_STATES:
            state_ok = True
        elif node_state == "active" and options.include_active:
            state_ok = True
        else:
            state_ok = False
        if not state_ok:
            continue
        if wanted and node.id not in wanted:
            continue
        if options.track is not None and node.track != options.track:
            continue

        node_records = records_by_node.get(node.id, [])
        evidence: list[SelectedEvidence] = []
        has_superseded = False
        for record in node_records:
            is_superseded = record.id in superseded
            has_superseded = has_superseded or is_superseded
            if is_superseded and not options.include_superseded:
                continue
            if not record.accepted and not options.include_rejected:
                continue
            evidence.append(
                SelectedEvidence(
                    record_id=record.id,
                    spec_id=record.artifact_spec_id,
                    accepted=record.accepted,
                    superseded=is_superseded,
                    artifact_path=_redaction.capture_location(record),
                    note=_redaction.capture_note(record),
                    gate_run=_redaction.capture_receipt(record),
                )
            )
        evidence.sort(key=lambda e: e.record_id)

        blockers = [
            {"id": b.id, "status": b.status, "description": b.description}
            for b in joined.blockers
            if b.node_id == node.id
        ]
        reviews = [
            {
                "id": r.id,
                "status": r.status,
                "outcome": getattr(r, "outcome", None),
                "result_summary": getattr(r, "result_summary", None),
            }
            for r in joined.reviews
            if r.node_id == node.id
        ]
        resources = [
            {
                "id": res.id,
                "url": getattr(res, "url", None),
                "last_verified": getattr(res, "last_verified", None),
                "broken": res.broken is not None,
            }
            for res in joined.resources_by_node.get(node.id, [])
        ]
        notes = [
            record.note
            for record in node_records
            if getattr(record, "note", None)
        ]
        notes.extend(
            work.notes
            for work in joined.work
            if work.node_id == node.id and getattr(work, "notes", None)
        )
        free_text = [
            text
            for spec in joined.specs_by_node.get(node.id, [])
            for text in (
                getattr(spec, "description", None),
                getattr(spec, "acceptance_summary", None),
            )
            if text
        ]

        has_live_accepted = any(e.accepted and not e.superseded for e in evidence)
        selected.append(
            SelectedNode(
                node_id=node.id,
                title=node.title,
                track=node.track,
                state=node_state or "",
                evidence=evidence,
                has_superseded=has_superseded,
                has_unverified_claim=not has_live_accepted,
                blockers=blockers,
                reviews=reviews,
                resources=resources,
                notes=notes,
                free_text=free_text,
            )
        )

    selected.sort(key=lambda n: n.node_id)
    return selected
