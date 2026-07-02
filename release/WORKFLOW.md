# Release Workflow

Run these commands from the package root.

```bash
python -m compiler.validate_release
python -m compiler.run_smoke_tests
python -m compiler.run_release_tests --allow-mutation
python -m compiler.validate_release
```

The `--allow-mutation` flag is required for the SQLite export test. No test passes or masters a node.
