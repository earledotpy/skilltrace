"""Single escape door and shared web micro-utilities (#315).

Four conventions that had drifted into copies become enforced facts here:

* every web-side HTML producer escapes through one function — the door in
  ``web/interface/text.py`` that the interface renderer escapes through — so a
  fourth local escaper cannot quietly come back;
* the count-agreement suffix is one helper (``plural``): no inline
  ``'s' if n != 1 else ''`` survives anywhere in the web tree;
* the Health resources card reads its staleness window off the joined view's
  policy — the accessor the node drill-down reads — never a second read of the
  policy seed;
* date-prefix parsing is one function (``execution.overdue.parse_date``).

What the restructuring did *not* change is behaviour: the golden route-body
snapshots (#312) stay byte-identical, and that diff — not this module's colour
— is the ticket's evidence. These tests pin the conventions themselves.
"""

from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml

from skilltrace.context import Loaders, load_context_lenient
from skilltrace.execution.overdue import parse_date
from skilltrace.policy.loading import load_policy_doc, load_policy_docs
from skilltrace.web import health as web_health
from skilltrace.web import views
from skilltrace.web.interface import esc, handoff, plural, render, text

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB = REPO_ROOT / "src" / "skilltrace" / "web"
DOOR = WEB / "interface" / "text.py"

# Every module that renders a count into copy: each must inflect through the
# one helper rather than one of its own.
COUNT_PRODUCERS = (
    WEB / "health.py",
    WEB / "views" / "finder.py",
    WEB / "views" / "shell.py",
    WEB / "views" / "today.py",
)

NODE_A = "math.arithmetic.order_operations_01"  # available in the seed
VERIFIED_ON = "2026-07-10"
TODAY = date(2026, 7, 20)  # 10 days on: inside the seed window, outside a 1-day one


def _web_modules() -> list[Path]:
    return sorted(WEB.rglob("*.py"))


def _code_text(path: Path) -> str:
    """File text minus docstrings and `#` comment lines (code usage only)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'"""(?!").*?"""', "", text, flags=re.DOTALL)
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )


# --- one escape door ---------------------------------------------------------------


def test_html_escaping_has_exactly_one_home_in_the_web_tree():
    offenders = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _web_modules()
        if "html.escape" in _code_text(path)
    )
    assert offenders == [DOOR.relative_to(REPO_ROOT).as_posix()], (
        "html.escape belongs to the one door (web/interface/text.py); "
        f"also found in {offenders}"
    )


def test_every_web_producer_escapes_through_the_same_object():
    assert esc is text.esc
    assert render._esc is text.esc  # the interface renderer
    assert handoff._esc is text.esc  # the handoff copy
    assert views._esc is text.esc  # the page layer (via _shared's re-export)
    assert web_health.esc is text.esc  # the Health guidance renderer


def test_the_door_escapes_every_kind_of_value_totally():
    assert esc("<a href=\"x\">&'") == "&lt;a href=&quot;x&quot;&gt;&amp;&#x27;"
    assert esc(5) == "5"
    assert esc(None) == "None"


# --- one pluralization helper ------------------------------------------------------


def test_no_inline_plural_suffix_survives_in_the_web_tree():
    inline = re.compile(r"[\"']s[\"'] if .*?else")
    offenders = [
        f"{path.relative_to(REPO_ROOT).as_posix()}: {line.strip()}"
        for path in _web_modules()
        for line in _code_text(path).splitlines()
        if inline.search(line)
    ]
    assert offenders == [], f"inline plural agreement left — use plural(): {offenders}"


def test_count_producers_inflect_through_the_one_helper():
    for path in COUNT_PRODUCERS:
        assert "plural(" in path.read_text(encoding="utf-8"), path


def test_plural_helper_agrees_with_its_count():
    assert (plural(0), plural(1), plural(2)) == ("s", "", "s")
    # The irregular pairs the tree needed: match/matches, falls/fall — an
    # explicit pair whenever the suffix is not the plain one.
    assert (plural(1, "es", ""), plural(2, "es", "")) == ("es", "")
    assert (plural(1, "s", ""), plural(3, "s", "")) == ("s", "")


# --- the resources card reads its window through the joined view --------------------


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """The seed curriculum with one resource on one available node.

    Verified ten days before :data:`TODAY`: inside the seed's 180-day window,
    outside a one-day one — so only the window decides the status.
    """
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    _write_yaml(
        tmp_path,
        "graph/resources.yaml",
        {
            "resources": [
                {
                    "id": "fixture-course",
                    "url": "https://example.test/course",
                    "cost": "free",
                    "supports": [NODE_A],
                    "last_verified": VERIFIED_ON,
                }
            ]
        },
    )
    return tmp_path


def _policies_with_window(window: int):
    """The real policy seed, with one in-memory window override."""

    def load(root: Path) -> dict[str, dict]:
        docs = dict(load_policy_docs(root))
        docs["resource_verification.yaml"] = {"stale_after_days": window}
        return docs

    return load


def _resources_card(root: Path, *, window: int | None = None):
    if window is None:
        view = load_context_lenient(root)
    else:
        loaders = Loaders(load_policies=_policies_with_window(window))
        view = load_context_lenient(root, loaders=loaders)
    card = web_health.derive_study_guidance(view, TODAY).cards[-1]
    assert card.title == "Study resources"  # the §C-ter card order is locked
    return card


def test_resources_card_follows_the_window_the_joined_view_carries(repo):
    # The file on disk keeps the seed window; the narrowing exists only in the
    # joined view's policy document.
    assert load_policy_doc(repo, "resource_verification.yaml")["stale_after_days"] == 180

    assert _resources_card(repo).why == web_health.RESOURCES_HEALTHY
    narrowed = _resources_card(repo, window=1)
    # The singular branch is the card's locked copy verbatim (this ticket keeps
    # output byte-identical); only the agreement suffix is the helper's.
    assert narrowed.why == (
        "1 of 1 supporting material need re-checking (broken or stale)."
    )
    assert narrowed.links[0][1] == f"/nodes/{NODE_A}"


def test_resources_card_does_not_re_read_the_policy_seed():
    source = (WEB / "health.py").read_text(encoding="utf-8")
    assert "view.policy.resource_stale_after_days" in source
    assert "resource_verification.yaml" not in source
    assert "view.policies" not in source


# --- date-prefix parsing -----------------------------------------------------------


def test_date_prefix_parsing_is_one_function():
    assert web_health.parse_date is parse_date
    assert not hasattr(web_health, "_as_date")
    inline = re.compile(r"fromisoformat\(.*\[:10\]")
    offenders = [
        f"{path.relative_to(REPO_ROOT).as_posix()}: {line.strip()}"
        for path in _web_modules()
        for line in _code_text(path).splitlines()
        if inline.search(line)
    ]
    assert offenders == [], f"a second date-prefix parser appeared: {offenders}"
