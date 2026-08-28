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

### Test Your Study Cockpit

```bash
# Terminal view of today's study agenda
st today

# Spin up the local browser dashboard (http://127.0.0.1:8341)
st ui
```

---

## 4. Offline & Local-First Operation

SkillTrace requires no internet access during daily operation. All curriculum, progress, evidence, and execution data reside as human-readable Markdown and YAML files in this repository.

---

## 5. Troubleshooting

* **`st` or `skilltrace` command not found:** Ensure your virtual environment is activated and you ran `pip install -e .` from the repository root.
* **Python version incompatible:** SkillTrace requires Python ≥ 3.14. Check your runtime with `python --version`.
* **PyYAML import error:** Run `pip install "PyYAML>=6.0"` inside your active virtual environment.
