# Skill Graph AI Learning v0.1.0-rc1

This is the final local-first release-candidate package for the Skill Graph AI Learning system.

## Quick start

```bash
pip install -r requirements.txt
python -m compiler.show_system_health
python -m compiler.show_home
python -m compiler.recommend_next --minutes 60 --limit 5 --show-locked
```

## Release validation

```bash
python -m compiler.validate_release
python -m compiler.run_smoke_tests
python -m compiler.run_release_tests --allow-mutation
python -m compiler.validate_release
```

## Included layers

1. Graph
2. Evidence
3. Execution
4. Interface
5. Policy
6. Release

The package is CLI-first and local-first. It does not include LMS integration, cloud sync, badges, analytics, automatic mastery, or automatic state mutation from dashboard cards.
