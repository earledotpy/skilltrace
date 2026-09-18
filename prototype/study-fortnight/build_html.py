"""Assemble the THROWAWAY prototype artifact + markdown reports.

Reads out/baseline.json, out/branches.json, out/probes.json, out/probes2.json
and the protected-hash files; writes prototype/study-fortnight.html and
prototype/study-fortnight/reports/*.md.

Everything in the artifact is labeled: ENGINE OUTPUT (verbatim captured), 
FABRICATED HISTORY (hand-authored fixture data), or PROPOSED MOCKUP (static
illustration of a hypothetical UI, not engine behavior, not a spec).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from day_stories import DAYS
from matrices import BRANCHES, CANDIDATES

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
REPORTS = HERE / "reports"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


BASE = load("baseline.json")["days"]
BRA = load("branches.json")["days"]
PROBES = load("probes.json")["days"]
PROBES2 = load("probes2.json")["days"]


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def find(days, label_sub: str, step_sub: str) -> str:
    for d in days:
        if label_sub in d["label"]:
            for s in d["steps"]:
                if step_sub in s["name"]:
                    return s["output"]
    return "(step not captured)"


def snippet(text: str, max_lines: int = 14) -> str:
    lines = text.strip().splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + f"\n… ({len(lines) - max_lines} more lines)"


def engine_block(title: str, text: str, max_lines: int = 14) -> str:
    return (
        f"<div class='engine'><div class='engine-title'>ENGINE OUTPUT — {esc(title)}</div>"
        f"<pre>{esc(snippet(text, max_lines))}</pre></div>"
    )


# ------------------------------------------------------------- mockup builders
def mock_discovery(query: str) -> str:
    return f"""
<div class='mock'>
  <div class='mock-title'>PROPOSED MOCKUP — discovery (dropdown / cards / combination), static illustration</div>
  <div class='mockbar'>Ask for a subject you actually want to learn…</div>
  <div class='mockinput'>{esc(query)} <span class='caret'>▾</span></div>
  <div class='mockdd'>
    <div class='ddrow'><b>Use variables and expressions in Python</b> <span class='chip ready'>ready</span><div class='ddsmall'>Python · 1 accepted submission needed · <code>programming.python.variables_01</code></div></div>
    <div class='ddrow'><b>Define and call Python functions</b> <span class='chip ready'>ready</span><div class='ddsmall'>Python · unlocks 6 downstream skills · <code>programming.python.functions_01</code></div></div>
    <div class='ddrow dim'><b>Read and write CSV files with Pandas</b> <span class='chip locked'>locked</span><div class='ddsmall'>needs “Use basic Pandas DataFrame operations” · <code>data.csv.read_csv_01</code></div></div>
  </div>
  <div class='mockcards'>
    <div class='card'><div class='chip ready'>Math</div><b>Apply order of operations</b><div class='ddsmall'>3 accepted submissions · Khan Arithmetic</div></div>
    <div class='card'><div class='chip ready'>Data</div><b>Query rows and columns with SELECT</b><div class='ddsmall'>1 accepted submission · SQLBolt</div></div>
    <div class='card'><div class='chip ready'>Python</div><b>Use variables and expressions in Python</b><div class='ddsmall'>1 accepted submission · Python Tutorial</div></div>
  </div>
  <div class='ddsmall'>Keyboard: type to filter, ↑/↓ to move, Enter to open the node card, Esc to dismiss. Mobile: stacked cards, 44 px tap targets, the dropdown becomes a full-screen list. No-script: the same query renders as a plain static results page (the tier-0 posture the repo already ships). All states above are illustrations, not engine output.</div>
</div>"""


def mock_health() -> str:
    return """
<div class='mock'>
  <div class='mock-title'>PROPOSED MOCKUP — learner-facing Health, static illustration</div>
  <div class='healthgrid'>
    <div class='hcard'><b>Study rhythm</b><div>4 sessions · 5.2 h · 1.6 items/week <span class='warn'>below 2/wk</span></div><div class='ddsmall'>Framed with the limited-data qualifier at &lt;3 sessions.</div></div>
    <div class='hcard'><b>Stuck right now</b><div>0 open blockers · 1 resolved (PY reassignment)</div><div class='ddsmall'>Shows the failed attempt + its remediation state, which no current surface shows.</div></div>
    <div class='hcard'><b>Due for review</b><div>None scheduled</div><div class='ddsmall'>No false “0% vs 80%” completion line when nothing was ever scheduled.</div></div>
    <div class='hcard'><b>Evidence gaps</b><div>MATH 1/3 · PY 0/1 · SQL 0/1</div><div class='ddsmall'>Per-node bars instead of a single 1% coverage alarm.</div></div>
    <div class='hcard warm'><b>Study resources</b><div>1 broken (khan-arithmetic) on a node with no replacement</div><div class='ddsmall'>Today this fact exists only in <code>resource-report</code>.</div></div>
    <div class='hcard quiet'><b>Repository diagnostics</b><div>graph OK · 38 evidence warnings · policy OK · resources OK <span class='ddsmall'>(collapsed)</span></div><div class='ddsmall'>Kept, but demoted: it is operator detail, not learner health.</div></div>
  </div>
</div>"""


# ------------------------------------------------------------------ rendering
def render_days() -> str:
    out = ["<h2 id='journey'>The fortnight, day by day</h2>",
           "<p class='lede'>The locked baseline contract (G-StudyContract §2): eight 105-minute sessions on days 1, 3, 5, 7, 8, 10, 12, 14. "
           "Every panel below labels its own evidence: ENGINE OUTPUT is verbatim capture from the isolated fixture; "
           "FABRICATED is hand-authored scenario data; PROPOSED is a static illustration.</p>"]
    for d in DAYS:
        friction = "".join(f"<li>{esc(x)}</li>" for x in d["friction"])
        actions = " · ".join(f"<code>{esc(a)}</code>" for a in d["actions"])
        quotes = ""
        for label, sub in d["quotes"]:
            text = find(BASE, label, sub)
            if text != "(step not captured)":
                quotes += engine_block(f"{label} — {sub}", text, 12)
        out.append(f"""
<section class='day'>
  <h3>Day {d['n']} <span class='date'>— {d['date']}</span> <span class='shape'>{esc(d['shape'])}</span></h3>
  <div class='grid2'>
    <div><b>Starting facts</b><div class='ddsmall'>{esc(d['facts'])}</div>
         <b>Actions</b><div class='acts'>{actions}</div></div>
    <div><b>Expected</b><div class='ddsmall'>{esc(d['expected'])}</div>
         <b>Observed</b><div class='ddsmall'>{esc(d['observed'])}</div>
         <b>Friction</b><ul class='friction'>{friction}</ul>
         <b>Uncertainty</b><div class='ddsmall'>{esc(d['uncertainty'])}</div></div>
  </div>
  {quotes}
</section>""")
    return "\n".join(out)


def render_branches() -> str:
    rows = "".join(
        "<tr>"
        f"<td class='bid'>{esc(b[0])}</td><td><b>{esc(b[1])}</b><div class='ddsmall'>{esc(b[2])}</div></td>"
        f"<td>{esc(b[3])}</td><td class='ddsmall'>{esc(b[4])}</td><td class='ddsmall'>{esc(b[5])}</td>"
        f"<td class='ddsmall warncell'>{esc(b[6])}</td><td class='ddsmall'>{esc(b[7])}</td>"
        f"<td class='ddsmall'>{esc(b[8])}</td><td class='ddsmall mono'>{esc(b[9])}</td></tr>"
        for b in BRANCHES
    )
    return f"""
<h2 id='branches'>Branch-coverage matrix</h2>
<p class='lede'>Every contract §5 branch, run on its own fixture. Stress branches are separate from the realistic baseline:
a branch never inherits another branch's fabricated history. "RUN" means the branch executed against the real engine;
nothing here was skipped silently — partial runs are named.</p>
<table class='matrix'>
<thead><tr><th>#</th><th>Branch (starting facts)</th><th>Actions</th><th>Expected</th><th>Observed</th><th>Friction</th><th>Candidate signal</th><th>Uncertainty</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody></table>"""


def render_candidates() -> str:
    cards = []
    for c in CANDIDATES:
        cards.append(f"""
<div class='cand'>
  <h3>{c[0]}. {esc(c[1])}</h3>
  <div class='trigger'><b>Trigger (verbatim, POST_V2 Beyond + #280):</b> “{esc(c[2])}”</div>
  <div class='grid2'>
    <div><b>Positive case</b><div class='ddsmall'>{esc(c[3])}</div>
         <b>Negative case</b><div class='ddsmall'>{esc(c[4])}</div>
         <b>Boundary case</b><div class='ddsmall'>{esc(c[5])}</div></div>
    <div><b>Measurable observation this fortnight</b><div class='ddsmall'>{esc(c[6])}</div>
         <b>Disposition</b><div class='disp'>{esc(c[7])}</div></div>
  </div>
</div>""")
    return f"""
<h2 id='candidates'>Deferred candidate – trigger matrix</h2>
<p class='lede'>Nine deferred candidates from the roadmap's Beyond section, adjudicated against this fortnight's evidence only.
Dispositions are <b>reconsideration-supported</b>, <b>deferral-supported</b>, or <b>insufficient-evidence</b>.
No disposition implements anything: a supported trigger warrants reconsideration, and a trigger this simulation cannot
trip is reported untested rather than argued away. Advisory AI remains an eligible non-slot candidate (#283) with no row here;
the five rejects (auto-pass/master, LLM-graded evidence, cloud sync, Elo/BKT, generative tutoring) stay rejected and are not rows.</p>
{''.join(cards)}"""
DISCOVERY_INPUT = "python for beginners"

HAZARDS = [
    ("H1", "The fixture clock cannot date engine-written records",
     "`start`/`close` stamp real wall-clock ids and timestamps (sessions came out `ses.2026-09-18.*`; record `created_at` likewise), "
     "`review schedule` reads `_now_iso()` directly, and `close --end` validates against the real clock. Fabricated histories therefore "
     "cannot be date-labeled by the engine itself: the fortnight's records carry real dates in an isolated fixture, and the "
     "simulated-day labels exist only in this artifact. Fixing it would mean threading `Context.clock` through those writers."),
    ("H2", "`next` prints a stale command form", "`next`'s DO THIS NEXT line says `skilltrace session start --node <id>`; that command does not exist — "
     "the real form printed by `today` is `skilltrace start <id>`. A learner following `next` verbatim hits an argparse error."),
    ("H3", "`next` ignores the learner's active work", "With one, two, and three active strands, OPTION 1 stayed a never-touched agents node every day. "
     "Only `today` picked up the open-session thread. Recommendation ranking and the daily view disagree about what matters."),
    ("H4", "Discovery is id-only", "No command accepts a subject query; `node` fails with a bare 'unknown node <id>' on a near-miss "
     "(`variables_01`, `python.vars_01`). Math/data/Python browsing is impossible without memorized ids."),
    ("H5", "Failures and resource problems are invisible where the learner looks", "2/3/4 failed attempts, a failed review, a rejected artifact, "
     "and a broken resource change nothing in `today` or `node`; each is reachable only through a separate command the learner must know to run."),
    ("H6", "Advisories overstate penalty on a sparse, pass-free fortnight",
     "'Review completion is below target: 0% (target: 80%)' printed with zero reviews ever scheduled, and 'evidence coverage is below target: 1%' "
     "with no passes possible under the contract. Only `analytics velocity` qualifies itself with a limited-data advisory."),
    ("H7", "Two review surfaces disagree on the due date", "On the due date `reviews` lists the review as due while `suggest reviews` says "
     "'nothing due — 1 scheduled ahead'. A day later both agree it is overdue."),
    ("H8", "The 12 h stale-session policy is never surfaced", "A session left open 13 hours still reads as '~0 min' with no staleness note."),
    ("H9", "`graph impact` escapes `--root` isolation", "Run against a fixture, it compared the fixture's edges to the host repo's git HEAD and "
     "reported unrelated no-op edges — advisory output from a fixture is meaningless."),
    ("H10", "`--show-locked` renders no locked rows visibly", "Probing locked-skill visibility via `next --show-locked` returned the same available-node "
     "OPTION 1 output; locked skills stayed undiscoverable."),
    ("H11", "Starting a passed node opens a session silently", "`start` on a passed node returned exit 0 and opened a session with no transition line "
     "and no explanation. The asserted state held (verified in the store) — the invariant is intact; the affordance is unexplained."),
]

UNTESTED = [
    ("Objective-gate judgment (check-script run)", "All three beginner entry gates are manual (`authority: manual`); no objective gate was hand-run.", "UNTESTED"),
    ("Mastery path and mastery eligibility", "No pass occurs in the locked arc (no required pass); mastery needs passed + spaced review.", "UNTESTED"),
    ("Review auto-scheduling after pass", "Scheduling is pass-driven; automating `pass` is forbidden, so the auto-schedule path was never triggered.", "UNTESTED"),
    ("Resource reachability checks (`check-resource(s)`)", "Deliberately not called: they perform network reads and this prototype stays offline.", "UNTESTED"),
    ("`graph impact` on a fixture", "Depends on git context; observed to escape `--root` (H9). Needs a git-context fixture to test properly.", "UNTESTED (observed hazard)"),
    ("`replace-resource` success path", "No same-node candidate exists for the broken math resource; refusal observed ('share no node') instead.", "UNTESTED"),
    ("Honest backdated `close --end` under a simulated clock", "Refused as future-dated because the check uses the real clock (H1).", "UNTESTED"),
    ("Keyboard / mobile / no-script behavior", "No shipped surface was probed in a browser; these remain PROPOSED mockup properties only.", "PROPOSED-ONLY"),
    ("Human comprehension, real study time, sustained demand", "Cannot be measured from automation (contract §7).", "NOT MEASURABLE"),
    ("Badge, MC/PKM, portable evidence locator, share-profile triggers", "Untestable by construction: no consumer, no PKM in use, no second export surface.", "UNTESTED BY CONSTRUCTION"),
    ("Sweep cadence, content-drift incident, gate-runner hand-run load", "Trigger conditions cannot be produced inside a fortnight.", "UNTESTED BY CONSTRUCTION"),
]


def render_discovery() -> str:
    cur = ""
    for sub in ["the only discovery surface's flags", "intent probe", "synonym probe: guess the id 'variables_01'",
                "synonym probe: guess 'python.vars_01'", "no-results probe", "ambiguity probe: two plausible"]:
        text = find(PROBES, "Discovery probes", sub)
        if text != "(step not captured)":
            cur += engine_block(sub, text, 8)
    return f"""
<h2 id='discovery'>Discovery — current behavior vs proposed (identical inputs)</h2>
<p class='lede'>One learner input, two renderings. On the left, the real engine given the input "{esc(DISCOVERY_INPUT)}" (plus the near-miss ids
a learner would actually guess). On the right, a PROPOSED mockup — a static illustration of a dropdown/card/combination surface for the same input.
The mockup is not engine behavior, not a spec, and not accepted; it exists to make the gap judgeable.</p>
<div class='grid2 cmp'>
  <div><b>CURRENT — engine output (verbatim)</b>{cur}</div>
  <div><b>PROPOSED — static mockup</b>{mock_discovery(DISCOVERY_INPUT)}</div>
</div>"""


def render_health() -> str:
    cur = ""
    for sub in ["health roll-up", "evidence warnings detail", "review health", "blocker health",
                "progress health", "resource health", "review suggestions"]:
        text = find(PROBES, "Health probes", sub)
        if text != "(step not captured)":
            cur += engine_block(sub, text, 8)
    adv = find(BASE, "Day 14", "analytics: velocity")
    if adv != "(step not captured)":
        cur += engine_block("baseline day 14 — analytics velocity advisories", adv, 6)
    return f"""
<h2 id='health'>Health — current behavior vs proposed (identical inputs)</h2>
<p class='lede'>Same fixture, same day-14 state, same facts. Left: the five commands a learner must know to assemble a health picture.
Right: a PROPOSED single Health view over exactly those facts. The proposed card is a static illustration, labeled as such.</p>
<div class='grid2 cmp'>
  <div><b>CURRENT — engine output (verbatim)</b>{cur}</div>
  <div><b>PROPOSED — static mockup</b>{mock_health()}</div>
</div>"""


def render_hazards() -> str:
    rows = "".join(
        f"<tr><td class='bid'>{esc(h[0])}</td><td><b>{esc(h[1])}</b><div class='ddsmall'>{esc(h[2])}</div></td></tr>"
        for h in HAZARDS
    )
    return f"""
<h2 id='hazards'>Engine observations worth a decision</h2>
<p class='lede'>Not a bug list, and not acceptance: the friction the fortnight exposed, each traceable to a captured step above.</p>
<table class='matrix'><tbody>{rows}</tbody></table>"""


def render_untested() -> str:
    rows = "".join(
        f"<tr><td><b>{esc(u[0])}</b></td><td class='ddsmall'>{esc(u[1])}</td><td class='mono'>{esc(u[2])}</td></tr>"
        for u in UNTESTED
    )
    return f"""
<h2 id='untested'>Runnable vs reported-untested</h2>
<p class='lede'>Nothing here is silently skipped. Everything not exercised is named with its reason.</p>
<table class='matrix'><thead><tr><th>Case</th><th>Why it was not exercised</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"""


def render_pins() -> str:
    return """
<h2 id='pins'>Pins, isolation and safety</h2>
<div class='grid2'>
<div>
<b>Source revision</b><div class='ddsmall'>`main` @ `6dafd42` (merge of #288), package 2.4.0 — the revision G-StudyContract §4 froze.</div>
<b>Simulated clock</b><div class='ddsmall'>Day 1 = 2026-09-22 (UTC); day N = day 1 + N−1. Session days 1/3/5/7/8/10/12/14, rest days 2/4/6/9/11/13.
Carried through the dispatcher's `Context.clock`. Engine-written record timestamps ignore it (H1) — every such record is labeled as fabricated fixture data.</div>
<b>Fixture</b><div class='ddsmall'>`fortnight-fixture v0` — one isolated root per scenario, built from this repo's shared read-only material
(`graph/nodes`, `edges.yaml`, `resources.yaml`, `evidence/{artifact_specs,validation_gates}.yaml`, `policy/*`) plus fabricated learner records.
Fixture roots are regenerable and deliberately not committed; the captured engine output under `out/` is.</div>
<b>Entry set</b><div class='ddsmall'>`math.arithmetic.order_operations_01` (gate: manual, spec min 3), `programming.python.variables_01` (manual, min 1),
`data.sql.select_basics_01` (manual, min 1). Each supports 1, 3 and 1 resources respectively.</div>
</div>
<div>
<b>Policy values</b><div class='ddsmall'>Live `policy/*.yaml` at the pinned revision, unmodified: workload daily 180/warn 120, session 180/warn 90,
active nodes 3/warn 2, stale 12 h, templates 15/45/90; remediation failed-attempt threshold 3, max 5 open;
review cadence 1/3/7 days with a 2-day grace; retention 7-day half-life, 0.5 attention threshold, 2-day on-time window;
analytics 30-day window, min 3 sessions, velocity 2/wk, review 0.80, coverage 0.60, blockers 3.</div>
<b>Isolation</b><div class='ddsmall'>Every learner record was written inside a throwaway fixture root via `--root`/`Context.root`.
Real `graph/state.yaml`, `evidence/` and `execution/` were hash-verified before and after — see the hash ledger below.</div>
<b>Boundaries respected</b><div class='ddsmall'>No `pass_node`, `master_node` or `delete_record` was invoked anywhere, including in helpers.
"Passed" starting facts are hand-authored scenario data (labeled), never the output of `pass`. No AI verdict was used as an acceptance authority:
every manual-gate verdict in the arc is the scripted learner's own explicit `--accept`/`--reject`.</div>
<b>Honesty riders</b><div class='ddsmall'>A simulation cannot show learning, comprehension, sustained demand, or real study time.
Hypothetical acceptance snapshots are illustrations, not learner evidence. Trigger support means "reconsider", never "implement".</div>
</div></div>"""


def render_hashes() -> str:
    before = json.loads((HERE / "protected_hashes_before.json").read_text())
    after = json.loads((HERE / "protected_hashes_after.json").read_text())
    rows = "".join(
        f"<tr><td class='mono'>{esc(k)}</td><td class='mono small'>{before.get(k,'—')[:16]}…</td>"
        f"<td class='mono small'>{after.get(k,'—')[:16]}…</td>"
        f"<td class='mono'>{'unchanged' if before.get(k) == after.get(k) else 'CHANGED'}</td></tr>"
        for k in sorted(before)
    )
    changed = [k for k in before if before.get(k) != after.get(k)]
    verdict = "No protected file changed." if not changed else "CHANGED: " + ", ".join(changed)
    return f"""
<h2 id='hashes'>Protected-record hash ledger</h2>
<p class='lede'>Contract §7: real learner records are protected. <b>{esc(verdict)}</b> The dirty working tree was never reset.</p>
<table class='matrix'><thead><tr><th>File</th><th>before (sha256, first 16)</th><th>after</th><th>verdict</th></tr></thead><tbody>{rows}</tbody></table>"""



def render_repro() -> str:
    return """
<h2 id='repro'>Reproduction</h2>
<div class='repro'>
<p>All scripts are on the throwaway branch <code>prototype/study-fortnight</code> and never touch real records:</p>
<pre>python prototype/study-fortnight/run_baseline.py    # 8 sessions  -> out/baseline.json
python prototype/study-fortnight/run_branches.py    # 18 branches -> out/branches.json
python prototype/study-fortnight/run_probes.py      # discovery + health -> out/probes.json
python prototype/study-fortnight/run_probes2.py     # corrected probes  -> out/probes2.json
python prototype/study-fortnight/check_protected.py # before/after hashes
python prototype/study-fortnight/assemble.py        # this page + reports/</pre>
<p>Fixture roots rebuild under <code>prototype/study-fortnight/fixture/</code> on every run (git-ignored, regenerable);
<code>out/*.json</code> holds the verbatim captured output this page quotes.</p>
</div>"""
