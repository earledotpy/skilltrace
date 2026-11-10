"""The axe-core half of the AX-11 gate (spec-v3-study-day §9 AX-11).

AX-11 asks for an automated axe pass over *real fixture data*, cheap
enough to run per slice. This module renders every served route body from
a pinned fixture repo, writes the exact document the shell serves
(:func:`skilltrace.web.views.shell.page`), and runs axe-core over all of
them.

Three rules shape the implementation:

* **No silent passes.** If node, npm, the network or axe-core is not
  available, the test *skips* with the reason spelled out. It never fails
  spuriously and never passes without having checked.
* **No hidden waivers.** A route that axe reports as failing is either
  fixed or recorded in ``tests/web/A11Y_FINDINGS.md`` with its rule id and
  message, and then skipped *with that reason*. The recorded rule ids are
  asserted against what axe actually reports, so a route's findings can
  never quietly grow — a new violation on a waived route still fails.
* **Nothing outside the repository.** The axe-core install and the driver
  script live in a temporary directory, so no ``node_modules``,
  ``package.json`` or lockfile is ever left in the tree. axe-core is a
  dev-only test dependency (ARC-8), never a runtime one.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from a11y_harness import (
    AXE_DRIVER,
    NODE_ACTIVE,
    AxeToolchain,
    build_fixture_repo,
    ensure_axe_toolchain,
    render_all,
    route_cases,
    run_axe,
)

# The axe-core work directory. It lives under the system temp directory,
# never in the repository — and it persists between runs so the npm install
# is paid once, not once per slice.
AXE_WORKDIR = Path(tempfile.gettempdir()) / "skilltrace-a11y-axe"

# The impacts that block the gate. axe grades an issue by how badly it
# hurts a learner; serious and critical are the two that make a surface
# unusable for someone, and AX-11's floor is WCAG 2.2 AA.
BLOCKING_IMPACTS = frozenset({"serious", "critical"})

# The WCAG 2.2 AA rule sets, as axe names them.
WCAG_AA_TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")

# The findings file: the named debt this gate records rather than hides.
FINDINGS = Path(__file__).resolve().parent / "A11Y_FINDINGS.md"

# The routes whose bodies cannot render at all, and the reason.
# A route that cannot render is *not checked* — it is reported, never
# counted as clean. See tests/web/A11Y_FINDINGS.md.
#
# The map is empty: every route in the normative table renders. It stays
# because the gate that consumes it must fail loudly if a route ever
# breaks again — an unrenderable route has to be *named* to exist, never
# quietly skipped.
UNRENDERABLE: dict[str, str] = {}

# The routes with recorded blocking findings, and the rule ids axe reports
# for them today. Each is recorded in tests/web/A11Y_FINDINGS.md; the
# test asserts the recorded set is exactly what axe reports, so the
# waiver can never widen unnoticed.
RECORDED_FINDINGS: dict[str, frozenset[str]] = {}


@pytest.fixture(scope="module")
def fixture_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A pinned fixture repo: the curriculum copied, learner stores authored."""
    root = tmp_path_factory.mktemp("a11y-fixture")
    return build_fixture_repo(root)


@pytest.fixture(scope="module")
def axe_toolchain() -> AxeToolchain:
    """The axe toolchain, installed outside the repository.

    Skips the module with a clear reason when node, npm or the packages
    are unavailable — the gate then reports "not checked", never "passed".
    """
    toolchain = ensure_axe_toolchain(AXE_WORKDIR)
    if not toolchain.available:
        pytest.skip(f"axe-core is unavailable: {toolchain.reason}")
    return toolchain


@pytest.fixture(scope="module")
def rendered(fixture_repo: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Every route body rendered to the document the shell serves.

    Returns ``(documents, errors)``: the served documents keyed by route
    name, and the error of every route whose body raised.
    """
    return render_all(fixture_repo)


@pytest.fixture(scope="module")
def axe_results(
    axe_toolchain: AxeToolchain, rendered: tuple[dict[str, str], dict[str, str]]
) -> dict[str, list[dict]]:
    """The axe violations per route, for every route that rendered."""
    documents, _errors = rendered
    results = run_axe(axe_toolchain, sorted(documents.items()))
    return {result["name"]: result["violations"] for result in results}


def test_the_toolchain_really_ran(axe_toolchain: AxeToolchain) -> None:
    """The gate did not silently no-op.

    A toolchain that reported itself available but has no axe-core in it
    would make every route look clean. This asserts the parts are there.
    """
    assert (axe_toolchain.workdir / "node_modules" / "axe-core").is_dir()
    assert (axe_toolchain.workdir / "driver.js").is_file()
    assert axe_toolchain.node


def test_the_findings_file_is_present() -> None:
    """The named debt lives in a file next to this gate.

    Without it, a waived route would be an invisible hole.
    """
    assert FINDINGS.exists(), "tests/web/A11Y_FINDINGS.md must exist"


def test_the_route_table_covers_every_served_body() -> None:
    """Every body the web layer serves is in the gate's route table.

    The view package publishes one ``*_body`` function per served route.
    A new route that nobody added to the table would be unchecked by the
    gate and look exactly like a checked, clean route — so the coverage is
    asserted here rather than assumed.
    """
    from skilltrace.web import views

    published = {
        name
        for name in dir(views)
        if name.endswith("_body") and not name.startswith("_")
    }
    covered = {case.body for case in route_cases()}
    assert covered == published, (
        f"the route table covers {sorted(covered)} but the view package "
        f"publishes {sorted(published)}"
    )


def test_the_route_table_covers_every_normative_destination() -> None:
    """Every §6 destination is in the gate's route table (ARC-7).

    The gate's route list is one of the four things the spec repoints at the
    normative table. A destination the spec names but the gate never renders
    would be an unchecked surface that looks exactly like a clean one.
    """
    from skilltrace.web.interface import FROZEN_ROUTES

    covered = {case.route.split(" ", 1)[1].split("?")[0] for case in route_cases()}
    missing = []
    for name, frozen in FROZEN_ROUTES.items():
        if "{" in frozen:
            prefix = frozen.split("{")[0]
            found = any(path.startswith(prefix) for path in covered)
        else:
            found = frozen in covered
        if not found:
            missing.append(f"{name} ({frozen})")
    assert missing == [], (
        "destinations the a11y gate never renders: " + ", ".join(sorted(missing))
    )
    # The table's two extra served paths (RT-14 node-centred, RT-17 preview).
    assert f"/graph/{NODE_ACTIVE}" in covered
    assert "/portfolio/preview" in covered


def test_the_wcag_aa_rule_sets_are_the_ones_asked_for() -> None:
    """The driver runs the WCAG 2.2 AA rule sets, not a subset.

    A subset would make the gate cheaper but weaker; the tag list is
    pinned here so a narrowing of it has to be a deliberate edit.
    """
    for tag in WCAG_AA_TAGS:
        assert f"'{tag}'" in AXE_DRIVER
    assert "runOnly" in AXE_DRIVER


def test_every_route_is_rendered_or_named_as_unrenderable(
    rendered: tuple[dict[str, str], dict[str, str]],
) -> None:
    """The gate covers the whole route table, and names what it cannot.

    A route that renders and is not in the table would be unchecked; a
    route that fails to render and is not named would be a silent hole.
    """
    documents, errors = rendered
    expected = {case.name for case in route_cases()}
    assert set(documents) | set(errors) == expected, (
        f"routes neither rendered nor reported: "
        f"{sorted(expected - (set(documents) | set(errors)))}"
    )
    assert set(errors) == set(UNRENDERABLE), (
        f"unexpected render failures: {sorted(set(errors) - set(UNRENDERABLE))}"
    )


@pytest.mark.parametrize("route", sorted(case.name for case in route_cases()))
def test_route_has_no_serious_or_critical_violations(
    route: str,
    rendered: tuple[dict[str, str], dict[str, str]],
    axe_results: dict[str, list[dict]],
) -> None:
    """One route: zero axe violations of impact serious or critical.

    The failure message names the rule id and the offending node targets,
    so the fix can be made without re-running the tool by hand.
    """
    documents, errors = rendered
    if route in errors:
        pytest.skip(f"{route} did not render, so it was not checked: {errors[route]}")
    assert route in documents
    violations = axe_results.get(route, [])
    blocking = [
        violation
        for violation in violations
        if violation["impact"] in BLOCKING_IMPACTS
    ]
    recorded = RECORDED_FINDINGS.get(route)
    if recorded is None:
        assert blocking == [], _describe(route, blocking)
        return
    # A recorded route: the waiver may not widen. The rule ids axe reports
    # must be exactly the recorded ones.
    found = {violation["id"] for violation in blocking}
    assert found == set(recorded), (
        f"{route}: the recorded findings changed — axe now reports "
        f"{sorted(found)}, the findings file records {sorted(recorded)}. "
        f"Fix the violation and drop the record, or record the new one.\n"
        + _describe(route, blocking)
    )
    pytest.skip(
        f"{route} has recorded axe findings ({', '.join(sorted(found))}); "
        f"see tests/web/A11Y_FINDINGS.md"
    )


def _describe(route: str, violations: list[dict]) -> str:
    """A failure message that names the rule ids and the node targets."""
    lines = [f"axe reported serious/critical WCAG 2.2 AA violations on {route}:"]
    for violation in violations:
        targets = "; ".join(
            " ".join(str(part) for part in node["target"]) for node in violation["nodes"]
        )
        lines.append(
            f"  {violation['id']} ({violation['impact']}) — "
            f"{violation.get('help', '')}\n    targets: {targets}"
        )
    return "\n".join(lines)


def test_every_recorded_finding_is_written_down() -> None:
    """Each recorded finding names its route and its rule id in the file.

    A finding nobody can find is a hidden waiver.
    """
    text = FINDINGS.read_text(encoding="utf-8")
    for route, rule_ids in RECORDED_FINDINGS.items():
        assert route in text, f"the finding for {route} is not recorded"
        for rule_id in rule_ids:
            assert rule_id in text, f"the rule id {rule_id} ({route}) is not recorded"


def test_every_unrenderable_route_is_written_down() -> None:
    """Each route that could not render is named in the findings file."""
    text = FINDINGS.read_text(encoding="utf-8")
    for route in UNRENDERABLE:
        assert route in text, f"the unrenderable route {route} is not recorded"
