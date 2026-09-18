"""Assemble the artifact page and the four markdown reports."""
from __future__ import annotations

from pathlib import Path

from build_html import (
    BASE, HAZARDS, HERE, PROBES, REPORTS, UNTESTED,
    find, render_branches, render_candidates, render_days, render_discovery,
    render_hazards, render_hashes, render_health, render_pins, render_repro,
    render_untested, snippet,
)
from day_stories import DAYS
from matrices import BRANCHES, CANDIDATES

CSS = """
:root { --ink:#1a1a1a; --mut:#5b6470; --line:#dfe3e8; --bg:#fbfbfc; --acc:#2f5d8a; --warn:#a2520a; --warm:#fff7ed; --ok:#1f6f43; }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif; color:var(--ink); background:var(--bg); }
main { max-width:1180px; margin:0 auto; padding:28px 22px 90px; }
h1 { font-size:26px; margin:0 0 6px; } h2 { font-size:20px; margin:38px 0 8px; border-bottom:2px solid var(--line); padding-bottom:6px; }
h3 { font-size:16px; margin:22px 0 8px; } .date { color:var(--mut); font-weight:400; font-size:13px; }
.shape { display:block; color:var(--mut); font-size:12.5px; font-weight:400; margin-top:2px; }
.throw { background:#3a2410; color:#ffd9a8; padding:6px 10px; border-radius:3px; font-size:12.5px; letter-spacing:.04em; }
.legend span { display:inline-block; margin-right:14px; font-size:12.5px; color:var(--mut); }
.tag { font-size:11px; letter-spacing:.05em; padding:1px 6px; border-radius:3px; border:1px solid currentColor; }
.eng-tag { color:var(--acc); } .fab-tag { color:#6b4a8a; } .prop-tag { color:var(--warn); }
.lede { color:var(--mut); max-width:88ch; }
pre { background:#0f1720; color:#e6edf3; padding:11px 13px; border-radius:5px; font-size:12px; overflow-x:auto; white-space:pre-wrap; }
code { background:#eef1f4; padding:1px 4px; border-radius:3px; font-size:12.5px; }
.engine { border-left:3px solid var(--acc); background:#fff; margin:10px 0; padding:8px 12px; border-radius:0 5px 5px 0; }
.engine-title { font:11px/1.4 ui-monospace,Consolas,monospace; color:var(--acc); letter-spacing:.04em; margin-bottom:6px; }
.mock { border:2px dashed var(--warn); background:var(--warm); border-radius:7px; padding:12px; }
.mock-title { font:11px/1.4 ui-monospace,Consolas,monospace; color:var(--warn); letter-spacing:.04em; margin-bottom:8px; }
.mockbar { font-size:12px; color:var(--mut); margin-bottom:4px; }
.mockinput { background:#fff; border:1px solid var(--line); border-radius:5px; padding:8px 10px; font-size:14px; }
.caret { float:right; color:var(--mut); }
.mockdd { background:#fff; border:1px solid var(--line); border-top:none; border-radius:0 0 5px 5px; }
.ddrow { padding:8px 10px; border-bottom:1px solid var(--line); } .ddrow.dim { opacity:.62; }
.ddsmall { font-size:12px; color:var(--mut); }
.chip { font-size:10.5px; padding:1px 6px; border-radius:9px; border:1px solid currentColor; margin-left:6px; }
.chip.ready { color:var(--ok); } .chip.locked { color:var(--mut); }
.mockcards { display:flex; gap:9px; margin-top:11px; flex-wrap:wrap; }
.card { background:#fff; border:1px solid var(--line); border-radius:6px; padding:9px 11px; flex:1 1 210px; }
.healthgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:9px; }
.hcard { background:#fff; border:1px solid var(--line); border-radius:6px; padding:9px 11px; }
.hcard.warm { background:#fff3e6; border-color:#f0c9a0; } .hcard.quiet { opacity:.78; }
.warn { color:var(--warn); font-weight:600; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:8px; }
.cmp > div { min-width:0; }
.acts code { display:inline-block; margin:2px 4px 2px 0; }
.friction { margin:4px 0 8px 18px; padding:0; font-size:12.5px; color:var(--warn); }
table.matrix { border-collapse:collapse; width:100%; margin-top:10px; font-size:12.5px; background:#fff; }
table.matrix th, table.matrix td { border:1px solid var(--line); padding:6px 8px; vertical-align:top; text-align:left; }
table.matrix th { background:#f2f5f8; font-size:11.5px; letter-spacing:.03em; }
.bid { font:12px ui-monospace,Consolas,monospace; color:var(--acc); white-space:nowrap; }
.mono { font-family:ui-monospace,Consolas,monospace; font-size:11.5px; } .small { font-size:11px; }
.warncell { color:var(--warn); }
.cand { border:1px solid var(--line); background:#fff; border-radius:7px; padding:12px 14px; margin:12px 0; }
.trigger { font-size:12.5px; color:var(--mut); margin:4px 0 8px; }
.disp { font-size:13px; font-weight:600; color:var(--acc); }
.day { border:1px solid var(--line); background:#fff; border-radius:7px; padding:14px 16px; margin:14px 0; }
.repro { font-size:12.5px; }
footer { margin-top:40px; color:var(--mut); font-size:12.5px; border-top:1px solid var(--line); padding-top:12px; }
"""


def write_reports() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    lines = ["# P-StudyFortnight — per-day reports (contract §8a)", "",
             "Eight 105-minute sessions, days 1/3/5/7/8/10/12/14; Day 1 = 2026-09-22 (UTC).",
             "Each day: starting facts -> explicit actions -> expected vs observed -> friction -> uncertainty.",
             "ENGINE OUTPUT quotes are verbatim captures; FABRICATED marks hand-authored scenario data.", ""]
    for d in DAYS:
        lines += [f"## Day {d['n']} — {d['date']}", "", f"**Shape.** {d['shape']}", "",
                  f"**Starting facts.** {d['facts']}", "",
                  "**Explicit actions.** " + ", ".join(f"`{a}`" for a in d["actions"]), "",
                  f"**Expected.** {d['expected']}", "", f"**Observed.** {d['observed']}", "",
                  "**Friction.**", *[f"- {x}" for x in d["friction"]], "",
                  f"**Uncertainty.** {d['uncertainty']}", ""]
        for label, sub in d["quotes"]:
            text = find(BASE, label, sub)
            if text != "(step not captured)":
                lines += ["```text", f"[ENGINE OUTPUT] {label} — {sub}", snippet(text, 12), "```", ""]
    (REPORTS / "day-reports.md").write_text("\n".join(lines), encoding="utf-8")

    lines = ["# P-StudyFortnight — branch-coverage matrix (contract §8b)", "",
             "Stress branches run on their own fixtures, separate from the realistic baseline.", "",
             "| # | Branch | Starting facts | Actions | Expected | Observed | Friction | Candidate signal | Uncertainty | Status |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for b in BRANCHES:
        lines.append("| " + " | ".join(x.replace("|", "\\|") for x in b) + " |")
    (REPORTS / "branch-coverage.md").write_text("\n".join(lines), encoding="utf-8")

    lines = ["# P-StudyFortnight — candidate-trigger matrix (contract §8c)", "",
             "Nine deferred candidates; triggers verbatim from `docs/POST_V2_ROADMAP.md` Beyond and #280.",
             "Dispositions: reconsideration-supported / deferral-supported / insufficient-evidence — never auto-implementation.", ""]
    for c in CANDIDATES:
        lines += [f"## {c[0]}. {c[1]}", "", f"**Trigger.** {c[2]}", "",
                  f"**Positive case.** {c[3]}", "", f"**Negative case.** {c[4]}", "",
                  f"**Boundary case.** {c[5]}", "",
                  f"**Measurable observation this fortnight.** {c[6]}", "",
                  f"**Disposition.** {c[7]}", ""]
    (REPORTS / "candidate-trigger-matrix.md").write_text("\n".join(lines), encoding="utf-8")

    lines = ["# P-StudyFortnight — current vs proposed comparisons (contract §8d)", "",
             "Identical input for discovery: `python for beginners`. Identical state for health: baseline fixture at day 14.", "",
             "## Discovery — current engine", ""]
    for sub in ["the only discovery surface's flags", "intent probe", "synonym probe: guess the id 'variables_01'",
                "synonym probe: guess 'python.vars_01'", "no-results probe", "ambiguity probe: two plausible"]:
        text = find(PROBES, "Discovery probes", sub)
        if text != "(step not captured)":
            lines += ["```text", f"[ENGINE OUTPUT] {sub}", snippet(text, 10), "```", ""]
    lines += ["## Discovery — PROPOSED mockup", "",
              "Dropdown/cards/combination surface for the same input; static illustration labeled PROPOSED in the HTML artifact "
              "(`prototype/study-fortnight.html`). Keyboard, mobile and no-script behavior are proposed properties only — no shipped "
              "surface was exercised in a browser, so they are reported untested.", "",
              "## Health — current engine", ""]
    for sub in ["health roll-up", "evidence warnings detail", "review health", "blocker health",
                "progress health", "resource health", "review suggestions"]:
        text = find(PROBES, "Health probes", sub)
        if text != "(step not captured)":
            lines += ["```text", f"[ENGINE OUTPUT] {sub}", snippet(text, 8), "```", ""]
    adv = find(BASE, "Day 14", "analytics: velocity")
    if adv != "(step not captured)":
        lines += ["```text", "[ENGINE OUTPUT] baseline day 14 — analytics velocity advisories", snippet(adv, 6), "```", ""]
    lines += ["## Health — PROPOSED mockup", "",
              "A single learner-facing Health view over exactly those facts (Study rhythm, Stuck right now, Due for review, "
              "Evidence gaps, Study resources, collapsed Repository diagnostics). Static illustration, labeled PROPOSED.", "",
              "## Engine observations worth a decision", ""]
    for h in HAZARDS:
        lines += [f"- **{h[0]} {h[1]}** — {h[2]}"]
    lines += ["", "## Runnable vs reported-untested", ""]
    for u in UNTESTED:
        lines += [f"- **{u[0]}** — {u[1]} ({u[2]})"]
    lines += ["", "## Protected-record hashes", "",
              "```json", (HERE / "protected_hashes_before.json").read_text().strip(), "```", "",
              "```json", (HERE / "protected_hashes_after.json").read_text().strip(), "```"]
    (REPORTS / "comparisons-and-hazards.md").write_text("\n".join(lines), encoding="utf-8")
    print("reports written to", REPORTS)


def build() -> None:
    write_reports()
    body = "\n".join([
        render_pins(), render_days(), render_branches(), render_candidates(),
        render_discovery(), render_health(), render_hazards(), render_untested(),
        render_hashes(), render_repro(),
    ])
    page = f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>P-StudyFortnight — THROWAWAY decision aid (map #289, ticket #292)</title>
<style>{CSS}</style></head>
<body><main>
<div class='throw'>THROWAWAY DECISION AID — not a spec, not a release artifact, never read by the engine, not acceptance of anything.
Evidence delivery for wayfinder ticket #292 on map #289. Static page: no scripts, no network.</div>
<h1>P-StudyFortnight — baseline journey and edge-case comparisons</h1>
<p class='lede'>An accelerated two-week simulation of the locked contract in G-StudyContract (#290): eight 105-minute sessions
on a beginner foundations arc, run against the real engine on isolated fabricated inputs. Every claim carries one of three labels.</p>
<div class='legend'>
<span><span class='tag eng-tag'>ENGINE OUTPUT</span> verbatim capture from the isolated fixture</span>
<span><span class='tag fab-tag'>FABRICATED</span> hand-authored scenario data, never a real learner record</span>
<span><span class='tag prop-tag'>PROPOSED</span> static illustration of a hypothetical UI, not engine behavior</span>
</div>
{body}
<footer>Built by the prototype session on branch <code>prototype/study-fortnight</code> from <code>main @ 6dafd42</code>.
Simulated days cannot demonstrate learning, retention, demand or comprehension. Substantive verdicts remain the learner's.</footer>
</main></body></html>
"""
    (HERE.parent / "study-fortnight.html").write_text(page, encoding="utf-8")
    print("wrote", HERE.parent / "study-fortnight.html")


if __name__ == "__main__":
    build()
