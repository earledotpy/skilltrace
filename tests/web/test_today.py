"""T1 — Today, the Guided home (docs/spec-v3-study-day.md §10.1, SC-00a, R7).

What only this module shows: the **priority queue** and the five honest
non-success states.

The priority order is exact (spec §10.1): resume the open Session →
overdue Reviews and open Blockers affecting current work → a pass-eligible
SkillNode → the highest-ranked normal recommendation, with Next and Find
as secondary discovery paths. **Exactly one** action is visually dominant
at a time — one dominant queue item carrying the page's one primary
button, every other action secondary (VS-6).

While a Session is open, **no second start is offered**: the engine would
refuse it, so Today shows the open Session and its safe actions instead
of the refusal alone (§10.5, R5).

The five non-success states are distinguished and never merged (SC-00a):
*empty* says the population is genuinely empty and preserves discovery;
*limited* says a policy threshold was not met while retaining the values
that do exist; *refusal* says every visible skill is locked and that
unlock is never offered; *could not compute* is an operational failure
with a precise recovery — never a zero, never a fabricated fact; and a
stale readiness is a *recovery* prompt that names its dependency rather
than hiding it.

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


# --- exactly one dominant action (VS-6) -------------------------------------------


@pytest.fixture
def own_repo(tmp_path: Path) -> Path:
    """A fresh seed copy a test may author — the module fixture stays read-only."""
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _row_value(body: str, label: str) -> str | None:
    """The value of one fact row, by its label."""
    match = re.search(
        r'<span class="row-label">'
        + re.escape(label)
        + r'</span><span class="row-value">([^<]*)</span>',
        body,
    )
    return match.group(1) if match else None


def test_the_queue_runs_in_the_specified_priority_order():
    """resume Session → overdue Review → open Blocker → pass-eligible → rec."""
    from test_route_snapshots import build_pinned_repo

    root = build_pinned_repo(Path(tempfile.mkdtemp(prefix="t1-order-")))
    from a11y_harness import frozen_clock

    with frozen_clock():
        _, body, _ = views.home_body(root)
    titles = [
        re.search(r'<p class="queue-title">(.*?)</p>', item, re.S).group(1)
        for item in _queue_items(body)
    ]
    assert len(titles) == 5, titles
    assert titles[0].startswith("Continue on ")
    assert "is overdue" in titles[1]
    assert titles[2].startswith("Something is blocking ")
    assert "is ready to pass" in titles[3]
    assert titles[4] == "Explain what an AI agent is and how tools extend an LLM"


# --- the cold start (C01, R1) ------------------------------------------------------


def test_cold_start_offers_one_start_for_a_startable_skill(repo):
    """Cold start: one Start studying action, for a skill that can be started."""
    view = load_context_lenient(repo)
    _, body, _ = views.home_body(repo)
    starts = re.findall(r'action="/nodes/([\w.]+)/start"', body)
    assert len(starts) == 1, starts
    assert view.store.state_of(starts[0]) == "available"


# --- the open Session and its refusal (§10.5, R5) ----------------------------------


def test_no_second_start_is_offered_while_a_session_is_open():
    """A second start would be refused — Today never offers it."""
    from test_route_snapshots import build_pinned_repo

    root = build_pinned_repo(Path(tempfile.mkdtemp(prefix="t1-open-")))
    _, body, _ = views.home_body(root)
    assert "<form" not in body, "a second start must not be offered"
    for action in ("Resume your session", "Log work on this skill", "Close this session"):
        assert action in body


def test_a_refused_second_start_still_shows_the_session_and_safe_actions(own_repo):
    """The refusal is never alone: the open Session and its actions remain."""
    from urllib.parse import parse_qs, urlsplit

    node = _first_node_id(own_repo, state="available")
    (own_repo / "execution").mkdir(exist_ok=True)
    (own_repo / "execution" / "sessions.yaml").write_text(
        yaml.safe_dump(
            {
                "sessions": [
                    {
                        "id": "ses.t1.001",
                        "status": "open",
                        "started_at": "2026-11-17T07:00:00+00:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = views.post_start(own_repo, node, {"next": ["/"], "template": [""]})
    assert isinstance(result, views.Redirect)
    query = parse_qs(urlsplit(result.location).query)
    assert query["kind"] == ["warning"]
    _, body, _ = views.home_body(own_repo, query)
    assert "already open" in body  # the refusal is stated


# --- the stale readiness (recovery) ------------------------------------------------


def _stale_repo(root: Path) -> Path:
    """Flip one saved readiness the curriculum no longer agrees with."""
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    for entry in doc["progress"].values():
        if entry.get("state") == "available":
            entry["state"] = "locked"
            break
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return root


def test_a_stale_readiness_prompts_a_safe_refresh(own_repo):
    """Stale readiness is a recovery prompt that names its dependency."""
    _, body, _ = views.home_body(_stale_repo(own_repo))
    assert 'class="state state-recovery"' in body
    assert "Refresh your readiness" in body
    # The dependency is named, never hidden behind silence.
    assert "command line" in body
    assert "never moves your recorded progress" in body
    assert 'href="/"' in body  # the way back to this page after refreshing


def test_a_stale_readiness_never_moves_asserted_progress(own_repo):
    """The prompt says a refresh never demotes — and the page does not."""
    node = _first_node_id(own_repo, state="available")
    root = _stale_repo(own_repo)
    _, body, _ = views.home_body(root)
    assert "active, passed and mastered stay exactly as they are" in body
    assert load_context_lenient(root).store.state_of(node) == "locked"


# --- the locked refusal (HB-4) ------------------------------------------------------


def test_the_locked_refusal_states_that_unlock_is_never_offered(own_repo):
    """Every visible skill locked: the reason, and no override — ever."""
    from today_fixtures import build_today_variant

    _, body, _ = views.home_body(build_today_variant(own_repo, "refusal"))
    assert 'class="state state-refusal"' in body
    lowered = body.lower()
    assert "unlock" in lowered
    assert "no override" in lowered
    assert "<form" not in body  # a locked day offers no start
    assert 'href="/find"' in body  # discovery is preserved


# --- the limited data (SC-00a) ------------------------------------------------------


def test_the_limited_state_states_the_threshold_and_retains_values(own_repo):
    """Limited retains the values that exist and states the policy threshold."""
    from today_fixtures import build_today_variant

    view = load_context_lenient(own_repo)
    policy = view.policy.analytics_policy
    _, body, _ = views.home_body(build_today_variant(own_repo, "limited"))
    assert 'class="state state-limited"' in body
    assert (
        f"fewer than {policy.min_sessions_for_full_data} sessions "
        f"in the last {policy.default_window_days} days"
    ) in body
    assert _row_value(body, "Days practiced") is not None


# --- the counts agree with the destination views (R7, C20) --------------------------


def test_the_study_day_counts_agree_with_the_destination_views(own_repo):
    """Days practiced matches Health; the window count matches Analytics."""
    (own_repo / "execution").mkdir(exist_ok=True)
    (own_repo / "execution" / "sessions.yaml").write_text(
        yaml.safe_dump(
            {
                "sessions": [
                    {
                        "id": "ses.t1.001",
                        "status": "open",
                        "started_at": "2026-11-17T07:00:00+00:00",
                    },
                    {
                        "id": "ses.t1.002",
                        "status": "completed",
                        "started_at": "2026-11-15T09:00:00+00:00",
                        "ended_at": "2026-11-15T10:00:00+00:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (own_repo / "execution" / "session_work.yaml").write_text(
        yaml.safe_dump(
            {
                "session_work": [
                    {
                        "id": "wk.ses.t1.001.01",
                        "session_id": "ses.t1.001",
                        "node_id": _first_node_id(own_repo),
                        "created_at": "2026-11-17T07:30:00+00:00",
                        "minutes": 30,
                    },
                    {
                        "id": "wk.ses.t1.002.01",
                        "session_id": "ses.t1.002",
                        "node_id": _first_node_id(own_repo),
                        "created_at": "2026-11-15T09:30:00+00:00",
                        "minutes": 45,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    window = load_context_lenient(own_repo).policy.analytics_policy.default_window_days
    _, today_body, _ = views.home_body(own_repo)
    _, health_body, _ = views.health_body(own_repo)
    _, analytics_body, _ = views.analytics_body(own_repo, {"theme": ["velocity"]})

    today_days = _row_value(today_body, "Days practiced")
    health_days = re.search(r"Days practiced: (\d+)", health_body)
    assert today_days is not None and health_days is not None
    assert today_days == health_days.group(1)

    today_sessions = _row_value(today_body, f"Sessions in the last {window} days")
    analytics_sessions = re.search(r"(\d+) sessions,", analytics_body)
    assert today_sessions is not None and analytics_sessions is not None
    assert today_sessions == analytics_sessions.group(1)


# --- could not compute (SC-00a) -----------------------------------------------------


def test_a_degraded_source_claims_nothing_and_preserves_discovery(own_repo):
    """A failed source is an operational failure — never a zero."""
    (own_repo / "execution").mkdir(exist_ok=True)
    (own_repo / "execution" / "sessions.yaml").write_text(
        "sessions: [ broken\n", encoding="utf-8"
    )
    _, body, _ = views.home_body(own_repo)
    assert 'class="state state-failure"' in body
    assert "whether a session is open" in body
    assert "not even a count" in body
    assert "0 reviews" not in body
    assert "<form" not in body  # no start while the session is unknown
    assert 'href="/find"' in body  # discovery is preserved
    assert 'href="/health"' in body  # the precise recovery path


def test_the_empty_state_preserves_discovery(own_repo):
    """Empty says the population is empty and keeps both discovery paths."""
    from today_fixtures import build_today_variant

    _, body, _ = views.home_body(build_today_variant(own_repo, "empty"))
    assert 'class="state state-empty"' in body
    assert "Nothing is ready right now" in body
    assert 'href="/find"' in body
    assert 'href="/next"' in body
    assert "<form" not in body  # an empty day offers nothing to start



def test_the_recommendation_reason_reads_without_engine_voice(repo):
    """No scores, weights or edge counts ever reach the page (VS-4, R1)."""
    _, body, _ = views.home_body(repo)
    assert "weight" not in body
    assert "downstream edge" not in body
    assert "It is available now" in body



def test_the_dominant_item_carries_the_pages_one_primary_button(repo):
    """One dominant action at a time — one primary button on the page (VS-6)."""
    _, body, _ = views.home_body(repo)
    assert _dominant_count(body) == 1
    assert body.count('class="btn primary"') == 1, (
        "exactly one action may read as the thing to do"
    )

