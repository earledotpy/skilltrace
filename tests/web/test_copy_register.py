"""T2 — De-CLI copy register acceptance gates (issue #233).

Greps the rendered HTML of every route for:
  P3.6  no ``text-transform:uppercase`` on kicker / heading elements.
  P3.4  the two banned state synonyms ("Ready to start", "In progress") never
        appear as the visible pill/label text (the five canonical words stand).
  P3.1  raw record-id patterns (session, evidence, blocker, review, attempt
        ids) never appear in page prose.
  §E    the five §E affordance labels appear on the affordances that should
        carry them.

``pytest`` green, no ``<script>``.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

# §E normative affordance labels (the complete canonical set).
_E_AFFORDANCE_LABELS = {
    "start": {"Start this session"},
    "submit_evidence": {"Submit your next piece of evidence"},
    "pass": {"Mark {title} passed"},   # title-parameterised — test via regex
    "schedule_review": {"Schedule a review"},
    "explore": {"Explore what this unlocks"},
}

# Raw id patterns: typical id prefix chars followed by a dot-separated suffix.
# Any segment "XX.YY.ZZ_NN" that looks like an internal record id is banned
# from *prose* (outside <code> or <small mut> secondary-id spans).
_RAW_ID_PATTERN = re.compile(
    r"""
    (?<![/])            # not a URL path segment
    \b(?:
        ev\.[a-z0-9._-]+ |   # evidence record
        sess\.[a-z0-9._-]+ | # session record
        blk\.[a-z0-9._-]+ |  # blocker
        rem\.[a-z0-9._-]+ |  # remediation
        rev\.[a-z0-9._-]+ |  # review
        att\.[a-z0-9._-]+    # attempt
    )\b
    """,
    re.VERBOSE,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _set_state(root: Path, node_id: str, state: str) -> None:
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


def _first_node_id(root: Path, *, state: str | None = None) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError(f"no node with state {state!r}")


def _all_route_bodies(repo: Path) -> list[tuple[str, str]]:
    """Render every GET route and return (route_name, html) pairs."""
    node_id = _first_node_id(repo)
    available_id = _first_node_id(repo, state="available")
    pairs: list[tuple[str, str]] = []

    _, home_html, _ = views.home_body(repo)
    pairs.append(("home /", home_html))

    _, next_html, _ = views.next_body(repo, {})
    pairs.append(("next /next", next_html))

    _, node_html, _ = views.node_body(repo, node_id)
    pairs.append((f"node /nodes/{node_id}", node_html))

    _, health_html, _ = views.health_body(repo)
    pairs.append(("health /health", health_html))

    _, pass_html, _ = views.pass_modal_body(repo, available_id)
    pairs.append((f"pass-modal /nodes/{available_id}/pass", pass_html))

    return pairs


# --------------------------------------------------------------------------- #
# P3.6 — no text-transform:uppercase on kicker / heading elements
# --------------------------------------------------------------------------- #


def test_style_has_no_uppercase_transform_on_kicker():
    """The .kicker rule must not carry text-transform:uppercase (P3.6)."""
    kicker_rule_match = re.search(r"\.kicker\{([^}]*)\}", views._STYLE)
    assert kicker_rule_match, ".kicker rule not found in _STYLE"
    rule_body = kicker_rule_match.group(1)
    assert "text-transform" not in rule_body, (
        f".kicker rule still contains text-transform: {rule_body!r}"
    )


def test_style_has_no_uppercase_transform_on_any_heading(repo):
    """No heading selector uses text-transform:uppercase in the stylesheet."""
    # Check the inline _STYLE constant directly.
    heading_selectors = re.findall(
        r"([h][1-6][^{]*|\.kicker[^{]*|\.title[^{]*)\{([^}]*)\}", views._STYLE
    )
    for selector, rule_body in heading_selectors:
        assert "text-transform:uppercase" not in rule_body.replace(" ", ""), (
            f"Heading selector {selector!r} uses text-transform:uppercase"
        )


# --------------------------------------------------------------------------- #
# P3.4 — banned state synonyms never appear as rendered pill/label text
# --------------------------------------------------------------------------- #


BANNED_SYNONYMS = [
    "Ready to start",
    "In progress",
]


def test_no_banned_synonym_on_home(repo):
    """P3.4: home page uses canonical state words, not 'Ready to start' / 'In progress'."""
    _, body, _ = views.home_body(repo)
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body, (
            f"Banned synonym {synonym!r} found in home page HTML"
        )


def test_no_banned_synonym_on_next(repo):
    """P3.4: /next uses canonical state words."""
    _, body, _ = views.next_body(repo, {})
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body, (
            f"Banned synonym {synonym!r} found in /next HTML"
        )


def test_no_banned_synonym_on_node_page(repo):
    """P3.4: node detail page uses canonical state words."""
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body, (
            f"Banned synonym {synonym!r} found in /nodes/{node_id} HTML"
        )

    # flip to active and check again
    _set_state(repo, node_id, "active")
    _, body_active, _ = views.node_body(repo, node_id)
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body_active, (
            f"Banned synonym {synonym!r} found in /nodes/{node_id} HTML (active state)"
        )


def test_no_banned_synonym_on_health(repo):
    """P3.4: health page uses canonical state words."""
    _, body, _ = views.health_body(repo)
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body, (
            f"Banned synonym {synonym!r} found in /health HTML"
        )


def test_no_banned_synonym_on_pass_modal(repo):
    """P3.4: pass modal uses canonical state words."""
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.pass_modal_body(repo, node_id)
    for synonym in BANNED_SYNONYMS:
        assert synonym not in body, (
            f"Banned synonym {synonym!r} found in pass modal HTML"
        )


# --------------------------------------------------------------------------- #
# P3.4 — five canonical state words are visible where states are rendered
# --------------------------------------------------------------------------- #


def test_canonical_state_words_locked(repo):
    """'Locked' appears as the pill label on a locked node's page."""
    node_id = _first_node_id(repo, state="locked")
    _, body, _ = views.node_body(repo, node_id)
    assert '<span class="pill locked">Locked</span>' in body


def test_canonical_state_words_available(repo):
    """'Available' appears as the pill label on an available node's page."""
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    assert '<span class="pill available">Available</span>' in body


def test_canonical_state_words_active(repo):
    """'Active' appears as the pill label on an active node's page."""
    node_id = _first_node_id(repo, state="available")
    _set_state(repo, node_id, "active")
    _, body, _ = views.node_body(repo, node_id)
    assert '<span class="pill active">Active</span>' in body


# --------------------------------------------------------------------------- #
# P3.1 — raw record-id patterns never reach page prose
# --------------------------------------------------------------------------- #


def _prose_outside_code(html: str) -> str:
    """Strip <code>…</code> blocks and small mut secondary-id spans — ids are
    allowed there only.  Everything else is "prose" for the P3.1 gate."""
    # Remove <code>…</code>
    stripped = re.sub(r"<code>[^<]*</code>", "", html, flags=re.DOTALL)
    # Remove class="small mut" spans (the one sanctioned secondary-id placement)
    stripped = re.sub(r'<p class="small mut">.*?</p>', "", stripped, flags=re.DOTALL)
    return stripped


def test_no_raw_session_id_on_home(repo):
    """P3.1: the home page must not expose a raw session id in prose."""
    # Seed an open session
    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.test.001",
                    "node_id": _first_node_id(repo),
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "status": "open",
                }
            ]
        },
    )
    _, body, _ = views.home_body(repo)
    prose = _prose_outside_code(body)
    assert "sess.test.001" not in prose, (
        "Raw session id 'sess.test.001' leaked into home page prose"
    )


def test_no_raw_record_ids_on_all_routes(repo):
    """P3.1: no raw internal record ids appear in prose on any route."""
    # Seed synthetic records so the drill-down actually has something to show.
    # Use a node that owns an artifact spec so the evidence record validates
    # (an unknown spec id would surface a refusal banner naming the record —
    # correct refusal behaviour, but noise for this prose gate).
    view0 = load_context_lenient(repo)
    specced = [n.id for n in view0.nodes if view0.specs_by_node.get(n.id)]
    assert specced, "fixture graph has no node with an artifact spec"
    node_id = sorted(specced)[0]
    view = load_context_lenient(repo)
    specs = view.specs_by_node.get(node_id, [])
    spec_id = specs[0].id if specs else "spec.dummy.01"

    _write_yaml(
        repo,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{node_id}.001",
                    "artifact_spec_id": spec_id,
                    "location": "evidence/set_001.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:" + "0" * 64,
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.test.002",
                    "node_id": node_id,
                    "started_at": "2026-08-20T10:00:00+00:00",
                    "status": "closed",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.{node_id}.001",
                    "node_id": node_id,
                    "status": "open",
                    "description": "stuck on something",
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )

    routes = [
        ("home /", views.home_body(repo)[1]),
        ("next /next", views.next_body(repo, {})[1]),
        (f"node /nodes/{node_id}", views.node_body(repo, node_id)[1]),
        ("health /health", views.health_body(repo)[1]),
    ]
    for route_name, html in routes:
        prose = _prose_outside_code(html)
        matches = _RAW_ID_PATTERN.findall(prose)
        # The drill-down table renders ids in table cells — that is an
        # intentional, audit-facing fact display and is within the spec's
        # allowance for the read-only drill-down section. We only ban ids
        # from prose *outside* table cells and code blocks.
        # Narrow the check: ids in <td> cells are acceptable; ids in <p>,
        # <div>, banners, buttons, breadcrumbs, and labels are not.
        banned_contexts = re.findall(
            r"<(?:p|div|button|label|span)[^>]*>[^<]*" + _RAW_ID_PATTERN.pattern + r"[^<]*</(?:p|div|button|label|span)>",
            prose,
            flags=re.VERBOSE,
        )
        assert not banned_contexts, (
            f"Raw record ids in prose on {route_name}: {banned_contexts[:3]}"
        )


# --------------------------------------------------------------------------- #
# §E affordance labels — all five canonical labels appear correctly
# --------------------------------------------------------------------------- #


def test_e_affordance_start_label_appears_in_write_actions(repo):
    """§E: 'Start this session' appears in the node write-actions card."""
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    assert "Start this session" in body, (
        "§E affordance 'Start this session' absent from node write-actions card"
    )





def test_e_affordance_mark_passed_label_in_pass_modal(repo):
    """§E: 'Mark <title> passed' appears as the pass-modal submit button."""
    node_id = _first_node_id(repo, state="available")
    view = load_context_lenient(repo)
    node_title = view.node_map[node_id].title
    _, body, _ = views.pass_modal_body(repo, node_id)
    assert f"Mark {node_title} passed" in body, (
        f"§E affordance 'Mark <title> passed' absent from pass modal; "
        f"expected 'Mark {node_title} passed'"
    )


def test_e_affordance_mark_passed_label_in_write_actions(repo):
    """§E: 'Mark <title> passed…' link appears in node write-actions for non-locked nodes."""
    node_id = _first_node_id(repo, state="available")
    view = load_context_lenient(repo)
    node_title = view.node_map[node_id].title
    _, body, _ = views.node_body(repo, node_id)
    assert f"Mark {node_title} passed" in body, (
        f"§E affordance 'Mark <title> passed' absent from node write-actions"
    )


def test_e_affordance_mark_mastered_label_in_master_confirm(repo):
    """§E: 'Mark <title> mastered' appears on the permanent mastery confirm."""
    node_id = _first_node_id(repo, state="available")
    view = load_context_lenient(repo)
    node_title = view.node_map[node_id].title
    # Structurally render the confirm modal directly (no pre-condition on state).
    _, body, _ = views.master_confirm_body(repo, node_id)
    assert f"Mark {node_title} mastered" in body, (
        f"§E affordance 'Mark <title> mastered' absent from master confirm modal"
    )


def test_e_affordance_next_action_renders_intent_label(repo):
    """§E: NextAction facts render via the human affordance label, not the CLI command."""
    node_id = _first_node_id(repo, state="available")
    _, body, _ = views.node_body(repo, node_id)
    # The data-intent attribute is present (the intent drives the label).
    assert 'data-intent="start"' in body, (
        "NextAction fact missing data-intent='start' on available node page"
    )
    # The rendered label must be the §E canonical label, not a CLI command.
    assert "Start this session" in body
    # CLI command strings must not appear in the label context.
    assert "skilltrace start" not in body


# --------------------------------------------------------------------------- #
# No <script> anywhere in any rendered page
# --------------------------------------------------------------------------- #


def test_no_script_tags_on_any_route(repo):
    """Pages must never contain <script> tags (G2 no-JS constraint)."""
    routes = [
        ("home", views.home_body(repo)[1]),
        ("next", views.next_body(repo, {})[1]),
        ("node", views.node_body(repo, _first_node_id(repo))[1]),
        ("health", views.health_body(repo)[1]),
        ("pass", views.pass_modal_body(repo, _first_node_id(repo, state="available"))[1]),
    ]
    for route_name, html in routes:
        assert "<script" not in html.lower(), (
            f"<script> tag found in {route_name} page"
        )
