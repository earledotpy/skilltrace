"""Objective gate checker for data.sql.select_basics_01.

Task: return the ``name`` and ``salary`` of every employee. Exit 0 means the
learner's SELECT projected exactly those two columns for all eight employees;
any missing row, extra column, or wrong value rejects. Row order is not the
skill here, so the comparison is order-insensitive.
"""

from __future__ import annotations

from _sql import check, run_learner_query

_EXPECTED = sorted(
    [
        ("Alice", 120000),
        ("Bob", 100000),
        ("Carol", 80000),
        ("Dan", 70000),
        ("Eve", 90000),
        ("Frank", 110000),
        ("Grace", 105000),
        ("Heidi", 60000),
    ]
)


def main() -> None:
    rows = run_learner_query("sql_select_basics_solution.sql")
    check(
        sorted(rows) == _EXPECTED,
        "query should return (name, salary) for all eight employees; "
        f"got {sorted(rows)!r}",
    )
    print("data.sql.select_basics_01: all checks passed.")


if __name__ == "__main__":
    main()
