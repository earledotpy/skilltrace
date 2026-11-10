"""The accessibility harness for the v3 web layer (spec-v3-study-day §9 AX-11).

Two jobs, one module, so the contrast gate and the axe gate read the *same*
facts and can never disagree about what the product serves:

* **Colour maths.** A WCAG 2.x relative-luminance and contrast-ratio
  implementation (stdlib only — no Pillow, no numpy, no runtime dep). It
  reads the v3 token table (:mod:`skilltrace.web.tokens`) so a palette
  change that breaks AA fails the build rather than shipping.
* **Fixture rendering.** A pinned fixture repo (the curriculum copied, the
  learner stores authored) and the route table that renders every served
  body into the exact document the shell serves
  (:func:`skilltrace.web.views.shell.page`).

Why a harness module and not two test modules each rolling their own: the
axe gate needs the *served document* and the contrast gate needs the
*token table*, and both must see the same fixture. Duplicating the fixture
builder would let the two gates drift onto different data — the exact
failure mode AX-11 exists to prevent.

The fixture is deliberately pinned to a fixed date (the same convention as
``docs/agents/fixture-clock.md`` and ``tests/web/test_route_snapshots.py``):
the rendered documents must not follow the wall clock, or the gate would
change every day for no reason.
"""

from __future__ import annotations

import json
import multiprocessing
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from skilltrace.web import views

__all__ = [
    "AXE_DRIVER",
    "AXE_PACKAGES",
    "FROZEN_DAY",
    "FROZEN_MOMENT",
    "AxeToolchain",
    "Pairing",
    "RouteCase",
    "build_fixture_repo",
    "contrast_ratio",
    "ensure_axe_toolchain",
    "frozen_clock",
    "meaningful_pairs",
    "relative_luminance",
    "render_all",
    "render_document",
    "route_cases",
    "run_axe",
]

REPO_ROOT = Path(__file__).resolve().parents[2]

# The pinned "today" and "now" every fixture record is authored against.
FROZEN_DAY = date(2026, 11, 17)
FROZEN_MOMENT = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)

# Immutable node ids (CONTEXT.md: node ids are never reused) covering the
# rendered state halves: one active node, one passed node, one left at
# derived readiness.
NODE_ACTIVE = "data.pandas.dataframe_basics_01"
NODE_PASSED = "programming.python.variables_01"
NODE_THIRD = "data.sql.select_basics_01"


# --- Colour maths (WCAG 2.x) ------------------------------------------------


def _channel(value: int) -> float:
    """One sRGB channel linearised for relative luminance."""
    ratio = value / 255
    if ratio <= 0.04045:
        return ratio / 12.92
    return ((ratio + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str) -> float:
    """The WCAG 2.x relative luminance of a ``#rrggbb`` colour.

    The definition (WCAG 2.2, "relative luminance") is reproduced here
    rather than approximated, because the gate's whole value is that the
    number the test asserts on is the number a browser would compute.
    """
    text = colour.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(char * 2 for char in text)
    if len(text) != 6:
        raise ValueError(f"not a #rrggbb colour: {colour!r}")
    red, green, blue = (int(text[index : index + 2], 16) for index in (0, 2, 4))
    return (
        0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)
    )


def contrast_ratio(first: str, second: str) -> float:
    """The WCAG 2.x contrast ratio between two ``#rrggbb`` colours."""
    lighter = max(relative_luminance(first), relative_luminance(second))
    darker = min(relative_luminance(first), relative_luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


# --- The meaningful pairings ------------------------------------------------

# WCAG 2.2 AA floors. 4.5:1 is SC 1.4.3 for normal text; 3:1 is SC 1.4.11
# for "visual information required to identify user interface components and
# states" (boundaries, focus indicators, meaningful status graphics).
TEXT_FLOOR = 4.5
BOUNDARY_FLOOR = 3.1

# The canvas steps a text colour may sit on.
CANVAS_ROLES = ("canvas-base", "canvas-raised", "canvas-subtle", "canvas-selected")
# The three text steps.
TEXT_ROLES = ("text-primary", "text-secondary", "text-muted")
# The four severity families; each carries a colour, a soft fill and an ink.
STATUS_FAMILIES = ("info", "success", "warning", "failure")
# The three border steps. ``border-default`` and ``border-strong`` bound
# controls and interactive regions, so they are *meaningful UI boundaries*
# and carry the 3:1 floor (WCAG SC 1.4.11, not SC 1.4.3).
#
# ``border-subtle`` is a decorative hairline — a table's row rules, a
# section divider. The structure it decorates is carried by the table's
# own header cells and captions, so it is not a boundary the learner needs
# in order to identify a control, and it stays quiet. It is checked
# separately: it must remain *distinguishable* from the canvas (>= 1.4:1)
# so the decoration is actually visible, but it is not held to 3:1.
BOUNDARY_BORDER_ROLES = ("border-default", "border-strong")
DECORATIVE_BORDER_ROLES = ("border-subtle",)
BORDER_ROLES = BOUNDARY_BORDER_ROLES + DECORATIVE_BORDER_ROLES

# The floor a decorative hairline must clear to remain visible at all.
DECORATIVE_FLOOR = 1.4


@dataclass(frozen=True)
class Pairing:
    """One meaningful foreground/background pairing the design system uses."""

    foreground: str
    background: str
    kind: str  # "text" or "boundary"
    note: str = ""

    @property
    def floor(self) -> float:
        return TEXT_FLOOR if self.kind == "text" else BOUNDARY_FLOOR

    @property
    def label(self) -> str:
        return f"{self.foreground} on {self.background}"


def meaningful_pairs() -> tuple[Pairing, ...]:
    """Every foreground/background pairing the v3 design system actually uses.

    Not every token pair — the *meaningful* ones. The list is derived from
    the stylesheet's own rules: text sits on the four canvas steps, each
    status ink sits on its own soft fill, the accent ink sits on the accent
    fill, the focus ring and the status colours are boundaries on the
    canvas, and the three border steps are boundaries on the canvas.
    """
    pairs: list[Pairing] = []
    for text_role in TEXT_ROLES:
        for canvas in CANVAS_ROLES:
            pairs.append(
                Pairing(text_role, canvas, "text", "body text on a canvas step")
            )
    for family in STATUS_FAMILIES:
        pairs.append(
            Pairing(
                f"status-{family}-ink",
                f"status-{family}-soft",
                "text",
                "status label text on its own soft fill",
            )
        )
    pairs.append(Pairing("accent-ink", "accent", "text", "primary button label"))
    pairs.append(
        Pairing("mastery-ink", "mastery-soft", "text", "mastery status label")
    )
    # The accent is the link colour (``a{color:var(--accent)}``), so it is
    # text wherever a link sits. ``canvas-selected`` is deliberately not
    # here: it is the hover fill of a button, whose text is text-primary,
    # and the accent on that step would fall below 4.5:1 in both themes.
    for canvas in ("canvas-base", "canvas-raised", "canvas-subtle"):
        pairs.append(Pairing("accent", canvas, "text", "link text"))
    # The mastery ink also labels a button on the plain canvas.
    pairs.append(
        Pairing("mastery-ink", "canvas-base", "text", "mastery button label")
    )
    # The focus ring is drawn over whatever the focused control sits on.
    for canvas in CANVAS_ROLES:
        pairs.append(
            Pairing("status-focus", canvas, "boundary", "keyboard focus ring")
        )
    for family in STATUS_FAMILIES:
        for canvas in CANVAS_ROLES:
            pairs.append(
                Pairing(
                    f"status-{family}",
                    canvas,
                    "boundary",
                    "meaningful status graphic",
                )
            )
    pairs.append(Pairing("accent", "canvas-base", "boundary", "action boundary"))
    # A meaningful boundary is checked against *every* canvas step it may
    # sit on, not just the base one: a control on a card is on canvas-raised.
    for border in BOUNDARY_BORDER_ROLES:
        for canvas in CANVAS_ROLES:
            pairs.append(
                Pairing(border, canvas, "boundary", "component boundary")
            )
    return tuple(pairs)


# --- The pinned fixture repo ------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def _ago(**fields: int) -> str:
    return _iso(FROZEN_MOMENT - timedelta(**fields))


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _pin_progress(path: Path) -> None:
    """Author the progress store: derived readiness plus two asserted states.

    The store is filled through the engine's own readiness writer, so every
    node carries the state ``sync`` would record. The two asserted entries
    are *authored fixture data* — a stand-in learner's store, exactly as
    the other web suites seed state; no engine pass/master path runs here
    (see AGENTS.md safety rule).
    """
    from skilltrace.graph.edges import load_edges
    from skilltrace.graph.nodes import load_nodes
    from skilltrace.graph.readiness import sync_readiness
    from skilltrace.graph.state import load_state, save_state

    (path / "graph" / "state.yaml").write_text("progress: {}\n", encoding="utf-8")
    store = load_state(path)
    nodes = load_nodes(path)
    sync_readiness(nodes, load_edges(path), store, now=_iso(FROZEN_MOMENT))
    for node in nodes:
        if node.id not in store.entries:
            store.write_readiness(node.id, "locked", now=_iso(FROZEN_MOMENT))
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
    """Author the execution records: session history, blockers and reviews.

    The fixture carries **one open Session**, with work logged against the
    active node: that is the product's most important state (Today resumes
    it, the Study cockpit runs it), and an accessibility gate that skipped it
    would be measuring the easy half. The bound node is derived from the
    session's work (``views._shared._session_node_id``), which is what the
    engine's record shape actually carries — a Session names no node itself.
    """
    _write_yaml(
        path,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "ses.a11y.000",
                    "status": "open",
                    "started_at": _ago(hours=2),
                },
                {
                    "id": "ses.a11y.001",
                    "status": "completed",
                    "started_at": _ago(days=2),
                    "ended_at": _iso(
                        FROZEN_MOMENT - timedelta(days=2) + timedelta(hours=1)
                    ),
                },
                {
                    "id": "ses.a11y.002",
                    "status": "completed",
                    "started_at": _ago(days=9),
                    "ended_at": _iso(
                        FROZEN_MOMENT - timedelta(days=9) + timedelta(hours=1)
                    ),
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
                    "id": "wk.ses.a11y.000.01",
                    "session_id": "ses.a11y.000",
                    "node_id": NODE_ACTIVE,
                    "created_at": _ago(minutes=90),
                    "notes": "drilled groupby on the sample frame",
                    "minutes": 45,
                },
                {
                    "id": "wk.ses.a11y.002.01",
                    "session_id": "ses.a11y.002",
                    "node_id": NODE_ACTIVE,
                    "created_at": _ago(days=2),
                    "notes": "read the selection docs",
                    "minutes": 30,
                },
                {
                    "id": "wk.ses.a11y.003.01",
                    "session_id": "ses.a11y.003",
                    "node_id": NODE_PASSED,
                    "created_at": _ago(days=9),
                    "notes": "variables practice",
                    "minutes": 25,
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
                    "id": "blk.a11y.001",
                    "node_id": NODE_ACTIVE,
                    "status": "open",
                    "description": "groupby output keeps surprising me",
                    "created_at": _ago(days=1),
                },
                {
                    "id": "blk.a11y.002",
                    "node_id": NODE_PASSED,
                    "status": "resolved",
                    "description": "loop-variable scope confused me",
                    "created_at": _ago(days=12),
                    "resolved_at": _ago(days=10),
                    "resolution_summary": "re-read the scoping section",
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
                    "id": "rvw.a11y.001",
                    "node_id": NODE_PASSED,
                    "status": "scheduled",
                    "scheduled_for": (FROZEN_DAY - timedelta(days=3)).isoformat(),
                    "created_at": _ago(days=30),
                },
                {
                    "id": "rvw.a11y.002",
                    "node_id": NODE_THIRD,
                    "status": "scheduled",
                    "scheduled_for": FROZEN_DAY.isoformat(),
                    "created_at": _ago(days=14),
                },
                {
                    "id": "rvw.a11y.003",
                    "node_id": NODE_ACTIVE,
                    "status": "scheduled",
                    "scheduled_for": (FROZEN_DAY + timedelta(days=7)).isoformat(),
                    "created_at": _ago(days=1),
                },
            ]
        },
    )
    _write_yaml(path, "execution/remediation_actions.yaml", {"remediation_actions": []})


def _pin_evidence(path: Path) -> None:
    """Author the evidence history: two superseding records and one rejection.

    The repository's own ``evidence/evidence_records.yaml`` is empty, so an
    accessibility sweep over the seed alone would only ever see the index's
    empty state. These are *authored fixture records* — a stand-in learner's
    history, exactly as the progress store is authored — never the output of
    ``evidence submit`` (no engine write path runs here). They give the gate
    the populated index, the derived standing (live / superseded / rejected)
    and the inspector's provenance.
    """
    _write_yaml(
        path,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{NODE_ACTIVE}.001",
                    "artifact_spec_id": f"spec.{NODE_ACTIVE.removesuffix('_01')}",
                    "location": "evidence/artifacts/data/pandas_basics.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "1" * 64,
                    "created_at": _ago(days=5),
                },
                {
                    "id": f"ev.{NODE_ACTIVE}.002",
                    "artifact_spec_id": f"spec.{NODE_ACTIVE.removesuffix('_01')}",
                    "location": "evidence/artifacts/data/pandas_basics.py",
                    "accepted": False,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "2" * 64,
                    "created_at": _ago(days=3),
                    "note": "the revenue column was summed, not listed",
                },
                {
                    "id": f"ev.{NODE_ACTIVE}.003",
                    "artifact_spec_id": f"spec.{NODE_ACTIVE.removesuffix('_01')}",
                    "location": "evidence/artifacts/data/pandas_basics.py",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "3" * 64,
                    "created_at": _ago(days=1),
                    "supersedes": f"ev.{NODE_ACTIVE}.001",
                    "supersede_reason": "corrected the region_rows column",
                },
            ]
        },
    )
    _write_yaml(
        path,
        "execution/events.yaml",
        {
            "events": [
                {
                    "timestamp": _ago(days=1),
                    "command": "evidence submit",
                    "args": {"node_id": NODE_ACTIVE},
                    "records_touched": [
                        f"ev.{NODE_ACTIVE}.003",
                        f"ev.{NODE_ACTIVE}.001",
                    ],
                },
            ]
        },
    )


def build_fixture_repo(path: Path) -> Path:
    """A read-only seed copy with the learner stores authored and pinned."""
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, path / dirname)
    _pin_progress(path)
    _pin_execution(path)
    _pin_evidence(path)
    return path


# --- The fixture clock ------------------------------------------------------


class _FrozenDatetime(datetime):
    """A ``datetime`` whose ``now()`` is the frozen moment.

    Subclassing (rather than replacing) keeps ``fromisoformat`` and the
    constructor working for the modules that read stored timestamps.
    """

    @classmethod
    def now(cls, tz=None):
        return FROZEN_MOMENT if tz is not None else FROZEN_MOMENT.replace(tzinfo=None)


@contextmanager
def frozen_clock():
    """Pin every module's view of the date funnel to :data:`FROZEN_DAY`.

    Mirrors ``tests/web/test_route_snapshots.py``: the modules that did
    ``from ..execution.overdue import utc_today`` keep their own binding, so
    patching the defining module is not enough — every module attribute
    still pointing at the wall-clock funnel is rebound too.
    """
    from skilltrace import commands, execution

    original = execution.overdue.utc_today

    def frozen(*, clock=None):
        return FROZEN_DAY

    saved: list[tuple[object, str, object]] = []
    execution.overdue.utc_today = frozen
    saved.append((execution.overdue, "utc_today", original))
    for module in list(sys.modules.values()):
        if getattr(module, "utc_today", None) is original:
            module.utc_today = frozen
            saved.append((module, "utc_today", original))
    for module, name in ((commands.today, "datetime"), (commands._common, "datetime")):
        saved.append((module, name, module.datetime))
        setattr(module, name, _FrozenDatetime)
    try:
        yield
    finally:
        for module, name, value in saved:
            setattr(module, name, value)


# --- The route table --------------------------------------------------------


@dataclass(frozen=True)
class RouteCase:
    """One served body: its name, the route it answers, and how to render it."""

    name: str
    route: str
    mode: str
    body: str
    render: Callable[[Path], tuple[str, str, int]]


def route_cases() -> tuple[RouteCase, ...]:
    """Every served GET body of the v3 route table (§6), in route order.

    The mode is the route's declared default presentation mode: a bare deep
    link always renders a sensible presentation (spec-v3-study-day IA-1).
    The ``body`` field names the view function that renders the route, so
    the gate can assert it covers every published body.
    """
    return (
        RouteCase("home", "GET /", "guided", "home_body", lambda r: views.home_body(r, {})),
        RouteCase("next", "GET /next", "guided", "next_body", lambda r: views.next_body(r, {})),
        RouteCase("find", "GET /find", "guided", "finder_body", lambda r: views.finder_body(r, {})),
        RouteCase(
            "node",
            f"GET /nodes/{NODE_ACTIVE}",
            "guided",
            "node_body",
            lambda r: views.node_body(r, NODE_ACTIVE, {}),
        ),
        RouteCase(
            "session",
            "GET /session",
            "guided",
            "session_body",
            lambda r: views.session_body(r, {}),
        ),
        RouteCase(
            "session-close",
            "GET /session/close",
            "guided",
            "session_close_body",
            lambda r: views.session_close_body(r, {}),
        ),
        RouteCase(
            "node-evidence",
            f"GET /nodes/{NODE_ACTIVE}/evidence",
            "guided",
            "node_evidence_body",
            lambda r: views.node_evidence_body(r, NODE_ACTIVE, {}),
        ),
        RouteCase(
            "evidence-index",
            "GET /evidence",
            "operations",
            "evidence_index_body",
            lambda r: views.evidence_index_body(r, {}),
        ),
        RouteCase(
            "evidence-inspector",
            f"GET /evidence?record=ev.{NODE_ACTIVE}.003",
            "operations",
            "evidence_index_body",
            lambda r: views.evidence_index_body(
                r, {"record": [f"ev.{NODE_ACTIVE}.003"]}
            ),
        ),
        RouteCase(
            "reviews",
            "GET /reviews",
            "guided",
            "reviews_body",
            lambda r: views.reviews_body(r, {}),
        ),
        RouteCase(
            "operations",
            "GET /operations",
            "operations",
            "operations_body",
            lambda r: views.operations_body(r, {}),
        ),
        RouteCase(
            "graph",
            "GET /graph",
            "operations",
            "graph_body",
            lambda r: views.graph_body(r, {}),
        ),
        RouteCase(
            "graph-node",
            f"GET /graph/{NODE_ACTIVE}",
            "operations",
            "graph_body",
            lambda r: views.graph_body(r, {}, node_id=NODE_ACTIVE),
        ),
        RouteCase(
            "health",
            "GET /health",
            "operations",
            "health_body",
            lambda r: views.health_body(r, {}),
        ),
        RouteCase(
            "analytics",
            "GET /analytics",
            "operations",
            "analytics_body",
            lambda r: views.analytics_body(r, {"theme": ["velocity"]}),
        ),
        RouteCase(
            "portfolio",
            "GET /portfolio",
            "operations",
            "portfolio_body",
            lambda r: views.portfolio_body(r, {}),
        ),
        RouteCase(
            "portfolio-preview",
            "GET /portfolio/preview",
            "operations",
            "portfolio_body",
            lambda r: views.portfolio_body(r, {"preview": ["1"]}),
        ),
        RouteCase(
            "pass",
            f"GET /nodes/{NODE_ACTIVE}/pass",
            "guided",
            "pass_modal_body",
            lambda r: views.pass_modal_body(r, NODE_ACTIVE, {}),
        ),
        RouteCase(
            "master",
            f"GET /nodes/{NODE_PASSED}/master",
            "guided",
            "master_body",
            lambda r: views.master_body(r, NODE_PASSED, {}),
        ),
        RouteCase(
            "master-confirm",
            f"GET /nodes/{NODE_PASSED}/master/confirm",
            "guided",
            "master_confirm_body",
            lambda r: views.master_confirm_body(r, NODE_PASSED, {}),
        ),
        RouteCase(
            "not-found",
            "GET <unrouted>",
            "guided",
            "not_found_body",
            lambda r: views.not_found_body(r),
        ),
    )


def render_document(case: RouteCase, root: Path) -> str:
    """The exact document the shell serves for one route case."""
    title, body, _status = case.render(root)
    return views.shell.page(title, body, mode=case.mode)


def _render_one(payload: tuple[str, str]) -> tuple[str, str | None, str | None]:
    """Render one route case in a worker process.

    Returns ``(name, html, error)``: the HTML, or the error message when the
    body raised. A route that cannot render is reported, never hidden.
    """
    name, root = payload
    case = {c.name: c for c in route_cases()}[name]
    try:
        return name, render_document(case, Path(root)), None
    except Exception as exc:  # noqa: BLE001 — reported to the caller verbatim
        return name, None, f"{type(exc).__name__}: {exc}"


def render_all(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Render every route case, in parallel, and report the ones that failed.

    Returns ``(documents, errors)`` — the served documents keyed by case
    name, and the error message of every route whose body raised. Rendering
    is parallel because each body re-joins the engine fresh (by design), and
    the gate must stay cheap enough to run per slice (AX-11).

    The frozen clock is applied here, in the parent, so the forked workers
    inherit it.
    """
    cases = route_cases()
    payloads = [(case.name, str(root)) for case in cases]
    documents: dict[str, str] = {}
    errors: dict[str, str] = {}
    context = multiprocessing.get_context("fork")
    with frozen_clock():
        with ProcessPoolExecutor(max_workers=8, mp_context=context) as pool:
            for name, html, error in pool.map(_render_one, payloads):
                if html is not None:
                    documents[name] = html
                else:
                    errors[name] = error or "unknown error"
    return documents, errors


# --- The axe driver (outside the repository) --------------------------------

# The axe-core driver script. It lives outside the repo on purpose: the
# gate must never leave node_modules, package.json or a lockfile in the
# tree (ADR 0008 keeps the JS posture tier-0; this is a *test* dependency,
# never a runtime one).
AXE_DRIVER = """\
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const axeSource = fs.readFileSync(
  path.join(__dirname, 'node_modules', 'axe-core', 'axe.min.js'),
  'utf8'
);

const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const output = process.argv[3];

// The WCAG 2.2 AA rule sets (SC 1.4.3, 1.4.11, 2.4.x, ...).
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

(async () => {
  const results = [];
  for (const doc of input) {
    const dom = new JSDOM(doc.html, {
      pretendToBeVisual: true,
      runScripts: 'dangerously',
      url: 'http://localhost/'
    });
    const { window } = dom;
    // jsdom has no canvas; axe only needs it for the colour-contrast rule,
    // which this gate does not rely on (the token contrast gate covers
    // colour). A stub keeps the run quiet and deterministic.
    window.HTMLCanvasElement.prototype.getContext = () => null;
    window.eval(axeSource);
    const result = await window.axe.run(window.document, {
      runOnly: { type: 'tag', values: TAGS }
    });
    results.push({
      name: doc.name,
      violations: result.violations.map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        help: violation.help,
        helpUrl: violation.helpUrl,
        nodes: violation.nodes.map((node) => ({
          target: node.target,
          html: node.html,
          failureSummary: node.failureSummary
        }))
      }))
    });
    window.close();
  }
  fs.writeFileSync(output, JSON.stringify(results, null, 2));
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""

# The pinned dev-only packages (ARC-8: automated accessibility tooling is a
# dev dependency, never a runtime dependency).
AXE_PACKAGES = ("axe-core@4.14.0", "jsdom@22.1.0")


@dataclass
class AxeToolchain:
    """The resolved axe toolchain: where node, npm and the packages live."""

    node: str
    npm: str
    workdir: Path
    available: bool
    reason: str = ""


def _which(program: str) -> str | None:
    return shutil.which(program)


def ensure_axe_toolchain(workdir: Path) -> AxeToolchain:
    """Install axe-core + jsdom into ``workdir`` (outside the repository).

    Returns a :class:`AxeToolchain` whose ``available`` flag is false — with
    a human-readable ``reason`` — when node, npm or the packages cannot be
    had. The caller skips; it never fails and never passes silently.
    """
    node = _which("node")
    if node is None:
        return AxeToolchain("", "", workdir, False, "node is not installed")
    npm = _which("npm")
    if npm is None:
        return AxeToolchain(node, "", workdir, False, "npm is not installed")
    workdir.mkdir(parents=True, exist_ok=True)
    if not _pinned_packages_present(workdir):
        # The packages must match the pins exactly. A workdir left behind by
        # an unpinned install (or by an interrupted one) would otherwise be
        # used as-is, and a version that axe-core does not agree with hangs
        # the gate rather than failing it.
        try:
            completed = subprocess.run(
                [npm, "install", "--no-audit", "--no-fund", "--silent", *AXE_PACKAGES],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return AxeToolchain(node, npm, workdir, False, f"npm install failed: {exc}")
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:400]
            return AxeToolchain(
                node,
                npm,
                workdir,
                False,
                f"npm install exited {completed.returncode}: {detail}",
            )
    (workdir / "driver.js").write_text(AXE_DRIVER, encoding="utf-8")
    return AxeToolchain(node, npm, workdir, True)


def _pinned_packages_present(workdir: Path) -> bool:
    """Whether the workdir holds exactly the pinned package versions."""
    expected = dict(package.split("@", 1) for package in AXE_PACKAGES)
    for name, version in expected.items():
        manifest = workdir / "node_modules" / name / "package.json"
        if not manifest.exists():
            return False
        try:
            installed = json.loads(manifest.read_text(encoding="utf-8")).get("version")
        except (OSError, ValueError):
            return False
        if installed != version:
            return False
    return True


def _run_axe_batch(toolchain: AxeToolchain, payload: list[dict]) -> list[dict]:
    """Run one node invocation over one batch of documents."""
    # One file pair per batch: the shards run concurrently in threads of
    # one process, so the name has to be unique per batch, not per process.
    tag = uuid.uuid4().hex
    input_path = toolchain.workdir / f"documents-{tag}.json"
    output_path = toolchain.workdir / f"results-{tag}.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    completed = subprocess.run(
        [
            toolchain.node,
            str(toolchain.workdir / "driver.js"),
            str(input_path),
            str(output_path),
        ],
        cwd=toolchain.workdir,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:2000]
        raise RuntimeError(f"axe driver failed ({completed.returncode}): {detail}")
    results = json.loads(output_path.read_text(encoding="utf-8"))
    input_path.unlink(missing_ok=True)
    output_path.unlink(missing_ok=True)
    return results


def run_axe(
    toolchain: AxeToolchain,
    documents: Iterable[tuple[str, str]],
    *,
    shards: int = 4,
) -> list[dict]:
    """Run axe-core over the given ``(name, html)`` documents.

    The batch is split across a few concurrent node invocations: axe-core
    over jsdom is CPU-bound, so one invocation per document would make the
    gate slow, and one invocation over everything would make it slow too.
    A handful of shards keeps the whole route table under a minute, which
    is what AX-11 asks of the gate (cheap enough to run per slice).
    """
    payload = [{"name": name, "html": html} for name, html in documents]
    if not payload:
        return []
    shard_count = max(1, min(shards, len(payload)))
    batches = [payload[index::shard_count] for index in range(shard_count)]
    batches = [batch for batch in batches if batch]
    with ThreadPoolExecutor(max_workers=len(batches)) as pool:
        results = list(pool.map(lambda batch: _run_axe_batch(toolchain, batch), batches))
    merged: list[dict] = []
    for batch_result in results:
        merged.extend(batch_result)
    return sorted(merged, key=lambda result: result["name"])
