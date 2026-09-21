"""The tree-wide gate reader (ADR 0009).

The five content gates that used to read ``web/views.py`` as a single file
now read the whole page layer instead: the concatenation of every
``web/**/*.py`` except ``web/interface/``. The exclusion is load-bearing —
the sublayer mentions ``render_cards`` twice in prose and code, which would
inflate a count-based gate from 2 to 4. Count-based gates keep counting over
the concatenation, so their exact semantics are preserved rather than
relaxed, and successor work never repoints them again.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB = REPO_ROOT / "src" / "skilltrace" / "web"


def web_source_text() -> str:
    """Concatenated source of every web module except the ADR 0007 sublayer."""
    parts = [
        path.read_text(encoding="utf-8")
        for path in sorted(WEB.rglob("*.py"))
        if path.relative_to(WEB).parts[0] != "interface"
    ]
    return "\n".join(parts)
