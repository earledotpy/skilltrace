"""Objective gate checker for data.pandas.filtering_selection_01.

Task: ``high_revenue(df)`` returns the rows of the sales frame with revenue at
least 100, keeping only the ``region``, ``product``, and ``revenue`` columns.
Exit 0 means boolean selection and column projection both landed; a wrong
threshold, extra columns, or the wrong rows reject. Row order is not the skill,
so the row comparison is order-insensitive.
"""

from __future__ import annotations

from _pandas import canonical_rows, check, columns_of, load_solution, sales_df

_EXPECTED_COLUMNS = ["region", "product", "revenue"]
_EXPECTED_ROWS = sorted(
    [
        ("North", "Widget", 100),
        ("North", "Gadget", 150),
        ("South", "Gadget", 360),
    ]
)


def main() -> None:
    sol = load_solution("pandas_filtering_selection_solution.py", subdir="data")
    result = sol.high_revenue(sales_df())

    check(
        columns_of(result) == _EXPECTED_COLUMNS,
        f"high_revenue should keep columns {_EXPECTED_COLUMNS}; got {columns_of(result)}",
    )
    check(
        canonical_rows(result) == _EXPECTED_ROWS,
        f"high_revenue should return the rows with revenue >= 100; got {canonical_rows(result)}",
    )
    print("data.pandas.filtering_selection_01: all checks passed.")


if __name__ == "__main__":
    main()
