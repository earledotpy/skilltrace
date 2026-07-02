"""Project-root discovery.

One git repository == one learner's curriculum + progress (PRD). Commands
operate on that repository. The root is the nearest ancestor of the working
directory that looks like a SkillTrace repo; a `--root` flag or an explicit
argument overrides discovery (used by tests against temp copies).
"""

from __future__ import annotations

from pathlib import Path

# A directory is a SkillTrace repo root if it carries one of these markers.
# `graph/edges.yaml` is the sole source of truth for relationships (invariant),
# so its presence is the strongest signal; `CLAUDE.md` covers a fresh repo whose
# graph has not been populated yet.
_MARKERS = (
    Path("graph") / "edges.yaml",
    Path("CLAUDE.md"),
)


def find_root(start: Path | str | None = None) -> Path:
    """Return the SkillTrace repo root at or above `start` (default: cwd).

    Falls back to the resolved start directory when no marker is found, so the
    caller always receives a concrete path rather than an error.
    """
    start_path = Path(start) if start is not None else Path.cwd()
    start_path = start_path.resolve()
    for directory in (start_path, *start_path.parents):
        for marker in _MARKERS:
            if (directory / marker).exists():
                return directory
    return start_path
