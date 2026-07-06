"""Objective gate checker for programming.python.variables_01.

Asserts the module-level values the node asks the learner to compute with
variables and expressions. Exit 0 means each name holds the stated result of its
expression; a wrong value fails the check and rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_variables_solution.py")

    # seconds_per_day = 24 * 60 * 60
    check(sol.seconds_per_day == 86400, "seconds_per_day should be 86400")

    # total_cost = price * quantity + tax, for price=4.90, quantity=5, tax=2.00
    check(sol.total_cost == 26.5, "total_cost should be 26.5 (4.90 * 5 + 2.00)")

    # average = the mean of 10, 20, 30
    check(sol.average == 20.0, "average should be 20.0 (mean of 10, 20, 30)")

    print("programming.python.variables_01: all checks passed.")


if __name__ == "__main__":
    main()
