"""Gate-run receipt provenance — one module for schema, build, validate, for_share.

A gate-run receipt is metadata on an objective-gate evidence record: how the
gate's verifier was invoked (argv, root-relative inputs, exit class, optional
exit code and output hashes). Receipts never judge, never touch eligibility,
passing, or readiness, and never carry raw gate output.

This module is the single receipt interface (issue #202):

- schema constants (key, allowed/required keys, exit classes, hash prefix),
- `build` (objective submit attaches via this builder),
- `validate` (evidence load validates via this same module),
- `for_share` (share-profile paths denial drops the whole receipt),
- `normalize_stream` (the one platform-normalization place affecting hashes).

`submission.py`, `evidence.py`, `portfolio/redaction.py`, and
`commands/submit.py` are thin adapters over this module.
"""

from __future__ import annotations

import hashlib
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._schema import EvidenceLoadError

#: Record key carrying the receipt mapping.
GATE_RUN_KEY = "gate_run"

#: Closed receipt key set (unknown keys fail like unknown record keys).
GATE_RUN_ALLOWED: frozenset[str] = frozenset(
    {
        "command_argv",
        "inputs",
        "exit_class",
        "exit_code",
        "stdout_hash",
        "stderr_hash",
        "tool",
        "version",
    }
)

#: Required receipt keys (presence-checked; `tool`/`version` stay unpopulated).
GATE_RUN_REQUIRED: tuple[str, ...] = ("command_argv", "inputs", "exit_class")

#: The two — and only two — exit classes. Inability to run is not a class.
EXIT_PASSED = "passed"
EXIT_FAILED = "failed"
EXIT_CLASSES: frozenset[str] = frozenset({EXIT_PASSED, EXIT_FAILED})

HASH_PREFIX = "sha256:"


def normalize_stream(text: str) -> str:
    """Platform-stable form of one captured gate output stream.

    The single normalization place in the builder/runner contract: CRLF
    becomes LF so a gate printing ``"\\n"`` hashes identically everywhere.
    Both the submit runner and the receipt hasher funnel through here.
    """
    return text.replace("\r\n", "\n")


def hash_stream(text: str) -> str:
    """`sha256:<hex>` over the normalized UTF-8 bytes of one stream."""
    return HASH_PREFIX + hashlib.sha256(normalize_stream(text).encode("utf-8")).hexdigest()


def exit_class_for(exit_code: int) -> str:
    """The receipt exit class for one gate exit code (0 → passed, else failed)."""
    return EXIT_PASSED if exit_code == 0 else EXIT_FAILED


@dataclass(frozen=True)
class GateReceipt:
    """Typed gate-run receipt (wire form is a plain dict for YAML)."""

    command_argv: tuple[str, ...]
    inputs: tuple[str, ...]
    exit_class: str
    exit_code: int | None = None
    stdout_hash: str | None = None
    stderr_hash: str | None = None
    tool: None = None
    version: None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "command_argv": list(self.command_argv),
            "inputs": list(self.inputs),
            "exit_class": self.exit_class,
        }
        if self.exit_code is not None:
            out["exit_code"] = self.exit_code
        if self.stdout_hash is not None:
            out["stdout_hash"] = self.stdout_hash
        if self.stderr_hash is not None:
            out["stderr_hash"] = self.stderr_hash
        return out


def build(
    command: str,
    location: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    root: Path | str | None = None,
    exists: Callable[[Path], bool] | None = None,
) -> dict[str, Any]:
    """Freeze the bounded `gate_run` receipt for one objective judgment.

    `command_argv` is the exact executed argv (`shlex.split`); `inputs` is
    the submitted artifact first, then every argv token resolving to an
    existing file under the repo root, deduplicated, root-relative, forward
    slashes. Each non-empty captured stream contributes its normalized hash
    — raw output never crosses the boundary. `tool`/`version` stay absent in
    v2.2. Without a root (or an `exists` probe) the receipt carries the
    artifact alone.
    """
    argv = shlex.split(command)
    inputs = [location]
    if root is not None and exists is not None:
        root_path = Path(root)
        for token in argv:
            candidate = root_path / token
            try:
                is_file = exists(candidate)
            except OSError:
                continue
            if not is_file:
                continue
            try:
                rel = candidate.resolve().relative_to(root_path.resolve())
            except ValueError:
                continue  # outside the repo — not an input
            rel_posix = rel.as_posix()
            if rel_posix not in inputs:
                inputs.append(rel_posix)
    inputs[1:] = sorted(inputs[1:])
    typed = GateReceipt(
        command_argv=tuple(argv),
        inputs=tuple(inputs),
        exit_class=exit_class_for(exit_code),
        exit_code=exit_code,
        stdout_hash=hash_stream(stdout) if stdout else None,
        stderr_hash=hash_stream(stderr) if stderr else None,
    )
    return typed.to_dict()


def validate(raw: dict[str, Any] | None, *, ident: str = "evidence record", where: str = "") -> dict[str, Any] | None:
    """Validate an optional receipt mapping, returning a copy (or None).

    Absent (`None`/missing) is valid — pre-v2.2 and manual records carry
    none. Raises `EvidenceLoadError` naming the record on a non-mapping,
    unknown key, missing required key, empty argv, bad exit class/code,
    populated `tool`/`version`, or malformed hash field.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EvidenceLoadError(
            f"{where}{ident} has non-mapping {GATE_RUN_KEY} {raw!r} — expected a "
            "gate-run receipt mapping."
        )
    unknown = sorted(set(raw) - GATE_RUN_ALLOWED)
    if unknown:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown {GATE_RUN_KEY} field(s): {', '.join(unknown)}."
        )
    missing = [key for key in GATE_RUN_REQUIRED if raw.get(key) is None]
    if missing:
        raise EvidenceLoadError(
            f"{where}{ident} has {GATE_RUN_KEY} missing required field(s): "
            f"{', '.join(missing)}."
        )
    for key in ("command_argv", "inputs"):
        value = raw[key]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise EvidenceLoadError(
                f"{where}{ident} has non-string-list {GATE_RUN_KEY}.{key} {value!r}."
            )
    if not raw["command_argv"]:
        raise EvidenceLoadError(
            f"{where}{ident} has empty {GATE_RUN_KEY}.command_argv — a receipt "
            "referencing nothing is not provenance."
        )
    if raw["exit_class"] not in EXIT_CLASSES:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown {GATE_RUN_KEY}.exit_class "
            f"{raw['exit_class']!r} — expected one of {', '.join(sorted(EXIT_CLASSES))}."
        )
    exit_code = raw.get("exit_code")
    if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
        raise EvidenceLoadError(
            f"{where}{ident} has non-integer {GATE_RUN_KEY}.exit_code {exit_code!r}."
        )
    for key in ("tool", "version"):
        if raw.get(key) is not None:
            raise EvidenceLoadError(
                f"{where}{ident} has populated {GATE_RUN_KEY}.{key} {raw[key]!r} — "
                "tool/version stay unpopulated in v2.2."
            )
    for key in ("stdout_hash", "stderr_hash"):
        value = raw.get(key)
        if value is None:
            continue
        if (
            not isinstance(value, str)
            or not value.startswith(HASH_PREFIX)
            or len(value) <= len(HASH_PREFIX)
            or any(c not in "0123456789abcdef" for c in value[len(HASH_PREFIX):])
        ):
            raise EvidenceLoadError(
                f"{where}{ident} has malformed {GATE_RUN_KEY}.{key} {value!r} — "
                "expected sha256:<hex> over the captured stream."
            )
    return dict(raw)


def for_share(receipt: dict[str, Any] | None, *, include_paths: bool) -> dict[str, Any] | None:
    """Share-profile view of one receipt: denied paths drop the whole receipt.

    The receipt is path-bearing provenance (`command_argv`/`inputs`), so it
    rides the *paths* dimension: denied it drops entirely (hashes and exit
    class never justify leaking where a checker ran); granted it passes
    through as a copy. `None` stays `None`.
    """
    if receipt is None:
        return None
    return dict(receipt) if include_paths else None


def capture(record: object) -> dict[str, Any] | None:
    """Copy one record's `gate_run` receipt into selection state (never redacts)."""
    receipt = getattr(record, GATE_RUN_KEY, None)
    return dict(receipt) if receipt is not None else None
