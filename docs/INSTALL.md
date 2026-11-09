# Installation Guide

SkillTrace is designed for zero-fuss local development. It requires only standard Python and PyYAML.

---

## 1. System Requirements

* **Python:** ≥ 3.14
* **Tools:** `git`, `pip`
* **Dependencies:** `PyYAML >= 6.0` (installed automatically)

---

## 2. Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/earledotpy/skilltrace.git
cd skilltrace

# 2. Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS / Linux:
source .venv/bin/activate

# 3. Install in editable mode
pip install -e .
```

This registers the `skilltrace` command and its convenience shortcut `st`.

---

## 3. Verification

Run the built-in diagnostic suite to confirm all five data layers are healthy:

```bash
st health
```

On a fresh checkout, `st health` should validate all nodes, edges, gates, execution records, and policies, reporting a clean exit with **OK** status.

### Launch it in one step

```bash
./start.sh
```

`start.sh` is the single entry point once the environment above exists: it
serves **this** repository, opens your browser, and reuses a copy that already
serves the same repository instead of colliding with it. It installs nothing,
remembers nothing, and stops on Ctrl+C. If the environment is missing it says
so in one sentence and points you back here.

### Test Your Study Cockpit

```bash
# Terminal view of today's study agenda
st today

# The same server from the command line (http://127.0.0.1:8341)
st serve        # `st ui` is the same command
```

---

## 4. Offline & Local-First Operation

SkillTrace requires no internet access during daily operation. All curriculum, progress, evidence, and execution data reside as human-readable Markdown and YAML files in this repository.

---

## 5. Troubleshooting

* **`st` or `skilltrace` command not found:** Ensure your virtual environment is activated and you ran `pip install -e .` from the repository root.
* **`./start.sh` says no Python environment was found:** It looked for `.venv/bin/python` in this repository and for an importable `skilltrace` on `python3`, and found neither. Run step 2 above, then launch again.
* **`no SkillTrace repository found at or above …`:** You ran `st` from a directory that is not inside a curriculum repository. `cd` into the repository, or pass `--root <path>` **before** the command (`st --root /path/to/repo today`).
* **A port is reported not available:** `./start.sh` walks up to ten ports past 8341 on its own and says which one it used. A port can be unavailable because another program holds it, or for about a minute after you stopped a SkillTrace of your own (the strict bind in ADR 0006 lets closed connections linger). An explicit `st serve --port <n>` does not relocate — it reports the busy port and stops.
* **Python version incompatible:** SkillTrace requires Python ≥ 3.14. Check your runtime with `python --version`.
* **PyYAML import error:** Run `pip install "PyYAML>=6.0"` inside your active virtual environment.
