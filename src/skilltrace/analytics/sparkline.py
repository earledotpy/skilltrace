"""Pure inline-SVG sparkline renderer shared by the Web UI and exports."""

from __future__ import annotations

import html


def sparkline_svg(
    points: list[tuple[str, int]],
    *,
    width: int = 200,
    height: int = 40,
    color: str = "#4a90d9",
    with_points: bool = False,
) -> str:
    """Return a self-contained SVG for an oldest-first ``(label, value)`` series.

    ``with_points`` is the tier-1 narrow opt-in (ADR 0008): real multi-point
    series gain one focusable marker per point, each carrying a native
    ``<title>`` (the tier-0 tooltip — full function with script absent) plus
    a ``data-tip`` hook the single granted analytics script upgrades to a
    hover/focus tooltip. Single-point series never gain markers (P2.2 bans
    pseudo-sparklines). Defaults keep every existing caller byte-identical.
    """
    if not points:
        return f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"></svg>'
    values = [max(0, v) for _, v in points]
    max_val = max(values) or 1  # avoid divide-by-zero
    pad_x, pad_y = 4, 4
    inner_w = width - pad_x * 2
    inner_h = height - pad_y * 2
    n = len(values)
    scale_x = inner_w / max(n - 1, 1)
    scale_y = inner_h / max_val
    coords = [
        f"{pad_x + i * scale_x:.1f},{pad_y + inner_h - value * scale_y:.1f}"
        for i, value in enumerate(values)
    ]
    if n == 1:
        coords.append(f"{pad_x + 1:.1f},{pad_y + inner_h - values[0] * scale_y:.1f}")
    points_attr = " ".join(coords)
    markers = ""
    if with_points and n >= 2:
        for i, (label, value) in enumerate(points):
            x = pad_x + i * scale_x
            y = pad_y + inner_h - max(0, value) * scale_y
            tip = html.escape(f"{label}: {value}", quote=True)
            markers += (
                f'<circle class="spark-point" cx="{x:.1f}" cy="{y:.1f}" r="3.5" '
                f'fill="{color}" tabindex="0" data-tip="{tip}">'
                f"<title>{tip}</title></circle>"
            )
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="sparkline"><polyline points="{points_attr}" fill="none" '
        f'stroke="{color}" stroke-width="1.5"/>'
        f"{markers}</svg>"
    )
