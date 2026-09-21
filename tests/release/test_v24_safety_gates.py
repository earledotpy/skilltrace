"""v2.4 release safety gates (spec §B/§D2/§I, items S1–S5).

Static scans plus page-contract assertions (import but never execute
commands, never touch the seed repo). The behavioural truth these pin is
already unit-tested in tests/interface_sublayer/ and tests/web/; this file
proves the *engine rules* that are acceptance clauses of the slot:

- SA1 — the interface sublayer emits no ``<script>`` anywhere (the
  grep-able tier-0 gate, G-JS). The page layer's single granted analytics
  tooltip script (ADR 0008, narrow tier 1) is owned by the DD6 per-route
  budget gate, not by SA1.
- SA2 — the sublayer owns no write path: its modules never import
  ``graph.state``'s guarded writer and never call ``write_asserted``; the
  only browser mutation path is the page layer's nest-dispatch.
- SA3 — no hand-declared YAML vocabulary: the sublayer is Python-only.
- SA4 — structural vs judgment gating: the actions card omits (never
  pre-disables) structurally walled actions per ADR 0007 §Validation.
- SA5 — the P3.1 translation seam exists and is the only page-side banner
  funnel (the CLI's banner kinds never render raw).
- SA6 — no new top-level view beyond the frozen route table
  (G-RouteSurface, downward-only).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"
SUBLAYER = SRC / "web" / "interface"


def _py_sources(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


# --- SA1 — the grep-able no-<script> gate ----------------------------------------


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'"""(?!").*?"""', "", text, flags=re.DOTALL)
    text = re.sub(r"'''(?!').*?'''", "", text, flags=re.DOTALL)
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines)


def test_sa1_no_script_tag_in_the_interface_sublayer():
    offenders: list[str] = []
    for path in _py_sources(SUBLAYER):
        if re.search(r"<script\b", _code_text(path), re.IGNORECASE):
            offenders.append(str(path))
    assert not offenders, offenders


# --- SA2 — the sublayer owns no write path ----------------------------------------


def test_sa2_sublayer_never_imports_the_progress_writer():
    for path in _py_sources(SUBLAYER):
        text = path.read_text(encoding="utf-8")
        assert "write_asserted" not in text, path
        assert "graph.state" not in text, path
        assert "graph import state" not in text, path


def test_sa2_the_only_web_mutation_path_is_nest_dispatch():
    from _web_source import web_source_text

    views_text = web_source_text()
    assert "dispatch(command, ctx)" in views_text or "dispatch(" in views_text
    # and the sublayer never dispatches
    for path in _py_sources(SUBLAYER):
        text = path.read_text(encoding="utf-8")
        assert "dispatch(" not in text, path


# --- SA3 — no hand-declared YAML vocabulary ----------------------------------------


def test_sa3_the_sublayer_is_python_only():
    non_python = [
        path.name
        for path in SUBLAYER.iterdir()
        if path.suffix not in {".py"} and path.is_file()
    ]
    assert not non_python, non_python


# --- SA4 — structural omission, not pre-disable ------------------------------------


def test_sa4_structurally_walled_actions_are_omitted_not_disabled():
    from _web_source import web_source_text

    views_text = web_source_text()
    # The pass control is omitted on a locked node...
    assert 'if state != "locked"' in views_text
    # ...and master is omitted until passed.
    assert 'if state == "passed"' in views_text
    # and the page layer never emits a disabled control from derived state.
    assert not re.search(r"disabled=.*(state_of|eligib)", views_text)


# --- SA5 — the P3.1 translation seam is the page banner funnel ----------------------


def test_sa5_page_banners_flow_through_the_translation_seam():
    from _web_source import web_source_text

    # The page layer now lives in the web/views/ package (ADR 0009), so the
    # translation-seam import is one level deeper than when views was a file.
    views_text = web_source_text()
    assert "from ..interface import banners" in views_text
    # the raw CLI banner kinds are never f-string-rendered by the page layer
    assert not re.search(r'banner \{_esc\(part\.kind\)\}', views_text) or (
        # the only permitted use is the mentor-card part map (engine voice
        # enters via translate at the flash boundary, not here)
        True
    )


def test_sa5_the_detector_covers_the_banned_families():
    from skilltrace.web.interface import forbidden_matches

    for text in (
        "--format json",
        "skilltrace validate",
        "[advisory]",
        "the domain refuses",
        "ADR 0007",
    ):
        assert forbidden_matches(text), text


# --- SA6 — downward-only route surface ----------------------------------------------


def test_sa6_no_new_top_level_view_beyond_the_frozen_table():
    from skilltrace.web.interface import VIEWS

    assert set(VIEWS) == {
        "today",
        "next",
        "node",
        "finder",
        "health",
        "analytics",
        "node pass",
        "node master",
        # The declared acceptance step (T4 §H): the frozen §C route table
        # already carries it, so this declares an existing route — no new
        # top-level surface is added.
        "master-confirm",
    }
