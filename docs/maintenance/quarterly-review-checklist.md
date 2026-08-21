# Quarterly Review Checklist

**Purpose:** Keep roadmap resources current — run every 3 months  
**Last Run:** August 2026  
**Next Due:** November 2026

---

## Checklist Template (Copy for Each Review)

### Review Metadata
- **Date:** YYYY-MM-DD
- **Reviewer:** [Name/GitHub handle]
- **Roadmap Version:** 1.0
- **Changes Made:** [Summary]

---

## 1. Resource Link Verification (All Phases)

For each resource in all phase files + resource files:
- [ ] URL accessible (200 OK)
- [ ] Content still free (no paywall added)
- [ ] Course version/edition current
- [ ] Certificate still offered (if applicable)
- [ ] Estimated hours still accurate

**Tool:** `curl -I <URL>` or browser check

**Priority Resources (Check First):**
- [ ] Hugging Face Courses (Agents, MCP, Context, LLM, CV, Diffusion, Deep RL, Audio)
- [ ] DeepLearning.AI Short Courses (beta status)
- [ ] Google ML Crash Course
- [ ] fast.ai (Part 1 & 2)
- [ ] Kaggle Learn micro-courses
- [ ] CS50P (edX)
- [ ] Stanford CS25 (new version?)
- [ ] Microsoft Agent Framework (AutoGen migration)
- [ ] Cloud free tiers (Colab, Kaggle, HF Spaces, Render, Lightning)

---

## 2. Course Content Updates

| Resource | Check For | Action if Changed |
|----------|-----------|-------------------|
| **HF Agents Course** | New units, GAIA benchmark changes | Update Phase 4 weekly breakdown |
| **HF MCP Course** | MCP spec version, new transports | Update MCP section |
| **HF Context Course** | New units, capstone changes | Update Context section |
| **HF LLM Course** | New chapters (RAG, agents, eval) | Update Phase 3 |
| **fast.ai** | New lessons, Part 3? | Update Phases 2, 3, 5 |
| **Google MLCC** | New modules (LLM, AutoML, responsible AI) | Update Phase 2 |
| **DeepLearning.AI** | Beta end date, PRO requirement | Update free course list |
| **Stanford CS25** | New version (V7?) | Update Phase 3 |
| **Kaggle Learn** | New micro-courses | Add to relevant phases |
| **CS50P** | New year edition (2025, 2026) | Update Phase 0 |

---

## 3. Compute Platform Changes

| Platform | Check | Threshold for Update |
|----------|-------|---------------------|
| **Kaggle** | GPU hours/week, accelerator types | <25h/wk or no P100 |
| **Colab** | GPU availability, session length | <10h/wk or K80 only |
| **HF Spaces ZeroGPU** | Free tier minutes, space count | <3 min/day or 1 space |
| **Render** | Free tier hours, spin-down time | <500h/mo or >30min idle |
| **Lightning AI** | Monthly hours, phone verify requirement | <40h/mo or credit card required |
| **Ollama** | New quantized models, Windows support | Major version release |

---

## 4. Certification Updates

| Cert | Check | Action |
|------|-------|--------|
| **AWS AI Practitioner** | Exam version (AIF-C01 current), price, free materials | Update cost, study links |
| **Azure AI-900** | Exam version, free voucher events | Note Build/Ignite dates |
| **HF Certificates** | Still free? New courses? | Add/remove from tracker |
| **Kaggle** | Still free? New certificates? | Update count |
| **CS50P** | Still free audit + cert? | Confirm |

---

## 5. Framework Updates

| Framework | Check | Action |
|-----------|-------|--------|
| **smolagents** | Version, breaking changes, new agents | Update Phase 4 |
| **LangGraph** | Version, Functional API changes, persistence | Update Phase 4, Capstone 2 |
| **LlamaIndex** | Version, Workflows API, LlamaParse credits | Update Phase 4, Capstone 3 |
| **DSPy** | Version, teleprompters, MCP support | Update Capstone 3 option |
| **CrewAI** | Version, Flows API, memory | Note in resources |
| **AutoGen/Agent Framework** | Migration status, Agent Framework GA | Update warning note |

---

## 6. Roadmap Structure Changes

- [ ] Phase hour estimates still accurate?
- [ ] Weekly breakdowns realistic for 6h/8h?
- [ ] Checkpoint exercises still valid?
- [ ] Capstone requirements current?
- [ ] New phase needed? (e.g., eval, safety, specific domain)
- [ ] Prerequisite chain still correct?

---

## 7. Global Relevance Check

- [ ] No region-specific content (Canada, US-only, EU-only)
- [ ] Cloud free tiers available globally (note restrictions)
- [ ] Certification exams available in target regions
- [ ] Job market references generic/global

---

## 8. Documentation Updates

- [ ] Update `last verified` dates in all files
- [ ] Increment version in `ai-engineering-roadmap.md`
- [ ] Add changelog entry
- [ ] Commit with message: `chore: quarterly review YYYY-MM-DD`

---

## 9. Community Feedback (If Applicable)

- [ ] Check GitHub Issues for broken links / outdated info
- [ ] Check Discussions for suggested additions
- [ ] Incorporate valid feedback

---

## 10. Publish Updates

- [ ] Push to main branch
- [ ] Update any external references (README, portfolio)
- [ ] Announce in relevant communities (optional)

---

## Known Volatile Items (Extra Attention)

| Item | Why Volatile | Check Frequency |
|------|--------------|-----------------|
| Google Colab GPU quotas | Dynamic, unpublished, changes silently | Monthly |
| DeepLearning.AI free access | Beta period, may end | Quarterly |
| HF ZeroGPU free tier | Recently added request limits | Quarterly |
| Microsoft exam pricing/vouchers | Regional, event-based | Quarterly |
| AutoGen → Agent Framework | Migration timeline unclear | Quarterly |
| Kaggle GPU/TPU quotas | Can change with platform updates | Quarterly |
| Render free tier | Spun down policies, hours | Quarterly |

---

## Stable Anchors (Low Maintenance)

| Resource | Why Stable |
|----------|------------|
| MIT OCW (18.06, 18.06SC) | Permanent archive, no changes |
| 3Blue1Brown YouTube | Permanent, no paywall |
| Khan Academy | Core content stable, free forever |
| Paul's Online Math Notes | Personal site, maintained since 2000s |
| ISL Book PDFs | Springer open access, permanent |
| Stanford CS25 Recordings | YouTube, permanent |
| FastAPI, Docker, MLflow Docs | Versioned, backward compatible |
| Hugging Face Course Content | Apache 2.0, GitHub repos, versioned |

---

## Review Log

| Date | Version | Reviewer | Key Changes |
|------|---------|----------|-------------|
| 2026-08-08 | 1.0 | [Initial] | Created all roadmap files |

---

## Quick Commands for Verification

```bash
# Check all URLs in markdown files (requires markdown-link-check)
npx markdown-link-check docs/**/*.md

# Or manually check key URLs
curl -sI https://huggingface.co/learn/agents-course | head -1
curl -sI https://course.fast.ai/ | head -1
curl -sI https://cs50.harvard.edu/python | head -1
curl -sI https://www.kaggle.com/learn | head -1
```

---

## Emergency Update Triggers (Run Review Immediately)

- [ ] Major framework breaking change (LangGraph v1.0, LlamaIndex v0.11+)
- [ ] Free tier removed from key platform (Colab GPU, Kaggle GPU, HF Spaces)
- [ ] Certification exam retired or major version change
- [ ] Course completely removed or paywalled
- [ ] New paradigm shift (e.g., post-transformer architecture mainstream)