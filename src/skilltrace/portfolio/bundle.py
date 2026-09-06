"""Disposable portfolio bundle (v2.0 spec §4, G-Bundle #177).

``bundle_portfolio`` writes ``data/portfolio-<date>/`` whole on each export:
the Markdown index, the self-contained HTML preview, the JSON contract (which
doubles as the manifest — it carries the node-to-artifact mapping and the
selection metadata), a ``manifest.json`` copy of that mapping, the flat
``artifacts/`` directory, and per-node ``nodes/`` detail pages. The bundle is
gitignored (``data/``) and never read back by the engine (SA7).

Local artifact paths are rewritten to bundle-relative links via
``redaction.bundle_relative``; external URLs stay as-is unless the share
profile redacts them. The wall clock enters only as ``today`` (§8.1).
"""

from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

from . import export as _export
from .export import load_view_or_raise
from .models import SelectionOptions
from .redaction import bundle_relative

#: Bundle directory stem: ``data/portfolio-<UTC ISO date>/``.
BUNDLE_PREFIX = "portfolio-"


def bundle_dir_name(today: datetime.date) -> str:
    """The disposable bundle directory name for a generation date."""
    return f"{BUNDLE_PREFIX}{today.isoformat()}"


def _is_external(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _unique_name(used: set[str], node_id: str, raw: str) -> str:
    candidate = Path(raw).name or f"{node_id}.bin"
    if candidate not in used:
        return candidate
    stem, suffix = Path(candidate).stem, Path(candidate).suffix
    counter = 2
    while f"{stem}__{counter}{suffix}" in used:
        counter += 1
    return f"{stem}__{counter}{suffix}"


def bundle_portfolio(
    root: Path,
    options: SelectionOptions,
    *,
    today: datetime.date,
    dest: Path | None = None,
) -> Path:
    """Write the disposable bundle; refuse (no partial output) on load error."""
    view = load_view_or_raise(root, options, today=today)

    dest = dest if dest is not None else root / "data" / bundle_dir_name(today)
    artifacts_dir = dest / "artifacts"
    nodes_dir = dest / "nodes"

    # Copy artifact bytes first (in memory of failures: refuse before writing
    # anything when the source tree cannot even be listed is handled by the
    # strict load above; a copy failure aborts via exception with nothing
    # rendered yet — callers see non-zero, never a half bundle presented OK).
    planned: dict[str, str] = {}  # raw local path -> bundle-relative link
    used: set[str] = set()
    copies: list[tuple[Path, str]] = []
    for node in view.nodes:
        for item in node.evidence:
            raw = item.artifact_path
            if not raw or raw in planned or _is_external(raw):
                continue
            source = root / raw
            if not source.is_file():
                continue
            name = _unique_name(used, node.node_id, raw)
            used.add(name)
            planned[raw] = bundle_relative(name)
            copies.append((source, name))

    dest.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    nodes_dir.mkdir(parents=True, exist_ok=True)
    for source, name in copies:
        shutil.copyfile(source, artifacts_dir / name)

    md = _export.render_markdown(view, options, links=planned)
    html_text = _export.render_html(view, options, links=planned)
    json_text = _export.render_json(view, options, links=planned)
    (dest / "portfolio.md").write_text(md, encoding="utf-8")
    (dest / "portfolio.html").write_text(html_text, encoding="utf-8")
    (dest / "portfolio.json").write_text(json_text, encoding="utf-8")
    (dest / "manifest.json").write_text(
        _manifest_json(view, options, planned), encoding="utf-8"
    )
    for node in view.nodes:
        (nodes_dir / f"{node.node_id}.md").write_text(
            _node_detail_md(node, view, options, planned), encoding="utf-8"
        )
    return dest


def _manifest_json(
    view, options: SelectionOptions, planned: dict[str, str]
) -> str:
    """The manifest: generation stamp, selection metadata, node→artifact map."""
    contract = json.loads(_export.render_json(view, options))
    mapping: dict[str, list[str]] = {}
    for entry in contract["nodes"]:
        links = [
            planned.get(item["location"], item["location"])
            for item in entry["evidence"]
            if item["location"] != "[redacted]"
        ]
        mapping[entry["node_id"]] = links
    manifest = {
        "generated_at": contract["generated_at"],
        "selection": contract["selection"],
        "honesty_banners": contract["honesty_banners"],
        "nodes": mapping,
        "summary": contract["summary"],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def _node_detail_md(
    node, view, options: SelectionOptions, planned: dict[str, str]
) -> str:
    """One per-node detail page (Markdown, same pipeline as the index)."""
    from .redaction import REDACTED, redaction_notices

    lines = [
        f"# {node.title}",
        "",
        f"Node: {node.node_id} — {node.state}",
        "",
    ]
    for banner in view.honesty_banners:
        lines.append(banner)
        lines.append("")
    for notice in redaction_notices(options):
        lines.append(notice)
    if view.honesty_banners or redaction_notices(options):
        lines.append("")
    lines.append("| Evidence | Location |")
    lines.append("| --- | --- |")
    if not node.evidence:
        lines.append("| (none) | - |")
    for item in node.evidence:
        if options.include_paths and item.artifact_path:
            loc = planned.get(item.artifact_path, item.artifact_path)
        else:
            loc = REDACTED
        lines.append(f"| {item.record_id} | {loc} |")
    lines.append("")
    return "\n".join(lines)
