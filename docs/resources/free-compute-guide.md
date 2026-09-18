# Free Compute Guide for AI Engineering

**Last Verified:** 2026-09-18 (G-ResourceRevisions #301; Render section re-verified against the primary source below)
**Purpose:** Reference for free GPU/CPU compute across all roadmap phases

> **Sources (fetched 2026-09-18):** [Render "Deploy for Free" docs](https://render.com/docs/free) (spin-down duration, service-type limits, Postgres expiry, usage caps). Other platforms' quotas below keep their 2026-08-08 verification date — re-check them on the next quarterly review.

---

## Combined Weekly GPU Budget: ~60 Hours

| Platform | GPU | VRAM | Weekly Quota | Session Max | Best Use Case | Verified |
|----------|-----|------|--------------|-------------|---------------|----------|
| **Kaggle** | T4 / P100 | 16GB | **30h guaranteed** | 12h (GPU), 9h (TPU) | Primary notebook platform, reliable quota | 2026-08-08 |
| **Google Colab** | T4 (sometimes K80) | 16GB | **15–30h dynamic** | 12h | Secondary, quick experiments, Colab-specific libs | 2026-08-08 |
| **HF Spaces (ZeroGPU)** | RTX Pro 6000 Blackwell | 48–96GB | **5 min/day free** | Per-request | Deploy demos, MCP servers, share agents | 2026-08-08 |
| **Lightning AI** | Various (A100, H100) | Up to 80GB | **80h/month** (phone verify) | 4h restart | Persistent VS Code dev environment | 2026-08-08 |
| **Paperspace Gradient** | T4 | 16GB | Unlimited restarts | 6h/session | Alternative notebook, longer sessions | 2026-08-08 |
| **Amazon SageMaker Studio Lab** | T4 | 16GB | 4h/24h | 4h | AWS-integrated, persistent storage | 2026-08-08 |
| **Intel Tiber AI Cloud** | Gaudi/Intel Max | 48GB | Shared queue | Batch | Non-CUDA, oneAPI/SYCL workloads | 2026-08-08 |

---

## Strategy: "Kaggle + Colab + HF Spaces" Trinity

### 1. Kaggle = Primary (Guaranteed 30h/wk)
- **Pros:** Guaranteed quota, P100/2×T4, auto-save, datasets integrated, free TPU (20h/wk)
- **Cons:** No internet by default (enable in Settings), 12h session max
- **Best For:** Training, fine-tuning, long experiments, Kaggle competitions

### 2. Colab = Secondary (Overflow 15–30h/wk)
- **Pros:** Different library versions, Colab-specific integrations, familiar UI
- **Cons:** Dynamic quota (unpublished), K80 at peak hours, 12h session max
- **Best For:** Quick experiments, prototyping, HF LLM Course notebooks

### 3. HF Spaces ZeroGPU = Deployment (5 min/day free)
- **Pros:** RTX Pro 6000 Blackwell (48–96GB), free for demos, MCP servers, 2 free spaces
- **Cons:** 5 min/day GPU for free accounts, request-based allocation
- **Best For:** Live demos, MCP servers, sharing agents with recruiters

### 4. Lightning AI = Persistent Dev (80h/month)
- **Pros:** VS Code in browser, persistent storage, A100/H100 available, phone verification only
- **Cons:** 4h session restart, monthly cap
- **Best For:** Development environment, debugging, long-running sessions

---

## Phase-by-Phase Compute Allocation

| Phase | Primary | Secondary | Deployment | Notes |
|-------|---------|-----------|------------|-------|
| **0: Prerequisites** | Local / Colab CPU | — | — | No GPU needed |
| **1: Math** | Local / Colab CPU | — | — | NumPy/Matplotlib only |
| **2: Classical ML** | Kaggle (CPU) | Colab CPU | — | scikit-learn, no GPU needed |
| **3: Deep Learning** | **Kaggle (GPU)** | Colab (GPU) | HF Spaces | Karpathy, HF LLM Course, fine-tuning |
| **4: Agentic AI** | **Kaggle (GPU)** | Colab (GPU) | **HF Spaces ZeroGPU** | Agent training, GAIA, MCP servers |
| **5: Specializations** | Kaggle / Colab | Lightning AI | HF Spaces + Render | LLMOps, Multimodal, Product demos |
| **Capstone** | Kaggle (train) | Lightning (dev) | **HF Spaces + Render** | 3 deployed apps + MCP servers |

---

## Pro Tips (2026)

### Kaggle
- **Enable Internet:** Settings → Internet → On (required for `pip install`)
- **Use Datasets:** `kaggle datasets download` directly in notebooks
- **TPU for Embeddings:** 20h/wk free TPU — faster for embedding large corpora
- **Auto-Save:** Enable in notebook settings (prevents loss on preemption)

### Colab
- **Request GPU Late-Night US:** T4 more available 10pm–6am ET
- **K80 at Peak:** Acceptable for inference, not training
- **Colab Pro ($10/mo):** Consider only for Phase 3–4 intensive weeks (1–2 months max)
- **Drive Mount:** `/content/drive` for persistent storage across sessions

### HF Spaces ZeroGPU
- **Free Tier:** 5 min/day GPU compute per account
- **Verified Account:** Email verified + 30 days old = 2 free spaces
- **Deployment:** `gradio` or `docker` mode; `docker` for MCP servers
- **Sharing:** Public spaces = portfolio links; private for testing

### Lightning AI
- **Phone Verification:** Required for 80h/month (one-time)
- **Studio Templates:** Pre-configured for PyTorch, HF, LangChain
- **Persistent Storage:** `/home/user` survives restarts
- **Team Features:** Free for personal use

---

## Local Compute (8GB RAM Laptop Strategy)

### What Runs Locally (No GPU Needed)
- All math, Python scripting, Pandas, data manipulation (Phases 0–1)
- scikit-learn ML models (Phase 2 classical ML)
- Small LLMs via **Ollama** with quantization:
  - Gemma 3 1B (0.5–4GB)
  - Phi-3 Mini / Llama 3.2 3B (4–6GB)
  - Qwen 2.5 1.5B / 3B (3–5GB)
- API-based LLM interaction (Claude, GPT-4o, Gemini) — laptop only processes response

### Ollama Setup (Recommended)
```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull quantized models
ollama pull gemma3:1b      # ~0.8GB
ollama pull phi3:mini      # ~2.3GB
ollama pull llama3.2:3b    # ~2.0GB
ollama pull qwen2.5:3b     # ~2.0GB

# Run
ollama run gemma3:1b
```

### When to Use Local vs Cloud
| Task | Local | Cloud |
|------|-------|-------|
| Data cleaning, EDA | ✅ | — |
| scikit-learn training | ✅ | — |
| LLM inference (<7B quantized) | ✅ (Ollama) | — |
| LLM fine-tuning (LoRA) | ❌ | ✅ Kaggle/Colab |
| Training from scratch | ❌ | ✅ Kaggle/Colab |
| Agent development | ✅ (Ollama + API) | ✅ (for GPU tools) |
| Deployment hosting | ❌ | ✅ HF Spaces/Render |

---

## Cost Tracking (Even Free Tiers Have Limits)

| Resource | Limit | Monitoring | Verified |
|----------|-------|------------|----------|
| **Kaggle GPU** | 30h/wk | Dashboard → GPU Usage | 2026-08-08 |
| **Colab GPU** | Dynamic | Runtime → Manage Sessions | 2026-08-08 |
| **HF ZeroGPU** | 5 min/day | Space Analytics | 2026-08-08 |
| **Lightning AI** | 80h/mo | Studio → Usage | 2026-08-08 |
| **Render** | 750h/mo (free web services) | Dashboard → Usage | 2026-09-18 |
| **Ollama** | Local RAM | `ollama ps` / Activity Monitor | 2026-08-08 |

---

## Render Free Tier (verified 2026-09-18)

Free instances exist **only** for these service types: **web services, Postgres, Key Value, and static sites**. Background workers and cron jobs are excluded — they have no free tier.

- **Spin-down (reconciled):** a free web service spins down after **15 minutes** without inbound traffic (HTTP or WebSocket); spin-up on the next request takes ~1 minute. The previous "30-minute" figure in this file was wrong and has been removed — 15 minutes is the documented value. (Per [Render docs](https://render.com/docs/free), fetched 2026-09-18.)
- **Postgres expiry:** free Postgres databases **expire 30 days after creation** (1 GB cap, one active free database per workspace); 14-day grace period to upgrade before deletion. No backups or connection pooling on free Postgres.
- **Monthly cap:** 750 free instance hours per workspace per month; spun-down services do not consume hours. Free services also count against monthly included bandwidth and build-pipeline minutes.
- **Ephemeral filesystem:** local file changes are lost on every redeploy, restart, or spin-down; free web services cannot attach persistent disks.
- **Key Value:** free instances are in-memory only — all data is lost on restart; one active free instance per workspace.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Kaggle "No GPU available" | Wait 5–10 min; try different accelerator (T4 vs P100) |
| Colab disconnects | Keep tab active; use `%%capture` for long outputs; Colab Pro for background |
| HF Space builds fail | Check `requirements.txt` pins; use `Dockerfile` for complex deps |
| Ollama OOM | Use smaller quantization (q4_k_m → q3_k_m); close other apps |
| Render spins down | Free tier spins down after 15 min idle (verified 2026-09-18); spin-up ~1 min, not ~30s — allow a full minute on first request |

---

## Links

- Kaggle Notebooks: https://www.kaggle.com/code
- Google Colab: https://colab.research.google.com/
- HF Spaces: https://huggingface.co/spaces
- Lightning AI: https://lightning.ai/
- Paperspace Gradient: https://gradient.paperspace.com/
- SageMaker Studio Lab: https://studiolab.sagemaker.aws/
- Intel Tiber AI Cloud: https://cloud.intel.com/
- Ollama: https://ollama.com/