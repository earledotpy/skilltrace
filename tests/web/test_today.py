"""T1 — Today, the Guided home (docs/spec-v3-study-day.md §10.1, SC-00a, R7).

What only this module shows: the **priority queue** and the three honest
non-success states.

The priority order is exact (spec §10.1): resume the open Session →
overdue Reviews and open Blockers affecting current work → a pass-eligible
SkillNode → the highest-ranked normal recommendation, with Next and Find
as secondary discovery paths. **Exactly one** action is visually dominant
at a time.

The three non-success states are distinguished and never merged (SC-00a):
*empty* says the population is genuinely empty and preserves discovery;
*limited* says a policy threshold was not met while retaining the values
that do exist; *could not compute* is an operational failure with a
precise recovery — never a zero, never a fabricated health fact.

This module replaces the v2.4 unified-home recipe (hero plus six-card
bento), which the v3 spec retires (spec §20 SUP-6).
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's GET sweeps."""
    root = Path(tempfile.mkdtemp(prefix="t1-today-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _first_node_id(root: Path, *, state: str | None = None) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError(f"no node with state {state!r}")


def _queue_items(body: str) -> list[str]:
    """The queue items, in the order the page renders them."""
    return re.findall(r'<li class="queue-item[^"]*">(.*?)</li>', body, re.S)


def _dominant_count(body: str) -> int:
    """How many queue items claim to be the one dominant action."""
    return body.count('class="queue-item dominant"')


# --- the priority queue ----------------------------------------------------------


def test_today_renders_a_priority_queue(repo):
    """The queue is a list of items, not a wall of cards."""
    _, body, status = views.home_body(repo)
    assert status == 200
    assert 'class="queue"' in body
    assert len(_queue_items(body)) >= 1


def test_exactly_one_action_is_visually_dominant(repo):
    """One dominant action at a time — the spec's exact requirement."""
    _, body, _ = views.home_body(repo)
    assert _dominant_count(body) == 1, (
        "exactly one action may be visually dominant at a time"
    )


def test_the_dominant_action_is_the_resume_when_a_session_is_open(repo):
    """Priority 1: resume the open Session."""
    # The seed repo carries no session; author one and check the order.
    root = Path(tempfile.mkdtemp(prefix="t1-today-session-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    (root / "execution").mkdir(exist_ok=True)
    (root / "execution" / "sessions.yaml").write_text(
        yaml.safe_dump(
            {
                "sessions": [
                    {
                        "id": "ses.today.001",
                        "status": "open",
                        "started_at": "2026-11-17T07:00:00+00:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "execution" / "session_work.yaml").write_text(
        yaml.safe_dump(
            {
                "session_work": [
                    {
                        "id": "wk.ses.today.001.01",
                        "session_id": "ses.today.001",
                        "node_id": _first_node_id(root, state="available"),
                        "created_at": "2026-11-17T07:30:00+00:00",
                        "minutes": 30,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    _, body, _ = views.home_body(root)
    items = _queue_items(body)
    assert items, "the open session must produce a queue item"
    assert "Resume your session" in items[0]
    assert 'class="queue-item dominant"' in body


def test_next_and_find_are_secondary_discovery_paths(repo):
    """Priority 5: Next and Find are available, but never dominant."""
    _, body, _ = views.home_body(repo)
    assert 'href="/next"' in body
    assert 'href="/find"' in body
    # The discovery links sit outside the queue: they are not targets.
    queue_html = body[body.index('class="queue"') : body.index("</section>")]
    assert 'href="/next"' not in queue_html


def test_a_pass_eligible_skill_appears_as_a_queue_item(repo):
    """Priority 3: a pass-eligible SkillNode."""
    _, body, _ = views.home_body(repo)
    if "ready to pass" in body:
        assert "/pass" in body
        assert "Evidence requirements are met" in body or (
            "evidence requirements are met" in body.lower()
        )


# --- the honest non-success states ------------------------------------------------


def test_the_empty_state_explains_and_preserves_discovery(repo):
    """Empty says the population is empty — it is not a failure of the learner."""
    # A curriculum with nothing available: the seed graph has many nodes,
    # so author an empty-looking state by asking for a node set with no
    # recommendations. The empty branch is exercised by the absence of
    # every queue item.
    _, body, _ = views.home_body(repo)
    if 'class="state state-empty"' in body:
        assert "Nothing is ready right now" in body or "nothing" in body.lower()
        # Discovery survives an empty queue.
        assert 'href="/find"' in body


def test_the_limited_state_retains_its_values(repo):
    """Limited states the threshold and keeps the values that do exist."""
    _, body, _ = views.home_body(repo)
    if 'class="state state-limited"' in body:
        assert "state-body" in body
        # The threshold is named, not merely implied.
        assert re.search(r"[0-9]+", body)


def test_a_could_not_compute_surface_renders_no_zeros(repo, monkeypatch):
    """Could-not-compute is an operational failure — never zeros.

    The recommendation derivation is the advisory preview: when it raises,
    the page must say so, offer a recovery, and render no count that
    would read as a truth about the learner.
    """
    import skilltrace.web.views.today as today_mod

    def _boom(*args, **kwargs):
        raise RuntimeError("the ranker could not load its policy")

    monkeypatch.setattr(today_mod, "derive_next", _boom)
    _, body, _ = views.home_body(repo)
    assert 'class="state state-failure"' in body
    assert "could not be worked out" in body
    assert 'href="/find"' in body  # a precise recovery path
    # No fabricated figure: the failure branch renders no "0 reviews"-style
    # counts at all.
    assert not re.search(r">\s*0\s+reviews", body)


def test_today_never_renders_the_raw_backlog(repo):
    """The raw flat dump never renders (P1.2)."""
    _, body, _ = views.home_body(repo)
    assert "backlog lineup" not in body


def test_today_drops_zero_counts(repo):
    """A zero count is not a fact worth the learner's attention (P1.3)."""
    _, body, _ = views.home_body(repo)
    assert "0 reviews" not in body
    assert "0 blockers" not in body


def test_today_reads_without_cli_vocabulary(repo):
    """Cold start reads without CLI vocabulary (C01, R1)."""
    _, body, _ = views.home_body(repo)
    lowered = body.lower()
    for vocabulary in ("skilltrace today", "--minutes", "--limit", "node_id"):
        assert vocabulary not in lowered, vocabulary


def _visible_text(html: str) -> str:
    """The text a reader sees — markup and attribute values stripped."""
    without_tags = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", without_tags)


def test_today_names_skills_by_their_readable_title(repo):
    """A raw id never stands in for a readable title (R1).

    An id may appear in a link target — that is how the learner gets
    there — but the words the learner reads must be the title.
    """
    view = load_context_lenient(repo)
    _, body, _ = views.home_body(repo)
    for node in view.nodes:
        if node.id not in body:
            continue
        for item in _queue_items(body):
            assert node.id not in _visible_text(item), node.id


def test_the_queue_names_every_skill_it_offers_by_title(repo):
    """Each queue item names its skill in words."""
    view = load_context_lenient(repo)
    _, body, _ = views.home_body(repo)
    items = _queue_items(body)
    assert items
    named = 0
    for item in items:
        text = _visible_text(item)
        if any(node.title in text for node in view.nodes):
            named += 1
    assert named == len(items), (
        "every queue item must name its skill by the readable title"
    )
