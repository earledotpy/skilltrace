"""Execution layer (v0.5): sessions, work items, blockers, remediation, reviews.

Execution records are the learner's study history. They live in
`execution/*.yaml`, reference graph nodes by id, and never compute or store
node state — the only state effect in the layer is `start`/`work` asserting
`active` as a forward move through the guarded progress store.
"""
