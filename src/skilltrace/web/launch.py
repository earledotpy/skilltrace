"""The launch program behind `./start.sh` (issue #366).

Why this exists. The v3 product made the web UI the learner's primary surface,
but reaching it was a developer path: clone, create a virtualenv, activate it,
`pip install -e .`, know that the command is `st`, and be standing in the right
directory. This module removes the last four. It is a *launcher*, not an engine
command: it is never registered with the dispatcher, never appears in
`st --help`, and never writes a truth file. The run it hands off to is `serve`,
which is READ_ONLY and appends no event (ADR 0006).

The decisions this file implements:

* **The root is pinned, never discovered.** `./start.sh` passes the directory
  the script lives in; that is the repository. No ancestor walk, no cwd, so the
  silent wrong-root failure cannot recur on this path at all.
* **A running instance that serves this same root is reused** rather than
  collided with. Anything else occupying a port is walked past, up to
  :data:`PORT_RANGE` ports above `serve`'s default.
* **An explicit `--port` means exactly that port.** `serve`'s fail-fast-if-busy
  trait is untouched, so a busy explicit port still reports itself.
* **Nothing is remembered.** No port memory, no root memory, no PID file, no
  daemon: the process runs in the foreground until it is stopped, and the
  terminal window is the stop affordance.

Identity, honestly. Nothing a served page exposes names its root, so "is the
instance on 8341 mine?" is answered by comparison: the pages at
:data:`FINGERPRINT_PATHS` are fetched and compared with what *this* root
renders for the same paths. `/health` alone is not enough — two roots that
differ only in curriculum text render the same counts — so `/` is compared too.
A render or fetch that cannot be completed counts as "not mine", which falls
through to the port walk: reuse is an optimisation, and failing to prove it
must never block a launch.
"""

from __future__ import annotations

import argparse
import socket
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from ..paths import is_repo_root
from .server import DEFAULT_PORT

# How many ports above `serve`'s default the launcher will try. Small on
# purpose: a bounded range is something the learner can reason about, an
# arbitrary scan is not.
PORT_RANGE = 10

# The pages that identify a root. `/` carries curriculum text plus the derived
# state; `/health` carries the per-layer counts and diagnostics.
FINGERPRINT_PATHS = ("/", "/health")

PROBE_TIMEOUT_SECONDS = 5


def _served_page(port: int, path: str) -> str | None:
    """The page `path` served on loopback `port`, or None if nothing answers."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}{path}", timeout=PROBE_TIMEOUT_SECONDS
        ) as response:
            if response.status != 200:
                return None
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError):
        return None


def _rendered_page(root: Path, path: str) -> str | None:
    """The same page rendered locally from `root` (the comparison baseline)."""
    from .views import health_body, home_body, page, route_default_mode

    body_for = {"/": home_body, "/health": health_body}.get(path)
    if body_for is None:  # pragma: no cover - guarded by FINGERPRINT_PATHS
        return None
    try:
        title, body, _status = body_for(root)
    except Exception:
        # A root that cannot render cannot be proven to be the one on the
        # port, so the answer is "not mine" — the walk continues.
        return None
    return page(title, body, mode=route_default_mode(path))


def _serves_root(port: int, root: Path) -> bool:
    """True when the instance on `port` renders this exact root."""
    for path in FINGERPRINT_PATHS:
        served = _served_page(port, path)
        if served is None:
            return False
        rendered = _rendered_page(root, path)
        if rendered is None or served != rendered:
            return False
    return True


def _port_is_free(port: int) -> bool:
    """True when a loopback listener could bind `port` right now.

    No ``SO_REUSEADDR``: the probe mirrors `SkillTraceServer`'s strict bind
    (``allow_reuse_address = False``, ADR 0006), so "free" here means exactly
    "free for `serve`".
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _pick(root: Path, *, first: int = DEFAULT_PORT, span: int = PORT_RANGE):
    """Choose what to do: ``("reuse", port)``, ``("serve", port)``, ``("none", None)``."""
    for port in range(first, first + span):
        if _serves_root(port, root):
            return "reuse", port
        if _port_is_free(port):
            return "serve", port
    return "none", None


def _dispatch_serve(root: Path, port: int, no_browser: bool) -> int:
    """Hand off to `serve` through the dispatcher.

    Read-only: the dispatcher appends no audit event for a READ_ONLY command,
    and `serve` itself writes nothing, so a launch leaves no trace in the log.
    """
    from ..cli import REGISTRY
    from ..dispatch import Context, dispatch

    command = REGISTRY.get("serve")
    args = argparse.Namespace(port=port, no_browser=no_browser)
    return dispatch(command, Context(root=root, args=args))


def launch(root: Path, *, port: int | None = None, no_browser: bool = False) -> int:
    """Launch the web UI for `root`. Returns a process exit code."""
    root = Path(root).resolve()

    if not is_repo_root(root):
        print(
            f"launch: {root} is not a SkillTrace repository "
            "(no graph/edges.yaml or AGENTS.md) — pass --root <path>",
            file=sys.stderr,
        )
        return 2

    # An explicit port is a request for that port. `serve` still fails fast on
    # a busy one; the launcher does not second-guess or relocate it.
    if port is not None:
        return _dispatch_serve(root, port, no_browser)

    outcome, chosen = _pick(root)

    if outcome == "reuse" and chosen is not None:
        url = f"http://127.0.0.1:{chosen}"
        print(f"launch: already serving {root} at {url}")
        if not no_browser:
            webbrowser.open(url)
        return 0

    if chosen is None:
        print(
            f"launch: no free port in {DEFAULT_PORT}-{DEFAULT_PORT + PORT_RANGE - 1} "
            "— free one, or pass --port <other>",
            file=sys.stderr,
        )
        return 1

    if chosen != DEFAULT_PORT:
        print(
            f"launch: port {DEFAULT_PORT} is not available; using {chosen}"
        )
    return _dispatch_serve(root, chosen, no_browser)


def main(argv: list[str] | None = None) -> int:
    """Console entry for ``python -m skilltrace.web.launch``."""
    parser = argparse.ArgumentParser(
        prog="launch",
        description=(
            "Start the SkillTrace web UI for this repository "
            "(the program behind ./start.sh)."
        ),
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Repository to serve. ./start.sh passes the directory it lives in.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Serve on exactly this port (fails fast if busy, like `st serve`).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser (the URL is still printed).",
    )
    args = parser.parse_args(argv)
    return launch(Path(args.root), port=args.port, no_browser=args.no_browser)


if __name__ == "__main__":
    raise SystemExit(main())
