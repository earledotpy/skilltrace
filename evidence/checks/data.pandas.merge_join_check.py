"""Objective gate checker for data.pandas.merge_join_01.

Task: ``attach_manager(sales, regions)`` merges the sales frame with the
region-to-manager lookup on ``region``, so every sales row gains its region's
``manager``. Exit 0 means the merge matched on the shared key and kept all six
sales rows; a wrong key, a cross product, or dropped rows reject. Row order is
not the skill, so the comparison is order-insensitive.
"""

from __future__ import annotations

from _pandas import canonical_rows, check, columns_of, load_solution, regions_df, sales_df

_EXPECTED_COLUMNS = ["region", "product", "units", "revenue", "manager"]
_EXPECTED_ROWS = sorted(
    [
        ("North", "Widget", 10, 100, "Ivan"),
        ("North", "Gadget", 5, 150, "Ivan"),
        ("South", "Widget", 8, 80, "Judy"),
        ("South", "Gadget", 12, 360, "Judy"),
        ("North", "Widget", 6, 60, "Ivan"),
        ("South", "Widget", 4, 40, "Judy"),
    ]
)


def main() -> None:
    sol = load_solution("pandas_merge_join_solution.py", subdir="data")
    result = sol.attach_manager(sales_df(), regions_df())

    check(
        columns_of(result) == _EXPECTED_COLUMNS,
        f"attach_manager should add a manager column, giving {_EXPECTED_COLUMNS}; "
        f"got {columns_of(result)}",
    )
    check(
        canonical_rows(result) == _EXPECTED_ROWS,
        f"each sales row should carry its region's manager; got {canonical_rows(result)}",
    )
    print("data.pandas.merge_join_01: all checks passed.")


if __name__ == "__main__":
    main()
