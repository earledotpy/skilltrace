"""Human affordance labels — two vocabularies, one module.

The dispatcher commands carry no presentation vocabulary (they are the
engine's action layer), and the ``NextAction`` facts carry intents, not
words. This module is the one place the sublayer names what a human act
*is*, for both:

* **Fact labels** (:func:`intent_label`) — keyed to the ``mentor.cards``
  ``Intent`` literal set (``start | submit_evidence | pass |
  schedule_review | explore``). This is what a rendered ``NextAction``
  affordance shows; a fact's ``command`` string is never rendered by the
  web. A missing label fails at import (via the structure check).
* **Command labels** (:func:`command_label`) — keyed to the registered
  dispatcher command names a view's forms nest-dispatch (the write
  paths). A declared affordance without a command label fails the
  sublayer check.

``{title}`` placeholders in either map are filled by the page composers.
"""

from __future__ import annotations

# Fact-intent labels: keyed to mentor.cards.Intent — the rendered
# affordance vocabulary (the web never renders the CLI command string).
FACT_AFFORDANCE_LABELS: dict[str, str] = {
    "start": "Start this session",
    "submit_evidence": "Submit your next piece of evidence",
    "pass": "Mark {title} passed",
    "schedule_review": "Schedule a review",
    "explore": "Explore what this unlocks",
}

# Command labels: keyed to the registered dispatcher command names (the
# write paths a view's forms nest-dispatch; validated at serve boot).
COMMAND_AFFORDANCE_LABELS: dict[str, str] = {
    "start": "Start this session",
    "evidence submit": "Submit your next piece of evidence",
    "pass": "Mark {title} passed",
    "master": "Mark {title} mastered",
    "work": "Record this work session",
    "attempt record": "Record a practice attempt",
    "session close": "Close this session",
    "blocker create": "Record the blocker",
    "blocker resolve": "Clear the blocker",
    "remediation create": "Record remediation",
    "remediation complete": "Complete remediation",
    "sync": "Sync your readiness",
    "review schedule": "Schedule a review",
    "review complete": "Complete the review",
    "review cancel": "Cancel the review",
    "export markdown": "Export your readiness",
    "export sqlite": "Export your readiness",
    "export html": "Export your readiness",
    "check-resource": "Check a resource now",
    "check-resources": "Check resources now",
}


def intent_label(intent: str, title: str | None = None) -> str:
    """The human affordance for one ``NextAction`` intent (fact vocabulary)."""
    try:
        raw = FACT_AFFORDANCE_LABELS[intent]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"no human affordance label for fact intent {intent!r} — add one "
            "to interface.affordances.FACT_AFFORDANCE_LABELS"
        ) from exc
    if "{title}" in raw:
        return raw.format(title=title) if title else raw.replace("{title}", "this").strip()
    return raw


def command_label(command: str, title: str | None = None) -> str:
    """The human affordance for one registered dispatcher command."""
    try:
        raw = COMMAND_AFFORDANCE_LABELS[command]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"no human affordance label for command {command!r} — add one "
            "to interface.affordances.COMMAND_AFFORDANCE_LABELS"
        ) from exc
    if "{title}" in raw:
        return raw.format(title=title) if title else raw.replace("{title}", "this").strip()
    return raw
