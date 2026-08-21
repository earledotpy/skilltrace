# Phase 5: Specializations Survey — LLMOps, Multimodal, AI Product Engineering

**Estimated Hours:** 60 (~20h each)  
**Weeks at 6h:** 10 | **Weeks at 8h:** 8  
**Prerequisites:** Phase 4 (Agentic AI Core) + Phase 3 (Deep Learning)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will have surveyed all three specializations at working depth:
- **LLMOps:** Track experiments, monitor models, A/B test, deploy to cloud (free tiers)
- **Multimodal:** Build vision-language pipelines, use CLIP, fine-tune Stable Diffusion
- **AI Product:** Ship user-facing AI apps (FastAPI + Streamlit/Gradio), implement eval/guardrails

**Goal:** Not mastery — working familiarity to choose capstone focus and communicate with specialists.

---

## Resource Table

### Shared Foundation (All Specializations)

| Resource | URL | Format | Est. Hours | Verified |
|----------|-----|--------|------------|----------|
| **Docker Getting Started** | https://docs.docker.com/get-started/ | Tutorial, hands-on | 5–10 | 2026-08-08 |
| **FastAPI Documentation** | https://fastapi.tiangolo.com/ | Tutorial, reference | 10–15 | 2026-08-08 |
| **Hugging Face Spaces (ZeroGPU)** | https://huggingface.co/docs/hub/spaces-overview | Deploy Gradio/Docker apps | 5–10 | 2026-08-08 |
| **Render Free Tier** | https://render.com/docs/free | Web services, Postgres, 750h/mo | 5–10 | 2026-08-08 |
| **MLflow** | https://mlflow.org/docs/latest/index.html | Tracking, projects, models | 10–15 | 2026-08-08 |

### Specialization 1: LLMOps & Deployment (~20h)

| Resource | URL | Format | Est. Hours | Verified |
|----------|-----|--------|------------|----------|
| **DeepLearning.AI: LLMOps Courses** | https://www.deeplearning.ai/courses | Multiple short courses (free beta) | 5–10 | 2026-08-08 |
| **MLflow Tutorial** | https://mlflow.org/docs/latest/tutorials-and-examples/index.html | End-to-end tracking | 5 | 2026-08-08 |
| **HF Spaces ZeroGPU Guide** | https://huggingface.co/docs/hub/spaces-gpu | Dynamic GPU allocation | 3 | 2026-08-08 |
| **Render + Docker Deploy** | https://render.com/docs/docker | Containerized deployment | 3 | 2026-08-08 |
| **Google Cloud / AWS / Azure Free Tiers** | Respective docs | Cloud ML platforms (intro only) | 5 | 2026-08-08 |

### Specialization 2: Multimodal AI (~20h)

| Resource | URL | Format | Est. Hours | Verified |
|----------|-----|--------|------------|----------|
| **fast.ai Part 2 (Lessons 10+)** | https://course.fast.ai/ | Stable Diffusion from scratch, CLIP | 15–20 | 2026-08-08 |
| **Hugging Face Computer Vision Course** | https://huggingface.co/learn/computer-vision-course | Image classification, detection, segmentation | 15–20 | 2026-08-08 |
| **Hugging Face Diffusion Models Course** | https://huggingface.co/learn/diffusion-course | DDPM, Stable Diffusion, ControlNet | 10–15 | 2026-08-08 |
| **CLIP / BLIP / LLaVA Papers + HF Demos** | https://huggingface.co/models | Vision-language models | Reference | 2026-08-08 |

### Specialization 3: AI Product Engineering (~20h)

| Resource | URL | Format | Est. Hours | Verified |
|----------|-----|--------|------------|----------|
| **Streamlit Documentation** | https://docs.streamlit.io/ | Data apps, chat interfaces | 5–10 | 2026-08-08 |
| **Gradio Documentation** | https://www.gradio.app/docs/ | ML demos, chat, custom components | 5–10 | 2026-08-08 |
| **DeepLearning.AI: Building AI Applications** | https://www.deeplearning.ai/courses | Short courses (free beta) | 3–6 | 2026-08-08 |
| **Guardrails AI** | https://www.guardrailsai.com/ | Input/output validation | 3–5 | 2026-08-08 |
| **LangSmith / Phoenix (Free Tiers)** | Respective docs | Observability, eval | 3–5 | 2026-08-08 |

---

## Recommended Approach

### Do All Three (Survey Depth)
Spend ~2 weeks (6h) or ~1.5 weeks (8h) per specialization. Build one working demo each.

### Order (Suggested)
1. **LLMOps** — Foundational for all deployments
2. **Multimodal** — Extends Phase 3 vision knowledge
3. **AI Product** — Synthesizes everything into user-facing apps

### Per Specialization: Minimum Viable Demo
| Specialization | Demo Requirements |
|----------------|-------------------|
| **LLMOps** | MLflow tracking → model registry → FastAPI endpoint → Docker → Render/HF Spaces |
| **Multimodal** | CLIP image-text search OR Stable Diffusion fine-tune (LoRA) → Gradio demo |
| **AI Product** | Streamlit/Gradio chat app with RAG + guardrails + eval logging → deployed |

---

## Weekly Breakdown

### At 6 Hours/Week (10 Weeks)

| Week | Specialization | Focus | Deliverable |
|------|----------------|-------|-------------|
| 1 | LLMOps | Docker + FastAPI + MLflow basics | Local MLflow tracking server |
| 2 | LLMOps | Model registry → FastAPI → Docker → Deploy | Deployed model endpoint (Render/HF) |
| 3 | Multimodal | fast.ai Part 2: Stable Diffusion / CLIP | Image generation / search demo |
| 4 | Multimodal | HF Computer Vision or Diffusion Course | Fine-tuned LoRA or detection demo |
| 5 | AI Product | Streamlit/Gradio + FastAPI backend | Chat interface with RAG |
| 6 | AI Product | Guardrails + Eval logging (LangSmith/Phoenix) | Production-ready app with monitoring |
| 7 | **Integration** | Combine: Agent (Phase 4) + LLMOps + Product | Agent deployed as product with monitoring |
| 8 | **Deep-Dive Choice** | Pick ONE specialization to go deeper | Extended project for capstone |
| 9 | **Consolidation** | Document all three demos, compare | `specializations-survey` repo |
| 10 | **Checkpoint + Capstone Plan** | Final review, choose capstone projects | Capstone proposal document |

### At 8 Hours/Week (8 Weeks)

| Week | Specialization | Focus | Deliverable |
|------|----------------|-------|-------------|
| 1 | LLMOps | Docker, FastAPI, MLflow, Deploy | End-to-end deployed pipeline |
| 2 | Multimodal | fast.ai Pt2 + HF CV/Diffusion | Multimodal demo deployed |
| 3 | AI Product | Streamlit/Gradio, Guardrails, Eval | Product demo deployed |
| 4 | **Integration Week** | Agent + LLMOps + Product unified | Full-stack agentic product |
| 5 | **Deep-Dive** | Choose one: extend significantly | Capstone foundation |
| 6 | **Cross-Cutting** | Observability, A/B testing, Cost optimization | Production hardening |
| 7 | **Consolidation** | Document, compare, portfolio | `specializations-survey` repo |
| 8 | **Checkpoint + Capstone Plan** | Final review, propose 3 capstones | Capstone proposals |

---

## Checkpoint Exercises (Per Specialization)

### LLMOps
1. **MLflow:** Track 5+ experiments (params, metrics, artifacts); register best model; serve via `mlflow models serve`
2. **FastAPI + Docker:** Containerize model endpoint; health check; graceful shutdown; deploy to Render
3. **Monitoring:** Log predictions, latency, drift metrics; dashboard in Grafana (free) or LangSmith
4. **A/B Test:** Route 10% traffic to new model version; compare metrics; automate rollback

### Multimodal
1. **CLIP Search:** Build image-text retrieval (index 1000 images; query by text; return top-k)
2. **Stable Diffusion LoRA:** Fine-tune SDXL LoRA on 20 custom images (Kaggle GPU); Gradio demo
3. **Vision-Language:** LLaVA or BLIP-2 for image captioning + VQA; evaluate on custom set
4. **Video/3D (Optional):** HF Diffusion Course ControlNet / AnimateDiff basics

### AI Product
1. **Streamlit/Gradio App:** Chat interface with session state, streaming, markdown rendering
2. **Guardrails:** Input validation (PII, prompt injection) + output validation (format, citations)
3. **Eval Logging:** Every interaction logged (input, output, latency, user feedback) to LangSmith/Phoenix
4. **User Feedback Loop:** Thumbs up/down → auto-collect for fine-tuning dataset

---

## GitHub Portfolio Task

Repository: `specializations-survey` with structure:
```
specializations-survey/
├── llmops/
│   ├── mlflow-tracking/
│   ├── model-registry/
│   ├── fastapi-endpoint/
│   ├── docker-deploy/
│   └── monitoring-dashboard/
├── multimodal/
│   ├── clip-search/
│   ├── stable-diffusion-lora/
│   ├── vision-language-qa/
│   └── hf-cv-course-projects/
├── ai-product/
│   ├── streamlit-chat-app/
│   ├── gradio-rag-demo/
│   ├── guardrails-implementation/
│   └── eval-logging/
├── integration/
│   └── agentic-product/  # Phase 4 agent + LLMOps + Product
├── deep-dive/            # One extended project
└── README.md
```

**Deployed Demos (Required, 3 minimum):**
- LLMOps: Model endpoint on Render/HF Spaces
- Multimodal: Gradio demo on HF Spaces
- AI Product: Streamlit/Gradio app on HF Spaces/Render

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Trying to master all three | **Survey only** — 20h each, build one demo each |
| Skipping Docker | **Every deploy needs Docker** — learn it once, use everywhere |
| No monitoring | **Add logging from Day 1** — LangSmith/Phoenix free tiers |
| Ignoring costs | **Track API/GPU costs** — even free tiers have limits |
| Perfect UI, broken backend | **Backend first** — FastAPI + model → then Streamlit/Gradio |

---

## Capstone Selection Guide

| If You Enjoyed... | Capstone Focus |
|-------------------|----------------|
| Building pipelines, monitoring, scaling | **LLMOps Capstone**: Multi-model serving, A/B framework, cost optimization |
| Vision, diffusion, creative AI | **Multimodal Capstone**: Fine-tuned generative pipeline, eval framework |
| User-facing apps, product thinking | **AI Product Capstone**: Full-stack AI product with users, feedback loop |
| Agentic systems (Phase 4) | **Agentic Capstone**: Multi-agent product with MCP, eval, guardrails |

**Recommendation:** Choose **one primary** for deep capstone; build **two secondary** at survey depth.

---

## Next Phase Preview

**Capstone Projects** — Build and deploy **3 agentic applications** using different frameworks:
1. **smolagents-based** (CodeAgent paradigm)
2. **LangGraph-based** (Stateful orchestration)
3. **LlamaIndex/DSPy-based** (Data-centric or optimization)

Each must: solve real problem, have eval, deploy on HF Spaces, include MCP server, document in blog post.

**Prepare:** Review Phase 4 projects; pick 3 distinct problems; design architecture.