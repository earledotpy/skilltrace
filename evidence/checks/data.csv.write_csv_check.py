"""Objective gate checker for data.csv.write_csv_01.

Task: ``write_rows(path, rows)`` writes ``rows`` (a list of dicts sharing keys)
to a CSV at ``path`` with a header row. The checker round-trips: it calls
``write_rows`` into a temp file, then reads that file back with the standard
library's ``csv.DictReader`` and confirms it recovers exactly the rows written —
header included, values intact, no blank lines. Exit 0 means the write produced
a well-formed CSV another reader can parse; a missing header, wrong delimiter,
or lost row rejects.
"""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from _loader import check, load_solution

_ROWS = [
    {"city": "Austin", "count": "3"},
    {"city": "Denver", "count": "1"},
    {"city": "Boston", "count": "5"},
]


def main() -> None:
    sol = load_solution("csv_write_csv_solution.py", subdir="data")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.csv"
        sol.write_rows(str(out), _ROWS)
        check(out.exists(), f"write_rows should create a file at the given path ({out})")
        with out.open(newline="", encoding="utf-8") as fh:
            recovered = [dict(row) for row in csv.DictReader(fh)]

    check(
        recovered == _ROWS,
        f"reading the written CSV back should recover the rows written; got {recovered}",
    )
    print("data.csv.write_csv_01: all checks passed.")


if __name__ == "__main__":
    main()
