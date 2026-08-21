# Install

## Requirements

- Python >= 3.14
- pip
- Git

The only runtime dependency is PyYAML.

## Fresh clone install

```bash
git clone https://github.com/earledotpy/skilltrace.git
cd skilltrace
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install in editable mode:

```bash
pip install -e .
```

This exposes two console scripts: `skilltrace` and `st` (an alias for the same
entry point). You can also run via `python -m skilltrace`.

## Verify the install

```bash
skilltrace health
```

This validates all five data layers and reports any issues. On fresh seed data
it should exit 0 with OK status.

## Offline use

SkillTrace requires no network access after install. All data lives in the
repo's `graph/`, `evidence/`, `execution/`, `policy/`, and `release/`
directories as Markdown and YAML files.

## Troubleshooting

**`skilltrace` is not recognized** -- make sure the virtual environment is
activated and you ran `pip install -e .` from the repo root.

**Python version errors** -- SkillTrace requires Python >= 3.14. Check with
`python --version`.

**PyYAML import errors** -- run `pip install PyYAML>=6.0` inside the active
virtual environment.
