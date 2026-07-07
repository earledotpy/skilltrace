"""Objective gate checker for data.sql.filtering_sorting_01.

Task: return the names of employees earning more than 90000, highest salary
first. Both the filter and the order are the skill here, so the comparison is
order-sensitive: the rows must arrive already sorted by descending salary. A
wrong threshold, a missing ORDER BY, or the wrong direction rejects.
"""

from __future__ import annotations

from _sql import check, run_learner_query

# > 90000, descending by salary: Alice 120k, Frank 110k, Grace 105k, Bob 100k.
_EXPECTED = [("Alice",), ("Frank",), ("Grace",), ("Bob",)]


def main() -> None:
    rows = run_learner_query("sql_filtering_sorting_solution.sql")
    check(
        rows == _EXPECTED,
        "query should return names earning over 90000, highest first "
        f"[Alice, Frank, Grace, Bob]; got {rows!r}",
    )
    print("data.sql.filtering_sorting_01: all checks passed.")


if __name__ == "__main__":
    main()
