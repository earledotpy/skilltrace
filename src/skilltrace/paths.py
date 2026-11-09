"""Project-root discovery.

One git repository == one learner's curriculum + progress (PRD). Commands
operate on that repository. The root is the nearest ancestor of the working
directory that looks like a SkillTrace repo; a `--root` flag or an explicit
argument overrides discovery (used by tests against temp copies, and by the
`./start.sh` launcher, which pins the directory it lives in).

Discovery never guesses. When no marker is found the search raises
:class:`RootNotFound` instead of handing back the start directory — a wrong
root that looks like a real one is indistinguishable from a repository with
no work in it, so `serve` would bind and render an empty curriculum
(issue #366, friction 4).
"""

from __future__ import annotations

from pathlib import Path

# A directory is a SkillTrace repo root if it carries one of these markers.
# `graph/edges.yaml` is the sole source of truth for relationships (invariant),
# so its presence is the strongest signal; `AGENTS.md` covers a fresh repo whose
# graph has not been populated yet.
_MARKERS = (
    Path("graph") / "edges.yaml",
    Path("AGENTS.md"),
)

_MARKER_LIST = ", ".join(str(marker) for marker in _MARKERS)


class RootNotFound(LookupError):
    """No SkillTrace repository marker at or above the search start.

    Carries the directory the search began in so a caller can phrase its own
    message; `str(exc)` is already the sentence the CLI prints.
    """

    def __init__(self, start: Path) -> None:
        self.start = start
        super().__init__(
            f"no SkillTrace repository found at or above {start} "
            f"(looked for {_MARKER_LIST}) — pass --root <path>, before the command"
        )


def is_repo_root(path: Path | str) -> bool:
    """True when `path` itself carries a repository marker (no walking).

    The launcher uses this to refuse a pinned root that is not a repository,
    which is a different question from "where is the nearest repository".
    """
    directory = Path(path)
    return any((directory / marker).exists() for marker in _MARKERS)


def find_root(start: Path | str | None = None) -> Path:
    """Return the SkillTrace repo root at or above `start` (default: cwd).

    Raises :class:`RootNotFound` when no marker is found. A caller holding a
    concrete root (a test temp copy, the launcher pinning its own directory)
    passes it explicitly and never calls this.
    """
    start_path = Path(start) if start is not None else Path.cwd()
    start_path = start_path.resolve()
    for directory in (start_path, *start_path.parents):
        for marker in _MARKERS:
            if (directory / marker).exists():
                return directory
    raise RootNotFound(start_path)
