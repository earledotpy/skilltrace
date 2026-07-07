"""Objective gate checker for data.pandas.dataframe_basics_01.

Task: three small functions over the sales frame that exercise the DataFrame
basics — inspect, summarize, filter:

- ``column_names(df)`` -> the column labels as a list
- ``total_revenue(df)`` -> the sum of the ``revenue`` column
- ``region_rows(df, region)`` -> the rows for one region

Exit 0 means all three return the stated result. Row order is not the skill for
``region_rows``, so that comparison is order-insensitive.
"""

from __future__ import annotations

from _pandas import canonical_rows, check, load_solution, sales_df

_EXPECTED_COLUMNS = ["region", "product", "units", "revenue"]
_EXPECTED_TOTAL = 790  # 100 + 150 + 80 + 360 + 60 + 40
_EXPECTED_NORTH = sorted(
    [
        ("North", "Widget", 10, 100),
        ("North", "Gadget", 5, 150),
        ("North", "Widget", 6, 60),
    ]
)


def main() -> None:
    sol = load_solution("pandas_dataframe_basics_solution.py", subdir="data")

    names = list(sol.column_names(sales_df()))
    check(
        names == _EXPECTED_COLUMNS,
        f"column_names should return {_EXPECTED_COLUMNS}; got {names}",
    )

    total = int(sol.total_revenue(sales_df()))
    check(
        total == _EXPECTED_TOTAL,
        f"total_revenue should sum the revenue column to {_EXPECTED_TOTAL}; got {total}",
    )

    north = sol.region_rows(sales_df(), "North")
    check(
        canonical_rows(north) == _EXPECTED_NORTH,
        f"region_rows(df, 'North') should return the three North rows; got {canonical_rows(north)}",
    )
    print("data.pandas.dataframe_basics_01: all checks passed.")


if __name__ == "__main__":
    main()
