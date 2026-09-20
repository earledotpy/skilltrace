#!/usr/bin/env python3
"""v0.3.0-rc1 exit-gate runner (issue #8).

Runs the roadmap's documented v0.3 exit-gate sequence and exits non-zero if any
step fails, so an RC sign-off is a single repeatable command:

    python scripts/exit_gate_v03.py

Steps (roadmap v0.3 "Exit gate"):

    1. pytest tests/graph
    2. skilltrace validate graph
    3. skilltrace next --minutes 60 --limit 5 --show-locked

The CLI is invoked as `python -m skilltrace` (not the bare `skilltrace` shim) so
the gate runs on a fresh clone without the console script being on PATH, and
offline — nothing here touches the network.

------------------------------------------------------------------------------
Traceability — roadmap v0.3 test list → the test that covers each item
------------------------------------------------------------------------------
Each bullet in the roadmap's "Tests" list for v0.3 maps to at least one test.
Kept here (not just in code) because "each item traceable to a test" is the
issue's acceptance criterion.

  * valid seed graph passes
        tests/graph/test_validation.py::test_seed_graph_validates_clean
        tests/graph/test_exit_gate_integration.py::test_exit_gate_sequence_all_exit_zero
  * duplicate node ID fails
        tests/graph/test_validation.py::test_duplicate_node_id_fails_naming_the_id
        tests/graph/test_exit_gate_fixtures.py::test_duplicate_node_id_fails_through_the_loader
  * missing edge source/target fails
        tests/graph/test_validation.py::test_missing_edge_source_fails
        tests/graph/test_validation.py::test_missing_edge_target_fails
        tests/graph/test_exit_gate_fixtures.py::test_missing_edge_source_fails_through_the_loader
        tests/graph/test_exit_gate_fixtures.py::test_missing_edge_target_fails_through_the_loader
  * hard-prerequisite cycle fails
        tests/graph/test_validation.py::test_hard_prerequisite_three_node_cycle_fails_with_path
        tests/graph/test_exit_gate_fixtures.py::test_hard_prerequisite_cycle_fails_through_the_loader
  * frontmatter containing state/prerequisites/unlocks fails loading
        tests/graph/test_nodes.py::test_forbidden_scalar_key_fails_naming_file_and_key
        tests/graph/test_nodes.py::test_forbidden_block_key_with_list_fails
        tests/graph/test_exit_gate_fixtures.py::test_frontmatter_state_key_fails_through_the_loader
  * (edge pruned field — strength — fails loading)
        tests/graph/test_edges.py::test_pruned_field_fails_naming_edge_and_field
        tests/graph/test_exit_gate_fixtures.py::test_edge_strength_field_fails_through_the_loader
  * sync never writes active/passed/mastered
        tests/graph/test_readiness.py::test_sync_never_writes_asserted_progress
        tests/graph/test_sync_command.py::test_sync_flips_target_available_after_source_passed
  * adding a hard prerequisite re-locks an un-started node but never an
    active/passed/mastered one
        tests/graph/test_readiness.py::test_adding_hard_prereq_relocks_an_unstarted_node
        tests/graph/test_readiness.py::test_adding_hard_prereq_never_relocks_a_started_node
  * locked node is never recommended as available
        tests/graph/test_recommendation.py::test_locked_node_never_recommended_even_with_show_locked
  * roadmap anchor never controls locking (or recommendation)
        tests/graph/test_roadmap_anchor.py::test_anchor_does_not_lock_a_node
        tests/graph/test_roadmap_anchor.py::test_anchor_does_not_remove_a_node_from_recommendations
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# (label, argv) for each gate step. The CLI steps go through `python -m
# skilltrace` so no console-script shim on PATH is required.
STEPS: list[tuple[str, list[str]]] = [
    ("pytest tests/graph", [sys.executable, "-m", "pytest", "tests/graph", "-q"]),
    ("validate graph", [sys.executable, "-m", "skilltrace", "validate", "graph"]),
    (
        "next --minutes 60 --limit 5 --show-locked",
        [sys.executable, "-m", "skilltrace", "next", "--minutes", "60", "--limit", "5", "--show-locked"],
    ),
]


def main() -> int:
    failures: list[str] = []
    for label, argv in STEPS:
        print(f"\n=== v0.3 exit gate: {label} ===", flush=True)
        result = subprocess.run(argv, cwd=REPO_ROOT)
        if result.returncode != 0:
            failures.append(label)

    print("\n" + "=" * 60)
    if failures:
        print(f"v0.3 exit gate FAILED: {', '.join(failures)}")
        return 1
    print("v0.3 exit gate PASSED: all steps green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
