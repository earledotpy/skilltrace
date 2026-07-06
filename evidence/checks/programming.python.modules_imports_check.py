"""Objective gate checker for programming.python.modules_imports_01.

Asserts results that can only be produced by reaching for the standard library —
`datetime` for calendar arithmetic, `math` for integer roots, `collections` for
frequency counting. Exit 0 means the learner imported and used the right module
to get the stated answer; a wrong answer rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_modules_imports_solution.py")

    # days_between("YYYY-MM-DD", "YYYY-MM-DD") -> whole days between the dates (datetime)
    check(
        sol.days_between("2026-01-01", "2026-01-31") == 30,
        "days_between should count 30 days across January",
    )

    # sqrt_floor(n) -> integer part of the square root (math)
    check(sol.sqrt_floor(17) == 4, "sqrt_floor(17) should be 4")
    check(sol.sqrt_floor(25) == 5, "sqrt_floor(25) should be 5")

    # most_common_char(s) -> the single most frequent character (collections)
    check(sol.most_common_char("banana") == "a", "most_common_char('banana') should be 'a'")

    print("programming.python.modules_imports_01: all checks passed.")


if __name__ == "__main__":
    main()
