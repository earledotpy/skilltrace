"""
Cross-cutting page primitives (ADR 0009): escaping, field
parsing, tables, the shared banner, and GET-side flash rendering.

"""

from __future__ import annotations

import html
import re

from ...context import JoinedView


def _esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


def _output_banners(lines: list[str], *, default_class: str = "advisory") -> str:
    """Captured handler output as banners — through the P3.1 translation seam.

    Every line flows through the interface sublayer's forbidden-vocabulary
    translation (no surface bypasses it): CLI voice is rewritten as the
    human act, and the CLI banner kinds map onto the sublayer's semantic
    classes (the alias classes never reach a page). Escaping stays total.
    """
    from ..interface import banners

    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    kind = class_map.get(default_class, "attention")
    parts: list[str] = []
    for banner_kind, banner_text in banners(lines, default_class=kind):
        css = banner_kind or kind
        parts.append(f'<p class="banner {_esc(css)}">{_esc(banner_text)}</p>')
    return "".join(parts)


def _flash_tuples(query: dict) -> list[tuple[str, str]]:
    """Flash banners carried across a redirect as (css, text) tuples."""
    from ..interface import banners

    text = (query.get("notice") or [""])[0]
    if not text:
        return []
    kind = (query.get("kind") or ["ok"])[0]
    if kind not in {"ok", "warning", "error"}:
        kind = "ok"
    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    css = class_map.get(kind, "attention")
    return [
        (banner_kind or css, banner_text)
        for banner_kind, banner_text in banners(text.splitlines(), default_class=css)
    ]


def _linkify_health(escaped_text: str) -> str:
    """Point operational failures at /health (P3.5) — the one link in a flash."""
    return escaped_text.replace("/health", '<a href="/health">/health</a>')


def _flash_html(query: dict, dismiss_path: str = "/") -> str:
    """Flash banners carried across a redirect in the query string (T5 §F+P3.5).

    Every banner is translated human copy from the one translation module
    (fixed at its source, never redacted at the address bar). Dismissal is
    a plain link to the path without the query string; operational failures
    point at /health.
    """
    parts: list[str] = []
    for css, text in _flash_tuples(query):
        banner = _linkify_health(_esc(text))
        parts.append(f'<p class="banner {_esc(css)}">{banner}</p>\n')
    if parts:
        parts.append(
            f'<p class="flash-dismiss"><a href="{_esc(dismiss_path)}">Dismiss</a></p>\n'
        )
    return "".join(parts)


def _field(form: dict, key: str) -> str | None:
    values = form.get(key)
    if not values or not values[0].strip():
        return None
    return values[0]


def _int_field(form: dict, key: str) -> tuple[int | None, str | None]:
    raw = _field(form, key)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{key} must be an integer."


def _degraded_banner(view: JoinedView) -> str:
    """Advisory notice when lenient layers degraded — reads as empty only."""
    if not view.degraded:
        return ""
    names = ", ".join(sorted(set(view.degraded)))
    return (
        '<p class="banner advisory">Some supporting details failed to load and read '
        f"as empty ({_esc(names)}) — everything you can do here still works, and a "
        "refusal on click remains the truth. The health roll-up carries the detail.</p>"
    )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.isupper():
        lowered = text.lower()
        return lowered[0].upper() + lowered[1:]
    return text


_CANONICAL_STATE_LABELS = {
    "locked": "Locked",
    "available": "Available",
    "active": "Active",
    "passed": "Passed",
    "mastered": "Mastered",
    "ready to start": "Available",
    "in progress": "Active",
}


def _normalize_pill_label(label: str) -> str:
    lowered = label.strip().lower()
    return _CANONICAL_STATE_LABELS.get(lowered, label)


def _parse_int(query: dict, key: str, default: int) -> int | None:
    values = query.get(key)
    if not values:
        return default
    try:
        return int(values[0])
    except ValueError:
        return None


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="dense"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'

