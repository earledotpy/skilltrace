# R-Phase2ML — 2026 source availability for the v1.2 Phase 2 ML seed graph

> **Ticket:** [#97](https://github.com/earledotpy/skilltrace/issues/97)
> **Map:** [#95](https://github.com/earledotpy/skilltrace/issues/95) (Consolidated post-v1 roadmap)
> **Scope question:** What is the current (2026) state of the six Phase 2 ML seed-graph source materials listed in the post-v1 backlog, so the roadmap's v1.2 version slot reflects 2026 availability rather than 2024 snapshots?
> **Researcher:** wayfinder research subagent
> **Date:** 2026-08-27
> **Status:** Complete — handed to G-Slot (#100) for the v1.2 shape call

## Scope and method

The six sources in question (per `docs/POST_V1_BACKLOG.md:35-36` and `docs/ai-engineering-roadmap.md:59-60`):

1. Google ML Crash Course
2. Andrew Ng's Machine Learning course (Coursera)
3. ISLR (An Introduction to Statistical Learning)
4. Kaggle (learning tracks / competitions)
5. FastAPI
6. Docker

For each source the ticket asks five sub-questions: (a) still active/recommended in 2026, (b) free and verifiable, (c) substantive content drift, (d) 2026 alternates, (e) Phase 2 shape implications. Findings below address each. Primary-source URLs are inlined; a consolidated list is at the bottom.

SkillTrace's free-first resource doctrine (per `graph/resources.yaml` convention — `cost: free`) is applied throughout.

---

## 1. Google Machine Learning Crash Course (MLCC)

**Primary sources**
- Course index: <https://developers.google.com/machine-learning/crash-course>
- Foundational courses hub: <https://developers.google.com/machine-learning/foundational-courses>
- Prerequisites / prework: <https://developers.google.com/machine-learning/crash-course/prereqs-and-prework>
- Google blog announcement of the 2024 refresh: <https://blog.google/innovation-and-ai/technology/developers-tools/machine-learning-crash-course/> (2024-11-12)

**a. Still active and recommended in 2026?** Yes — actively maintained. Google announced a major refresh in November 2024 ("completely reimagined version of MLCC") adding LLM, AutoML, responsible AI, and expanded data sections, with 130+ exercise questions and per-module completion badges. The "About" page (support.google.com/machinelearningeducation) confirms the refreshed scope teaches "the basics of machine learning **and large language models**." Still the default free Google-owned ML primer in 2026.

**b. Free and verifiable?** Yes. The course is free; programming exercises run in browser-based Google Colab with no setup. No certificate of completion that is widely recognized outside Google, but the badges-of-completion are issued free per module.

**c. Substantive content drift?** Material drift from 2024 snapshot → 2026:
- Added: LLM module, AutoML coverage, responsible AI, expanded data section, interactive visualizations.
- Updated: re-recorded video explainers, new quizzes, refreshed intro for generative-AI audience.
- Removed/reduced: the older TensorFlow Playground-centric framing is de-emphasized in favor of more language-agnostic conceptual content.
- Implications: the 2024-era curriculum author note "15h, updated 2024 with LLM modules" is still accurate. The course has *gained* relevance, not lost it.

**d. 2026 alternates**
- **fast.ai Practical Deep Learning Part 1** — top-down, PyTorch, hands-on; better for learners who already code.
- **Kaggle Learn — Intro to Machine Learning** (3h) + **Intermediate Machine Learning** (4h) — shorter, more applied.
- **DL.AI / Coursera Machine Learning Specialization** (Andrew Ng, see #2) — more rigorous, longer.
- **StatQuest (Josh Starmer) YouTube** — conceptual reinforcement, free.

**e. Phase 2 shape implications** Keep as a core primary resource. Its LLM additions in 2024 mean the course now reaches beyond classical ML — usable to bridge Phase 2 → Phase 3. Free, no certificate claim required. Map to a single Phase 2 node (e.g. `ml.classical.intro_to_ml_concepts`).

---

## 2. Andrew Ng's Machine Learning course (Coursera)

**Primary sources**
- Coursera specialization (3 courses, DeepLearning.AI + Stanford Online): <https://www.coursera.org/specializations/machine-learning-introduction>
- First course landing: <https://www.coursera.org/learn/machine-learning/>
- Course author site: DeepLearning.AI

**a. Still active and recommended in 2026?** Yes. The legacy 2011/2012 Octave-based Stanford MOOC has been retired in favor of a **three-course Python-era "Machine Learning Specialization"** (Supervised ML → Advanced Learning Algorithms → Unsupervised Learning, Recommenders, Reinforcement Learning). The new specialization is the "updated and expanded version of Andrew's pioneering Machine Learning course" (per Coursera's own description), now rated 4.9/5 with 4.8M+ learners cumulatively. Pivot News (May 2026) and CourseFacts (May 2026) both rate it the default first stop in 2026.

**b. Free and verifiable?** Yes — **free audit is still available** (no certificate, full content access). Certificate path is ~$49/month on Coursera; financial aid available. Tools used: Python, NumPy, scikit-learn, TensorFlow. The original Octave/MATLAB path is gone — listing "Octave-based Andrew Ng course" in 2026 would be a factual error.

**c. Substantive content drift?** Major drift:
- Stack: Octave/MATLAB → Python (NumPy, scikit-learn, TensorFlow).
- Structure: one course → three-course specialization.
- Scope: classical supervised ML + neural nets + decision trees + recommender systems + RL intro (third course).
- What has *not* changed: the math-first, intuition-first pedagogy; the focus on "why" rather than "how to call an API."
- The course is widely considered **incomplete by itself** for a 2026 AI engineer portfolio — it is strong on foundations, weak on LLM applications, MLOps, and production deployment.

**d. 2026 alternates**
- **fast.ai Practical Deep Learning** — top-down, project-first, PyTorch.
- **Kaggle Learn tracks** (see #4) — shorter, applied, free, no certificate cost.
- **Google MLCC** (see #1) — also free, more interactive, slightly less rigorous.
- **Stanford CS229 (YouTube)** — mathematically deeper, no certificate, post-ML-Specialization deepening step.
- For a learner who already codes: **DeepLearning.AI short courses** (free on the DL.AI site) cover LLM/RAG/agents.

**e. Phase 2 shape implications** Keep as a core primary resource, but **update the reference**: point to the *Machine Learning Specialization* (three courses, Python), not the legacy Octave course. Best framed as the rigorous track for learners who want math-aware foundations; pair with fast.ai or Kaggle for applied breadth. Two Phase 2 nodes (supervised + unsupervised/recommenders) is reasonable; one "complete specialization" node is also defensible.

---

## 3. ISLR (An Introduction to Statistical Learning)

**Primary sources**
- Official book site (Trevor Hastie): <https://trevorhastie.github.io/ISLR/>
- Free PDF (2nd ed., corrected 7th printing, June 2023): <https://hastie.su.domains/ISLRv2_website.pdf>
- Springer record (2nd ed., 2021/2022, ISBN 978-1-0716-1418-1): <https://link.springer.com/book/10.1007/978-1-0716-1418-1>
- Open Tech Book mirror (CC BY-NC-SA, 2nd ed., 622 pp.): <https://opentechbook.com/book/an-introduction-to-statistical-learning-2nd-edition-with-applications-in-r/>

**a. Still active and recommended in 2026?** Yes — the **2nd edition (2021/2022)** is the current standard, with a corrected printing maintained through June 2023 and the PDF on the author's site labelled "corrected 7th printing." Self-paced MOOC by Hastie and Tibshirani is offered covering the entire book. The 2nd edition is widely cited as the standard undergraduate/graduate intro to statistical learning in 2026.

**b. Free and verifiable?** Yes — **free PDF download from the author's site**; the book is licensed CC BY-NC-SA. (Note: CC BY-NC-SA is non-commercial; the printed hardcover/softcover from Springer is paid.) Author-hosted PDF, R labs, datasets, and the `ISLR2` R package on CRAN are all free. Code throughout is in R.

**c. Substantive content drift?** Yes — the 1st edition (2013) → 2nd edition (2021/2022) added three chapters and expanded four:
- **New:** Chapter 10 (Deep Learning), Chapter 11 (Survival Analysis), Chapter 13 (Multiple Testing).
- **Expanded:** Naïve Bayes and GLMs (Ch. 4), Bayesian Additive Regression Trees (Ch. 8), Matrix Completion (Ch. 12).
- **Refreshed:** R code throughout for modern R compatibility.
- What has *not* drifted: the R-only tooling (a 2026 drawback for Python-first learners), the textbook-rather-than-course format, and the academic depth.

**d. 2026 alternates**
- **Python translation: "An Introduction to Statistical Learning with Applications in Python" (ISLP)** — James/Witten/Hastie/Tibshirani, 2023, with Python labs. Same authors, same scope, Python tooling.
- **"The Elements of Statistical Learning" (ESL, Hastie/Tibshirani/Friedman)** — the deeper, math-rigorous predecessor; free PDF on Hastie's site.
- **Probabilistic Machine Learning: An Introduction (Murphy, 2022)** — newer, broader, free PDF.
- For learners who will only read one book: **ISLP (Python)** is the better default over **ISLR (R)** in 2026 unless the curriculum explicitly teaches R.

**e. Phase 2 shape implications** The 2024 roadmap says "Andrew Ng + ISL" as the theory option. In 2026 the better default is **ISLP (the Python edition)**, not ISLR (R edition), for a Python-first curriculum. SkillTrace's existing `graph/resources.yaml` is Python-first (Khan + scikit-learn convention), so ISLP is the natural fit. Either keep ISLR as a free, theory-rich option *or* swap to ISLP. Suggest one node for "statistical learning theory" and explicitly note the Python vs R tooling choice in the resource annotation.

---

## 4. Kaggle (learning tracks / competitions)

**Primary sources**
- Learn hub: <https://www.kaggle.com/learn>
- Intro to Machine Learning: <https://www.kaggle.com/learn/intro-to-machine-learning>
- Intermediate Machine Learning: <https://www.kaggle.com/learn/intermediate-machine-learning>
- Kaggle Learn order thread: <https://www.kaggle.com/general/198508>

**a. Still active and recommended in 2026?** Yes — Kaggle Learn tracks remain a standard free starting point in 2026 reviews. Statnzee (Apr 2026) ranks them among the best free ways to learn data science. Each course is short (3–8 hours), practical, browser-based, with free certificates of completion.

**b. Free and verifiable?** Yes — all Kaggle Learn courses are free; certificates are now issued at no cost. No-cost notebooks (Kaggle Notebooks, 30h/week GPU on P100/T4), free competitions, free datasets. The platform's free-tier compute is documented in `docs/resources/free-compute-guide.md` (the existing SkillTrace file), so the source is already partially baked into the project.

**c. Substantive content drift?** Modest drift; the canonical ML courses (Intro ML, Intermediate ML, Pandas, Feature Engineering, ML Explainability) are stable. The "competitions" side has evolved — the platform emphasizes code competitions and now has tighter integration with Kaggle Models. Curriculum implication: the older "Kaggle competitions" framing is fine, but the most accessible entry point in 2026 is the **Learn tracks**, not competitions.

**d. 2026 alternates**
- **Google MLCC** (see #1) — more conceptual, longer.
- **fast.ai** — top-down, longer projects.
- **Hugging Face course chapters** (relevant for Phase 3, not Phase 2).
- For competitions specifically: **DrivenData** and **Zindi** (social-impact focus), **AIcrowd** (research focus).

**e. Phase 2 shape implications** Keep as a primary resource; in 2026 the most useful entry is the **Learn tracks** (Intro ML + Intermediate ML + Feature Engineering), not raw competitions. A learner new to ML gets more traction from the tracks than from a competition. Free compute + free courses + free certificates is the strongest free-first story in this list. Map to two Phase 2 nodes: "applied ML basics" (Intro/Intermediate ML) and "competitions as practice" (optional, separate node).

---

## 5. FastAPI

**Primary sources**
- Official site: <https://fastapi.tiangolo.com/>
- GitHub: <https://github.com/fastapi/fastapi>
- Release feed: <https://github.com/fastapi/fastapi/releases> (current stable 0.141.1 as of 2026-07-29 per release-alert.dev)

**a. Still active and recommended in 2026?** Yes — actively maintained, default Python API framework. Per Medium / Pravin (Mar 2026), ~38% of Python developers use FastAPI in 2026 surveys, and it is "becoming the default choice for many Python API projects." The framework sits on Starlette + Pydantic, has a strong AI/ML ecosystem fit (Pydantic models map cleanly to LLM tool schemas), and is now shipped with `fastapi-cli[standard]` for `fastapi deploy` to FastAPI Cloud.

**b. Free and verifiable?** Yes — MIT-licensed framework, free for any use. Documentation is free; courses are free (third-party). No "certification" track owned by FastAPI itself; the proof-of-competence is the project portfolio.

**c. Substantive content drift?** Material drift:
- Versioning: 0.115 → 0.141 in ~12 months — rapid release cadence, no 1.0 yet.
- Stack: Pydantic v2, free-threaded Python 3.14t support (0.137+), native type-hints.
- New: `fastapi[standard]` install extra with Uvicorn + `fastapi-cli`; FastAPI Cloud deploy target.
- Unchanged: the OpenAPI/Swagger story, the dependency-injection style, the type-hint-first API.
- SkillTrace note: this is a 0.x version framework; some risk for long-term curriculum claims. The framework's API has been stable for several minor versions despite the high version number.

**d. 2026 alternates**
- **Django + DRF** — heavier, batteries-included, better if you also need admin/auth/ORM.
- **Flask** — older, simpler, but losing mindshare.
- **Litestar** — newer ASGI alternative, similar ergonomics, growing.
- **Starlette** directly — if you don't need the FastAPI abstractions.

**e. Phase 2 shape implications** This is a notable **content-fit drift**: FastAPI is the right 2026 default for *Phase 5 / deployment* (serving ML models, agent APIs, LLM tool servers), not *Phase 2 ML* itself. The roadmap's original placement of FastAPI in the "Phase 2 ML seed graph" (per `POST_V1_BACKLOG.md:35-36`) is mis-grouped — FastAPI is a serving/deployment concern, not a classical-ML concept. **Suggest G-Slot (#100) re-scope FastAPI to v1.3 (LLM/agents) or v1.5 (analytics/portfolio deployment) rather than v1.2.** Two possible Phase 2 framings: (i) drop FastAPI from Phase 2 entirely; (ii) keep one node titled "ML model serving primer" with FastAPI as the implementation. Both are defensible — call is for G-Slot.

---

## 6. Docker

**Primary sources**
- Docker pricing (official): <https://www.docker.com/pricing/>
- Docker Subscription Service Agreement: <https://www.docker.com/legal/docker-subscription-service-agreement>
- Docker Desktop 2026 landscape articles: <https://www.youngju.dev/blog/culture/2026-05-15-docker-desktop-alternatives-2026-podman-orbstack-colima-finch-rancher-deep-dive.en> (May 2026), <https://env.dev/guides/docker-on-windows> (Apr 2026), <https://tech-insider.org/au/podman-vs-docker-desktop-vs-finch-2026/> (Aug 2026)

**a. Still active and recommended in 2026?** Yes — Docker Engine and the Docker CLI remain standard, but **the "Docker Desktop" product is no longer the universal default**. The 2022/2024-tightened Docker Subscription Service Agreement requires paid Docker Desktop for any organization with 250+ employees **or** $10M+ annual revenue (or any government entity). Free Docker Engine inside Linux/WSL2 is unaffected. In 2026 the mainstream free alternatives are **Podman Desktop** (Red Hat, Apache 2.0), **Finch** (AWS, Apache 2.0), **Rancher Desktop** (SUSE, Apache 2.0), **Colima** (MIT, Mac/Linux), and **Apple Container** (macOS 15.4+, Apache 2.0, Apple Silicon).

**b. Free and verifiable?** **Conditionally yes.** Free for individuals, education, open-source, and small businesses (under 250 employees **and** under $10M revenue). **Both conditions must hold.** Not free for any government entity regardless of size. The underlying Docker Engine remains Apache 2.0 and free regardless of company size. The SkillTrace free-first doctrine has a clean answer: use Docker Engine (Linux/WSL2) or a free alternative (Podman, Finch, Colima); Docker Desktop specifically is not unconditionally free.

**c. Substantive content drift?** **Major drift, mostly in the last 18 months:**
- **Pricing model change:** 2022 introduction of the 250-employee / $10M threshold; 2024 tightening of terms.
- **Free alternatives matured:** Podman Desktop 1.20.x, Finch 1.14.1 (Jan 2026), Rancher Desktop 1.18.x, OrbStack 1.10.x (commercial, ~$8/user/mo), Apple Container 1.0 (June 2026).
- **Apple Container (WWDC 2025, GA June 2026)** is a genuinely new entrant: per-container lightweight VMs via Apple's Virtualization framework, Apple Silicon only, Apache 2.0.
- **Engine-side:** Docker Engine is still Apache 2.0 and unchanged; the licensing change is to Docker Desktop, not the engine.

**d. 2026 alternates** (in order of fit for a single-learner local environment)
- **Docker Engine in WSL2** (Linux) — free, Apache 2.0, no company-size restriction. Best for a CLI-first learner on Windows.
- **Podman Desktop** — free, daemonless, rootless, Red Hat-backed. Best for learners who care about rootless/daemonless security.
- **Rancher Desktop** — free, Apache 2.0, GUI + k3s. Best for a Docker-Desktop-like experience without the license.
- **Colima** — free, MIT, Mac/Linux, lightweight. Best for solo Mac developers on a budget.
- **Finch** — free, AWS-backed, ECR/Fargate-friendly. Best for AWS-deployment-oriented learners.
- **OrbStack** — paid (~$8/user/mo) but fast; free for personal use; Mac only.
- **Apple Container** — free, Mac 15.4+ Apple Silicon only; future-bet.

**e. Phase 2 shape implications** Same re-scope concern as FastAPI: Docker is a **deployment / environment** concern, not a classical-ML concept. The roadmap's placement of Docker in the Phase 2 ML seed graph is mis-grouped. **Suggest G-Slot (#100) re-scope Docker to v1.3 or v1.5 (deployment context), not v1.2 (classical ML content).** If a Phase 2 framing is wanted, the cleanest move is to teach the *concept* of containerized ML environments using Docker Engine / Podman (both Apache 2.0, both free) rather than Docker Desktop specifically — that preserves the free-first doctrine regardless of the learner's future employer size.

---

## Implications for v1.2 (one paragraph)

Of the six sources, **four remain strong primary choices for a 2026 Phase 2 ML seed graph**: Google MLCC, Andrew Ng's *Machine Learning Specialization* (note: the Python three-course version, not the legacy Octave course), ISLR/ISLP, and Kaggle Learn. The MLCC 2024 refresh actually *increased* its relevance by adding LLM coverage; Ng's course is the same default first stop as it was in 2024 but in a modernized Python form; ISLR's 2nd edition (2021/2022) added deep-learning, survival, and multiple-testing chapters, and the Python translation (ISLP, 2023) is a more natural default for a Python-first curriculum. **Two sources are mis-grouped rather than deprecated**: FastAPI and Docker are 2026-stable and recommended — but for *deployment* and *environment* concerns, not for classical-ML theory. G-Slot (#100) should re-scope them out of v1.2 (toward v1.3 agent deployment or v1.5 portfolio/analytics deployment). Docker specifically carries a free-first caveat: Docker *Engine* is Apache 2.0, but Docker *Desktop* requires a paid subscription for organizations ≥250 employees or ≥$10M revenue, so the curriculum should default to Docker Engine (Linux/WSL2) or to a free alternative (Podman, Rancher Desktop, Finch, Colima) to preserve SkillTrace's free-first doctrine.

---

## Citations / primary sources used

- Google MLCC course index — <https://developers.google.com/machine-learning/crash-course>
- Google blog, MLCC 2024 refresh — <https://blog.google/innovation-and-ai/technology/developers-tools/machine-learning-crash-course/>
- Google MLCC prerequisites — <https://developers.google.com/machine-learning/crash-course/prereqs-and-prework>
- Google ML foundational courses — <https://developers.google.com/machine-learning/foundational-courses>
- Coursera: Machine Learning Specialization (Andrew Ng, DeepLearning.AI + Stanford Online) — <https://www.coursera.org/specializations/machine-learning-introduction>
- Coursera: Supervised Machine Learning: Regression and Classification — <https://www.coursera.org/learn/machine-learning/>
- Pivot News (May 2026) — "Why Andrew Ng's Coursera ML Course Still Anchors AI…" — <https://pivotnews.ai/education/andrew-ng-coursera-ml-foundational>
- CourseFacts (May 2026) — Andrew Ng ML Course Review 2026 — <https://www.coursefacts.com/guides/andrew-ng-ml-course-review-2026>
- ISLR official book site (Trevor Hastie) — <https://trevorhastie.github.io/ISLR/>
- ISLR 2nd ed. free PDF (corrected 7th printing, June 2023) — <https://hastie.su.domains/ISLRv2_website.pdf>
- ISLR 2nd ed. Springer record — <https://link.springer.com/book/10.1007/978-1-0716-1418-1>
- ISLR 2nd ed. CC BY-NC-SA mirror — <https://opentechbook.com/book/an-introduction-to-statistical-learning-2nd-edition-with-applications-in-r/>
- Kaggle Learn hub — <https://www.kaggle.com/learn>
- Kaggle Learn: Intro to Machine Learning — <https://www.kaggle.com/learn/intro-to-machine-learning>
- Kaggle Learn: Intermediate Machine Learning — <https://www.kaggle.com/learn/intermediate-machine-learning>
- Statnzee (Apr 2026) — Kaggle Learn Review 2026 — <https://statnzee.com/kaggle-learn-review-2026-one-of-the-best-free-ways-to-learn-data-science/>
- FastAPI official site — <https://fastapi.tiangolo.com/>
- FastAPI GitHub — <https://github.com/fastapi/fastapi>
- FastAPI releases (release-alert.dev feed) — <https://releasealert.dev/github/fastapi/fastapi>
- Medium / Pravin (Mar 2026) — "Is FastAPI Still Relevant in 2026?" — <https://medium.com/@pravinkunnure9/is-fastapi-still-relevant-in-2026-46fb6da63c26>
- Docker pricing — <https://www.docker.com/pricing/>
- Docker Subscription Service Agreement — <https://www.docker.com/legal/docker-subscription-service-agreement>
- Young Ju (May 2026) — Docker Desktop alternatives 2026 — <https://www.youngju.dev/blog/culture/2026-05-15-docker-desktop-alternatives-2026-podman-orbstack-colima-finch-rancher-deep-dive.en>
- env.dev (Apr 2026) — Docker on Windows 2026 — <https://env.dev/guides/docker-on-windows>
- Tech-Insider (Aug 2026) — Podman vs Docker Desktop vs Finch 2026 — <https://tech-insider.org/au/podman-vs-docker-desktop-vs-finch-2026/>
- TechRiseUps (Jul 2026) — Podman vs Docker 2026 — <https://techriseups.com/articles/podman-vs-docker-2026-rootless-security-real-costs>

## Local files referenced

- `docs/POST_V1_BACKLOG.md` (v1.2 line 35-36)
- `docs/ai-engineering-roadmap.md` (Phase 2 line 59-60, current version 1.0, August 2026)
- `docs/resources/free-compute-guide.md` (Kaggle compute already documented)
- `graph/resources.yaml` (resource-registry convention: `cost: free`, `last_verified: YYYY-MM-DD`)
