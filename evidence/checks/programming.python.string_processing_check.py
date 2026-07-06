"""Objective gate checker for programming.python.string_processing_01.

Asserts the string-transformation functions the node asks for. Exit 0 means each
cleans, splits, or measures its input string to the stated result; a wrong
result rejects.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_string_processing_solution.py")

    # normalize(s) -> surrounding whitespace stripped, lower-cased
    check(sol.normalize("  Hello World  ") == "hello world", "normalize should strip and lower-case")

    # initials(full_name) -> dotted upper-case initials, e.g. "Ada Lovelace" -> "A.L."
    check(sol.initials("Ada Lovelace") == "A.L.", "initials('Ada Lovelace') should be 'A.L.'")
    check(
        sol.initials("grace brewster hopper") == "G.B.H.",
        "initials should handle any number of names, upper-cased",
    )

    # count_vowels(s) -> number of vowels (a, e, i, o, u), case-insensitive
    check(sol.count_vowels("Education") == 5, "count_vowels('Education') should be 5")

    print("programming.python.string_processing_01: all checks passed.")


if __name__ == "__main__":
    main()
