"""The §6 route contract over the real router (#350, SL1).

What only this module shows: the *served* product, not the view functions.
Every destination in the normative route table
(``docs/spec-v3-study-day.md`` §6) is fetched cold over HTTP, from a fresh
server, in its own request — so "renders at its own URL, and no destination
is reachable only through another" is a measurement rather than a claim.
The same sweep carries the shell-level contracts the ticket binds to the
route substrate:

* the seventeen destinations exist once each, flat and mode-neutral;
* mode rides a URL parameter (a bare deep link renders the route's default,
  an explicit mode overrides it, and the switch is reversible without losing
  the destination's context);
* the selected context rides a URL parameter too — a shared or reloaded
  inspector link reproduces exactly what was seen;
* the page frame is a section, never a card (VS-5);
* no status is carried by colour alone: every status word and label state is
  text (VS-3, AX-1);
* the five engine layers and the web-only sublayer boundary are untouched,
  and the runtime dependency set is unchanged (ARC-7, ARC-8).

The pinned fixture is the AX-11 one (``a11y_harness.build_fixture_repo``):
real curriculum, authored learner stores, and the open-Session plus
evidence-record states the product actually has.
"""

from __future__ import annotations

import html.parser
import threading
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from a11y_harness import NODE_ACTIVE, build_fixture_repo

from skilltrace.web.interface import FROZEN_ROUTES
from skilltrace.web.server import make_server

REPO_ROOT = Path(__file__).resolve().parents[2]

# The pinned evidence record the fixture authors (see a11y_harness).
RECORD_SELECTED = f"ev.{NODE_ACTIVE}.003"


# --- the served product -----------------------------------------------------


@pytest.fixture(scope="module")
def fixture_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The one pinned fixture repo: real curriculum, authored learner stores."""
    root = tmp_path_factory.mktemp("route-contract")
    return build_fixture_repo(root)


@pytest.fixture(scope="module")
def base_url(fixture_repo: Path) -> str:
    """One real server over the fixture repo, serving for the module."""
    server, failure = make_server(fixture_repo, 0)
    assert server is not None, failure
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _get(base_url: str, path: str) -> tuple[int, str]:
    """GET one path over HTTP; return ``(status, body)`` for every outcome.

    Redirects are **not** followed: a destination that answered 303 would be
    a destination with no address of its own, so it surfaces as a status
    rather than disappearing into a followed hop.
    """
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(f"{base_url}{path}") as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse to follow a redirect, so the router cannot hide one."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def _concrete(route: str) -> str:
    """A frozen route as a real URL — the ``{id}`` slot names a live node."""
    return route.replace("{id}", NODE_ACTIVE)


# The table also names a node-centred graph destination and a non-writing
# portfolio preview (RT-14, RT-17): served paths of the contract that the
# frozen constant names by their parent.
EXTRA_PATHS: tuple[str, ...] = (f"/graph/{NODE_ACTIVE}", "/portfolio/preview")

ALL_PATHS = tuple(_concrete(route) for route in FROZEN_ROUTES.values()) + EXTRA_PATHS


# --- the route table: seventeen destinations, once each ---------------------


def test_the_frozen_table_is_the_normative_spec_table() -> None:
    """``FROZEN_ROUTES`` and §6 are one table: neither can drift alone.

    The spec's table is the normative contract and the constant is what the
    engine serves; a gate that reads the table itself is what keeps them from
    becoming two sources of truth. Parsing stops at the next ``## `` heading,
    so the notes below the table are never mistaken for rows.
    """
    import re

    text = (REPO_ROOT / "docs" / "spec-v3-study-day.md").read_text(encoding="utf-8")
    section = text.split("## 6. Route table (RT) — normative", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(
        r"^\| RT-\d+ \| `([a-z-]+)`[^|]*\| `([^`]+)`", section, re.MULTILINE
    )
    spec_table = {name: route for name, route in rows}
    assert spec_table == FROZEN_ROUTES, (
        "the frozen route table and docs/spec-v3-study-day.md §6 disagree"
    )


def test_the_route_table_has_seventeen_unique_flat_paths() -> None:
    """Seventeen destinations exist once each, flat and mode-neutral.

    A duplicated path would make two screen names answers to one URL; a mode
    prefix would make a destination exist twice. The closed destinations of
    §6 note 3 are closed here too — a ``/today`` alias, a top-level
    ``/blockers``, a generic ``/settings`` and a standalone audit log.
    """
    assert len(FROZEN_ROUTES) == 17
    paths = list(FROZEN_ROUTES.values())
    assert len(set(paths)) == len(paths), "two destinations share one path"
    for path in paths:
        assert not path.startswith(("/guided/", "/operations/")), (
            f"{path} carries a mode prefix — mode is a URL parameter"
        )
    for closed in ("/today", "/blockers", "/settings", "/events", "/audit"):
        assert closed not in paths, f"{closed} is a closed destination (RT note 3)"


@pytest.mark.parametrize("path", ALL_PATHS)
def test_every_destination_renders_at_its_own_url(path: str, base_url: str) -> None:
    """Each §6 destination answers its own URL, cold, as a whole page.

    Fetched in isolation: nothing else in the module's session is visited
    first, so nothing can be "reachable only through another" destination —
    a fresh request to the destination's own path either renders or it does
    not. A redirect is a failure here, because a destination that answers by
    sending the learner somewhere else has no address of its own.
    """
    status, body = _get(base_url, path)
    assert status == 200, f"{path} answered {status}"
    assert "That page doesn't exist." not in body, f"{path} fell through to the 404"
    assert '<main class="shell" id="content">' in body, f"{path} is not a full page"
    assert 'class="skip" href="#content"' in body, f"{path} lost the skip link"


# --- mode rides a URL parameter ---------------------------------------------


def _body_mode(body: str) -> str:
    """The document's presentation mode, read off the body class."""
    marker = '<body class="mode-'
    start = body.index(marker) + len(marker)
    return body[start : body.index('"', start)]


def test_a_bare_deep_link_renders_the_routes_default_mode(base_url: str) -> None:
    """A bare link lands in a sensible presentation: the route's own register."""
    for path, expected in (
        ("/", "guided"),
        ("/next", "guided"),
        ("/session", "guided"),
        ("/operations", "operations"),
        ("/graph", "operations"),
        ("/health", "operations"),
        ("/evidence", "operations"),
    ):
        _, body = _get(base_url, path)
        assert _body_mode(body) == expected, path


def test_an_explicit_mode_overrides_the_default(base_url: str) -> None:
    """Mode is presentation context: either mode renders either destination."""
    for path in ("/", "/graph", "/health", f"/nodes/{NODE_ACTIVE}"):
        _, guided = _get(base_url, f"{path}?mode=guided")
        _, operations = _get(base_url, f"{path}?mode=operations")
        assert _body_mode(guided) == "guided", path
        assert _body_mode(operations) == "operations", path


def test_an_unknown_mode_falls_back_to_the_default(base_url: str) -> None:
    """A mistyped parameter never dead-ends a deep link."""
    _, body = _get(base_url, "/graph?mode=nonsense")
    assert _body_mode(body) == "operations"
    _, body = _get(base_url, "/?mode=nonsense")
    assert _body_mode(body) == "guided"


def test_switching_mode_is_explicit_and_reversible(base_url: str) -> None:
    """The switch changes the mode and keeps the destination's context.

    The link out of a mode is fetched and switched back: the filters survive
    both directions, and only the ``mode`` parameter differs.
    """
    _, operations = _get(base_url, "/next?minutes=45&mode=operations")
    assert _body_mode(operations) == "operations"
    assert "/next?minutes=45&amp;mode=guided" in operations or (
        "/next?mode=guided" in operations and "minutes=45" in operations
    ), "the switch lost the destination's filters"

    _, guided = _get(base_url, "/next?minutes=45&mode=guided")
    assert _body_mode(guided) == "guided"
    assert "minutes=45" in guided
    assert "mode=operations" in guided


# --- the selected context rides a URL parameter -----------------------------


def test_a_shared_inspector_link_reproduces_the_selection(base_url: str) -> None:
    """``?record=`` is the whole selection — reload gives the same document."""
    path = f"/evidence?record={RECORD_SELECTED}"
    first_status, first = _get(base_url, path)
    second_status, second = _get(base_url, path)
    assert (first_status, second_status) == (200, 200)
    assert '<aside class="inspector"' in first
    assert RECORD_SELECTED in first
    assert "Selected evidence record" in first
    assert first == second, "the inspector is not reproducible from its URL"


def test_the_bare_index_renders_no_inspector(base_url: str) -> None:
    """No selection is the default: the index renders without an inspector."""
    status, body = _get(base_url, "/evidence")
    assert status == 200
    assert '<aside class="inspector"' not in body


def test_the_selection_survives_a_mode_switch(base_url: str) -> None:
    """Switching presentation keeps the selected context (IA-4)."""
    _, body = _get(base_url, f"/evidence?record={RECORD_SELECTED}")
    assert f"record={RECORD_SELECTED}" in body
    assert "mode=guided" in body


def test_an_unknown_selection_is_a_refusal_with_a_way_back(base_url: str) -> None:
    """A selection that names no record refuses; it never 500s or lies."""
    status, body = _get(base_url, "/evidence?record=ev.nowhere.999")
    assert status == 200
    assert "state-refusal" in body
    assert "That evidence record is not in this repository" in body
    assert "Back to the evidence index" in body


def test_the_inspector_has_no_route_of_its_own(base_url: str) -> None:
    """RT note 2: the contextual inspector is a region, never a destination.

    No frozen path names it, and no URL renders it in isolation: it appears
    only inside a route that owns the fact, driven by that route's
    ``record`` parameter. A standalone inspector path would be a new
    top-level view, which ADR 0007's amendment permits only where §6 names
    it — and §6 names none.
    """
    paths = set(FROZEN_ROUTES.values())
    assert not any("inspector" in path for path in paths)
    for guess in ("/inspector", "/evidence/inspector", f"/evidence/{RECORD_SELECTED}"):
        status, body = _get(base_url, guess)
        assert '<aside class="inspector"' not in body or status != 200, guess


def test_the_evidence_surfaces_offer_no_edit_or_delete(base_url: str) -> None:
    """HB-5: records are immutable — no edit, no delete, no bulk mutation.

    An affordance is a form or a link whose target would mutate a record.
    The surfaces may *submit* new evidence (a POST that appends) but never
    offer a route that edits, deletes, or batch-modifies what exists.
    """
    for path in (
        "/evidence",
        f"/evidence?record={RECORD_SELECTED}",
        f"/nodes/{NODE_ACTIVE}/evidence",
    ):
        status, body = _get(base_url, path)
        assert status == 200, path
        for banned in ('action="/evidence/delete', 'action="/evidence/edit'):
            assert banned not in body, f"{path} offers {banned}"
        assert "delete record" not in body.lower(), path
        assert "edit record" not in body.lower(), path


# --- the page frame: sections, rows, tables and disclosures -----------------


class _PageScan(html.parser.HTMLParser):
    """Collect the two structural facts the frame and status gates assert.

    ``cards_outside_sections`` counts card-class elements that are not inside
    a ``<section class="section">`` frame — a card used as a page frame
    rather than a fact container. ``texts`` pairs every element's class
    attribute with the text it carries, so a status element that shows only a
    colour is visible to the gate.
    """

    _TRACKED = ("status-label", "pill", "state-title")

    # Void elements never carry children: pushing them would corrupt the
    # frame depth every later card is judged against (an ``<input>`` inside a
    # section would make every element after it look framed).
    _VOID = frozenset(
        {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, str]] = []
        self.sections = 0
        self.cards_outside_sections = 0
        self.texts: list[tuple[str, str]] = []
        self._open: list[tuple[int, int, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        classes = dict(attrs).get("class") or ""
        depth = len(self.stack)
        if tag == "section":
            self.sections += 1
        if "card" in classes.split() and tag != "section":
            # A card is a fact container. It is legitimate markup only inside
            # a section frame; as the page's own frame it is the anti-pattern
            # VS-5 names. (The safety panels are ``<section class="card">``:
            # a section frame that carries card chrome, not a bare card div.)
            framed = any(name == "section" for name, _outer in self.stack)
            if not framed:
                self.cards_outside_sections += 1
        for token in self._TRACKED:
            if token in classes.split():
                self.texts.append((classes, ""))
                self._open.append((depth, tag, classes))
        if tag not in self._VOID:
            self.stack.append((tag, classes))

    def handle_endtag(self, tag: str) -> None:
        while self.stack:
            name, _classes = self.stack.pop()
            if name == tag:
                break
        self._open = [entry for entry in self._open if entry[0] < len(self.stack)]

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for _depth, _tag, classes in list(self._open):
            for index in range(len(self.texts) - 1, -1, -1):
                if self.texts[index][0] == classes:
                    self.texts[index] = (classes, self.texts[index][1] + data)
                    break


def _scan(base_url: str) -> dict[str, _PageScan]:
    """Scan every served destination's document."""
    scans: dict[str, _PageScan] = {}
    for path in ALL_PATHS + (f"/evidence?record={RECORD_SELECTED}",):
        status, body = _get(base_url, path)
        assert status == 200, path
        scan = _PageScan()
        scan.feed(body)
        scans[path] = scan
    return scans


@pytest.fixture(scope="module")
def scans(base_url: str) -> dict[str, _PageScan]:
    """The structural scan of every document, rendered once for the module."""
    return _scan(base_url)


def test_the_page_frame_is_a_section_never_a_card(scans) -> None:
    """Structure comes from sections, rows, tables and disclosures (VS-5)."""
    for path, scan in scans.items():
        assert scan.sections >= 1, f"{path} has no section frame"
        assert scan.cards_outside_sections == 0, (
            f"{path} uses a card as the page frame — a card is a fact "
            "container inside a section, not the frame"
        )


def test_no_status_is_carried_by_colour_alone(scans) -> None:
    """Every status label and pill carries words (VS-3, AX-1)."""
    for path, scan in scans.items():
        for classes, text in scan.texts:
            assert text.strip(), f"{path}: {classes!r} renders no text"


# --- boundaries: five layers, one sublayer, no new runtime dependency -------


def test_the_five_engine_layers_are_unchanged() -> None:
    """``criterion.layers.present`` stays 5 (ARC-7)."""
    from skilltrace.commands.health import health_report

    report = health_report(REPO_ROOT)
    assert len(report.layers) == 5
    assert [layer.line.split(":")[0] for layer in report.layers] == [
        "graph",
        "evidence",
        "execution",
        "policy",
        "resources",
    ]


def test_the_interface_sublayer_is_a_one_way_seam() -> None:
    """ADR 0007: the sublayer reads the engine, and nothing reads it back.

    Two directions, both architectural facts rather than style preferences:
    no engine module imports ``web.interface`` (the engine would then depend
    on a presentation layer), and the sublayer imports no page, router or
    server module (it would then depend on the surface it is supposed to be
    independent of).
    """
    engine_root = REPO_ROOT / "src" / "skilltrace"
    upward: list[str] = []
    for path in engine_root.rglob("*.py"):
        relative = path.relative_to(engine_root)
        if relative.parts[0] == "web":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("from ") and "web.interface" in stripped:
                upward.append(f"{relative}: {stripped}")
    assert upward == [], f"the engine reached into the sublayer: {upward}"

    downward: list[str] = []
    for path in (engine_root / "web" / "interface").glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("from "):
                continue
            for surface in ("views", "handler", "server", "launch"):
                if f"from ..{surface}" in stripped:
                    downward.append(f"{path.name}: {stripped}")
    assert downward == [], f"the sublayer reached above itself: {downward}"


def test_no_new_runtime_dependency() -> None:
    """The runtime dependency set is still PyYAML alone (ARC-8)."""
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["dependencies"] == ["PyYAML>=6.0"]
