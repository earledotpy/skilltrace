"""Objective gate checker for data.sql.aggregation_01.

Task: for each department, return the department_id, the number of employees in
it, and their average salary. The skill is GROUP BY with COUNT and AVG, not the
row order, so the comparison is order-insensitive. A missing GROUP BY (which
collapses to one row), the wrong aggregate, or a miscount rejects.
"""

from __future__ import annotations

from _sql import check, run_learner_query

# dept 1: 3 employees, avg (120k+100k+110k)/3 = 110000.0
# dept 2: 3 employees, avg (80k+70k+60k)/3   = 70000.0
# dept 3: 2 employees, avg (90k+105k)/2       = 97500.0
_EXPECTED = sorted(
    [
        (1, 3, 110000.0),
        (2, 3, 70000.0),
        (3, 2, 97500.0),
    ]
)


def main() -> None:
    rows = run_learner_query("sql_aggregation_solution.sql")
    check(
        sorted(rows) == _EXPECTED,
        "query should return (department_id, employee count, average salary) "
        f"per department; got {sorted(rows)!r}",
    )
    print("data.sql.aggregation_01: all checks passed.")


if __name__ == "__main__":
    main()
