"""Share-profile redaction enforcement (v2.0 spec §3, G-Redaction #176).

Default-deny: no paths, notes, blocker text, review text, free text, or URLs
appear in outbound surfaces unless the matching per-invocation
``--include-*`` override flag is passed. Every outbound surface (Markdown,
HTML, JSON, bundle file list) passes through this module; no format may
bypass it.

SA5 invariant: this module is the only place in ``portfolio/`` (and
``commands/portfolio.py``) that reads an evidence record's artifact path.
Callers use ``visible_location`` / ``capture_location`` / ``bundle_relative``
and never touch the path attribute on engine records directly.
"""

from __future__ import annotations

from ..evidence.gate_receipt import capture as _capture_receipt
from ..evidence.gate_receipt import for_share as _receipt_for_share
from .models import SelectedNode, SelectionOptions

#: What a denied field reads as in the JSON contract (spec §3.3).
REDACTED = "[redacted]"

#: (dimension, flag attribute, CLI flag, human banner label)
_DIMENSIONS: tuple[tuple[str, str, str, str], ...] = (
    ("paths", "include_paths", "--include-paths", "artifact paths"),
    ("notes", "include_notes", "--include-notes", "learner notes"),
    ("blockers", "include_blockers", "--include-blockers", "blocker descriptions"),
    ("reviews", "include_reviews", "--include-reviews", "review notes"),
    ("free_text", "include_free_text", "--include-free-text", "free-text fields"),
    ("urls", "include_urls", "--include-urls", "URLs"),
)


def visible_location(record: object, *, include_paths: bool) -> str:
    """The report-visible form of one evidence record's artifact path.

    The single funnel for artifact-path reads: denied paths surface as
    ``[redacted]`` instead of leaking host-local layout. A record's
    ``gate_run`` receipt (v2.2) is path-bearing provenance, so it is
    classified under the same *paths* dimension: denied receipts drop
    entirely, granted receipts pass through verbatim. Hashes and the exit
    class are not path-bearing — shareable under the profile's other rules.
    """
    location = getattr(record, "location", None)
    if include_paths:
        return str(location) if location is not None else REDACTED
    return REDACTED


def visible_receipt(receipt: dict | None, *, include_paths: bool) -> dict | None:
    """The report-visible form of one selected evidence item's receipt.

    Thin adapter over `gate_receipt.for_share` — takes the *receipt mapping
    itself* (as carried on ``SelectedEvidence``), not an engine record.
    A denied *paths* dimension drops the whole receipt; granted, the receipt
    passes through untouched. ``None`` stays ``None``.
    """
    return _receipt_for_share(receipt, include_paths=include_paths)


def capture_location(record: object) -> str | None:
    """Copy one record's artifact path into internal selection state.

    The only other sanctioned path read: it moves the path into
    ``SelectedEvidence`` so renderers never touch engine records.
    Outbound surfaces still funnel through ``visible_location``.
    """
    location = getattr(record, "location", None)
    return str(location) if location is not None else None


def capture_receipt(record: object) -> dict | None:
    """Copy one record's ``gate_run`` receipt into internal selection state.

    Thin adapter over `gate_receipt.capture`: moves the receipt dict (or
    ``None``) into ``SelectedEvidence`` so renderers read from selection
    state, never engine records. Outbound surfaces still funnel through
    ``visible_receipt`` — capture itself never redacts.
    """
    return _capture_receipt(record)


def capture_note(record: object) -> str | None:
    """Copy one record's learner note into internal selection state."""
    note = getattr(record, "note", None)
    return str(note) if note is not None else None


def bundle_relative(filename: str) -> str:
    """Rewrite an artifact filename to its bundle-relative link."""
    return f"artifacts/{filename}"


def visible_url(url: str | None, *, include_urls: bool) -> str | None:
    """The report-visible form of one resource URL (None stays None)."""
    if url is None:
        return None
    return url if include_urls else REDACTED


def redact_node_block(block: dict, options: SelectionOptions) -> dict:
    """Return the JSON-contract form of one node block under the share profile.

    Each denied dimension is replaced with ``[redacted]``; each granted
    dimension passes through untouched. Artifact bytes the learner selected
    are never touched — only the surrounding report fields are redacted.
    A record's ``gate_run`` receipt is path-bearing provenance, so it rides
    the *paths* dimension via ``gate_receipt.for_share``: denied it drops
    out of the block entirely; granted it passes through as a copy (hashes
    and the exit class are shareable under the profile's other rules only
    because the whole receipt is present).
    """
    evidence = [
        {
            "id": item.get("id"),
            "location": (
                item.get("location")
                if options.include_paths
                else REDACTED
            ),
            "note": item.get("note") if options.include_notes else REDACTED,
            "gate_run": _receipt_for_share(
                item.get("gate_run"), include_paths=options.include_paths
            ),
        }
        for item in block.get("evidence", [])
    ]
    blockers = [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "description": (
                item.get("description")
                if options.include_blockers
                else REDACTED
            ),
        }
        for item in block.get("blockers", [])
    ]
    reviews = [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "result_summary": (
                item.get("result_summary")
                if options.include_reviews
                else REDACTED
            ),
        }
        for item in block.get("reviews", [])
    ]
    resources = [
        {
            "id": item.get("id"),
            "url": (
                item.get("url")
                if options.include_urls and item.get("url") is not None
                else (None if item.get("url") is None else REDACTED)
            ),
        }
        for item in block.get("resources", [])
    ]
    return {
        "node_id": block.get("node_id"),
        "state": block.get("state"),
        "title": block.get("title"),
        "evidence": evidence,
        "artifacts": [
            loc if options.include_paths else REDACTED
            for loc in block.get("artifacts", [])
        ],
        "blockers": blockers,
        "reviews": reviews,
        "resources": resources,
        "notes": (
            list(block.get("notes", [])) if options.include_notes else [REDACTED]
            if block.get("notes") else []
        ),
        "free_text": (
            list(block.get("free_text", []))
            if options.include_free_text
            else [REDACTED]
            if block.get("free_text")
            else []
        ),
    }


def redaction_notices(options: SelectionOptions) -> list[str]:
    """Banner lines naming each still-denied dimension (Markdown/HTML)."""
    notices: list[str] = []
    for _dimension, flag, cli_flag, label in _DIMENSIONS:
        if not getattr(options, flag):
            notices.append(
                f"[redacted] {label} hidden by the share profile "
                f"(pass {cli_flag} to reveal)."
            )
    return notices


def denied_dimensions(options: SelectionOptions) -> list[str]:
    """Dimension names (``paths``, ``notes``, …) still denied."""
    return [
        dimension
        for dimension, flag, _cli_flag, _label in _DIMENSIONS
        if not getattr(options, flag)
    ]


def block_to_report_dict(node: SelectedNode, options: SelectionOptions) -> dict:
    """Build one raw node block from a ``SelectedNode`` for redaction.

    Centralizes how internal state maps to report fields so renderers never
    invent their own field mapping (and never bypass this module).
    """
    return {
        "node_id": node.node_id,
        "state": node.state,
        "title": node.title,
        "evidence": [
            {
                "id": e.record_id,
                "location": e.artifact_path,
                "note": e.note,
                "gate_run": e.gate_run,
            }
            for e in node.evidence
        ],
        "artifacts": [e.artifact_path for e in node.evidence if e.artifact_path],
        "blockers": node.blockers,
        "reviews": node.reviews,
        "resources": node.resources,
        "notes": node.notes,
        "free_text": node.free_text,
    }
