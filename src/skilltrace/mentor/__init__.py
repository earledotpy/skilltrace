"""Mentor-voice prose layer (v1.x deepening, issue #144).

One seam for the per-handler `_brief_*` ladders, divergent
`_state_label` tables, and the three duplicated `_resource_lines`
copies. The seam is `mentor.prose.brief_for(state, facts,
perspective)` — a state-keyed dispatch returning a typed
`list[MentorSection]` value, not a template.
"""
