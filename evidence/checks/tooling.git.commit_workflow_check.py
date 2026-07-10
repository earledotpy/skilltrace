"""Objective gate checker for tooling.git.commit_workflow_01.

Interrogates the Git repository the learner builds at the fixed artifact path and
asserts the mechanical result of the commit workflow: it is a real work tree,
`HEAD` resolves to at least one commit, that commit carries a non-empty message,
and it actually tracks a file. Exit 0 means a genuine commit captured content
with a message; an empty repo, an uncommitted staging area, or a message-less
commit rejects.

This is the PRD-blessed "interrogate the repo artifact" check, not a proxy: it
does not test that a `.git` folder exists, it asks Git what was committed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1] / "artifacts" / "git_repo"


def git(*args: str) -> subprocess.CompletedProcess:
    """Run a git command inside the artifact repo, capturing output."""
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
    )


def check(condition: object, message: str) -> None:
    """Fail the gate with a non-zero exit when `condition` is falsy.

    Not `assert`: `-O`/`PYTHONOPTIMIZE` strips assert statements, which would let
    the checker exit 0 for a repo with no commit. `raise SystemExit` always runs.
    """
    if not condition:
        raise SystemExit(f"FAILED: {message}")


def main() -> None:
    if not REPO.exists():
        raise SystemExit(
            f"no repository found at {REPO} — initialize a Git repo there, add a "
            "file, and commit it first (see the node's Learning target)."
        )

    inside = git("rev-parse", "--is-inside-work-tree")
    check(
        inside.returncode == 0 and inside.stdout.strip() == "true",
        f"{REPO} is not a Git work tree",
    )

    head = git("rev-parse", "HEAD")
    check(head.returncode == 0, "HEAD does not resolve — the repo has no commit yet")

    message = git("log", "-1", "--pretty=%s")
    check(message.stdout.strip(), "the latest commit has an empty message")

    tracked = git("ls-tree", "-r", "--name-only", "HEAD")
    check(tracked.stdout.strip(), "the commit tracks no files — stage and commit a file")

    print("tooling.git.commit_workflow_01: all checks passed.")


if __name__ == "__main__":
    main()
