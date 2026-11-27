"""The repository evidence index and its drill-down (spec-v3-study-day §11.2).

What only this module shows: the index is a *repository-wide immutable-history*
view, distinct from the node-bound workspace (§10.9).

* records are newest first with a stable secondary order, and each row drills
  down to the contextual inspector inside the same route;
* filters are GET parameters and the selected context is URL-addressable;
* an empty history and an unreadable evidence store are different facts — a
  failed source is an operational failure, never a fabricated empty history
  (SC-00a);
* there is no edit, delete or bulk-mutation affordance (HB-5), and event
  provenance renders as record detail rather than a separate destination.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "data.pandas.dataframe_basics_01"
SPEC = "spec.data.pandas.dataframe_basics"
LIVE = f"ev.{NODE}.003"
REJECTED = f"ev.{NODE}.002"
SUPERSEDED = f"ev.{NODE}.001"


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _record(record_id: str, *, accepted: bool, created_at: str, **extra) -> dict:
    record = {
        "id": record_id,
        "artifact_spec_id": SPEC,
        "location": "evidence/artifacts/data/pandas_basics.py",
        "accepted": accepted,
        "accepted_by": "objective_gate",
        "artifact_hash": "sha256:" + record_id[-1] * 64,
        "created_at": created_at,
    }
    record.update(extra)
    return record


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


@pytest.fixture
def history(repo: Path) -> Path:
    """One rejection, one superseded acceptance, and a live correction."""
    _write_yaml(
        repo,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                _record(
                    SUPERSEDED,
                    accepted=True,
                    created_at="2026-11-12T09:00:00+00:00",
                ),
                _record(
                    REJECTED,
                    accepted=False,
                    created_at="2026-11-14T09:00:00+00:00",
                    note="the revenue column was summed, not listed",
                ),
                _record(
                    LIVE,
                    accepted=True,
                    created_at="2026-11-16T09:00:00+00:00",
                    supersedes=SUPERSEDED,
                    supersede_reason="corrected the region_rows column",
                ),
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/events.yaml",
        {
            "events": [
                {
                    "timestamp": "2026-11-16T09:00:00+00:00",
                    "command": "evidence submit",
                    "records_touched": [LIVE, SUPERSEDED],
                }
            ]
        },
    )
    return repo


def test_the_index_lists_history_newest_first_and_each_row_drills_down(history):
    _, body, status = views.evidence_index_body(history, {})
    assert status == 200
    assert "3 records, newest first" in body
    assert body.index(LIVE) < body.index(REJECTED) < body.index(SUPERSEDED)
    for record_id in (LIVE, REJECTED, SUPERSEDED):
        assert f'href="/evidence?record={record_id}"' in body
    # Standing is derived and visible on the record itself, never in prose
    # alone: the correction leaves the old record superseded.
    assert ">superseded<" in body
    assert ">live<" in body


def test_selecting_a_record_opens_the_inspector_in_the_same_route(history):
    _, body, status = views.evidence_index_body(history, {"record": [LIVE]})
    assert status == 200
    assert '<aside class="inspector"' in body
    assert "Selected" in body
    assert LIVE in body
    # The canonical record, its related skill and its event provenance.
    assert "Use basic Pandas DataFrame operations" in body
    assert "Artifact" in body
    assert "Event provenance (1)" in body
    assert "evidence submit" in body
    # The inspector is detail, not a destination: the URL is still /evidence.
    assert 'href="/evidence?record=' in body


def test_filters_are_get_parameters_on_the_owning_route(history):
    _, rejected, _ = views.evidence_index_body(history, {"outcome": ["False"]})
    assert f'record={REJECTED}' in rejected
    assert f'record={LIVE}' not in rejected

    _, superseded, _ = views.evidence_index_body(
        history, {"standing": ["superseded"]}
    )
    assert f'record={SUPERSEDED}' in superseded
    assert f'record={LIVE}' not in superseded

    _, by_node, _ = views.evidence_index_body(history, {"node": [NODE]})
    assert f'record={LIVE}' in by_node
    # A filter that names another skill's population is empty, not an error.
    _, nowhere, _ = views.evidence_index_body(
        history, {"node": ["programming.python.variables_01"]}
    )
    assert "No evidence records" in nowhere


def test_the_outcome_filter_reads_learner_words_and_never_guesses(history):
    """A deep link may spell the verdict; an unknown value matches neither."""
    _, accepted, _ = views.evidence_index_body(history, {"outcome": ["accepted"]})
    assert f'record={LIVE}' in accepted
    assert f'record={REJECTED}' not in accepted

    _, rejected, _ = views.evidence_index_body(history, {"outcome": ["rejected"]})
    assert f'record={REJECTED}' in rejected
    assert f'record={LIVE}' not in rejected

    # An unrecognised value is not silently read as one verdict — the page
    # must not show the rejected set as if it were the answer to "bogus".
    _, bogus, _ = views.evidence_index_body(history, {"outcome": ["bogus"]})
    assert "No evidence records" in bogus
    assert f'record={REJECTED}' not in bogus


def test_an_empty_history_is_empty_not_a_failure(repo):
    _write_yaml(repo, "evidence/evidence_records.yaml", {"evidence_records": []})
    _, body, _ = views.evidence_index_body(repo, {})
    assert "No evidence records" in body
    assert "not a problem with you" in body
    assert "could not be loaded" not in body
    assert "state-failure" not in body


def test_an_unreadable_store_is_an_operational_failure_not_an_empty_history(repo):
    (repo / "evidence" / "evidence_records.yaml").write_text(
        "evidence_records: [ { broken", encoding="utf-8"
    )
    _, body, status = views.evidence_index_body(repo, {})
    assert status == 200
    assert '<h2 class="section-title">Evidence history</h2>' in body
    assert "Evidence history could not be loaded" in body
    assert "operational failure, not an empty history" in body
    assert "sources unavailable" in body.lower()
    assert 'href="/health"' in body
    # No fabricated empty fact, no zero, no filter over an unknown population.
    assert "No evidence records" not in body
    assert "Nothing has been submitted" not in body
    assert 'class="filters"' not in body


def test_a_selected_record_is_refused_with_its_store_failure(repo):
    (repo / "evidence" / "evidence_records.yaml").write_text(
        "evidence_records: [ { broken", encoding="utf-8"
    )
    _, body, _ = views.evidence_index_body(repo, {"record": [LIVE]})
    assert "The selected record cannot be shown" in body
    # The failure is not rewritten as "that record does not exist".
    assert "is not in this repository" not in body


def test_a_degraded_event_log_never_fabricates_empty_provenance(history):
    """The inspector's provenance is a source too: unknown is not ``(0)``."""
    (history / "execution" / "events.yaml").write_text(
        "events: [ { broken", encoding="utf-8"
    )
    _, body, _ = views.evidence_index_body(history, {"record": [LIVE]})
    assert "Event provenance unavailable" in body
    assert "nothing is claimed about what happened" in body
    assert "Event provenance (0)" not in body
    assert "No audit event names this record yet" not in body


def test_the_index_offers_no_edit_delete_or_bulk_mutation(history):
    _, body, _ = views.evidence_index_body(history, {})
    assert 'action="/evidence/delete' not in body
    assert 'action="/evidence/edit' not in body
    assert "edit record" not in body.lower()
    assert "delete record" not in body.lower()
    assert "<form" not in body or 'method="get"' in body
