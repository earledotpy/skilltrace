"""Objective gate checker for programming.python.dictionaries_01.

Asserts the dictionary-building and lookup functions the node asks for. Exit 0
means each creates, indexes, or transforms a dict to the stated result; a wrong
result rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_dictionaries_solution.py")

    # word_count(text) -> {word: number of occurrences}
    check(
        sol.word_count("a b a c b a") == {"a": 3, "b": 2, "c": 1},
        "word_count('a b a c b a') should be {'a': 3, 'b': 2, 'c': 1}",
    )

    # get_or_default(d, key, default) -> the value, or default when the key is absent
    check(sol.get_or_default({"x": 1}, "x", 0) == 1, "get_or_default should return the value")
    check(sol.get_or_default({"x": 1}, "y", 0) == 0, "get_or_default should fall back to default")

    # invert(d) -> {value: key}
    check(sol.invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}, "invert swaps keys and values")

    print("programming.python.dictionaries_01: all checks passed.")


if __name__ == "__main__":
    main()
