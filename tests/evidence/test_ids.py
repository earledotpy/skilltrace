"""Evidence/attempt ID shape validation and per-node sequence allocation.

Issue #10: `ev.<node_id>.NNN` / `att.<node_id>.NNN` embed a real node ID; the
sequence is allocated max+1 per node — never reused, never backfilled.
"""

from __future__ import annotations

import pytest

from skilltrace.evidence.ids import (
    allocate_attempt_id,
    allocate_evidence_id,
    is_valid_attempt_id,
    is_valid_evidence_id,
    split_attempt_id,
    split_evidence_id,
)

NODE = "math.arithmetic.order_operations_01"


def test_valid_evidence_id_splits_into_node_and_sequence():
    assert split_evidence_id(f"ev.{NODE}.003") == (NODE, 3)
    assert is_valid_evidence_id(f"ev.{NODE}.003")


def test_valid_attempt_id_splits_into_node_and_sequence():
    assert split_attempt_id(f"att.{NODE}.012") == (NODE, 12)
    assert is_valid_attempt_id(f"att.{NODE}.012")


@pytest.mark.parametrize(
    "bad",
    [
        "ev.math.arithmetic.order_operations_01",  # no sequence
        "ev.math.arithmetic.order_operations_01.",  # empty sequence
        "ev.math.arithmetic.order_operations_01.abc",  # non-numeric
        "att.math.arithmetic.order_operations_01.003",  # wrong prefix for evidence
        "ev.notanode.003",  # node id has no numeric suffix segment
        "ev..003",  # empty node id
        "ev.math.arithmetic.order_operations_01.003.004",  # trailing extra is fine? no
        "math.arithmetic.order_operations_01.003",  # missing prefix
        "",
    ],
)
def test_malformed_evidence_ids_rejected(bad):
    assert not is_valid_evidence_id(bad)
    assert split_evidence_id(bad) is None


def test_prefixes_do_not_cross():
    # An attempt id is not a valid evidence id and vice versa.
    assert not is_valid_evidence_id(f"att.{NODE}.001")
    assert not is_valid_attempt_id(f"ev.{NODE}.001")


def test_unicode_digit_sequence_rejected_not_crash():
    # `str.isdigit()` is true for a superscript digit that `int()` refuses; the
    # splitter must reject it cleanly, never raise ValueError.
    assert split_evidence_id(f"ev.{NODE}.³") is None
    assert not is_valid_evidence_id(f"ev.{NODE}.³")


def test_non_string_id_is_not_valid():
    assert not is_valid_evidence_id(None)  # type: ignore[arg-type]
    assert split_attempt_id(12345) is None  # type: ignore[arg-type]


def test_allocate_first_evidence_id_starts_at_one():
    assert allocate_evidence_id(NODE, []) == f"ev.{NODE}.001"


def test_allocate_first_attempt_id_starts_at_one():
    assert allocate_attempt_id(NODE, []) == f"att.{NODE}.001"


def test_allocate_evidence_id_is_max_plus_one_not_count_plus_one():
    # A gap (002 absent) must not be backfilled: next is one past the highest.
    existing = [f"ev.{NODE}.001", f"ev.{NODE}.005"]
    assert allocate_evidence_id(NODE, existing) == f"ev.{NODE}.006"


def test_allocate_ignores_other_nodes_and_other_types():
    other = "programming.python.variables_01"
    existing = [
        f"ev.{other}.009",  # different node
        f"att.{NODE}.007",  # attempt, not evidence
    ]
    # Neither should influence this node's evidence sequence.
    assert allocate_evidence_id(NODE, existing) == f"ev.{NODE}.001"


def test_allocate_attempt_sequence_is_independent_of_evidence():
    existing = [f"ev.{NODE}.004", f"att.{NODE}.002"]
    assert allocate_attempt_id(NODE, existing) == f"att.{NODE}.003"


def test_allocated_ids_are_valid():
    allocated = allocate_evidence_id(NODE, [f"ev.{NODE}.001"])
    assert is_valid_evidence_id(allocated)
