"""Unit tests for share-profile redaction (v2.0 spec §3, T-TestArch #180).

Calls ``redaction`` functions directly with hand-built blocks; pins exact
deny-all defaults and per-dimension overrides.
"""

from __future__ import annotations

from skilltrace.portfolio.models import SelectionOptions
from skilltrace.portfolio.redaction import (
    REDACTED,
    block_to_report_dict,
    denied_dimensions,
    redact_node_block,
    redaction_notices,
    visible_location,
    visible_receipt,
    visible_url,
)
from skilltrace.portfolio.models import SelectedEvidence, SelectedNode


def _block() -> dict:
    return {
        "node_id": "portfolio.project.slope_calculator_01",
        "state": "passed",
        "title": "Slope calculator",
        "evidence": [
            {"id": "ev.001", "location": "evidence/a.md", "note": "my note"}
        ],
        "artifacts": ["evidence/a.md"],
        "blockers": [
            {"id": "blk.1", "status": "open", "description": "stuck here"}
        ],
        "reviews": [
            {"id": "rev.1", "status": "completed", "result_summary": "recalled"}
        ],
        "resources": [{"id": "res-1", "url": "https://example.com/x"}],
        "notes": ["learner note"],
        "free_text": ["spec description"],
    }


def test_default_deny_all_redacts_every_dimension():
    redacted = redact_node_block(_block(), SelectionOptions())
    assert redacted["evidence"][0]["location"] == REDACTED
    assert redacted["evidence"][0]["note"] == REDACTED
    assert redacted["artifacts"] == [REDACTED]
    assert redacted["blockers"][0]["description"] == REDACTED
    assert redacted["reviews"][0]["result_summary"] == REDACTED
    assert redacted["resources"][0]["url"] == REDACTED
    assert redacted["notes"] == [REDACTED]
    assert redacted["free_text"] == [REDACTED]
    # Identity fields are never redacted.
    assert redacted["node_id"] == "portfolio.project.slope_calculator_01"
    assert redacted["state"] == "passed"
    assert redacted["title"] == "Slope calculator"


def test_each_override_reveals_only_its_dimension():
    full = SelectionOptions(
        include_paths=True,
        include_notes=True,
        include_blockers=True,
        include_reviews=True,
        include_free_text=True,
        include_urls=True,
    )
    redacted = redact_node_block(_block(), full)
    assert redacted["evidence"][0]["location"] == "evidence/a.md"
    assert redacted["evidence"][0]["note"] == "my note"
    assert redacted["artifacts"] == ["evidence/a.md"]
    assert redacted["blockers"][0]["description"] == "stuck here"
    assert redacted["reviews"][0]["result_summary"] == "recalled"
    assert redacted["resources"][0]["url"] == "https://example.com/x"
    assert redacted["notes"] == ["learner note"]
    assert redacted["free_text"] == ["spec description"]

    paths_only = redact_node_block(_block(), SelectionOptions(include_paths=True))
    assert paths_only["evidence"][0]["location"] == "evidence/a.md"
    assert paths_only["evidence"][0]["note"] == REDACTED
    assert paths_only["blockers"][0]["description"] == REDACTED


def test_redaction_notices_name_every_denied_dimension():
    notices = redaction_notices(SelectionOptions())
    assert len(notices) == 6
    assert denied_dimensions(SelectionOptions()) == [
        "paths",
        "notes",
        "blockers",
        "reviews",
        "free_text",
        "urls",
    ]
    assert redaction_notices(
        SelectionOptions(
            include_paths=True,
            include_notes=True,
            include_blockers=True,
            include_reviews=True,
            include_free_text=True,
            include_urls=True,
        )
    ) == []


def test_visible_location_funnel():
    class Rec:
        location = "evidence/a.md"

    assert visible_location(Rec(), include_paths=True) == "evidence/a.md"
    assert visible_location(Rec(), include_paths=False) == REDACTED
    assert visible_url("https://example.com", include_urls=False) == REDACTED
    assert visible_url("https://example.com", include_urls=True) == (
        "https://example.com"
    )


# --- Gate-run receipts under the paths dimension (v2.2, spec §3) ------------


class _ReceiptRecord:
    """Minimal *selected-evidence* double carrying a receipt mapping."""

    def __init__(self, receipt):
        self.gate_run = receipt


def _visible(receipt, *, include_paths: bool) -> dict | None:
    """Read the funnel the way renderers do: from selection-state mapping."""
    from skilltrace.portfolio.redaction import capture_receipt

    return visible_receipt(
        capture_receipt(_ReceiptRecord(receipt)), include_paths=include_paths
    )


def test_receipt_without_paths_grant_drops_entirely():
    assert _visible({"command_argv": ["python", "evidence/math/check.py"]}, include_paths=False) is None


def test_receipt_with_paths_grant_passes_through_verbatim():
    receipt = {
        "command_argv": ["python", "evidence/math/check.py"],
        "inputs": ["evidence/math/set_001.md"],
        "exit_class": "passed",
    }
    assert _visible(receipt, include_paths=True) == receipt


def test_record_without_receipt_is_none_in_both_dimensions():
    assert _visible(None, include_paths=False) is None
    assert _visible(None, include_paths=True) is None


def test_capture_receipt_never_redacts_and_copies():
    from skilltrace.portfolio.redaction import capture_receipt

    receipt = {"command_argv": ["python", "check.py"], "exit_class": "passed"}
    captured = capture_receipt(_ReceiptRecord(receipt))
    assert captured == receipt and captured is not receipt
    assert capture_receipt(_ReceiptRecord(None)) is None
    assert visible_url(None, include_urls=True) is None


def test_block_to_report_dict_maps_selected_node():
    node = SelectedNode(
        node_id="portfolio.project.slope_calculator_01",
        title="Slope calculator",
        track="portfolio",
        state="passed",
        evidence=[
            SelectedEvidence(
                record_id="ev.001",
                spec_id="spec.1",
                accepted=True,
                superseded=False,
                artifact_path="evidence/a.md",
                note="n",
            )
        ],
    )
    raw = block_to_report_dict(node, SelectionOptions())
    assert raw["evidence"] == [
        {"id": "ev.001", "location": "evidence/a.md", "note": "n", "gate_run": None}
    ]
    assert raw["artifacts"] == ["evidence/a.md"]


def test_block_to_report_dict_carries_captured_receipt():
    node = SelectedNode(
        node_id="portfolio.project.slope_calculator_01",
        title="Slope calculator",
        track="portfolio",
        state="passed",
        evidence=[
            SelectedEvidence(
                record_id="ev.001",
                spec_id="spec.1",
                accepted=True,
                superseded=False,
                artifact_path="evidence/a.md",
                note="n",
                gate_run={"command_argv": ["python", "check.py"]},
            )
        ],
    )
    raw = block_to_report_dict(node, SelectionOptions())
    assert raw["evidence"][0]["gate_run"] == {"command_argv": ["python", "check.py"]}
