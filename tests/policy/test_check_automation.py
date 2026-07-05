"""`skilltrace check-automation <action>` — a read-only boundary query.

The command answers "may automation do this?"; answering is success (exit 0)
even when the answer is "forbidden" — the roadmap exit gate runs it for all
three hard-boundary actions and expects the query itself to pass.
"""

from __future__ import annotations

import pytest

from skilltrace import cli
from skilltrace.events import load_events


@pytest.mark.parametrize("action", ["pass_node", "master_node", "delete_record"])
def test_hard_boundary_actions_report_forbidden(policy_repo, capsys, action):
    rc = cli.run(["check-automation", action], root=policy_repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "forbidden" in out
    assert action in out
    # Read-only query: no audit event.
    assert load_events(policy_repo) == []
