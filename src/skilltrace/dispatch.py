"""Command registry and dispatcher.

The dispatcher is the single chokepoint for the two cross-cutting rules
(roadmap decision 13):

1. **Audit** — a *mutating* command that succeeds appends exactly one event to
   the log; a *read-only* command appends none. Commands never write the event
   log themselves; the dispatcher does it, so the guarantee cannot drift.
2. **Automation boundary** — before a command runs, if it carries an
   `automation_action`, that action is checked and a forbidden one is refused
   with a non-zero exit *before* the handler runs and without logging an event.

Command handlers stay thin: they do the work and report which records they
touched via `CommandResult`. Classification (read-only vs mutating) lives on the
`Command`, so the audit rule is declarative.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .automation import check_automation
from .events import append_event


class Kind(str, Enum):
    """Whether a command may mutate files (and therefore must log an event)."""

    READ_ONLY = "read_only"
    MUTATING = "mutating"


@dataclass
class Context:
    """Everything a handler needs: the repo root and parsed arguments."""

    root: Path
    args: argparse.Namespace


@dataclass
class CommandResult:
    """What a handler reports back to the dispatcher.

    `records_touched` is meaningful only for mutating commands; it becomes the
    audit event's record list. `exit_code` non-zero means the command failed and
    no event is logged even for a mutating command.
    """

    records_touched: list[str] = field(default_factory=list)
    exit_code: int = 0


Handler = Callable[[Context], CommandResult]


@dataclass
class Command:
    """A registered subcommand."""

    name: str  # dispatch key and display name, e.g. "validate graph"
    kind: Kind
    handler: Handler
    help: str = ""
    # Optional automation-boundary label checked before dispatch. None means the
    # command is a plain learner action with no boundary gate.
    automation_action: str | None = None


class Registry:
    """An ordered collection of registered commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> Command:
        if command.name in self._commands:
            raise ValueError(f"Command already registered: {command.name}")
        self._commands[command.name] = command
        return command

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def names(self) -> list[str]:
        return list(self._commands)

    def all(self) -> list[Command]:
        return list(self._commands.values())


def _event_args(args: argparse.Namespace) -> dict[str, Any]:
    """Serialize invocation arguments for the audit log.

    Internal/plumbing fields (leading underscore, plus `root`) are dropped;
    Paths are stringified so the event stays plain, diffable YAML.
    """
    result: dict[str, Any] = {}
    for key, value in vars(args).items():
        if key.startswith("_") or key == "root":
            continue
        result[key] = str(value) if isinstance(value, Path) else value
    return result


def dispatch(command: Command, ctx: Context) -> int:
    """Run one command, enforcing the automation boundary and audit rule.

    Returns the process exit code.
    """
    # 1. Automation boundary — refuse forbidden actions before doing anything.
    if command.automation_action is not None:
        verdict = check_automation(command.automation_action, ctx.root)
        if verdict.forbidden:
            print(f"[REFUSED] {command.name}: {verdict.reason}")
            return 2

    # 2. Run the handler.
    result = command.handler(ctx)

    # 3. Audit — exactly one event for a mutating command that succeeded.
    if command.kind is Kind.MUTATING and result.exit_code == 0:
        append_event(
            ctx.root,
            command=command.name,
            args=_event_args(ctx.args),
            records_touched=result.records_touched,
        )

    return result.exit_code
