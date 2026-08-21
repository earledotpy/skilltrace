# Phase 0: Prerequisites — Python, Git, SQL

**Estimated Hours:** 40  
**Weeks at 6h:** 7 | **Weeks at 8h:** 5  
**Prerequisites:** None (complete beginner start)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will be able to:
- Write Python scripts with functions, loops, conditionals, and basic data structures
- Use Git for version control: init, commit, branch, merge, push/pull to GitHub
- Write SQL queries: SELECT, WHERE, JOIN, GROUP BY, aggregations
- Navigate the command line (cd, ls, mkdir, git, python)
- Have a GitHub portfolio repository with README

---

## Resource Table

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **Harvard CS50P (edX audit)** | https://cs50.harvard.edu/python | Video, problem sets, auto-graded, browser VS Code | 30–40 | **Free CS50 cert** | 2026-08-08 |
| **Python for Everybody (PY4E)** | https://www.py4e.com/ | Interactive lessons, autograded labs, free textbook | 20–30 | No (UMich only) | 2026-08-08 |
| **PY4E Labs** | https://labs.py4e.com/ | Autograded exercises | Included | No | 2026-08-08 |
| **Kaggle Learn: Python** | https://www.kaggle.com/learn/python | Micro-course, notebook-based | 5 | **Yes (free)** | 2026-08-08 |
| **Kaggle Learn: Pandas** | https://www.kaggle.com/learn/pandas | Micro-course, notebook-based | 4 | **Yes (free)** | 2026-08-08 |
| **Kaggle Learn: Intro to SQL** | https://www.kaggle.com/learn/intro-to-sql | Micro-course, BigQuery | 4 | **Yes (free)** | 2026-08-08 |
| **Kaggle Learn: Advanced SQL** | https://www.kaggle.com/learn/advanced-sql | Micro-course | 4 | **Yes (free)** | 2026-08-08 |
| **freeCodeCamp Git Course** | https://www.freecodecamp.org/learn | Interactive | 5–10 | **Yes (free)** | 2026-08-08 |
| **GitHub Skills** | https://skills.github.com/ | Interactive repo-based tutorials | 2–5 | No | 2026-08-08 |
| **Mode SQL Tutorial** | https://mode.com/sql-tutorial/ | Interactive SQL in browser | 10–15 | No | 2026-08-08 |
| **Automate the Boring Stuff** | https://automatetheboringstuff.com/ | Free online book, practical scripts | 10–20 | No | 2026-08-08 |

---

## Recommended Path (Choose One Primary)

### Option A: Structured + Certificate (Recommended)
**Primary:** Harvard CS50P (edX audit) — complete all problem sets + final project ≥70% for free certificate  
**Supplementary:** Kaggle Learn micro-courses for quick wins (Python, Pandas, SQL = 3 certs)  
**Git/CLI:** freeCodeCamp Git + GitHub Skills

### Option B: Gentle + Data-Focused
**Primary:** Python for Everybody (PY4E) + Labs  
**Supplementary:** Automate the Boring Stuff (practical scripts)  
**Data Stack:** Kaggle Learn sequence (Python → Pandas → SQL)  
**Git/CLI:** freeCodeCamp Git + GitHub Skills

---

## Weekly Breakdown

### At 6 Hours/Week (7 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | Python basics: variables, types, control flow | CS50P Weeks 0–1 OR PY4E Ch 1–4 | GitHub repo: `python-basics` with 5+ scripts |
| 2 | Functions, data structures (lists, dicts, sets) | CS50P Week 2 OR PY4E Ch 5–8 | GitHub: `data-structures-exercises` |
| 3 | File I/O, exceptions, modules, pip | CS50P Week 3 OR PY4E Ch 9–12 | GitHub: `file-processing-scripts` |
| 4 | **Git + GitHub** (dedicated week) | freeCodeCamp Git + GitHub Skills | All repos pushed with clear READMEs |
| 5 | **SQL** (dedicated week) | Kaggle Intro + Advanced SQL | GitHub: `sql-practice` with 10+ queries |
| 6 | **Pandas + Data Wrangling** | Kaggle Learn Pandas | GitHub: `pandas-analysis` with 3+ notebooks |
| 7 | **Consolidation + Portfolio Polish** | Review, Automate the Boring Stuff Ch 1–5 | Update all READMEs, write Phase 0 reflection blog post |

### At 8 Hours/Week (5 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | Python basics + functions | CS50P Weeks 0–2 | GitHub: `python-fundamentals` |
| 2 | Data structures + file I/O + Git | CS50P Week 3 + freeCodeCamp Git | All code on GitHub |
| 3 | SQL (both Kaggle courses) | Intro + Advanced SQL | GitHub: `sql-portfolio` |
| 4 | Pandas + Automate the Boring Stuff | Kaggle Pandas + ATBS Ch 1–10 | GitHub: `data-projects` |
| 5 | Consolidation + Portfolio | Review, finalize READMEs | Phase 0 reflection blog post |

---

## Checkpoint Exercises

### Python (must pass before Phase 1)
1. **File processor:** Read a CSV, filter rows by condition, compute column statistics, write JSON output
2. **Web scraper:** Fetch a public page, extract structured data, save to SQLite database
3. **API client:** Call a public REST API (e.g., OpenWeather, GitHub), parse JSON, display formatted output

### Git (must pass)
- Initialize repo, create 3+ commits with meaningful messages
- Create feature branch, make changes, merge back to main
- Push to GitHub with README, .gitignore, requirements.txt

### SQL (must pass)
- Write query with JOIN across 3+ tables
- Write query with GROUP BY + HAVING + window function
- Explain EXPLAIN output for a query

---

## GitHub Portfolio Task

Create repository: `ai-engineering-portfolio` with structure:
```
ai-engineering-portfolio/
├── phase-0/
│   ├── python-basics/
│   ├── data-structures/
│   ├── file-processing/
│   ├── sql-practice/
│   └── pandas-analysis/
├── README.md           # Overview, links to each project
└── requirements.txt    # Shared dependencies
```

Each sub-project needs: `main.py` / `notebook.ipynb`, `README.md`, `requirements.txt`.

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Skipping Git | **Do Git in Week 1** — every project from Day 1 lives on GitHub |
| Tutorial hell (watching without coding) | **Code along** — pause video, type code, run, modify, break, fix |
| Perfectionism | **Done > perfect** — submit CS50P problem sets even if not elegant |
| Ignoring errors | **Read tracebacks** — they tell you exactly what's wrong |

---

## Optional Deep-Dives (If Time Permits)

| Topic | Resource | Hours |
|-------|----------|-------|
| Python testing (pytest) | pytest docs + Real Python tutorial | 5 |
| Virtual environments / uv | python.org venv + astral.sh/uv | 3 |
| CLI tools (click, typer) | click.palletsprojects.com | 5 |
| Regex | regex101.com + Automate Ch 7 | 3 |

---

## Next Phase Preview

**Phase 1: Math Foundations** — Linear algebra, calculus, and statistics intuition. You'll need Python from this phase to implement math concepts in code (NumPy, Matplotlib).

**Prepare:** Install Anaconda or Miniconda (free) for managed Python + Jupyter. Or use Kaggle/Colab notebooks (no install needed).