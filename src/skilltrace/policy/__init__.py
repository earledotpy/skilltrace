"""Policy layer (v0.6): hard boundaries enforced, advisory values loaded.

Seed values live in `policy/*.yaml` (curriculum-agnostic data, never engine
code). The one exception is the automation boundary's forbidden trio, which
is code-authoritative (`skilltrace.automation.FORBIDDEN_ACTIONS`, ADR 0004):
the YAML must agree with the constants, and `validate policy` fails when it
does not.
"""
