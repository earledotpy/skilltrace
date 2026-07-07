"""Objective gate checker for data.pandas.transform_columns_01.

Task: ``add_unit_price(df)`` returns the sales frame with a new ``unit_price``
column equal to ``revenue / units``, leaving the existing columns intact. Exit 0
means the derived column was computed row-wise and appended correctly; a wrong
formula, a dropped column, or a mangled order rejects. The numbers divide
cleanly, so a correct solution never fails on floating-point noise.
"""

from __future__ import annotations

from _pandas import canonical_rows, check, columns_of, load_solution, sales_df

_EXPECTED_COLUMNS = ["region", "product", "units", "revenue", "unit_price"]
# unit_price = revenue / units: 100/10=10, 150/5=30, 80/8=10, 360/12=30, 60/6=10, 40/4=10
_EXPECTED_ROWS = sorted(
    [
        ("North", "Widget", 10, 100, 10.0),
        ("North", "Gadget", 5, 150, 30.0),
        ("South", "Widget", 8, 80, 10.0),
        ("South", "Gadget", 12, 360, 30.0),
        ("North", "Widget", 6, 60, 10.0),
        ("South", "Widget", 4, 40, 10.0),
    ]
)


def main() -> None:
    sol = load_solution("pandas_transform_columns_solution.py", subdir="data")
    result = sol.add_unit_price(sales_df())

    check(
        columns_of(result) == _EXPECTED_COLUMNS,
        f"add_unit_price should append a unit_price column to {_EXPECTED_COLUMNS[:-1]}; "
        f"got columns {columns_of(result)}",
    )
    check(
        canonical_rows(result) == _EXPECTED_ROWS,
        f"unit_price should equal revenue / units per row; got {canonical_rows(result)}",
    )
    print("data.pandas.transform_columns_01: all checks passed.")


if __name__ == "__main__":
    main()
