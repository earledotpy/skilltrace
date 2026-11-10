#!/usr/bin/env bash
# SkillTrace launcher — the one entry point from "I have the repository" to
# "I am looking at Today" (issue #366).
#
# This script does exactly one job: find the Python environment this repository
# was installed into, and hand off to `skilltrace.web.launch`, which pins the
# root to *this* directory, reuses a running instance serving the same root,
# and otherwise starts `serve`.
#
# It installs nothing, remembers nothing, and writes nothing. If the
# environment is missing it says so in one sentence and stops.
#
#   ./start.sh                 # http://127.0.0.1:8341 (or the next free port)
#   ./start.sh --no-browser    # do not open a browser; the URL is printed
#   ./start.sh --port 8399     # exactly this port; fails fast if it is busy
set -euo pipefail

REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [ -x "$REPO/.venv/bin/python" ]; then
  PYTHON="$REPO/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import skilltrace' >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  printf '%s\n' \
    "launch: no Python environment with SkillTrace installed was found." \
    "        Set one up first:" \
    "          python3 -m venv .venv && source .venv/bin/activate && pip install -e ." \
    "        Full steps: docs/INSTALL.md" >&2
  exit 2
fi

exec "$PYTHON" -m skilltrace.web.launch --root "$REPO" "$@"
