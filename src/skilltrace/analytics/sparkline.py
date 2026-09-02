"""Inline-SVG sparkline renderer for analytics export (G5/G7, issue #130).

Pure function — no I/O, no JavaScript. Produces a self-contained ``<svg>``
element from a list of (label, value) pairs that can be embedded directly
in the HTML export body. ≤40 lines of non-comment logic per G5.
"""

from __future__ import annotations


def sparkline_svg(
    points: list[tuple[str, int]],
    *,
    width: int = 200,
    height: int = 40,
    color: str = "#4a90d9",
) -> str:
    """Return a self-contained inline SVG sparkline string.

    ``points`` is a list of ``(label, value)`` pairs ordered oldest-first.
    An empty or all-zero series renders a flat baseline.
    """
    if not points:
        return f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"></svg>'

    values = [max(0, v) for _, v in points]
    max_val = max(values) or 1  # avoid divide-by-zero

    pad_x, pad_y = 4, 4
    inner_w = width - pad_x * 2
    inner_h = height - pad_y * 2
    n = len(values)

    def x(i: int) -> float:
        return pad_x + (i / max(n - 1, 1)) * inner_w

    def y(v: int) -> float:
        return pad_y + inner_h - (v / max_val) * inner_h

    if n == 1:
        pts = f"{x(0):.1f},{y(values[0]):.1f} {x(0) + 1:.1f},{y(values[0]):.1f}"
    else:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))

    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="sparkline">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        f"</svg>"
    )
