# Phase 3: Deep Learning & Transformers

**Estimated Hours:** 80  
**Weeks at 6h:** 13 | **Weeks at 8h:** 10  
**Prerequisites:** Phase 2 (Classical ML) + Phase 1 (Calculus intuition for backprop)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will be able to:
- Build neural networks from scratch (micrograd → MLP → GPT) — Karpathy Zero to Hero
- Explain transformer architecture: self-attention, multi-head, residual connections, layer norm
- Fine-tune pretrained LLMs using Hugging Face Transformers (LoRA, QLoRA)
- Implement RAG (Retrieval-Augmented Generation) pipeline end-to-end
- Evaluate LLM outputs (perplexity, BLEU, ROUGE, LLM-as-judge)
- Train vision models (CNNs, ResNet) and multimodal basics (fast.ai Part 2)

---

## Resource Table

### Primary Path (~80 Hours)

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **Andrej Karpathy: Neural Networks Zero to Hero** | https://karpathy.ai/zero-to-hero.html | YouTube + GitHub notebooks (micrograd → makemore → GPT) | 25–30 | No | 2026-08-08 |
| **Hugging Face LLM Course** | https://huggingface.co/learn/llm-course | 12 chapters, notebooks, Colab | 40–50 | No (planned) | 2026-08-08 |
| **fast.ai Practical Deep Learning Part 2** | https://course.fast.ai/ | Lessons 10+ (Stable Diffusion, advanced) | 20–30 | No | 2026-08-08 |
| **3Blue1Brown: Neural Networks** | https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi | YouTube (4 videos, ~3h) | 4–5 | No | 2026-08-08 |
| **Stanford CS25: Transformers United V6** | https://web.stanford.edu/class/cs25/ | 9 lectures (~75min), YouTube recordings | 11–12 | No | 2026-08-08 |

### Supplementary (Reference / Deep-Dive)

| Resource | URL | Format | Est. Hours | Verified |
|----------|-----|--------|------------|----------|
| **Annotated Transformer** | https://nlp.seas.harvard.edu/annotated-transformer/ | Interactive tutorial | 10–15 | 2026-08-08 |
| **DeepLearning.AI Short Courses (Free Beta)** | https://www.deeplearning.ai/courses | 100+ courses, 1–3h each | Pick 3–5 | 2026-08-08 |
| **Attention Is All You Need (Paper)** | https://arxiv.org/abs/1706.03762 | Original transformer paper | Read 3× | 2026-08-08 |

---

## Recommended Approach

### Sequence (Do Not Reorder)
1. **Karpathy Zero to Hero** (25h) — Build micrograd (autodiff) → makemore (char RNN) → GPT from scratch. **Take notes. Re-watch.** This is the single most important resource for architectural intuition.
2. **3Blue1Brown Neural Networks** (4h) — Watch in parallel with Karpathy for backprop visualization.
3. **Hugging Face LLM Course** (40h) — Chapters 1–12: Transformers, tokenization, pretraining, fine-tuning, RAG, evaluation, deployment. Run all notebooks on Kaggle/Colab.
4. **Stanford CS25 V6** (11h) — Frontier awareness: Hinton, Vaswani, Karpathy, Gu (SSMs), Modal (production), Mistral, Anthropic. Watch annually.
5. **fast.ai Part 2** (select lessons, 20h) — Stable Diffusion from scratch, advanced vision, deployment.

### DeepLearning.AI Short Courses (Pick 3–5, Free During Beta)
- "How Transformer LLMs Work" (Alammar/Grootendorst, 1h44m)
- "Building and Evaluating Data Agents" (Datta/Reini, 1h59m)
- "DSPy: Build and Optimize Agentic Apps" (Chen Qian, 59m)
- "Evaluating AI Agents" (Gilhuly/Khan, 2h36m)
- "LLMOps" courses (multiple)

---

## Weekly Breakdown

### At 6 Hours/Week (13 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | micrograd: autodiff engine | Karpathy Ep 1–2 | GitHub: `micrograd-replica` |
| 2 | makemore: char-level RNN | Karpathy Ep 3–4 | GitHub: `makemore-replica` |
| 3 | GPT from scratch | Karpathy Ep 5–6 | GitHub: `nanoGPT-replica` |
| 4 | Transformer theory + 3B1B | Karpathy Ep 7 + 3B1B NN | Annotated Transformer walkthrough |
| 5 | HF LLM Course Ch 1–3 | Transformers, Tokenization, Pretraining | Run all notebooks on Kaggle |
| 6 | HF LLM Course Ch 4–6 | Fine-tuning (LoRA/QLoRA), PEFT | Fine-tune 7B model on custom data |
| 7 | HF LLM Course Ch 7–9 | RAG, Evaluation, Quantization | RAG pipeline on custom docs |
| 8 | HF LLM Course Ch 10–12 | Deployment, Agents intro, Ethics | Deploy model to HF Spaces |
| 9 | Stanford CS25 V6 (Lectures 1–3) | Hinton, Vaswani, Karpathy | Notes + reflection blog post |
| 10 | Stanford CS25 V6 (Lectures 4–6) | Gu (SSMs), Modal, DeepMind agents | Notes + architecture comparison |
| 11 | Stanford CS25 V6 (Lectures 7–9) | Mistral, Anthropic, Generalization | Notes + future trends summary |
| 12 | fast.ai Part 2 (Select Lessons) | Stable Diffusion, Vision | GitHub: `fastai-part2-projects` |
| 13 | **Checkpoint + Portfolio** | Review, consolidate | `deep-learning-transformers` repo |

### At 8 Hours/Week (10 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | Karpathy Zero to Hero Complete | Ep 1–7 (micrograd → GPT) | 3 replica repos |
| 2 | HF LLM Course Ch 1–6 | Transformers → Fine-tuning | Fine-tuned model on HF Hub |
| 3 | HF LLM Course Ch 7–12 | RAG → Deployment | RAG pipeline + deployed demo |
| 4 | Stanford CS25 V6 Complete | All 9 lectures | 3 blog posts / notes |
| 5 | fast.ai Part 2 + DL.AI Short Courses | Stable Diffusion + 3 short courses | Projects + certificates |
| 6 | **Consolidation + From-Scratch Re-implementation** | Re-build GPT attention from memory | GitHub: `transformer-from-scratch` |
| 7 | **Checkpoint Exercises** | Timed, no notes | Pass all checkpoints |
| 8 | **Portfolio Polish** | READMEs, blog posts, demos | `deep-learning-transformers` repo |
| 9 | **Buffer / Deep-Dive** | Annotated Transformer, paper re-read | Annotated code + notes |
| 10 | **Transition to Phase 4** | Review agentic concepts preview | Plan Phase 4 projects |

---

## Checkpoint Exercises (Must Pass Before Phase 4)

### From-Scratch (No Libraries Except NumPy)
1. **Micrograd:** Build scalar autodiff engine with backward pass; compute gradients for `f = (x * y + z).relu()`
2. **Multi-head Attention:** Implement `MultiHeadAttention` from scratch; verify against PyTorch `nn.MultiheadAttention`
3. **Transformer Block:** Assemble attention + FFN + residual + layer norm; run forward pass on dummy data
4. **GPT Mini:** Train character-level GPT on Shakespeare (Karpathy style); generate coherent text

### Hugging Face Ecosystem
1. **Fine-tune:** LoRA fine-tune Llama-3.2-1B on custom dataset (e.g., Alpaca, code); push to HF Hub
2. **RAG Pipeline:** Ingest 10 PDFs → chunk → embed (bge-small) → FAISS index → retrieve → generate (Llama-3.2-1B) → cite sources
3. **Evaluation:** Compute perplexity, BLEU, ROUGE on test set; implement LLM-as-judge for qualitative eval

### Conceptual (Explain Without Notes)
1. **Self-Attention:** Derive Q, K, V from input; explain scaled dot-product; why multi-head?
2. **Positional Encoding:** Why needed? Compare sinusoidal vs. learned vs. RoPE
3. **Scaling Laws:** What do Kaplan/Chinchilla laws say about data/compute tradeoffs?
4. **QLoRA:** How does 4-bit quantization + LoRA work? Memory savings vs. full fine-tune?

---

## GitHub Portfolio Task

Repository: `deep-learning-transformers` with structure:
```
deep-learning-transformers/
├── karpathy-replicas/
│   ├── micrograd/
│   ├── makemore/
│   └── nanoGPT/
├── hf-llm-course/
│   ├── ch01-transformers.ipynb
│   ├── ch04-finetuning-lora.ipynb
│   ├── ch07-rag-pipeline.ipynb
│   └── ch10-deployment.ipynb
├── from-scratch/
│   ├── multihead-attention.py
│   ├── transformer-block.py
│   └── minigpt-train.ipynb
├── stanford-cs25/
│   ├── lecture-notes.md
│   └── architecture-comparison.md
├── fastai-part2/
│   ├── stable-diffusion.ipynb
│   └── vision-advanced.ipynb
├── dlai-short-courses/
│   ├── transformer-internals.ipynb
│   ├── dspy-optimization.ipynb
│   └── agent-evaluation.ipynb
└── README.md
```

**Deployed Demos (HF Spaces):**
- Fine-tuned model chat interface
- RAG pipeline with document upload
- nanoGPT text generation

---

## Key Updates (2026)

| Change | Details |
|--------|---------|
| **HF LLM Course** | 12 chapters, added RAG evaluation, quantization, agent intro chapters |
| **Karpathy** | Added "Building a GPT from Scratch" as standalone course site |
| **Stanford CS25 V6** | Spring 2026: Hinton, Vaswani, SSMs, production inference, Mistral, Anthropic |
| **DL.AI Short Courses** | 100+ free during beta; agentic focus (DSPy, LangGraph, evaluation) |
| **fast.ai Part 2** | Stable Diffusion from scratch; uses free Kaggle/Paperspace GPUs |

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Watching Karpathy without coding | **Code along every episode** — pause, type, run, modify |
| Skipping from-scratch attention | **It's the gateway** — if you can't build it, you don't understand transformers |
| Fine-tuning without eval | **Always evaluate** — perplexity + qualitative + LLM-as-judge |
| Ignoring CS25 | **Watch annually** — it's your frontier radar |
| Not deploying | **HF Spaces is free** — every model needs a demo link |

---

## Optional Deep-Dives (If Time Permits)

| Topic | Resource | Hours |
|-------|----------|-------|
| Diffusion models (math + code) | "Denoising Diffusion Probabilistic Models" + HF Diffusers course | 20 |
| RLHF / DPO / PPO | HF Alignment Handbook + TRL library | 20 |
| Model compression (quant, distill, prune) | LLM.int8(), GPTQ, AWQ papers + tutorials | 15 |
| Alternative architectures (Mamba, RWKV) | Original papers + HF implementations | 15 |

---

## Next Phase Preview

**Phase 4: Agentic AI Core** — Three certified Hugging Face courses:
1. **Agents Course** (25h, 2 certs): smolagents, LlamaIndex, LangGraph, GAIA benchmark
2. **MCP Course** (20h, 2 certs): Model Context Protocol with Anthropic partnership
3. **Context Course** (25h, 2 certs): Skills, MCP, Plugins, Subagents, Hooks

This is the **emphasis phase** — agentic coding is the dominant paradigm in production AI engineering.

**Prepare:** Complete HF LLM Course Ch 11 (Agents intro). Create HF account for certificates.