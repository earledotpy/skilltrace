"""Export layer tests for analytics export (T-TestArch D2/D4/D5, issue #130).

Layer: Export (T-TestArch D2)
Assertion granularity (T-TestArch D4):
  - Markdown : presence only (tables + advisory banner).
  - HTML     : self-contained (one inline <style>, zero <script> bytes),
               inline-SVG sparklines present per theme, advisory banner present.
  - JSON     : exact fields pinned (the published G7 contract).
  - Refusal  : load-error path exits non-zero with a message.

Pattern mirrors test_analytics_command.py: disposable repo via _seed_repo,
_write_yaml helper, in-process cli.run, load_events assertion.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_repo(tmp_path: Path) -> Path:
    """Disposable copy of the live seed repo."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    shutil.copytree(REPO_ROOT / "execution", tmp_path / "execution")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _seed_with_threshold_trips(tmp_path: Path) -> Path:
    """Seed repo that trips at least one advisory threshold.

    Seeds 3 open blockers (>= blockers_active_threshold=3) so
    analytics_warnings() returns a non-empty list.
    """
    root = _seed_repo(tmp_path)
    # Enough sessions to clear the limited-data soft threshold
    sessions_doc = {
        "sessions": [
            {
                "id": f"ses.2026-08-{10 + i:02d}.001",
                "status": "completed",
                "started_at": f"2026-08-{10 + i:02d}T10:00:00Z",
                "ended_at": f"2026-08-{10 + i:02d}T11:00:00Z",
            }
            for i in range(3)
        ]
    }
    _write_yaml(root, "execution/sessions.yaml", sessions_doc)
    # 3 open blockers >= blockers_active_threshold=3
    blockers_doc = {
        "blockers": [
            {
                "id": f"blk.math.arithmetic.order_operations_01.{n:03d}",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "open",
                "description": f"stuck on step {n}",
                "created_at": "2026-08-01T10:00:00Z",
            }
            for n in range(1, 4)
        ]
    }
    _write_yaml(root, "execution/blockers.yaml", blockers_doc)
    return root


# ---------------------------------------------------------------------------
# Registration and mutating contract
# ---------------------------------------------------------------------------


def test_analytics_export_is_registered_mutating():
    cmd = cli.REGISTRY.get("analytics export")
    assert cmd is not None
    assert cmd.kind.value == "mutating"


def test_analytics_export_appends_one_audit_event(tmp_path):
    root = _seed_repo(tmp_path)
    initial = len(load_events(root))
    rc = cli.run(["analytics", "export", "--format", "md"], root=root)
    assert rc == 0
    assert len(load_events(root)) == initial + 1


def test_analytics_export_audit_event_command_name(tmp_path):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "export", "--format", "json"], root=root)
    assert rc == 0
    events = load_events(root)
    assert events[-1]["command"] == "analytics export"


# ---------------------------------------------------------------------------
# Markdown: presence assertions
# ---------------------------------------------------------------------------


class TestMarkdownExport:
    def test_md_exits_zero(self, tmp_path):
        root = _seed_repo(tmp_path)
        rc = cli.run(["analytics", "export", "--format", "md"], root=root)
        assert rc == 0

    def test_md_file_created_at_default_path(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        assert (root / "data" / "analytics-report.md").exists()

    def test_md_theme_segment_in_path(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md", "--theme", "velocity"], root=root)
        assert (root / "data" / "analytics-report-velocity.md").exists()

    def test_md_contains_all_four_theme_headers(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        content = (root / "data" / "analytics-report.md").read_text(encoding="utf-8")
        assert "## Velocity" in content
        assert "## Blockers" in content
        assert "## Reviews" in content
        assert "## Evidence" in content

    def test_md_contains_generated_at_line(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        content = (root / "data" / "analytics-report.md").read_text(encoding="utf-8")
        assert "Generated:" in content

    def test_md_contains_period_line(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        content = (root / "data" / "analytics-report.md").read_text(encoding="utf-8")
        assert "Period:" in content

    def test_md_advisory_banner_present_when_threshold_tripped(self, tmp_path):
        root = _seed_with_threshold_trips(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        content = (root / "data" / "analytics-report.md").read_text(encoding="utf-8")
        assert "[advisory]" in content

    def test_md_no_raw_html_tags(self, tmp_path):
        """Markdown must be readable as plain text — no raw HTML."""
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "md"], root=root)
        content = (root / "data" / "analytics-report.md").read_text(encoding="utf-8")
        assert "<div" not in content
        assert "<span" not in content
        assert "<table" not in content

    def test_md_output_flag_writes_to_custom_path(self, tmp_path):
        root = _seed_repo(tmp_path)
        dest = tmp_path / "out" / "custom.md"
        rc = cli.run(
            ["analytics", "export", "--format", "md", "--output", str(dest)],
            root=root,
        )
        assert rc == 0
        assert dest.exists()


# ---------------------------------------------------------------------------
# HTML: self-contained + sparkline + zero-JS assertions
# ---------------------------------------------------------------------------


class TestHTMLExport:
    def test_html_exits_zero(self, tmp_path):
        root = _seed_repo(tmp_path)
        rc = cli.run(["analytics", "export", "--format", "html"], root=root)
        assert rc == 0

    def test_html_file_created_at_default_path(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        assert (root / "data" / "analytics-report.html").exists()

    def test_html_has_exactly_one_style_block(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        assert content.count("<style") == 1
        assert content.count("</style>") == 1

    def test_html_zero_script_bytes(self, tmp_path):
        """Self-contained contract: zero <script> tags allowed."""
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        raw = (root / "data" / "analytics-report.html").read_bytes()
        assert b"<script" not in raw.lower()

    def test_html_no_external_assets(self, tmp_path):
        """No src= or href= pointing outside the file (no CDN links)."""
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        assert 'src="http' not in content
        assert "href=\"http" not in content

    def test_html_sparklines_present_per_theme(self, tmp_path):
        """Each of the four theme sections embeds at least one inline SVG sparkline."""
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        # Four sparklines — one per theme section
        assert content.count("<svg") >= 4
        assert content.count("</svg>") >= 4
        assert "polyline" in content

    def test_html_advisory_banner_present_when_threshold_tripped(self, tmp_path):
        root = _seed_with_threshold_trips(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        assert "[advisory]" in content

    def test_html_snapshot_footer_present(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        assert "Snapshot" in content

    def test_html_contains_all_four_theme_headers(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "html"], root=root)
        content = (root / "data" / "analytics-report.html").read_text(encoding="utf-8")
        assert "<h2>Velocity</h2>" in content
        assert "<h2>Blockers</h2>" in content
        assert "<h2>Reviews</h2>" in content
        assert "<h2>Evidence</h2>" in content


# ---------------------------------------------------------------------------
# JSON: exact fields pinned (published G7 contract)
# ---------------------------------------------------------------------------

# The published subset from the G7 resolution comment.
_REQUIRED_TOP_KEYS = {
    "generated_at",
    "period",
    "group_by",
    "state",
    "advisory_warnings",
    "velocity",
    "blockers",
    "reviews",
    "evidence",
}

_REQUIRED_PERIOD_KEYS = {"start", "end", "days"}

_REQUIRED_VELOCITY_KEYS = {
    "work_items_count",
    "minutes_logged",
    "node_progress",
    "by_week",
    "by_group",
}

_REQUIRED_BLOCKERS_KEYS = {"active_count", "by_track", "by_prefix"}

_REQUIRED_REVIEWS_KEYS = {"scheduled", "completed", "overdue", "completion_rate"}

_REQUIRED_EVIDENCE_KEYS = {
    "total_records",
    "accepted",
    "rejected",
    "nodes_with_gaps",
    "submission_rate",
}


def _load_json(root: Path, theme: str = "all") -> dict:
    if theme == "all":
        path = root / "data" / "analytics-report.json"
    else:
        path = root / "data" / f"analytics-report-{theme}.json"
    return json.loads(path.read_text(encoding="utf-8"))


class TestJSONExport:
    def test_json_exits_zero(self, tmp_path):
        root = _seed_repo(tmp_path)
        rc = cli.run(["analytics", "export", "--format", "json"], root=root)
        assert rc == 0

    def test_json_file_created_at_default_path(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        assert (root / "data" / "analytics-report.json").exists()

    def test_json_top_level_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload.keys()) == _REQUIRED_TOP_KEYS, (
            f"JSON top-level keys mismatch.\n"
            f"  Expected: {sorted(_REQUIRED_TOP_KEYS)}\n"
            f"  Got:      {sorted(payload.keys())}"
        )

    def test_json_period_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload["period"].keys()) == _REQUIRED_PERIOD_KEYS

    def test_json_velocity_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload["velocity"].keys()) == _REQUIRED_VELOCITY_KEYS

    def test_json_blockers_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload["blockers"].keys()) == _REQUIRED_BLOCKERS_KEYS

    def test_json_reviews_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload["reviews"].keys()) == _REQUIRED_REVIEWS_KEYS

    def test_json_evidence_keys_exact(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert set(payload["evidence"].keys()) == _REQUIRED_EVIDENCE_KEYS

    def test_json_generated_at_is_iso8601_utc(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        ts = payload["generated_at"]
        assert isinstance(ts, str)
        # Must end with Z (UTC) and be parseable
        assert ts.endswith("Z"), f"generated_at should end with Z: {ts!r}"
        from datetime import datetime
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")  # raises on bad format

    def test_json_period_days_is_int(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert isinstance(payload["period"]["days"], int)

    def test_json_state_is_list(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert isinstance(payload["state"], list)

    def test_json_advisory_warnings_is_list(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert isinstance(payload["advisory_warnings"], list)

    def test_json_advisory_warnings_populated_when_threshold_tripped(self, tmp_path):
        root = _seed_with_threshold_trips(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert len(payload["advisory_warnings"]) >= 1
        assert any("blocker" in w.lower() for w in payload["advisory_warnings"])

    def test_json_completion_rate_is_float(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert isinstance(payload["reviews"]["completion_rate"], float)

    def test_json_submission_rate_is_float(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        assert isinstance(payload["evidence"]["submission_rate"], float)

    def test_json_by_week_items_have_correct_shape(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        payload = _load_json(root)
        for bucket in payload["velocity"]["by_week"]:
            assert "week_start" in bucket
            assert "items" in bucket

    def test_json_deterministic_ordering_across_two_runs(self, tmp_path):
        """JSON field ordering must be stable (published contract)."""
        root = _seed_repo(tmp_path)
        cli.run(["analytics", "export", "--format", "json"], root=root)
        first = json.loads((root / "data" / "analytics-report.json").read_text(encoding="utf-8"))
        cli.run(["analytics", "export", "--format", "json"], root=root)
        second = json.loads((root / "data" / "analytics-report.json").read_text(encoding="utf-8"))
        # All keys except generated_at must be identical
        first.pop("generated_at")
        second.pop("generated_at")
        assert first == second, "JSON payload (minus generated_at) must be identical across consecutive runs"

    def test_json_state_filter_reflected_in_payload(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(
            ["analytics", "export", "--format", "json", "--state", "active", "--state", "passed"],
            root=root,
        )
        payload = _load_json(root)
        assert set(payload["state"]) == {"active", "passed"}

    def test_json_group_by_reflected_in_payload(self, tmp_path):
        root = _seed_repo(tmp_path)
        cli.run(
            ["analytics", "export", "--format", "json", "--group-by", "track"],
            root=root,
        )
        payload = _load_json(root)
        assert payload["group_by"] == "track"


# ---------------------------------------------------------------------------
# Refusal on load error
# ---------------------------------------------------------------------------


class TestExportRefusal:
    def test_refusal_exits_nonzero_on_corrupt_nodes(self, tmp_path, capsys):
        """A broken graph/nodes.yaml must cause exit 1 with a clear message."""
        root = _seed_repo(tmp_path)
        # Corrupt the nodes directory so load_nodes fails
        nodes_dir = root / "graph" / "nodes"
        # Write an unparseable frontmatter file
        if nodes_dir.exists():
            bad_node = nodes_dir / "bad_node.md"
            bad_node.write_text(
                "---\nid: [this is not a valid scalar\n---\nBody.\n",
                encoding="utf-8",
            )
        rc = cli.run(["analytics", "export", "--format", "md"], root=root)
        assert rc != 0
        out = capsys.readouterr().out + capsys.readouterr().err
        # Either a FAILED message or an exception was surfaced
        assert rc == 1

    def test_refusal_does_not_write_partial_file(self, tmp_path):
        """On a load error the default output path must not be created."""
        root = _seed_repo(tmp_path)
        nodes_dir = root / "graph" / "nodes"
        if nodes_dir.exists():
            bad_node = nodes_dir / "bad_node.md"
            bad_node.write_text(
                "---\nid: [this is not valid\n---\nBody.\n",
                encoding="utf-8",
            )
        rc = cli.run(["analytics", "export", "--format", "md"], root=root)
        assert rc == 1
        # Default path must not exist when data could not be loaded
        default_path = root / "data" / "analytics-report.md"
        assert not default_path.exists()

    def test_refusal_message_is_clear(self, tmp_path, capsys):
        """Error message must name the failure, not silently swallow it."""
        root = _seed_repo(tmp_path)
        # Corrupt a node file to force a load error (missing nodes dir is
        # treated as an empty graph, not an error — corrupt frontmatter is).
        nodes_dir = root / "graph" / "nodes"
        if nodes_dir.exists():
            bad_node = nodes_dir / "bad_node.md"
            bad_node.write_text(
                "---\nid: [this is not a valid scalar\n---\nBody.\n",
                encoding="utf-8",
            )
        rc = cli.run(["analytics", "export", "--format", "md"], root=root)
        out_err = capsys.readouterr()
        combined = out_err.out + out_err.err
        assert rc != 0
        assert "FAILED" in combined or "error" in combined.lower()
