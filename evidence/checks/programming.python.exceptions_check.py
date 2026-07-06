"""Objective gate checker for programming.python.exceptions_01.

Verifies that the learner's functions *catch* the stated errors and return the
fallback rather than propagating — the substance of try/except. Exit 0 means the
happy path returns the real result and the failing path is caught and handled; a
function that lets the exception escape (or returns the wrong fallback) rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_exceptions_solution.py")

    # safe_divide(a, b) -> a / b, or None when b == 0 (ZeroDivisionError caught)
    check(sol.safe_divide(10, 2) == 5, "safe_divide(10, 2) should be 5")
    check(sol.safe_divide(1, 0) is None, "safe_divide(1, 0) should catch and return None")

    # parse_int(s) -> int(s), or None when s is not an integer (ValueError caught)
    check(sol.parse_int("42") == 42, "parse_int('42') should be 42")
    check(sol.parse_int("not a number") is None, "parse_int of junk should return None")

    print("programming.python.exceptions_01: all checks passed.")


if __name__ == "__main__":
    main()
