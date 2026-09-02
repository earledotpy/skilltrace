"""Event-log analytics package (v1.6).

Pure derivation layer for the four analytics themes: velocity, blockers,
reviews, and evidence. All public entry points live in ``derive.py``;
``models.py`` carries the typed view shapes consumed by the CLI and web
surfaces. No I/O, no wall-clock calls in this package — every function
that produces time-keyed output takes ``today: datetime.date`` as a
required keyword argument (T-TestArch D1).
"""
