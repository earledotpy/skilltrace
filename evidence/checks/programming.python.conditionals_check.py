"""Objective gate checker for programming.python.conditionals_01.

Exercises the branching functions the node asks for across each branch. Exit 0
means every branch returns the stated result; a wrong branch rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_conditionals_solution.py")

    # classify(n) -> "negative" / "zero" / "positive"
    check(sol.classify(-3) == "negative", "classify(-3) should be 'negative'")
    check(sol.classify(0) == "zero", "classify(0) should be 'zero'")
    check(sol.classify(7) == "positive", "classify(7) should be 'positive'")

    # is_even(n) -> bool
    check(sol.is_even(4) is True, "is_even(4) should be True")
    check(sol.is_even(5) is False, "is_even(5) should be False")

    # larger(a, b) -> the larger of the two
    check(sol.larger(3, 8) == 8, "larger(3, 8) should be 8")
    check(sol.larger(10, 2) == 10, "larger(10, 2) should be 10")

    print("programming.python.conditionals_01: all checks passed.")


if __name__ == "__main__":
    main()
