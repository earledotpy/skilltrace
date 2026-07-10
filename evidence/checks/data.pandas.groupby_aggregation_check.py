"""Objective gate checker for data.pandas.groupby_aggregation_01.

Task: ``revenue_by_region(df)`` returns a Series of total revenue per region
(``df.groupby("region")["revenue"].sum()``). Exit 0 means the grouping and the
sum are both right; a wrong aggregate or grouping key rejects. The result is
compared as a ``{region: total}`` mapping, so the Series index order is not the
skill.
"""

from __future__ import annotations

from _pandas import check, load_solution, sales_df

# North: 100 + 150 + 60 = 310; South: 80 + 360 + 40 = 480.
_EXPECTED = {"North": 310, "South": 480}


def main() -> None:
    sol = load_solution("pandas_groupby_aggregation_solution.py", subdir="data")
    result = sol.revenue_by_region(sales_df())

    try:
        as_dict = {str(k): int(v) for k, v in result.items()}
    except (AttributeError, TypeError) as exc:
        raise SystemExit(
            f"FAILED: revenue_by_region should return a Series of totals per region ({exc})"
        ) from exc

    check(
        as_dict == _EXPECTED,
        f"revenue_by_region should total revenue per region {_EXPECTED}; got {as_dict}",
    )
    print("data.pandas.groupby_aggregation_01: all checks passed.")


if __name__ == "__main__":
    main()
