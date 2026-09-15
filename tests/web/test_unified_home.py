"""S3 — the unified single-page home (§A as amended, map #252, ticket #254).

What only the amended home can show:

* the hero focus viewport — double-weight (full grid span, 30px display
  heading, 28px padding, accent left border), carrying the page's only
  primary CTA in the pronoun, state-honest form (P1.1a/P1.1b as amended);
* the six-card bento at the dense register — queue, pressure, spine, week,
  session history, browse — every card links-only;
* the dense band literals in use (20/28/14/20, 1120px rich shell,
  20px bento gutters, section gap > intra-card gap);
* focus named once as a heading plus at most one locator repetition;
* celebration past-tense/factual at real events only (CSS-only keyframe).

``pytest`` green, no ``<script>`` (the per-route budget gate covers it).
"""

from __future__ import annotations

import re
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest
import yaml

from skilltrace.commands.today import derive_today
from skilltrace.context import load_context_lenient
from skilltrace.execution.overdue import utc_today
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

_BLOCK_MARKERS = (
    '<div class="hero">',
    '<div class="bento-card queue">',
    '<div class="bento-card pressure">',
    '<div class="bento-card spine">',
    '<div class="bento-card week">',
    '<div class="bento-card history">',
    '<div class="bento-card browse">',
)


def _seed_repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's GET sweeps."""
    return _seed_repo(Path(tempfile.mkdtemp(prefix="s3-unified-home-")))


@pytest.fixture
def fresh_repo(tmp_path: Path) -> Path:
    return _seed_repo(tmp_path)


def _focus(repo: Path):
    view = load_context_lenient(repo)
    model = derive_today(view, repo, minutes=30)
    assert model.focus_node_id, "seed carries a focus for the unified-home sweep"
    return view, model, view.node_map[model.focus_node_id]


def _home(repo: Path) -> str:
    title, body, status = views.home_body(repo)
    assert (title, status) == ("Today", 200)
    return body


def _block(body: str, marker: str) -> str:
    """One home block's markup, from its marker to the next block in DOM order."""
    start = body.index(marker)
    order = _BLOCK_MARKERS.index(marker)
    ends = [
        body.index(m, start + 1)
        for m in _BLOCK_MARKERS[order + 1 :]
        if body.find(m, start + 1) != -1
    ]
    ends.append(body.index("</div>\n</div>\n</div>", start))  # bento + shell close
    return body[start : min(ends)]


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- The seven blocks (hero + 6 bento; ≤8 cap, amended P5.3) -----------------------


def test_home_is_the_hero_plus_six_bento_blocks(repo):
    body = _home(repo)
    assert body.count('<div class="hero">') == 1
    for name in ("queue", "pressure", "spine", "week", "history", "browse"):
        assert f'<div class="bento-card {name}">' in body, name
    assert body.count('<div class="bento-card ') == 6
    blocks = body.count('<div class="hero">') + body.count('<div class="bento-card ')
    assert blocks == 7  # ≤ 8 cap (amended P5.3)


# --- One primary CTA, pronoun + state-honest (P1.1a/P1.1b) -------------------------


def test_exactly_one_primary_cta_pronoun_and_state_honest(repo):
    body = _home(repo)
    assert body.count('class="btn primary"') == 1
    view, model, focus = _focus(repo)
    assert "Start studying" in body  # the pronoun form at zero sessions
    assert f"Start studying {focus.title}" not in body  # never `Start <title>`
    assert "Start this session" not in body  # the hero CTA is the pronoun form


def test_bento_cards_are_links_only(repo):
    body = _home(repo)
    for name in ("queue", "pressure", "spine", "week", "history", "browse"):
        section = _block(body, f'<div class="bento-card {name}">')
        assert "<form" not in section, name
        assert "btn primary" not in section, name
        assert "btn secondary" not in section, name


# --- One blessed grouped-count table; disclosures off the primary path --------------


def test_one_blessed_grouped_count_table_with_live_counts(repo):
    body = _home(repo)
    assert body.count("<table") == 1
    browse = _block(body, '<div class="bento-card browse">')
    assert "<table" in browse
    assert ">Track</th>" in browse
    assert ">Ready</th>" in browse
    assert ">Locked</th>" in browse
    view = load_context_lenient(repo)
    available = sum(1 for n in view.nodes if view.store.state_of(n.id) == "available")
    locked = sum(1 for n in view.nodes if view.store.state_of(n.id) == "locked")
    assert f"{available} ready, {locked} locked" in browse  # live reads, not hardcoded


def test_no_disclosures_on_home(repo):
    assert "<details" not in _home(repo)


def test_browse_links_to_the_finder(repo):
    browse = _block(_home(repo), '<div class="bento-card browse">')
    assert 'href="/nodes/jump"' in browse


# --- Focus named once as a heading (+ one locator repetition at most) ---------------


def test_focus_named_once_as_heading_plus_one_locator(repo):
    view, model, focus = _focus(repo)
    title = focus.title
    body = _home(repo)
    assert body.count('<p class="display">') == 1  # the heading names it once
    assert body.count(title) <= 2  # + one locator repetition at most
    hero = _block(body, '<div class="hero">')
    assert title in hero
    assert title not in _block(body, '<div class="bento-card queue">')


# --- Queue: ranked preview rows naming other nodes ----------------------------------


def test_queue_rows_name_other_nodes_and_link_the_full_ranking(repo):
    view, model, focus = _focus(repo)
    body = _home(repo)
    queue = _block(body, '<div class="bento-card queue">')
    assert 'href="/next"' in queue  # the full ranking lives on /next
    assert queue.count('class="queue-row"') >= 1
    assert focus.title not in queue  # rows name *other* nodes
    assert 'href="/nodes/' in queue  # rows are links


# --- Pressure: one calm line, honest blanks at zero ---------------------------------


def test_pressure_is_one_calm_line_with_honest_blanks(repo):
    body = _home(repo)
    pressure = _block(body, '<div class="bento-card pressure">')
    assert "Nothing is waiting" in pressure  # the zero state, honestly blank
    assert "0 reviews" not in body  # zero-count pills dropped (P1.3)
    for phrase in ("you're behind", "don't break", "keep it up", "streak"):
        assert phrase not in body.lower()


def test_pressure_stays_calm_and_raw_backlog_never_renders(fresh_repo):
    view = load_context_lenient(fresh_repo)
    focus_id = sorted(view.nodes, key=lambda n: n.id)[0].id
    _write_yaml(
        fresh_repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.01",
                    "node_id": focus_id,
                    "status": "open",
                    "description": "stuck on the derivation",
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    body = _home(fresh_repo)
    pressure = _block(body, '<div class="bento-card pressure">')
    assert "1 open blocker" in pressure  # the calm count line
    assert "stuck on the derivation" not in body  # raw backlog never renders
    assert "blk.01" not in body


# --- Spine: pronoun-headed, downstream named ----------------------------------------


def test_spine_is_pronoun_headed_and_names_downstream(repo):
    view, model, focus = _focus(repo)
    spine = _block(_home(repo), '<div class="bento-card spine">')
    assert "What your focus opens" in spine
    kids = [
        e.target
        for e in view.edges
        if e.source == focus.id
        and e.active
        and e.edge_type in ("hard_prerequisite", "soft_prerequisite")
    ]
    if kids:
        titles = [view.node_map[t].title for t in kids if t in view.node_map]
        assert titles, "the seed focus opens downstream skills"
        for t in titles[:4]:
            assert f">{t}</a>" in spine  # downstream named and linked
        assert f"From {focus.title}" in spine  # the one locator repetition
    else:
        assert "unlock" in spine.lower()  # the honest empty spine


# --- Week: strip + honest blanks + the mirror line ----------------------------------


def test_week_strip_seven_days_with_honest_blanks(repo):
    week = _block(_home(repo), '<div class="bento-card week">')
    assert week.count('<div class="day') == 7
    assert ">\u2014</div>" in week  # honest blanks
    assert 'class="day today"' in week
    today = utc_today()
    monday = today - timedelta(days=today.weekday())
    names = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    assert f"<b>{names[monday.weekday()]} {monday.day}</b>" in week
    # The mirror line, never a metronome (P1.7).
    assert "day so far" in week or "days so far" in week or "Nothing logged" in week
    for phrase in ("missed", "owed", "don't break", "keep it up", "streak"):
        assert phrase not in week.lower()


# --- Session history: empty state + format preview; real lines when present ---------


def test_session_history_empty_state_with_format_preview(repo):
    history = _block(_home(repo), '<div class="bento-card history">')
    assert "No sessions yet" in history
    assert "what you worked on" in history  # the format preview
    for banned in (".yaml", "execution/", "session_work"):
        assert banned not in history  # engine file paths never render (P3.1)


def test_session_history_reads_real_sessions_when_present(fresh_repo):
    view = load_context_lenient(fresh_repo)
    node_ids = sorted(n.id for n in view.nodes)[:2]
    today = utc_today()
    yesterday = today - timedelta(days=1)
    _write_yaml(
        fresh_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.hist.001",
                    "status": "completed",
                    "started_at": f"{yesterday.isoformat()}T10:00:00+00:00",
                    "ended_at": f"{yesterday.isoformat()}T10:40:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        fresh_repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "work.hist.001",
                    "session_id": "sess.hist.001",
                    "node_id": node_ids[0],
                    "created_at": f"{yesterday.isoformat()}T10:05:00+00:00",
                    "minutes": 20,
                },
                {
                    "id": "work.hist.002",
                    "session_id": "sess.hist.001",
                    "node_id": node_ids[1],
                    "created_at": f"{yesterday.isoformat()}T10:25:00+00:00",
                    "minutes": 12,
                },
            ]
        },
    )
    history = _block(_home(fresh_repo), '<div class="bento-card history">')
    assert "No sessions yet" not in history
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    assert f"{yesterday.day} {months[yesterday.month - 1]}" in history  # the date
    assert "32 min" in history  # the minutes, summed from live work records
    for node_id in node_ids:
        assert f">{view.node_map[node_id].title}</a>" in history  # node titles linked
    assert "sess.hist." not in history  # raw record ids never render (P3.1)


# --- Hero: resumable state stays honest ----------------------------------------------


def test_hero_resumes_and_closes_the_open_session(fresh_repo):
    today = utc_today()
    _write_yaml(
        fresh_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.open.001",
                    "status": "open",
                    "started_at": f"{today.isoformat()}T08:00:00+00:00",
                }
            ]
        },
    )
    body = _home(fresh_repo)
    assert "Session open since" in body
    assert 'action="/session/close"' in body  # the close affordance rides the hero
    assert 'class="btn secondary"' in body  # close is never the primary CTA
    assert "Continue where you left" in body  # the pronoun, resumable CTA
    assert "/start" not in body  # a second start would be refused — omitted


# --- The dense register, in use (20/28/14/20, 1120px shell) --------------------------


def test_home_uses_the_locked_dense_register():
    style = views._STYLE
    # The rich shell is 1120px (amended §B); the home wrap uses it.
    assert "main.wrap:has(.home-rich){max-width:var(--shell-rich)}" in style
    # The bento grid: section gap 28px between blocks, 20px gutters between cards.
    assert (
        "gap:var(--section-gap-dense) var(--bento-gutter-dense)" in style
    ), "the bento grid must carry the locked section/gutter gaps"
    # The hero is double-weight: full grid span, 28px padding, accent left
    # border, 30px display heading.
    assert ".hero{grid-column:1/-1" in style
    hero_rule = re.search(r"\.hero\{[^}]*\}", style).group(0)
    assert "border-left:4px solid var(--accent)" in hero_rule
    assert "padding:var(--card-pad)" in hero_rule  # 28px
    assert ".hero .display{font-size:30px}" in style
    # Bento cards sit at the dense 20px pad with the 14px intra-card rhythm.
    assert "padding:var(--card-pad-dense)" in style
    assert "var(--intra-gap-dense)" in style
    # Section gap > intra-card gap (28 > 14).
    section = int(re.search(r"--section-gap-dense:(\d+)px", style).group(1))
    intra = int(re.search(r"--intra-gap-dense:(\d+)px", style).group(1))
    assert section > intra


# --- Celebration: CSS-only keyframe at real events only ------------------------------


def test_celebration_is_css_only_at_real_events_only(repo):
    style = views._STYLE
    assert "@keyframes" in style  # the CSS-only keyframe
    assert re.search(r"\.banner\.success\{[^}]*animation:", style), (
        "the success banner carries the CSS-only celebration"
    )
    body = _home(repo)
    assert 'class="banner success"' not in body  # nothing fires on a plain GET
    assert "Congratulations" not in body
    for phrase in ("you're ahead", "your memory is", "ahead of"):
        assert phrase not in body.lower()  # never comparative, never predictive

