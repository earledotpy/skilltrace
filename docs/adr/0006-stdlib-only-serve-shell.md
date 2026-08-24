# ADR 0006 — Stdlib-only serve shell for the Tier 1 web UI

Date: 2026-08-23
Status: accepted

## Context

Tier 1 (`docs/POST_V1_BACKLOG.md:7-14`) adds a live local web server
(`st ui` / `skilltrace serve`) as the primary daily UI. Map #62's grilling
fixed the surrounding seams before the stack question: G1 (#64) locked the
MVP to the daily loop (today / next / node detail / health + pass/master
behind confirmation modals) targeting v1.1; G2 (#66) locked browser writes to
in-process dispatch through the same registry as the CLI and reads rendered
fresh per request. What remained open (G3, #67) was the serve topology and
stack itself.

Standing constraints made the choice unusual for Python web work: the tool
is single-learner, binds loopback only, has no auth, installs offline, and
ships exactly one runtime dependency (`pyproject.toml`:
`dependencies = ["PyYAML>=6.0"]`, Python >=3.14). The MVP surface is six
routes — four GETs and two confirmed POST flows — all server-rendered HTML
forms, no JavaScript required.

Four options were weighed:

1.  **Stdlib `http.server.ThreadingHTTPServer`** — owned glue (~150–250
    lines: routing, query/form parsing, HTML assembly), zero new deps.
2.  **Flask** — battle-tested routing + Jinja templating, but pulls ~7
    transitive packages (flask, werkzeug, jinja2, click, itsdangerous,
    markupsafe, blinker) for a localhost single-user tool.
3.  **FastAPI + uvicorn + Jinja2** — heaviest chain; async machinery nobody
    needs for one learner; API-oriented where Tier 1 is server-rendered.
4.  **Serving the disposable exports** (`data/export.html`,
    `data/skilltrace.db`) — dead on arrival: exports are never read back by
    the engine (`src/skilltrace/export_data.py:1`, safety boundaries), and
    G1 made live serve primary anyway.

## Decision

Option 1 — **stdlib-only**. The serve shell is
`http.server.ThreadingHTTPServer` behind a thin `BaseHTTPRequestHandler`
router living in a new `src/skilltrace/web/` subpackage (deliberately not
named `interface/` or `views/`, the cut layer's vocabulary per ADR 0002).
`serve` registers as a READ_ONLY command (+ `ui` alias) so the CLI stays
self-describing; it appends no event itself, while browser mutations ride
G2's nested dispatch. Reads call `load_context_lenient` fresh on every
request — no cache, no file-watch. Pages reuse the existing `render.py`
helpers verbatim with mechanical line→HTML transforms; styling is one inline
`<style>` block, so there is no static-file routing at all. Serve traits:
port 8341 default with fail-fast-if-busy (`--port` override), browser
auto-open (`--no-browser` opt-out), foreground process until Ctrl+C,
loopback bind with no `--host` flag.

## Consequences

*   Zero supply-chain growth: offline install stays `PyYAML`-clean; the
    Python floor and dependency list are untouched by the entire Tier 1
    server effort.
*   The project owns its HTTP glue and escaping discipline instead of
    borrowing Flask's — acceptable because the surface is six routes;
    escaping correctness must be pinned by tests, not trusted to memory.
*   HTML is assembled in code, not templates. If the mechanical
    `render.py` transforms prove crusty during build slices, the sanctioned
    escalation is refactoring `render.py` into structured section data
    consumed by both surfaces — never parallel hand-declared vocabulary,
    which would recreate the drift ADR 0002 cut.
*   Reversal cost is a serve-shell rewrite plus a new ADR; the daily-view
    specs, route table, and domain seams survive any such swap unchanged.

See: ADR 0002, Map #62, G1 #64, G2 #66, G3 #67.
