# Windows Install Notes (Fresh clone)

These instructions cover a clean, offline-capable install from a fresh clone on Windows and troubleshooting notes specific to Windows consoles and encoding.

Prerequisites
- Git available on PATH.
- Python 3.14 installed and on PATH (python --version should report 3.14+).

Steps
1. Clone the repo and change directory:

   git clone https://github.com/earledotpy/skilltrace.git
   cd skilltrace

2. Create and activate a venv (PowerShell):

   python -m venv .venv
   .\.venv\Scripts\Activate

   (Command Prompt: .venv\Scripts\activate.bat)

3. Upgrade pip and install in editable mode:

   python -m pip install --upgrade pip
   pip install -e .

4. Verify the install:

   skilltrace health

   On seed data a clean install should exit 0 with OK status.

Windows console encoding note
- The CLI configures UTF-8 output for Windows consoles (em-dash and Unicode rendering) in cli.py. If you still see mojibake, try:

  - Use Windows Terminal or PowerShell which already prefer UTF-8 in newer Windows.
  - Run `chcp 65001` before invoking the CLI to set the console code page to UTF-8.

Troubleshooting
- "skilltrace is not recognized": Ensure the venv is activated and pip install -e . finished successfully.
- Python version error: Confirm `python --version` is >= 3.14.
- PyYAML import error: `pip install PyYAML>=6.0` inside the active venv.
- If Windows blocks script execution: prefer PowerShell with default execution policy; do not change system policies unless you understand security implications.

Notes for packagers
- v1 release tags and assets are in GitHub Releases. v1 is intended to install from a fresh clone; packaging (wheel, sdist, executables) is out of scope for v1 but may be added post-v1.

Contact
- For install problems, open an issue on the repository with your platform, Python version, and `skilltrace health` output attached.
