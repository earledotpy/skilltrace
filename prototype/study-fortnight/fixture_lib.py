"""fortnight-fixture v0 — isolated fabricated inputs for P-StudyFortnight (#292).

Builds a throwaway SkillTrace fixture root from this repo's shared,
read-only material (graph/nodes, edges, resources, evidence specs/gates,
policy) plus fabricated learner records. Never touches the real
graph/state.yaml, evidence/, or execution/ — the real dirty working tree is
never reset. Fabricated history is labeled and isolated.

THROWAWAY decision aid for wayfinder map #289, ticket #292. Never read by
the engine. Never automates pass_node, master_node, or delete_record.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE_BASE = Path(__file__).resolve().parent / "fixture"

# Shared, read-only material copied into every fixture (curriculum + evidence
# definitions + policy values; never learner records).
SHARED_COPY = [
    (Path("graph") / "nodes", True),
    (Path("graph") / "edges.yaml", False),
    (Path("graph") / "resources.yaml", False),
    (Path("evidence"), True),
    (Path("policy"), True),
]


def build_fixture(name: str) -> Path:
    """Create fixture <name> from shared material + fabricated empty progress."""
    dest = FIXTURE_BASE / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel, is_dir in SHARED_COPY:
        src = REPO / rel
        target = dest / rel
        if is_dir:
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    (dest / "graph" / "state.yaml").write_text("progress: {}\n", encoding="utf-8")
    # Empty execution + evidence record stores (fabricated isolation).
    for rel, content in [
        ("execution/sessions.yaml", "sessions: []\n"),
        ("execution/session_work.yaml", "session_work: []\n"),
        ("execution/blockers.yaml", "blockers: []\n"),
        ("execution/remediation_actions.yaml", "remediation_actions: []\n"),
        ("execution/reviews.yaml", "reviews: []\n"),
        ("execution/events.yaml", "events: []\n"),
        ("evidence/evidence_records.yaml", "evidence_records: []\n"),
        ("evidence/attempts.yaml", "attempts: []\n"),
    ]:
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return dest


def clock_at(day: str, hh: int = 9, mm: int = 0):
    """Fixed UTC clock for the fixture sim (Day 1 = 2026-09-22)."""
    dt = datetime.fromisoformat(f"{day}T{hh:02d}:{mm:02d}:00+00:00")
    return lambda: dt.astimezone(timezone.utc)


def run_step(root: Path, clock, argv: list[str]) -> tuple[int, str]:
    """Run one skilltrace command against the fixture root with the fixture
    clock; capture stdout/stderr as text. Read-only or fixture-local mutating
    only; never pass/master/delete."""
    out = io.StringIO()
    err = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            from skilltrace.cli import run as cli_run

            code = cli_run(argv, root=str(root), clock=clock)
        except SystemExit as exc:  # argparse errors
            code = exc.code if isinstance(exc.code, int) else 1
    text = out.getvalue()
    if err.getvalue():
        text += "\n[stderr]\n" + err.getvalue()
    return code, text


class Recorder:
    """Captures labeled steps into a day report structure."""

    def __init__(self) -> None:
        self.days: list[dict] = []
        self._day: dict | None = None

    def day(self, label: str, day_id: str) -> None:
        self._day = {
            "label": label,
            "day": day_id,
            "steps": [],
            "friction": [],
            "uncertainty": [],
        }
        self.days.append(self._day)

    def step(self, name: str, argv: list[str], root: Path, clock) -> str:
        code, text = run_step(root, clock, argv)
        self._day["steps"].append(
            {"name": name, "argv": " ".join(argv), "exit": code, "output": text}
        )
        return text

    def note(self, kind: str, text: str) -> None:
        self._day[kind].append(text)

    def write(self, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps({"days": self.days}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
