"""`skilltrace next` command: the end-to-end read-only recommendation path.

The pure ranking rule is tested in test_recommendation.py. Here we drive the real
command through the CLI on a temp copy of the seed repo — asserting the exit-gate
invocation succeeds, no audit event is written (read-only), the policy track-weight
map is actually read, and an unmapped track warns without failing.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from skilltrace import cli
from skilltrace.policy.weights import load_track_weights
from skilltrace.events import load_events
from skilltrace.graph.nodes import load_nodes

from _builders import write_node

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    """Copy graph/ and policy/ so a real `next` run resolves nodes and weights.

    Unlike sync, `next` reads policy/recommendation.yaml, so the policy dir must
    be present or every track reads as unmapped (advisor point 1).
    """
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def _set_track_weights(root: Path, weights: dict) -> None:
    path = root / "policy" / "recommendation.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["recommendation_policy"]["track_weights"] = weights
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _recommended_order(capsys) -> list[str]:
    """Parse the ranked node IDs from Mentor-voice stdout, in order.

    Mentor-voice kicker lines look like:  OPTION 1 — 60-MIN SESSION
    The node ID appears in the DO THIS NEXT action line:
      Start studying <node_id>: `skilltrace start <node_id>`
    or Continue <node_id>: `skilltrace work <node_id>` (session open).
    We extract the node ID from the backticked real command.
    """
    import re
    out = capsys.readouterr().out
    # Match "`skilltrace start <node_id>`" / "`skilltrace work <node_id>`"
    # where node_id ends before a backtick, whitespace, or end.
    ids = re.findall(r"`skilltrace\s+(?:start|work)\s+([^\s`]+)`", out)
    return ids


# --- Exit gate --------------------------------------------------------------

def test_next_on_seed_exits_zero_and_logs_no_event(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["next", "--minutes", "60", "--limit", "5", "--show-locked"], root=root)
    assert rc == 0
    # Read-only: the dispatcher appends no audit event.
    assert load_events(root) == []
    out = capsys.readouterr().out
    # Mentor-voice output (issue #44): kicker opens each candidate block.
    assert "OPTION 1" in out


def test_next_seed_emits_no_unmapped_track_warning(tmp_path, capsys):
    # Every seed track (foundational/core/portfolio) is in the shipped policy map.
    root = _seed_repo(tmp_path)
    cli.run(["next", "--minutes", "60", "--limit", "20", "--show-locked"], root=root)
    assert "[warning]" not in capsys.readouterr().out


# --- Policy map is actually read --------------------------------------------

def test_custom_policy_map_changes_ordering(tmp_path, capsys):
    root = _seed_repo(tmp_path)

    # Foundational-heavy map: a foundational node leads.
    _set_track_weights(root, {"foundational": 100.0, "core": 1.0, "portfolio": 1.0})
    cli.run(["next", "--minutes", "60", "--limit", "20"], root=root)
    foundational_first = _recommended_order(capsys)

    # Portfolio-heavy map: a portfolio node leads instead.
    _set_track_weights(root, {"foundational": 1.0, "core": 1.0, "portfolio": 100.0})
    cli.run(["next", "--minutes", "60", "--limit", "20"], root=root)
    portfolio_first = _recommended_order(capsys)

    assert foundational_first and portfolio_first
    assert foundational_first[0] != portfolio_first[0]
    # The new leader is a portfolio node (the only track boosted to 100).
    top_node = next(n for n in load_nodes(root) if n.id == portfolio_first[0])
    assert top_node.track == "portfolio"


def test_next_seed_recommendations_all_have_reason_lines(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    cli.run(["next", "--minutes", "60", "--limit", "5"], root=root)
    out = capsys.readouterr().out.splitlines()
    # Mentor-voice output (issue #44): each candidate opens with "OPTION N — ..."
    # followed by a non-empty title line.
    option_indices = [i for i, ln in enumerate(out) if ln.startswith("OPTION ")]
    assert option_indices, "Expected at least one OPTION kicker in next output"
    for i in option_indices:
        # The line after the kicker is the node title (non-empty).
        assert i + 1 < len(out) and out[i + 1].strip()


def test_unmapped_track_warns_but_exits_zero(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    # Drop 'foundational' from the map: its available nodes become unmapped.
    _set_track_weights(root, {"core": 2.0, "portfolio": 1.0})
    rc = cli.run(["next", "--minutes", "60", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[warning]" in out
    assert "foundational" in out


def test_load_track_weights_reads_the_shipped_map(tmp_path):
    root = _seed_repo(tmp_path)
    weights = load_track_weights(root)
    assert weights == {
        "foundational": 3.0,
        "core": 2.0,
        "consolidation": 2.0,
        "portfolio": 1.0,
        "remediation": 0.5,
    }


def test_load_track_weights_missing_policy_returns_empty(tmp_path):
    (tmp_path / "graph").mkdir()
    assert load_track_weights(tmp_path) == {}


# --- Issue #306: honest handoff + active-work awareness ----------------------
#
# `next` printed `skilltrace session start --node <id>` — a command that does
# not exist — and ignored the open session entirely (contradicting `today`,
# which picks the open thread up as its focus). Every printed command must be
# a real one (`start` opens, `work` adds to the open session), and an open
# session must surface in the report the way `today` surfaces it.


def _write_doc(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _session_repo(tmp_path: Path, *, with_work: bool) -> Path:
    """Minimal repo: shipped policy, one node, and one open session."""
    node_id = "testing.next.subject_01"
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    _write_doc(tmp_path, "evidence/artifact_specs.yaml", {"artifact_specs": []})
    _write_doc(tmp_path, "evidence/validation_gates.yaml", {"validation_gates": []})
    _write_doc(tmp_path, "evidence/evidence_records.yaml", {"evidence_records": []})
    _write_doc(tmp_path, "evidence/attempts.yaml", {"attempts": []})
    _write_doc(tmp_path, "graph/resources.yaml", {"resources": []})
    write_node(tmp_path, node_id)
    _write_doc(
        tmp_path,
        "graph/state.yaml",
        {"progress": {node_id: {"state": "active"}}},
    )
    _write_doc(
        tmp_path,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.001",
                    "status": "open",
                    "started_at": "2020-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    if with_work:
        _write_doc(
            tmp_path,
            "execution/session_work.yaml",
            {
                "session_work": [
                    {
                        "id": "work.001",
                        "session_id": "sess.001",
                        "node_id": node_id,
                        "created_at": "2020-01-01T00:05:00+00:00",
                    }
                ]
            },
        )
    return tmp_path


def test_next_prints_only_real_commands(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["next", "--minutes", "60", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # The stale form names a subcommand that does not exist.
    assert "session start" not in out
    assert "--node" not in out
    # The honest handoff: `start` opens a session on the candidate.
    assert "`skilltrace start " in out


def test_next_with_open_session_names_the_open_thread(tmp_path, capsys):
    root = _session_repo(tmp_path, with_work=True)
    rc = cli.run(["next", "--minutes", "60", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # Consistent with `today`: the open thread is the lead, not ignored.
    assert "session open" in out
    assert "thread to pick up" in out
    assert "testing.next.subject_01" in out
    # While a session is open `start` would be refused — the honest
    # continuation is `work` on the open session.
    assert "`skilltrace work testing.next.subject_01`" in out
    assert "`skilltrace start " not in out


def test_next_with_open_session_and_no_logged_work(tmp_path, capsys):
    root = _session_repo(tmp_path, with_work=False)
    rc = cli.run(["next", "--minutes", "60", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "session open" in out
    assert "nothing's logged on it yet" in out
    assert "`skilltrace work " in out
    assert "`skilltrace start " not in out
