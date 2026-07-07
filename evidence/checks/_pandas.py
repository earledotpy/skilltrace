"""Shared Pandas harness for the objective-gated ``data.pandas.*`` checkers.

Every Pandas node's objective gate imports the learner's solution and calls the
function the node asks for on a *fixed input* — the small ``sales`` frame (and,
for the merge node, ``regions``) built below. Embedding the input in code rather
than shipping a CSV keeps the run deterministic, lets the node body show the
learner the exact data, and avoids any ``data/*.db``-style artifact.

Results are compared through ``canonical_rows`` — a sorted list of row tuples —
so the check is order-insensitive wherever row order is not the skill, while
``columns_of`` pins column identity and order separately. The numbers are chosen
so every derived value is exact (revenue/units divides cleanly), so a correct
solution never fails on floating-point noise.
"""

from __future__ import annotations

import pandas as pd

from _loader import check, load_solution

__all__ = ["check", "load_solution", "sales_df", "regions_df", "canonical_rows", "columns_of"]


def sales_df() -> pd.DataFrame:
    """The fixed six-row sales table every Pandas checker feeds its solution."""
    return pd.DataFrame(
        {
            "region": ["North", "North", "South", "South", "North", "South"],
            "product": ["Widget", "Gadget", "Widget", "Gadget", "Widget", "Widget"],
            "units": [10, 5, 8, 12, 6, 4],
            "revenue": [100, 150, 80, 360, 60, 40],
        }
    )


def regions_df() -> pd.DataFrame:
    """The region-to-manager lookup table the merge node joins against."""
    return pd.DataFrame({"region": ["North", "South"], "manager": ["Ivan", "Judy"]})


def canonical_rows(df: pd.DataFrame) -> list[tuple]:
    """A DataFrame's rows as a sorted list of plain tuples (order-insensitive)."""
    return sorted(tuple(row) for row in df.itertuples(index=False, name=None))


def columns_of(df: pd.DataFrame) -> list[str]:
    """The DataFrame's column labels in order, as plain strings."""
    return [str(col) for col in df.columns]
