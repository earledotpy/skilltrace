"""Serve shell — stdlib-only local web server (Tier-1 slice T2, ADR 0006).

`skilltrace serve` (alias `st ui`) binds `127.0.0.1` only — there is no
`--host` flag by design — on port 8341 unless `--port` says otherwise, and
fails fast with a clear message when the port is already taken. After a
successful bind it opens the browser at the served URL (`--no-browser` opts
out) and runs in the foreground until Ctrl+C. The command registers
READ_ONLY: it appends no audit event itself; later slices' browser mutations
nest-dispatch through the same registry as the CLI (G2#66). Truth files are
read fresh per request by the handler; `data/*` is never touched.
"""

from __future__ import annotations

import errno
import webbrowser
from pathlib import Path

from http.server import ThreadingHTTPServer

from ..dispatch import Command, CommandResult, Context, Kind, Registry
from .handler import SkillTraceHandler

DEFAULT_PORT = 8341


class SkillTraceServer(ThreadingHTTPServer):
    """Loopback-only server carrying the resolved repo root.

    ``allow_reuse_address`` stays off: on Windows SO_REUSEADDR would let a
    second server bind a port that is actively serving, defeating ADR 0006's
    fail-fast-if-busy trait. Clean Ctrl+C shutdown keeps the cost of a strict
    bind negligible.
    """

    allow_reuse_address = False
    daemon_threads = True

    def __init__(self, root: Path, port: int) -> None:
        super().__init__(("127.0.0.1", port), SkillTraceHandler)
        self.root = root


def make_server(root: Path, port: int) -> tuple[SkillTraceServer | None, str]:
    """Bind once, up front; report a clear failure instead of half-starting."""
    try:
        return SkillTraceServer(root, port), ""
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            return None, (
                f"serve: cannot bind 127.0.0.1:{port} — address already in use. "
                f"Another skilltrace serve may be running; try --port <other>."
            )
        reason = exc.strerror or str(exc)
        return None, f"serve: cannot bind 127.0.0.1:{port} — {reason}."


def serve(ctx: Context) -> CommandResult:
    """Run until Ctrl+C. The root was resolved once by the CLI before dispatch."""
    server, failure = make_server(Path(ctx.root), ctx.args.port)
    if server is None:
        print(failure)
        return CommandResult(exit_code=1)

    url = f"http://127.0.0.1:{server.server_port}"
    print(f"serve: serving {ctx.root}")
    print(f"  {url}  (Ctrl+C to stop)")
    if not ctx.args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nserve: stopped.")
    finally:
        server.server_close()
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="serve",
            kind=Kind.READ_ONLY,
            handler=serve,
            help="Run the local web UI on loopback (foreground; read-only).",
        )
    )
