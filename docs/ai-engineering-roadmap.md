# AI Engineering Roadmap with Agentic Coding Emphasis

> **Scope:** Canonical index to `roadmap/*` (`reference_only` per `docs/curriculum-authoring.md:12-13`). Roadmap anchors never control locking — see `graph/edges.yaml`. Phases 2–5 are post-v1 reference (PRD:52, backlog v1.2/v1.3). Detail lives in `roadmap/phase-0:prerequisites` → `phase-5` + `capstone-projects.md`; annexes in `resources/*`.

**Version:** 1.0 (August 2026)  
**Audience:** Complete beginners  
**Pace:** Self-paced, 6–8 hours/week  
**Scope:** Global, free resources only (paid noted where high ROI)  
**Maintenance:** Quarterly review (see `maintenance/quarterly-review-checklist.md`)

---

## Executive Summary

This roadmap guides a complete beginner from zero to employable AI engineer with emphasis on **agentic coding** — building autonomous systems where LLMs reason, plan, use tools, and self-correct over multi-step tasks. All resources are free unless explicitly marked; paid options are included only when they significantly outweigh free alternatives.

**Total core curriculum:** ~380 hours  
**Estimated calendar time:** 13–16 months at 6–8 hrs/week (includes quarterly consolidation weeks)  
**Free certificates available:** 13+ (Hugging Face, Kaggle, Harvard CS50P)  
**Recommended paid certification:** AWS Certified AI Practitioner ($100)

---

## Visual Timeline

| Phase | Focus | Hours | Weeks (6h) | Weeks (8h) | Key Certificates |
|-------|-------|-------|------------|------------|------------------|
| **0** | Prerequisites: Python, Git, SQL | 40 | 7 | 5 | CS50P, Kaggle Python/Pandas/SQL (3) |
| **1** | Math Foundations: LA, Calculus, Stats | 60 | 10 | 8 | — |
| **2** | Classical ML | 60 | 10 | 8 | Kaggle Intro/Intermediate ML (2) |
| **3** | Deep Learning & Transformers | 80 | 13 | 10 | — |
| **4** | **Agentic AI Core** | 80 | 13 | 10 | **HF Agents (2), MCP (2), Context (2)** |
| **5** | Specializations Survey (LLMOps, Multimodal, AI Product) | 60 | 10 | 8 | — |
| **Capstone** | 3 Deployed Agentic Applications | Ongoing | — | — | HF Completion Certificates |
| **Consolidation** | Quarterly review weeks (every 12 weeks) | +4 weeks | 4 | 4 | — |
| **Total** | | **380** | **~67** | **~53** | **13+ free** |

---

## Quick-Start Checklist

- [ ] Create GitHub account (portfolio starts Day 1)
- [ ] Set up Google Colab + Kaggle accounts (free GPU compute)
- [ ] Complete **Phase 0** prerequisites before advancing
- [ ] Bookmark all resource URLs (listed in each phase file)
- [ ] Schedule weekly study blocks (6–8 hours, consistent days)
- [ ] Plan first consolidation week at Week 12

---

## Phase Overview

### Phase 0: Prerequisites (`roadmap/phase-0-prerequisites.md`)
Python fundamentals, Git/CLI, SQL basics. **Start here.** CS50P provides structure + free certificate.

### Phase 1: Math Foundations (`roadmap/phase-1-math-foundations.md`)
Linear algebra intuition (3Blue1Brown), calculus intuition (3Blue1Brown), statistics/probability (Khan Academy + Udacity). Tiered: Core (~40h) + Deep optional (~60h).

### Phase 2: Classical ML (`roadmap/phase-2-classical-ml.md`)
Google ML Crash Course (15h, updated 2024 with LLM modules) → fast.ai Practical Deep Learning Part 1 (40h). Theory option: Andrew Ng + ISL.

### Phase 3: Deep Learning & Transformers (`roadmap/phase-3-deep-learning.md`)
Karpathy Zero to Hero (25h, from-scratch GPT) → Hugging Face LLM Course Ch 1–12 (50h) → fast.ai Part 2 selections (30h).

### Phase 4: Agentic AI Core (`roadmap/phase-4-agentic-ai.md`) ⭐ **Emphasis**
Three certified Hugging Face courses: **Agents** (25h, 2 certs), **MCP** (20h, 2 certs), **Context Engineering** (25h, 2 certs) + Stanford CS25 V6 (11h).

### Phase 5: Specializations Survey (`roadmap/phase-5-specializations.md`)
All three at survey depth (~20h each): LLMOps/Deployment, Multimodal AI, AI Product Engineering.

### Capstone (`roadmap/capstone-projects.md`)
Build and deploy 3 agentic applications using different frameworks (smolagents, LangGraph, LlamaIndex/DSPy). Publish on Hugging Face Spaces.

---

## Free Compute Strategy (Summary)

| Platform | Weekly GPU | Best For |
|----------|------------|----------|
| **Kaggle** | 30h guaranteed (P100/T4) | Primary notebook platform |
| **Google Colab** | 15–30h dynamic (T4) | Overflow, quick experiments |
| **HF Spaces (ZeroGPU)** | 5 min/day free | Deploy demos, MCP servers |
| **Lightning AI** | 80h/month | Persistent VS Code dev env |

**Strategy:** Train on Kaggle/Colab → Deploy on HF Spaces → Share links in portfolio.

See `resources/free-compute-guide.md` for details.

---

## Certification Roadmap (Summary)

| Tier | Certificates | Cost |
|------|--------------|------|
| **Free (13+)** | HF Agents (2), MCP (2), Context (2), Deep RL (2), Audio (2), Kaggle (6+), CS50P | $0 |
| **$100** | AWS Certified AI Practitioner (AIF-C01) | $100 |
| **$250+** | AWS ML Engineer Associate (MLA-C01) | +$150 |

See `resources/certification-roadmap.md` for details.

---

## Agentic Frameworks Covered

| Framework | Role in Curriculum | Course Coverage |
|-----------|-------------------|-----------------|
| **smolagents** | Learning/prototyping (CodeAgent paradigm) | HF Agents Course Unit 2.1 |
| **LangGraph** | Production orchestration (stateful, durable) | HF Agents Course Unit 2.3 |
| **LlamaIndex** | Data-centric agents, RAG | HF Agents Course Unit 2.2 |
| **DSPy** | Optimization (signatures, teleprompters) | DL.AI short course |
| **CrewAI** | Role-based multi-agent | Referenced in Phase 4/5 |
| **Microsoft Agent Framework** | AutoGen successor (enterprise) | Migration noted |

See `resources/agentic-frameworks-comparison.md` for deep-dive.

---

## Maintenance

- **Quarterly review:** Check all URLs, course updates, pricing changes
- **Version dating:** Each file shows last verified date
- **Community reports:** GitHub Issues template for broken links

See `maintenance/quarterly-review-checklist.md`.

---

## How to Use This Roadmap

1. **Read the index** (this file) for the big picture
2. **Start with Phase 0** — do not skip prerequisites
3. **Follow resource tables** — primary resources are required; optional/deep-dive are supplementary
4. **Complete checkpoints** — each phase has exercises with expected outputs
5. **Push to GitHub** — every project, every phase
6. **Earn certificates** — track in `resources/certification-roadmap.md`
7. **Consolidate quarterly** — use the template in `maintenance/quarterly-review-checklist.md`

---

## License & Attribution

All resources linked are free per their respective licenses (MIT, Apache 2.0, CC-BY, etc.). This roadmap document is CC0 (public domain). No affiliate links. Verified August 2026.