"""Objective gate checker for programming.python.comprehensions_01.

Asserts the results the node asks the learner to produce with comprehensions.
The gate judges *behavior*, not syntax — but each stated result is the natural
product of a list or dict comprehension over the input. A wrong result rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_comprehensions_solution.py")

    # evens(nums) -> the even numbers, in order
    check(sol.evens([1, 2, 3, 4, 5, 6]) == [2, 4, 6], "evens should keep the even numbers")

    # square_map(nums) -> {n: n*n}
    check(sol.square_map([2, 3, 4]) == {2: 4, 3: 9, 4: 16}, "square_map maps n to n*n")

    # long_words(words, min_len) -> words at least min_len long
    check(
        sol.long_words(["a", "bb", "ccc", "dddd"], 3) == ["ccc", "dddd"],
        "long_words should keep words with length >= min_len",
    )

    print("programming.python.comprehensions_01: all checks passed.")


if __name__ == "__main__":
    main()
