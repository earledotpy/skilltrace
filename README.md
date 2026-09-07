# SkillTrace

> **Your personal study tracker: a guided skill map that shows what to learn next and keeps proof of everything you've mastered.**

SkillTrace is for anyone working through a long, structured subject — school math, learning to code, data skills, machine learning, or modern AI tools — who wants to know exactly where they stand and what to study today. Instead of a generic to-do list, you get a map of skills in the right order, daily recommendations sized to the time you have, and a permanent record of your work.

Everything runs on your own computer. There are no accounts, no cloud sync, no telemetry, and no auto-grading. An AI assistant can help you research and review, but **you** always decide when your work is good enough.

---

## What's inside (v2.0.0)

- **A ready-made curriculum of 100 skills** — math foundations, Python programming, data analysis, classical machine learning, and building with AI agents — supported by 45 curated learning resources.
- **A daily dashboard** (`st today`) that shows your top recommendation, anything due for review, and current obstacles.
- **Smart recommendations** (`st next`) that respect prerequisites, so you never start something you're not ready for.
- **Evidence-based progress** — you pass a skill by showing real work (a solved problem set, a script, a short report), not by checking a box.
- **Memory-aware reviews** — spaced check-ins keep older skills fresh, with reminders when something starts to fade.
- **Study analytics** — simple views of your pace, obstacles, review habits, and coverage over time.
- **A portfolio builder** — turn your finished work into a clean Markdown, web, or data bundle you can share, with privacy controls that keep your private notes private unless you choose to include them.
- **A local web dashboard** (`st ui`) if you prefer working in a browser instead of the terminal.

---

## Quickstart

### What you need

- Python 3.14 or newer
- Git

### Install

```bash
# Clone the repository
git clone https://github.com/earledotpy/skilltrace.git
cd skilltrace

# Set up and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install
pip install -e .
```

This gives you the `skilltrace` command and its short alias `st`.

### Check that it works

```bash
# 1. Confirm everything is healthy
st health

# 2. See your daily dashboard
st today

# 3. Open the browser dashboard (optional)
st ui
```

---

## A typical study day

1. **See your agenda:** `st today` shows your top pick, anything due for review, and open obstacles.
2. **Get a recommendation:** `st next --minutes 60` ranks suitable skills for the time you have.
3. **Start a session:** `st start <skill>` opens your study session.
4. **Log your work:** `st work <skill> --minutes 25 --notes "Solved the exercise set"` keeps a time log.
5. **Attach your proof:** `st submit <skill> --location <your-file> --accept` links your finished work to the skill.
6. **Check readiness:** `st eligibility <skill>` tells you whether the requirements are met.
7. **Mark it passed:** `st pass <skill>` records your achievement. *(Only you can do this — nothing passes a skill automatically.)*
8. **Wrap up:** `st close` ends the session.

Over time, `st reviews` and `st retention status` keep earlier skills fresh, and `st portfolio export` packages your best work for sharing.

---

## Everyday commands

| What you want | Command |
| :--- | :--- |
| Morning brief: top pick, due reviews, blockers | `st today` |
| Recommendations for a study window | `st next --minutes 60` |
| Look up a skill in detail | `st node <skill>` |
| Open / log / close a study session | `st start`, `st work`, `st close` |
| Submit finished work as proof | `st submit <skill> --location <file> --accept` |
| Check whether a skill is ready to pass | `st eligibility <skill>` |
| Mark a skill passed / mastered | `st pass <skill>` / `st master <skill>` |
| Review queue and memory health | `st reviews`, `st retention status` |
| Record or clear an obstacle | `st blocker create` / `st blocker resolve` |
| Progress, obstacle, and evidence reports | `st report progress` (also: `blockers`, `reviews`, `evidence`) |
| Study pace and coverage charts | `st analytics` |
| Browser dashboard | `st ui` |
| Share your finished work | `st portfolio preview` / `st portfolio export` |
| Whole-system health check | `st health` |
| Back up your data | `st backup` |

Run any command with `--help` for full details.

---

## Why you can trust it

SkillTrace is designed so your record stays honest even after years of use:

- **Nothing passes without you.** Passing or mastering a skill is always your explicit decision. No automation, script, or AI can do it for you.
- **AI advises; you decide.** AI feedback is treated as a suggestion attached to your work, never as a verdict.
- **Progress never goes backward.** Once you've earned a skill, recalculations and updates will never demote it.
- **Your data stays yours.** Everything lives on your disk in plain, readable files. Exports and backups are one-way copies — they can never overwrite your record.
- **Corrections leave a trail.** Records are never silently edited or deleted; fixes are added as new entries that reference what they replace.
- **One person per copy.** Each copy of the repository tracks one learner. To share the curriculum with someone else, they clone it fresh.

---

## Learn more

- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — full user manual with everyday workflows and browser-dashboard tips.
- [`docs/INSTALL.md`](docs/INSTALL.md) — installation, environment setup, and troubleshooting.
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — quick operational reference and command cheatsheet.
- [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md) — what each release added.
- [`docs/POST_V1_ROADMAP.md`](docs/POST_V1_ROADMAP.md) — where the project is headed next.

---

## License

Built for focused, disciplined, and lifelong learning. Distributed under the MIT License.
