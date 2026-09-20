"""Golden route-body snapshots — every served GET route, byte-exact (#312).

What only this module shows: the exact HTML every served GET route and every
step/modal body renders for one pinned learner state. The goldens live beside
this module in ``snapshots/*.html``; a later structural refactor of the web
layer can prove "structure changed, output didn't" by diffing against them,
and any byte that moves fails with a unified diff naming the file.

Two rules keep the goldens stable, per ``docs/agents/fixture-clock.md``:

* **Fixture clock.** The serve shell has no clock context, so this harness
  supplies one: the single date funnel (``execution.overdue.utc_today``) is
  pinned to :data:`FROZEN_DAY` in every module that bound it, and the two
  read-path modules that call ``datetime.now`` directly
  (``commands.today``, ``commands._common``) get a frozen ``datetime``. No
  body can follow the wall clock.
* **Stable seeding.** The learner-mutable stores (``graph/state.yaml`` and the
  ``execution/*.yaml`` records) are authored here from fixed dates relative to
  the frozen clock, so the suite neither reads nor churns with the learner's
  own study activity. The curriculum half (nodes, edges, gates, specs,
  resources, policy) is a read-only copy of the seed repo.

Routes covered (the router in ``web/handler.py`` serves exactly these bodies):

======================  ==============================================
route                   case
======================  ==============================================
``GET /``               ``home``
``GET /next``           ``next``, ``next-locked`` (``?locked=1``)
``GET /nodes/jump``     ``finder``, ``finder-query`` (``?q=…``)
``GET /nodes/{id}``     ``node``
``GET /health``         ``health``
``GET /analytics``      ``analytics-velocity``, ``-blockers``, ``-reviews``,
                        ``-evidence`` (one per theme)
``GET /nodes/{id}/pass``  ``pass``
``GET /nodes/{id}/master``  ``master``
``GET /nodes/{id}/master/confirm``  ``master-confirm``
anything else           ``error-404`` (the one unified error body)
======================  ==============================================

The ``/nodes/jump?node_id=…`` jump and every POST are redirects or write
routes, not rendered bodies — they are pinned by the write suites instead.
``next`` and ``next-locked`` render the same bytes today (the locked half is a
card, not a flag); both are pinned so the flag's behavior stays on record.

Updating goldens (review the diff before committing)::

    SKILLTRACE_UPDATE_SNAPSHOTS=1 python -m pytest tests/web/test_route_snapshots.py
"""

from __future__ import annotations

import difflib
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"
UPDATE_ENV = "SKILLTRACE_UPDATE_SNAPSHOTS"

# The pinned "today" and "now" every body is rendered against. The wall clock
# is never consulted; the seed records below are all offsets from these.
FROZEN_DAY = date(2026, 11, 17)
FROZEN_MOMENT = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)
FROZEN_STAMP = FROZEN_MOMENT.isoformat(timespec="seconds")

# Immutable node ids (CONTEXT.md: node ids are never reused) chosen to cover
# the rendered state halves: one active gated node, one passed node, one
# sibling left at derived readiness.
NODE_ACTIVE = "data.pandas.dataframe_basics_01"
NODE_PASSED = "programming.python.variables_01"
NODE_THIRD = "data.sql.select_basics_01"


# --- The pinned repo: curriculum copied, learner stores authored -------------


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def _ago(**fields) -> str:
    return _iso(FROZEN_MOMENT - timedelta(**fields))


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _pin_progress(path: Path) -> None:
    """Author the progress store: derived readiness plus two asserted states.

    The store is cleared and then filled through the engine's own readiness
    writer, so every node carries the state ``sync`` would record (the locked
    default included — a half-populated store would draw the liveness
    warning). The two asserted entries are *authored fixture data* — a
    stand-in learner's starting store, exactly as the other web suites seed
    state; no engine pass/master path runs here (see AGENTS.md safety rule).
    """
    from skilltrace.graph.edges import load_edges
    from skilltrace.graph.nodes import load_nodes
    from skilltrace.graph.readiness import sync_readiness
    from skilltrace.graph.state import load_state, save_state

    (path / "graph" / "state.yaml").write_text("progress: {}\n", encoding="utf-8")
    store = load_state(path)
    nodes = load_nodes(path)
    sync_readiness(nodes, load_edges(path), store, now=FROZEN_STAMP)
    for node in nodes:
        if node.id not in store.entries:
            store.write_readiness(node.id, "locked", now=FROZEN_STAMP)
    save_state(store, path)

    doc = yaml.safe_load((path / "graph" / "state.yaml").read_text(encoding="utf-8"))
    doc["progress"][NODE_ACTIVE] = {
        "state": "active",
        "changed_at": _ago(days=2),
        "transitions": {"active": _ago(days=2)},
    }
    doc["progress"][NODE_PASSED] = {
        "state": "passed",
        "changed_at": _ago(days=30),
        "transitions": {"active": _ago(days=40), "passed": _ago(days=30)},
    }
    _write_yaml(path, "graph/state.yaml", {"progress": doc["progress"]})


def _pin_execution(path: Path) -> None:
    """Author the execution records: one open session, history, blockers, reviews."""
    _write_yaml(
        path,
        "execution/sessions.yaml",
        {
            "sessions": [
                {"id": "ses.snapshot.001", "status": "open", "started_at": _ago(hours=2)},
                {
                    "id": "ses.snapshot.002",
                    "status": "completed",
                    "started_at": _ago(days=2),
                    "ended_at": _iso(FROZEN_MOMENT - timedelta(days=2) + timedelta(hours=1)),
                },
                {
                    "id": "ses.snapshot.003",
                    "status": "completed",
                    "started_at": _ago(days=9),
                    "ended_at": _iso(FROZEN_MOMENT - timedelta(days=9) + timedelta(hours=1)),
                },
                {
                    "id": "ses.snapshot.004",
                    "status": "completed",
                    "started_at": _ago(days=20),
                    "ended_at": _iso(FROZEN_MOMENT - timedelta(days=20) + timedelta(hours=1)),
                },
            ]
        },
    )
    _write_yaml(
        path,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "wk.ses.snapshot.001.01",
                    "session_id": "ses.snapshot.001",
                    "node_id": NODE_ACTIVE,
                    "created_at": _ago(minutes=90),
                    "notes": "drilled groupby on the sample frame",
                    "minutes": 45,
                },
                {
                    "id": "wk.ses.snapshot.002.01",
                    "session_id": "ses.snapshot.002",
                    "node_id": NODE_ACTIVE,
                    "created_at": _ago(days=2),
                    "notes": "read the selection docs",
                    "minutes": 30,
                },
                {
                    "id": "wk.ses.snapshot.003.01",
                    "session_id": "ses.snapshot.003",
                    "node_id": NODE_PASSED,
                    "created_at": _ago(days=9),
                    "notes": "variables practice",
                    "minutes": 25,
                },
                {
                    "id": "wk.ses.snapshot.004.01",
                    "session_id": "ses.snapshot.004",
                    "node_id": NODE_THIRD,
                    "created_at": _ago(days=20),
                    "notes": "select basics workout",
                    "minutes": 40,
                },
            ]
        },
    )
    _write_yaml(
        path,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.snapshot.001",
                    "node_id": NODE_ACTIVE,
                    "status": "open",
                    "description": "groupby output keeps surprising me",
                    "created_at": _ago(days=1),
                },
                {
                    "id": "blk.snapshot.002",
                    "node_id": NODE_PASSED,
                    "status": "resolved",
                    "description": "loop-variable scope confused me",
                    "created_at": _ago(days=12),
                    "resolved_at": _ago(days=10),
                    "resolution_summary": "re-read the scoping section and re-ran the drills",
                },
            ]
        },
    )
    _write_yaml(
        path,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rvw.snapshot.001",
                    "node_id": NODE_PASSED,
                    "status": "scheduled",
                    "scheduled_for": (FROZEN_DAY - timedelta(days=3)).isoformat(),
                    "created_at": _ago(days=30),
                },
                {
                    "id": "rvw.snapshot.002",
                    "node_id": NODE_THIRD,
                    "status": "scheduled",
                    "scheduled_for": FROZEN_DAY.isoformat(),
                    "created_at": _ago(days=14),
                },
                {
                    "id": "rvw.snapshot.003",
                    "node_id": NODE_ACTIVE,
                    "status": "scheduled",
                    "scheduled_for": (FROZEN_DAY + timedelta(days=7)).isoformat(),
                    "created_at": _ago(days=1),
                },
                {
                    "id": "rvw.snapshot.004",
                    "node_id": NODE_PASSED,
                    "status": "completed",
                    "scheduled_for": (FROZEN_DAY - timedelta(days=20)).isoformat(),
                    "created_at": _ago(days=50),
                    "completed_at": _ago(days=19),
                    "outcome": "satisfactory",
                    "result_summary": "recalled it cold",
                },
            ]
        },
    )
    _write_yaml(path, "execution/remediation_actions.yaml", {"remediation_actions": []})


def build_pinned_repo(path: Path) -> Path:
    """A read-only seed copy with the learner stores authored and pinned."""
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, path / dirname)
    _pin_progress(path)
    _pin_execution(path)
    return path


# --- The fixture clock: one funnel, every binding ---------------------------


class _FrozenDatetime(datetime):
    """A ``datetime`` whose ``now()`` is the frozen moment.

    Subclassing (rather than replacing) keeps ``fromisoformat`` and the
    constructor working for the modules that read stored timestamps.
    """

    @classmethod
    def now(cls, tz=None):
        return FROZEN_MOMENT if tz is not None else FROZEN_MOMENT.replace(tzinfo=None)


def _freeze_read_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin every module's view of the one date funnel to :data:`FROZEN_DAY`.

    Modules that did ``from ..execution.overdue import utc_today`` keep their
    own binding, so patching the defining module is not enough: the scan
    rebinds every module attribute that still points at the wall-clock
    funnel. The two read paths that call ``datetime.now`` directly
    (``commands.today`` for a session's open minutes, ``commands._common`` for
    liveness receipts) get :class:`_FrozenDatetime`.
    """
    from skilltrace import commands, execution

    original = execution.overdue.utc_today

    def frozen(*, clock=None):
        return FROZEN_DAY

    monkeypatch.setattr(execution.overdue, "utc_today", frozen)
    for module in list(sys.modules.values()):
        if getattr(module, "utc_today", None) is original:
            monkeypatch.setattr(module, "utc_today", frozen)
    monkeypatch.setattr(commands.today, "datetime", _FrozenDatetime)
    monkeypatch.setattr(commands._common, "datetime", _FrozenDatetime)


# --- The route table: one case per served body ------------------------------


@dataclass(frozen=True)
class RouteCase:
    """One served body: the route it answers, and how to render it."""

    name: str
    route: str
    title: str
    status: int
    render: Callable[[Path], tuple[str, str, int]]


CASES: tuple[RouteCase, ...] = (
    RouteCase("home", "GET /", "Today", 200, lambda r: views.home_body(r, {})),
    RouteCase("next", "GET /next", "Next", 200, lambda r: views.next_body(r, {})),
    RouteCase(
        "next-locked",
        "GET /next?locked=1",
        "Next",
        200,
        lambda r: views.next_body(r, {"locked": ["1"]}),
    ),
    RouteCase(
        "node",
        f"GET /nodes/{NODE_ACTIVE}",
        "Use basic Pandas DataFrame operations",
        200,
        lambda r: views.node_body(r, NODE_ACTIVE, {}),
    ),
    RouteCase(
        "finder", "GET /nodes/jump", "Find a skill", 200, lambda r: views.finder_body(r, {})
    ),
    RouteCase(
        "finder-query",
        "GET /nodes/jump?q=pandas",
        "Find a skill",
        200,
        lambda r: views.finder_body(r, {"q": ["pandas"]}),
    ),
    RouteCase("health", "GET /health", "Health", 200, views.health_body),
    RouteCase(
        "analytics-velocity",
        "GET /analytics?theme=velocity",
        "Analytics",
        200,
        lambda r: views.analytics_body(r, {"theme": ["velocity"]}),
    ),
    RouteCase(
        "analytics-blockers",
        "GET /analytics?theme=blockers",
        "Analytics",
        200,
        lambda r: views.analytics_body(r, {"theme": ["blockers"]}),
    ),
    RouteCase(
        "analytics-reviews",
        "GET /analytics?theme=reviews",
        "Analytics",
        200,
        lambda r: views.analytics_body(r, {"theme": ["reviews"]}),
    ),
    RouteCase(
        "analytics-evidence",
        "GET /analytics?theme=evidence",
        "Analytics",
        200,
        lambda r: views.analytics_body(r, {"theme": ["evidence"]}),
    ),
    RouteCase(
        "pass",
        f"GET /nodes/{NODE_ACTIVE}/pass",
        "Use basic Pandas DataFrame operations",
        200,
        lambda r: views.pass_modal_body(r, NODE_ACTIVE, {}),
    ),
    RouteCase(
        "master",
        f"GET /nodes/{NODE_PASSED}/master",
        "Use variables and expressions in Python",
        200,
        lambda r: views.master_body(r, NODE_PASSED, {}),
    ),
    RouteCase(
        "master-confirm",
        f"GET /nodes/{NODE_PASSED}/master/confirm",
        "Use variables and expressions in Python",
        200,
        lambda r: views.master_confirm_body(r, NODE_PASSED, {}),
    ),
    RouteCase("error-404", "GET <unrouted>", "Not found", 404, views.not_found_body),
)

_CASES_BY_NAME = {case.name: case for case in CASES}

# --- Golden files: read, diff, update ---------------------------------------

_DIFF_LINE_BUDGET = 60


def _read_text(path: Path) -> str:
    """Read exactly the bytes on disk — no newline translation either way."""
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _unified_diff(expected: str, actual: str, name: str) -> str:
    """A bounded unified diff of golden vs rendered, for the failure message."""
    lines = list(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"snapshots/{name}.html (golden)",
            tofile=f"rendered {name} body",
        )
    )
    if len(lines) > _DIFF_LINE_BUDGET:
        extra = len(lines) - _DIFF_LINE_BUDGET
        lines = lines[:_DIFF_LINE_BUDGET] + [f"... ({extra} more diff lines)\n"]
    return "".join(lines)


def _compare_or_update(name: str, body: str, *, directory: Path | None = None) -> None:
    """Assert the body matches its golden, or rewrite the golden in update mode."""
    directory = SNAPSHOT_DIR if directory is None else directory
    path = directory / f"{name}.html"
    if os.environ.get(UPDATE_ENV):
        _write_text(path, body)
        return
    if not path.exists():
        pytest.fail(
            f"no golden snapshot at {path} — create it with "
            f"{UPDATE_ENV}=1 python -m pytest tests/web/test_route_snapshots.py"
        )
    expected = _read_text(path)
    if expected != body:
        pytest.fail(
            f"{path} no longer matches the rendered body. If the change is "
            f"intended, re-bless with {UPDATE_ENV}=1 and review the diff:\n"
            + _unified_diff(expected, body, name)
        )


# --- Fixtures ---------------------------------------------------------------


@pytest.fixture(scope="module")
def snapshot_repo() -> Path:
    """One pinned, read-only seed copy shared by every case in this module."""
    return build_pinned_repo(Path(tempfile.mkdtemp(prefix="route-snapshots-")))


@pytest.fixture(scope="module")
def frozen_clock():
    """The pinned clock, active for every render in this module."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        _freeze_read_clock(monkeypatch)
        yield FROZEN_DAY


@pytest.fixture(scope="module")
def rendered(snapshot_repo: Path, frozen_clock) -> dict[str, tuple[str, str, int]]:
    """Every case rendered once — the bytes the goldens must equal."""
    return {case.name: case.render(snapshot_repo) for case in CASES}


# --- The goldens ------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_served_body_matches_its_golden(case: RouteCase, rendered) -> None:
    """Every served body equals ``snapshots/<case>.html`` byte for byte."""
    title, body, status = rendered[case.name]
    assert (title, status) == (case.title, case.status), case.route
    _compare_or_update(case.name, body)


def test_snapshot_directory_has_no_orphans(rendered) -> None:
    """A golden with no case behind it is a stale file, not coverage."""
    if os.environ.get(UPDATE_ENV):
        pytest.skip("update mode rewrites goldens; orphan check is not meaningful")
    on_disk = {path.name for path in SNAPSHOT_DIR.glob("*.html")}
    expected = {f"{case.name}.html" for case in CASES}
    assert on_disk - expected == set(), "orphan goldens — delete or re-add the case"
    assert expected - on_disk == set(), "missing goldens"


def test_rendering_is_repeatable(snapshot_repo: Path, frozen_clock, rendered) -> None:
    """A second render in the same process produces the same bytes.

    Guards the hash-order hazards (set/dict iteration in a card builder) that
    a single render per run would only catch intermittently.
    """
    for name in ("home", "analytics-velocity"):
        again = _CASES_BY_NAME[name].render(snapshot_repo)
        assert again == rendered[name], f"{name} rendered differently on a second pass"


# --- Harness guards: the pinned clock, the pinned data, the diff ------------


def test_frozen_clock_is_the_only_date_source(frozen_clock) -> None:
    """The harness really did pin the one funnel — no body reads the wall clock."""
    from skilltrace.execution.overdue import utc_today

    assert utc_today() == FROZEN_DAY
    assert views.utc_today() == FROZEN_DAY


def test_seed_repo_pins_the_learner_state(snapshot_repo: Path, frozen_clock) -> None:
    """The store is fully recorded and the two asserted states are as authored."""
    from skilltrace.graph.nodes import load_nodes
    from skilltrace.graph.state import load_state

    store = load_state(snapshot_repo)
    assert set(store.entries) == {node.id for node in load_nodes(snapshot_repo)}
    assert store.state_of(NODE_ACTIVE) == "active"
    assert store.state_of(NODE_PASSED) == "passed"
    assert store.state_of(NODE_THIRD) == "available"


def test_seed_repo_is_a_copy_not_the_live_repo(snapshot_repo: Path) -> None:
    """The goldens read a copy — nothing in this module writes the live repo."""
    assert snapshot_repo != REPO_ROOT
    assert REPO_ROOT not in snapshot_repo.parents


def test_seed_repo_is_legal(snapshot_repo: Path, frozen_clock) -> None:
    """The pinned data passes every layer validator — else goldens record noise."""
    from skilltrace.commands.health import health_report

    report = health_report(snapshot_repo)
    assert [layer.line for layer in report.layers if not layer.ok] == []
    assert report.error_count == 0


def test_diff_reports_both_sides() -> None:
    diff = _unified_diff("<p>a</p>\n<p>b</p>\n", "<p>a</p>\n<p>c</p>\n", "sample")
    assert "-<p>b</p>" in diff
    assert "+<p>c</p>" in diff


def test_diff_is_bounded() -> None:
    diff = _unified_diff("x\n" * 200, "y\n" * 200, "big")
    assert "more diff lines" in diff
    assert len(diff.splitlines()) <= _DIFF_LINE_BUDGET + 1


def test_changed_body_fails_with_a_diff(tmp_path: Path, monkeypatch) -> None:
    """Any HTML change fails, and the failure carries the diff."""
    monkeypatch.delenv(UPDATE_ENV, raising=False)  # compare, never rewrite
    _write_text(tmp_path / "sample.html", "<p>golden</p>\n")
    assert _read_text(tmp_path / "sample.html") == "<p>golden</p>\n"
    with pytest.raises(pytest.fail.Exception) as failure:
        _compare_or_update("sample", "<p>changed</p>\n", directory=tmp_path)
    assert "-<p>golden</p>" in str(failure.value)
    assert "+<p>changed</p>" in str(failure.value)


def test_update_mode_rewrites_the_golden(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(UPDATE_ENV, "1")
    _compare_or_update("sample", "<p>fresh</p>\n", directory=tmp_path)
    assert _read_text(tmp_path / "sample.html") == "<p>fresh</p>\n"
    monkeypatch.delenv(UPDATE_ENV)
    _compare_or_update("sample", "<p>fresh</p>\n", directory=tmp_path)  # now matches
