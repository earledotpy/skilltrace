"""Objective gate checker for data.sql.joins_01.

Task: pair every employee's name with their department's name. This is an INNER
JOIN of employees to departments on the department key; row order is not the
skill, so the comparison is order-insensitive. A cross join (every name against
every department), the wrong join key, or dropped rows rejects.
"""

from __future__ import annotations

from _sql import check, run_learner_query

_EXPECTED = sorted(
    [
        ("Alice", "Engineering"),
        ("Bob", "Engineering"),
        ("Frank", "Engineering"),
        ("Carol", "Sales"),
        ("Dan", "Sales"),
        ("Heidi", "Sales"),
        ("Eve", "Marketing"),
        ("Grace", "Marketing"),
    ]
)


def main() -> None:
    rows = run_learner_query("sql_joins_solution.sql")
    check(
        sorted(rows) == _EXPECTED,
        "query should return (employee name, department name) for all eight "
        f"employees; got {sorted(rows)!r}",
    )
    print("data.sql.joins_01: all checks passed.")


if __name__ == "__main__":
    main()
