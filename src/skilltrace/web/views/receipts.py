"""Gate-run receipt rendering (spec-v3-study-day §10.9).

An objective gate freezes a bounded receipt onto the evidence record it judged:
the executed command, the repository-relative inputs, the exit class and any
available output hashes. The evidence workspace and the contextual inspector
both show that receipt through this module, so the two surfaces cannot drift
about what the gate recorded.

The receipt is *provenance*, never authority: it never changes a verdict or
eligibility, and the raw gate output is not stored — only its hash.
"""

from __future__ import annotations

from ._shared import _esc
from .sections import Rows


def receipt_rows(receipt: dict) -> str:
    """One receipt as labelled fact rows — canonical facts, no raw output."""
    argv = " ".join(str(token) for token in receipt.get("command_argv") or [])
    inputs = ", ".join(str(item) for item in receipt.get("inputs") or [])
    pairs: list[tuple[str, str]] = [
        ("Command", f"<code>{_esc(argv)}</code>"),
        (
            "Inputs",
            f"<code>{_esc(inputs)}</code>"
            if inputs
            else '<span class="mut">No repository input was named</span>',
        ),
        ("Result", _esc(str(receipt.get("exit_class") or ""))),
    ]
    if receipt.get("exit_code") is not None:
        pairs.append(("Exit code", _esc(str(receipt["exit_code"]))))
    stdout_hash = receipt.get("stdout_hash")
    if stdout_hash:
        pairs.append(("Output hash", f"<code>{_esc(stdout_hash)}</code>"))
    stderr_hash = receipt.get("stderr_hash")
    if stderr_hash:
        pairs.append(("Error output hash", f"<code>{_esc(stderr_hash)}</code>"))
    return Rows(tuple(pairs), separated=True).render()


def receipt_disclosure(record, *, summary: str) -> str:
    """One record's receipt behind a disclosure, or ``""`` when it has none."""
    receipt = getattr(record, "gate_run", None)
    if not receipt:
        return ""
    return (
        '<details class="disclosure">\n'
        f"<summary>{_esc(summary)}</summary>\n"
        f"{receipt_rows(receipt)}"
        "</details>\n"
    )
