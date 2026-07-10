"""Objective gate checker for programming.python.functions_01.

Imports the learner's solution and asserts the *stated behavior* of the three
functions the node asks them to write. Exit 0 means the code does what the node
states; a failed check (or an error in the solution) raises and exits non-zero —
the rejection verdict the objective gate records.

Not a proxy check: it calls the actual functions and compares return values
against the contract stated in the node body.
"""

from __future__ import annotations

from _loader import check, load_solution


def main() -> None:
    sol = load_solution("python_functions_solution.py")

    # rectangle_area(width, height) -> width * height
    check(sol.rectangle_area(4, 5) == 20, "rectangle_area(4, 5) should be 20")
    check(sol.rectangle_area(3, 3) == 9, "rectangle_area(3, 3) should be 9")

    # celsius_to_fahrenheit(c) -> c * 9/5 + 32
    check(sol.celsius_to_fahrenheit(0) == 32, "celsius_to_fahrenheit(0) should be 32")
    check(sol.celsius_to_fahrenheit(100) == 212, "celsius_to_fahrenheit(100) should be 212")

    # greet(name) -> "Hello, <name>!"
    check(sol.greet("Ada") == "Hello, Ada!", "greet('Ada') should be 'Hello, Ada!'")

    print("programming.python.functions_01: all checks passed.")


if __name__ == "__main__":
    main()
