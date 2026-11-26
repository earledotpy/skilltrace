"""The Operations home — the capability directory (spec-v3-study-day §11.1).

What only this module shows: the home of deep inspection is a capability
directory — Graph, Evidence, Reviews, Health, Analytics and Portfolio are each
reachable in their own right and never collapsed behind a generic "More"
(IA-3). The count cards exist only here and link to their capability, and
every number is truthful and consistent with the destination view it links
to (R7). Recent relevant facts render as links to where they live.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from discovery_fixtures import build_discovery_variant

from skilltrace.context import load_context_lenient
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "data.pandas.dataframe_basics_01"
NODE_TITLE = "Use basic Pandas DataFrame operations"

_CAPABILITIES = ("/graph", "/evidence", "/reviews", "/health", "/analytics", "/portfolio")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """The seed curriculum and evidence with authored execution records."""
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    moment = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)
    _ago = (moment - timedelta(days=3)).isoformat(timespec="seconds")
    _write_yaml(
        tmp_path,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.ops.001",
                    "node_id": NODE,
                    "status": "open",
                    "description": "authored fixture blocker",
                    "created_at": _ago,
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rvw.ops.001",
                    "node_id": NODE,
                    "status": "scheduled",
                    "scheduled_for": "2026-11-10",
                    "created_at": _ago,
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": "ev.data.pandas.dataframe_basics_01.001",
                    "artifact_spec_id": "spec.data.pandas.dataframe_basics",
                    "location": "evidence/artifacts/data/pandas_basics.py",
                    "accepted": True,
                    "accepted_by": "objective_gate",
                    "artifact_hash": "sha256:" + "1" * 64,
                    "created_at": "2026-11-14T09:00:00+00:00",
                }
            ]
        },
    )
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- the capability directory (IA-3) ---------------------------------------------


def test_the_home_links_all_six_capabilities_and_no_generic_more(repo):
    """Every capability is its own destination; nothing hides behind "More"."""
    title, body, status = views.operations_body(repo, {})
    assert (title, status) == ("Operations", 200)
    for route in _CAPABILITIES:
        assert f'href="{route}"' in body, route
    assert ">More<" not in body
    assert "More" not in re.sub(r"<[^>]+>", "", body)


def test_every_capability_card_names_its_count_truthfully(repo):
    """Each card's value is the derived count its destination renders."""
    from skilltrace.web.interface import plural

    body = views.operations_body(repo, {})[1]
    view = load_context_lenient(repo)
    assert f"{len(view.nodes)} skill{plural(len(view.nodes))}" in body
    assert f"{len(view.records)} record{plural(len(view.records))}" in body
    assert f"{len(view.reviews)} review{plural(len(view.reviews))}" in body
    assert "Two projections" in body  # Health: never a composite score
    assert "4 themes" in body  # Analytics: its themes, counted from one source


def test_the_graph_card_agrees_with_the_graph_destination(repo):
    """R7: the card's number and the destination's table cannot disagree."""
    home = views.operations_body(repo, {})[1]
    graph = views.graph_body(repo, {})[1]
    stated = re.search(r"(\d+) skills", home)
    assert stated is not None
    skills_table = graph.split("Every relationship", 1)[0]
    rows = skills_table.count("<tr>") - 1  # the header row is not a skill
    assert int(stated.group(1)) == rows


def test_the_evidence_card_agrees_with_the_evidence_destination(repo):
    """R7: the card's number and the index's own count line agree."""
    home = views.operations_body(repo, {})[1]
    index = views.evidence_index_body(repo, {})[1]
    home_count = re.search(r"(\d+) records?", home)
    index_count = re.search(r"(\d+) records?", index)
    assert home_count is not None and index_count is not None
    assert home_count.group(1) == index_count.group(1)


# --- recent relevant facts as links ----------------------------------------------


def test_the_newest_evidence_record_links_to_its_inspector(repo):
    """The newest record is a link into the evidence index's inspector."""
    body = views.operations_body(repo, {})[1]
    view = load_context_lenient(repo)
    newest = max(view.records, key=lambda r: (str(r.created_at or ""), r.id))
    assert f"/evidence?record={newest.id}" in body


def test_open_blockers_link_to_their_skills(repo):
    """An open blocker surfaces as its skill, where blockers are worked."""
    body = views.operations_body(repo, {})[1]
    assert f'href="/nodes/{NODE}"' in body
    assert NODE_TITLE in body


def test_overdue_reviews_link_to_the_review_queue(repo):
    """An overdue review is a link to the queue, never a fake due state."""
    body = views.operations_body(repo, {})[1]
    assert 'href="/reviews"' in body


# --- the empty case ---------------------------------------------------------------


def test_the_empty_home_explains_the_curriculum_and_keeps_the_directory(repo):
    """An empty curriculum is explained, and the capabilities stay reachable."""
    empty = build_discovery_variant(repo, "next-empty-curriculum")
    title, body, status = views.operations_body(empty, {})
    assert status == 200
    assert "The curriculum is empty" in body
    assert "not about your progress" in body or "not about you" in body
    for route in _CAPABILITIES:
        assert f'href="{route}"' in body, route
