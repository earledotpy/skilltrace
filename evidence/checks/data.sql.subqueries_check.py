"""Objective gate checker for data.sql.subqueries_01.

Task: return the names of employees who earn more than the company-wide average
salary. The threshold must be computed by a subquery — ``(SELECT AVG(salary)
FROM employees)`` — not hardcoded, though the checker can only observe the rows;
a hardcoded 91875 that happens to match is acceptable for a single honest
learner (the honesty rule governs the author, not adversarial-proofing). Order
is not the skill, so the comparison is order-insensitive.
"""

from __future__ import annotations

from _sql import check, run_learner_query

# Company average salary = 735000 / 8 = 91875.0; strictly greater than it:
# Alice 120k, Bob 100k, Frank 110k, Grace 105k (Eve at 90k falls below).
_EXPECTED = sorted([("Alice",), ("Bob",), ("Frank",), ("Grace",)])


def main() -> None:
    rows = run_learner_query("sql_subqueries_solution.sql")
    check(
        sorted(rows) == _EXPECTED,
        "query should return names earning above the company average "
        f"[Alice, Bob, Frank, Grace]; got {sorted(rows)!r}",
    )
    print("data.sql.subqueries_01: all checks passed.")


if __name__ == "__main__":
    main()
