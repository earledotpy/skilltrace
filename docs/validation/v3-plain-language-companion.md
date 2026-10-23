# v3 validation — the plain-language companion

**This is for you, the learner.** It says the same things as `v3-usability-runbook.md` (the official rulebook) but in everyday language, click by click. If the two ever disagree, the rulebook wins — but you shouldn't need it. Nothing here expects you to know any commands, code, or jargon. If a word still puzzles you, ask me — that's what I'm for.

## 1. What you're actually doing

SkillTrace is getting a new design, and two draft web pages were built to try that design out before anyone commits to it:

- the **Guided page** — a draft of a normal study day (find something to study, work on it, note the time, close up);
- the **Operations page** — a draft of the "look under the hood" area (your graph, your evidence, your reviews, and so on).

Your job is to pretend you've **never seen SkillTrace before**, and then simply try to do normal study things on these pages. You'll do it three times: once the ordinary way (mouse), once using only the keyboard, and once with a screen reader (a voice that reads the page aloud).

**The most important rule in this whole document:** your confusion is the point, not a problem. These drafts are supposed to work for a person who knows no commands and no jargon. So every time you think *"wait — what?"*, that thought is exactly the evidence this project needs. Write it down in your own words. There is no way to do this "wrong" — the only mistake is hiding your confusion to look capable.

## 2. Who does what

**You** (needs your hands, eyes, ears, and honest reactions):

- run the 18 small tasks, three times over;
- fill in a short answer form after each one (a copy-paste form is provided in §4);
- talk out loud while you work — what you're looking for, what you expect, what surprises you.

**Me, the agent** (all the technical chores):

- turn your messy notes into the official report — you never touch it;
- do all the pass/fail math;
- run the machine accessibility scan (a tool called axe automatically checks colours, labels, and structure) — already set up on your machine;
- post the finished report on the GitHub ticket and close it.

When I fill in the official report, everything you said is filed under "what the learner actually did and said", and anything I ran or judged myself is filed separately. The report has three separate columns for exactly that — it's how we stay honest.

## 3. One-time setup (about 20 minutes)

**3.1 Open the two pages.**

1. Press the Windows key, type `File Explorer`, press Enter.
2. Click through: This PC → Local Disk (C:) → `skilltrace` → `prototype`.
3. Double-click **p-core-journey.html** → it opens in your browser. Press **Ctrl+D**, then "Done" — that bookmarks it. Think of it as "the Guided page".
4. Back in File Explorer, double-click **p-operations-workspace.html**, bookmark it the same way ("the Operations page").

**3.2 The magic reset rule.** Both pages keep everything in temporary memory, like a scribble pad. Press **F5** and the page forgets everything and starts over. You cannot break anything — there is no real data behind these pages, they are drafts.

**3.3 A timer.** Your phone's stopwatch is perfect. You'll start it when you read a task, stop it when you feel done.

**3.4 Optional but nice: recording.** Windows can record your screen: press **Win+Alt+R** to start, the same to stop. (The first time it may ask to enable a "gaming" feature — allow it.) If you skip recording, just take notes as you go.

**3.5 That's it for now.** The screen-reader program (NVDA) is only needed before pass 3 — see §8. Don't install it yet.

## 4. The little loop (the same 6 steps for every task)

1. **Reset.** Press **F5**, then click the task's setup button (each card says which), and read the message box near the top until it says "…fixture restored".
2. **Check the starting line.** Each card lists what the page should say before you begin. If it doesn't match: stop, write "starting line didn't match", press F5, and do the setup again. A task started from the wrong state simply doesn't count — that's a rerun, not your failure.
3. **Read the task card out loud.**
4. **Start the timer.**
5. **Try it — talking the whole time.** Say what you're looking for, what you expect each button to do, and whenever something surprises or annoys you. If you get stuck: struggle a little first. The Guided page has a "Guided walkthroughs" panel on the right — that's the *hint ladder*. Don't open it until you're truly stuck, and note how far you got before you did. That's not cheating; it's data.
6. **Stop the timer, then fill one answer form:**

```
TASK: ___   (pass: mouse / keyboard / screen reader)
Finished?   yes / yes-with-hint / no
Time: ___
Where I got confused or clicked the wrong thing: ___
What saved me:   nothing / worked it out myself / hint step ___
Did I need to know a command name?   yes / no
In my own words, what just happened: "___"
Anything annoying about the look, sound, or focus: ___
```

Keep the filled forms in any text file or notebook, in order. That is all the "official recording" you ever do.

Two of the 18 tasks (G9 and O9) are different: the thing they ask about **isn't on the page — on purpose**. For those, just write down what you expected to find and what you found instead. Neither counts as a pass or a fail.

## 5. Task cards — the Guided page

First, the page's four areas (use these names in your notes):

- **Message box** — the bordered box near the top ("Prototype ready…" when you start). **Read it after every button you press.** It always tells you what just happened.
- **Today card** — the big panel about "Use basic Pandas DataFrame operations", with buttons that change as things change (*Start studying*, *Resume Session*, *Log work here*, *Submit accepted evidence*, *Close Session now*, …).
- **Current facts** — the little table of facts ("Session", "Recorded time", "Open Blockers", "Pass eligibility"…) in the main area. This is where you check the starting-line numbers. (The right-hand "Full relevant state" table shows raw ids — including a `reviews` row — you can ignore it unless you want the details.)
- **Guided walkthroughs** — the right-hand panel with eight named buttons. Each one resets the page to that scenario's starting state (and its step list is the hint ladder). Below it, the **Free play** panel has *every* button, including the "do a wrong thing on purpose" ones.

The two starting lines you'll check (from **Current facts**):

- **COLD start** — no open Session, progress "available", 0 minutes recorded, 0 open Blockers, "not pass eligible", and the **Review** branch (in the *Distinct paths* area) shows **1 overdue**.
- **ACTIVE day** — Session `ses.snapshot.001 · open`, progress "active", **45 minutes** recorded, **1 open Blocker**, "not pass eligible", and the **Review** branch shows **1 overdue**.

The cards (read each goal out loud; the "note" lines are reminders of what to pay attention to, not instructions):

**G1 — First visit.** Setup: click *Cold start & discovery*, check the COLD line. Goal: *"You've never opened this before. Find what you should study first and begin — without changing anything you don't mean to."* Note: how did you decide what to study? Was anything unclear about what "beginning" would do?

**G2 — Pick up where you left off.** Setup: *Normal active study*, ACTIVE line. Goal: *"Your Session is already open. Pick up where you left off and record 30 more minutes of work on this node."* Note: before pressing anything — could you tell a Session was open? After — what proved the work was recorded?

**G3 — Stuck on groupby.** Setup: *Blocked work & Blocker*, ACTIVE line. Goal: *"You're stuck on groupby and don't want to lose that. Make the stuckness visible, and make sure it stays visible even if you close the Session."* Note: the page has *Log blocked work* and *Create Blocker* — did the difference between them make sense?

**G4 — Evidence, then pass.** Setup: *Evidence & pass*, ACTIVE line. Goal: *"Your solution script passed your own check — submit it as evidence and become eligible to pass; then pass."* Note: did "submit evidence" and "pass" clearly feel like two separate decisions? Did anything explain what made you "eligible"?

**G5 — Closing up.** Setup: *Safe Session close*, ACTIVE line. Goal: *"You're done for today. Close the Session — and be clear what closing does not do."* Note: afterwards, in your own words — what did closing *not* do?

**G6 — The system says no.** Setup: *Refusal & recovery*, ACTIVE line. Goal: *"You try to pass, but the system refuses. Recover: correct what was rejected, notice a stale confirmation when truth changes, and pass when genuinely eligible."* Note: what did the refusal actually say? Check **Current facts** — did anything get written down anyway? When "truth changed" while a confirmation was open, did you notice, and what did you do?

**G7 — An overdue review.** Setup: *Review completion*, ACTIVE line. Goal: *"A review you were meant to do earlier is overdue. Do it — it must not disturb your Session or your progress."* Note: afterwards — did the review touch your Session or your progress in any way? How could you tell?

**G8 — Three wrong things on purpose.** Setup: *Failure & empty recovery*, ACTIVE line. Goal: *"Deliberately do three wrong things: start a second Session, close in the future, and submit to a gate that can't run. Then close the Session honestly."* (The buttons are in the **Free play** panel: *Try a second Session*, *Try a future close*, *Simulate unrunnable gate*, then *Close forgotten Session honestly*.) Note: after each refusal — what was left behind? Any moment where you couldn't tell whether something had been saved?

**G9 — Mastery (not on the page — on purpose).** Setup: none. Goal: *"Mastery is a separate, deliberate act after passing. Show how you would master this node."* There is no mastery button anywhere. Note: where did you look for it? What did you expect to find? Then stop — that's the whole task.

After finishing G1–G9 (not during), answer these in your own words — there are no wrong answers:

1. What's the difference between *passing* and *mastering*?
2. Did anything you saw get written down permanently? How do you know?
3. If you corrected something, what happened to the original?
4. What does closing the Session do — and not do?
5. What makes a node locked, and what would change that?
6. When you saw a refusal — what did it refuse, and what state did it leave?

## 6. Task cards — the Operations page

Four things to know first:

- **Top-right label** — "Prototype state: seeded" (or "limited"). That's your starting-line check.
- **The bottom bar** — "← A — Persistent workspace shell →". A and B are two different drafts of the same page (the team hasn't picked one — partly what this test decides). Flip between them with the arrow buttons or the keyboard's ← → keys.
- **Draft A** — a menu down the left side (Graph, Evidence, Reviews, Analytics, Portfolio, Health) that stays put.
- **Draft B** — no side menu; a row of links and small summary cards.
- **The two setup buttons** — "Seeded fixture" (rich data) and "Limited fixture" (nearly empty) — sit near the top of **both** drafts. Click one to change the data; the top-right label confirms which one is active.

Starting lines:

- **Seeded** — top right says *seeded*; somewhere on the page you can find: 100 nodes, 49 available, 51 locked, 8 sessions, 12 evidence records, 3 reviews.
- **Limited** — top right says *limited*; 3 nodes, 1 available, 2 locked, 1 session, 0 evidence, 0 reviews.

Do O1–O7 in **draft A** on the seeded line; for O8, click **"Limited fixture"** (the buttons are at the top of either draft) and check the limited line; then do **O1 again in draft B** to compare the two home pages.

**O1 — Cold landing.** Goal: *"Land here cold: what is the state of this learner's graph in one glance?"* Note: roughly how many seconds until you could answer? What gave you the answer first?

**O2 — One node.** Goal: *"Find out whether `agents.agent_fundamentals_01` can be started, and what evidence it wants."* Note: could you see what it *wants* before starting anything?

**O3 — Recent evidence.** Goal: *"Find the most recent evidence record and describe its status."*

**O4 — Reviews.** Goal: *"Which reviews are due, and which are overdue?"*

**O5 — Can you trust analytics?** Goal: *"What can analytics tell you — and how would you know it isn't invented?"* Note: the page says its numbers are "derived facts only". Did you believe it? Why or why not?

**O6 — Portfolio.** Goal: *"Prepare a portfolio export view; say what it does and doesn't claim."*

**O7 — Health.** Goal: *"Is this repository healthy? Where would you look?"* Note: did "health" sound like a score about *you*? It shouldn't — did the page avoid that?

**O8 — Nearly-empty learner.** Switch to **Limited** first. Goal: *"Same landing, but the learner has almost no history — what does the product tell you?"* Note: when a number was 0, did it feel like a fact ("you have none") or like nothing-at-all?

**O9 — The number that can't be computed (not on the page — on purpose).** Goal: *"A number the product can't compute — where does that appear?"* Note: what did you expect, what did you find?

**O1 again, in draft B** — same goal as O1. Note: which home page (A or B) let you orient faster, and why? One sentence is enough.

## 7. The three passes

- **Pass 1 — mouse.** The ordinary way. Guided page first (G1→G9), then Operations (O1→O9 + the draft-B repeat).
- **Pass 2 — keyboard only.** **Operations first, then Guided** (the order flips on purpose). No mouse at all — put it somewhere out of reach. Your keys: **Tab** (next thing), **Shift+Tab** (back), **Enter** (press), **Space** (press), **arrows**, **Esc** (close a pop-up). Every time you instinctively reach for the mouse, write that down — that's a finding, not a failure.
- **Pass 3 — screen reader.** **Operations first, then Guided.** Setup in §8.

Between passes: close the tabs and reopen from your bookmarks (fresh page = clean memory).

## 8. The screen reader (NVDA) — what it is, setup, and the only keys you need

A screen reader is a program that reads the page aloud, for people who can't see it (well). The draft must make sense **by ear alone** — that's what this pass checks.

**Setup once (≈10 min):**

1. If you don't have Firefox, get it from mozilla.org and install it (Next → Next → Finish).
2. Go to **nvaccess.org** → Download → run the installer → keep clicking Next → leave "Start NVDA after installation" ticked.
3. To start it any time: press **Ctrl+Alt+N**, or Start menu → NVDA. It starts talking immediately — that's normal.

**The keys** (print this bit):

- **Ctrl** — make it stop talking, momentarily.
- The **NVDA key** = the **Insert** key or **Caps Lock** (both work — pick one and stick with it).
- **↓ / ↑** — read the next / previous line.
- **H** — jump to the next heading. **D** — jump to the next section.
- **Tab** — next button or link; **Enter** — press it.
- **NVDA key + Q**, then Enter — quit NVDA for the day.

**What to note in this pass:** after you press a button, does the page *tell you* what changed (listen for the message box being read out)? Can you find the counts (49 available…) by ear alone? On the Operations page — can you get any sense of the *graph* (names, what's available, what depends on what) without seeing it? What was there but never mentioned aloud (that you only knew because you'd seen the page before)?

## 9. The two small extra checks (narrow window and zoom)

**Narrow window** — during each pass, once per page:

1. Press **F12** — a code panel opens on the side. Touch nothing in it.
2. Press **Ctrl+Shift+M** — the page shrinks into a phone-shaped frame with a toolbar that says "Dimensions".
3. Click **Responsive**, type **480**, press Enter. Look around, and try to actually use the page.
4. Change it to **320**, look again.
5. **Ctrl+Shift+M**, then **F12** — back to normal.

Best moments: on the Guided page, during G2's state; on Operations, the home page. Note anything cut off, squashed, or unreachable.

**Zoom** — hold **Ctrl** and tap **+** until the browser says **200%** (the ⋮ menu → Zoom shows it). Everything should still be readable and usable. **Ctrl+0** puts it back.

## 10. A sensible calendar (split it up — that's fine)

- **Sitting 1** — setup (§3) + mouse pass on the Guided page. About 2 hours.
- **Sitting 2** — mouse pass, Operations page (+ narrow/zoom checks). About 1 hour.
- **Sitting 3** — keyboard-only pass, both pages. About 2 hours.
- **Sitting 4** — install NVDA (§8) + screen-reader pass, both pages. About 2 hours.
- **Sitting 5, with me** — leftover accessibility checks, the wrap-up chat (what confused you most overall? what would you fear doing wrong? where did the keyboard and ear passes break?), and handing me your notes.

## 11. When you're done

Hand me everything — answer forms, scribbles, timings, anything. I will then: (1) add the machine accessibility scan I've already set up, (2) pour your notes into the official report and show you the draft to check, (3) do the pass/fail math, and (4) post the report on the ticket and close it — which lets the next ticket in the chain start. You never have to open the official report, the rulebook, GitHub, or a calculator.

---

*Decision aid for wayfinder map #327, like the runbook and report template; the engine never reads it. The official protocol is `v3-usability-runbook.md`; the official evidence file is `v3-observation-report.md`.*




