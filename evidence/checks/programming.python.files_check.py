"""Objective gate checker for programming.python.files_01.

Verifies the learner's file read/write functions by round-tripping real data
through a temporary file: write a list of lines, read them back, and assert they
survive. Exit 0 means the write and read functions actually persist and recover
the data; a broken one rejects. Uses a temp file so the check leaves no artifact
behind.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_files_solution.py")

    lines = ["first line", "second line", "third line"]
    with tempfile.TemporaryDirectory() as tmp:
        target = str(Path(tmp) / "roundtrip.txt")

        # write_lines(path, lines) writes each line to the file at path.
        sol.write_lines(target, lines)
        check(Path(target).exists(), "write_lines did not create the file")

        # read_lines(path) returns the lines back (without trailing newlines).
        got = sol.read_lines(target)
    check(got == lines, f"read_lines should return {lines!r}, got {got!r}")

    print("programming.python.files_01: all checks passed.")


if __name__ == "__main__":
    main()
