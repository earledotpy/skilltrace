"""Shared SQLite harness for the objective-gated ``data.sql.*`` checkers.

Every SQL node's objective gate is the honest "does your query return exactly
these rows?" check. This module ships the fixed dataset once — an in-memory
SQLite database seeded from the literals below — so each checker only has to
state its task's expected rows. Nothing here touches the filesystem beyond
reading the learner's ``.sql`` text, so there is no ``data/*.db`` artifact and
the run is deterministic.

The learner writes one SQL statement to a fixed path under
``evidence/artifacts/data/`` (gitignored — the seed ships the harness and the
checkers, never the learner's query). ``run_learner_query`` executes it against
a freshly seeded database and returns the result rows for the checker to
compare. A missing solution is a clean ``SystemExit`` instruction, not a
traceback.

The dataset — two small tables an ML practitioner would recognise as a join —
is chosen so every task's expected result is exact (clean group averages, no
ties in the sorted task). Keep the seed and the checkers' expected rows in
lockstep: changing a salary here changes several expected results.
"""

from __future__ import annotations

import sqlite3

from _loader import check, solution_path

__all__ = ["check", "run_learner_query"]

# id, name, location
_DEPARTMENTS = [
    (1, "Engineering", "Austin"),
    (2, "Sales", "Denver"),
    (3, "Marketing", "Austin"),
]

# id, name, department_id, salary, hire_year
_EMPLOYEES = [
    (1, "Alice", 1, 120000, 2019),
    (2, "Bob", 1, 100000, 2020),
    (3, "Carol", 2, 80000, 2018),
    (4, "Dan", 2, 70000, 2021),
    (5, "Eve", 3, 90000, 2019),
    (6, "Frank", 1, 110000, 2022),
    (7, "Grace", 3, 105000, 2020),
    (8, "Heidi", 2, 60000, 2023),
]

_SCHEMA = """
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    salary INTEGER NOT NULL,
    hire_year INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments (id)
);
"""


def _seeded_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO departments VALUES (?, ?, ?)", _DEPARTMENTS)
    conn.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", _EMPLOYEES)
    conn.commit()
    return conn


def run_learner_query(filename: str) -> list[tuple]:
    """Execute the learner's single SQL statement and return its result rows.

    Reads the query text from ``evidence/artifacts/data/<filename>``, runs it
    against a freshly seeded in-memory database, and returns the rows as a list
    of tuples. A missing file, an empty query, or a SQL error exits non-zero with
    a message — all "you haven't written a correct query yet" signals, never a
    silent pass.
    """
    path = solution_path(filename, subdir="data")
    if not path.exists():
        raise SystemExit(
            f"no query found at {path} — write your SQL statement there first "
            "(see the node's Learning target for the exact question to answer)."
        )
    query = path.read_text(encoding="utf-8").strip()
    check(query, f"the query file {path.name} is empty — write your SQL statement")

    conn = _seeded_connection()
    try:
        try:
            cursor = conn.execute(query)
        except sqlite3.Error as exc:
            raise SystemExit(f"FAILED: your query did not run — {exc}") from exc
        return cursor.fetchall()
    finally:
        conn.close()
