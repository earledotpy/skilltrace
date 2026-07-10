"""Objective gate checker for data.csv.read_csv_01.

Task: ``read_rows(path)`` opens the CSV at ``path`` and returns its data rows as
a list of dicts keyed by the header, in file order. The checker calls it on a
shipped three-row ``people.csv`` and compares the result exactly. Exit 0 means
the header was used as keys and every row parsed; a missing row, a dropped
column, or including the header as data rejects.

The dataset ships alongside this checker (not under the gitignored artifacts
dir); the node body names its path so the learner can read the same file.
"""

from __future__ import annotations

from pathlib import Path

from _loader import check, load_solution

_DATASET = Path(__file__).resolve().parent / "data" / "datasets" / "people.csv"

# csv reads every field as a string, so the ages stay strings here too.
_EXPECTED = [
    {"name": "Alice", "age": "30", "city": "Austin"},
    {"name": "Bob", "age": "25", "city": "Denver"},
    {"name": "Carol", "age": "35", "city": "Austin"},
]


def main() -> None:
    sol = load_solution("csv_read_csv_solution.py", subdir="data")
    rows = sol.read_rows(str(_DATASET))
    # Normalise each row to a plain dict so a csv.DictReader row (an OrderedDict
    # subclass) or any mapping compares equal on content.
    normalized = [dict(row) for row in rows]
    check(
        normalized == _EXPECTED,
        f"read_rows should return one dict per data row keyed by the header; got {normalized}",
    )
    print("data.csv.read_csv_01: all checks passed.")


if __name__ == "__main__":
    main()
