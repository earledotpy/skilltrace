"""Objective gate checker for programming.python.lists_loops_01.

Asserts the results of the loop-driven functions the node asks for. Exit 0 means
each accumulates or builds the stated result over its input; a wrong result
rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_lists_loops_solution.py")

    # sum_list(nums) -> the total of the list
    check(sol.sum_list([1, 2, 3, 4]) == 10, "sum_list([1, 2, 3, 4]) should be 10")
    check(sol.sum_list([]) == 0, "sum_list([]) should be 0")

    # count_evens(nums) -> how many are even
    check(sol.count_evens([1, 2, 3, 4, 6]) == 3, "count_evens([1,2,3,4,6]) should be 3")

    # squares_up_to(n) -> [1, 4, 9, ..., n*n]
    check(sol.squares_up_to(4) == [1, 4, 9, 16], "squares_up_to(4) should be [1,4,9,16]")

    print("programming.python.lists_loops_01: all checks passed.")


if __name__ == "__main__":
    main()
