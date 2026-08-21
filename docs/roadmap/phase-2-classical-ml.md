# Phase 2: Classical Machine Learning

**Estimated Hours:** 60  
**Weeks at 6h:** 10 | **Weeks at 8h:** 8  
**Prerequisites:** Phase 0 (Python, Git, SQL) + Phase 1 (Math intuition)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will be able to:
- Frame problems as supervised/unsupervised ML tasks
- Split data properly (train/validation/test), avoid data leakage
- Train, evaluate, and interpret models using scikit-learn
- Explain bias-variance tradeoff, overfitting, regularization
- Implement linear/logistic regression from scratch (NumPy)
- Complete Kaggle Titanic and House Prices competitions (3+ submissions each)
- Deploy a simple model as a FastAPI endpoint (preview of Phase 5)

---

## Resource Table

### Primary Path (Practice-First, ~55 Hours)

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **Google ML Crash Course (Updated 2024)** | https://developers.google.com/machine-learning/crash-course | Interactive widgets, Colab exercises, video | 15 | Badges | 2026-08-08 |
| **fast.ai Practical Deep Learning for Coders Part 1** | https://course.fast.ai/ | 9×90min videos + notebooks (Lessons 1–5 for classical ML) | 25–30 | No | 2026-08-08 |
| **Kaggle Learn: Intro to Machine Learning** | https://www.kaggle.com/learn/intro-to-machine-learning | Micro-course, notebook-based | 3 | **Yes (free)** | 2026-08-08 |
| **Kaggle Learn: Intermediate Machine Learning** | https://www.kaggle.com/learn/intermediate-machine-learning | Micro-course | 4 | **Yes (free)** | 2026-08-08 |
| **ISL: Intro to Statistical Learning (Free PDF)** | https://www.statlearning.com/ | Book (Python edition ISLP), labs | Reference | No | 2026-08-08 |

### Theory Deep-Dive (Optional, +80 Hours)

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **Andrew Ng ML Specialization (Coursera audit)** | https://www.coursera.org/specializations/machine-learning-introduction | 3 courses, theory-heavy, Python/scikit-learn | 60–80 | No (paid only) | 2026-08-08 |
| **ISL: Full Book + Labs** | https://www.statlearning.com/ | Read corresponding chapters + R/Python labs | 60–80 | No | 2026-08-08 |

---

## Recommended Approach

**Default: Practice-First (Google MLCC → fast.ai → Kaggle)**
1. **Google ML Crash Course** (15h) — updated 2024 with LLM modules, interactive widgets, Colab exercises. Complete all modules.
2. **fast.ai Part 1, Lessons 1–5** (25h) — tabular data, random forests, gradient boosting, collaborative filtering. Run notebooks on Kaggle/Colab.
3. **Kaggle Learn ML micro-courses** (7h) — quick reinforcement, 2 certificates.
4. **Implement from scratch** — Linear regression, logistic regression in NumPy (required checkpoint).
5. **Kaggle Competitions** — Titanic + House Prices, 3+ submissions each, improving score.

**Theory Option:** If you want mathematical depth, do Andrew Ng + ISL *instead of* or *after* practice path. Not required for engineering roles.

---

## Weekly Breakdown

### At 6 Hours/Week (10 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | ML workflow, framing, data prep | Google MLCC: Framing, Data Prep | GitHub: `ml-crash-course-notes` |
| 2 | Linear regression, loss functions | Google MLCC: Linear Regression | NumPy linear regression from scratch |
| 3 | Classification, logistic regression | Google MLCC: Logistic Regression | NumPy logistic regression from scratch |
| 4 | Model evaluation, validation | Google MLCC: Evaluation, Validation | Titanic: 1st submission + analysis |
| 5 | Decision trees, ensembles | fast.ai Lesson 1–2 (tabular) | Titanic: 2nd submission (improved) |
| 6 | Random forests, gradient boosting | fast.ai Lesson 3–4 | House Prices: 1st submission |
| 7 | Unsupervised learning, embeddings | fast.ai Lesson 5 + Google MLCC | House Prices: 2nd submission |
| 8 | **Kaggle Competitions Push** | Titanic + House Prices | Both: 3+ submissions, best scores |
| 9 | **From-scratch implementations** | Linear/Logistic regression in NumPy | GitHub: `ml-from-scratch` |
| 10 | **Checkpoint + Mini-Deploy** | FastAPI wrapper for best model | Deployed endpoint (preview Phase 5) |

### At 8 Hours/Week (8 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | Google MLCC Complete (Framing → Validation) | All MLCC modules | Notes repo + Colab notebooks |
| 2 | fast.ai Lessons 1–3 (Tabular, RF, GB) | Videos + notebooks on Kaggle | GitHub: `fastai-tabular` |
| 3 | fast.ai Lessons 4–5 + Kaggle Micro-courses | Collab filtering, embeddings | Kaggle certs (2) |
| 4 | Titanic Competition Deep Dive | 3+ submissions, feature engineering | Best score + writeup |
| 5 | House Prices Competition Deep Dive | 3+ submissions, stacking | Best score + writeup |
| 6 | From-Scratch: Linear + Logistic Regression | NumPy only, no sklearn | GitHub: `ml-from-scratch` |
| 7 | Model Deployment Preview | FastAPI + Docker (Phase 5 skills) | Local endpoint working |
| 8 | Checkpoint + Portfolio Consolidation | Review, GitHub push | `classical-ml` portfolio repo |

---

## Checkpoint Exercises (Must Pass Before Phase 3)

### Conceptual (Explain Without Notes)
1. **Bias-Variance:** Draw bias-variance tradeoff curve; explain how model complexity affects each
2. **Overfitting:** Describe 3 signs of overfitting; name 2 regularization techniques
3. **Validation:** Why is test set sacred? What is data leakage? Give 2 examples
4. **Metrics:** When to use accuracy vs. F1 vs. ROC-AUC vs. RMSE? Real example each

### Practical (Code From Memory)
1. **Linear Regression from Scratch:** NumPy implementation with gradient descent; compare to sklearn
2. **Logistic Regression from Scratch:** NumPy with sigmoid, log-loss, gradient descent
3. **Full Pipeline:** Load CSV → clean → split → train RandomForest → evaluate → save model (joblib)
4. **Feature Engineering:** Titanic — create 3+ new features (family size, title, deck), show impact

### Kaggle Competitions (Minimum)
- **Titanic:** ≥0.78 accuracy (top 50% threshold)
- **House Prices:** RMSE ≤ 0.15 (log scale, top 50% threshold)
- **Documentation:** Each submission has commit message explaining what changed

---

## GitHub Portfolio Task

Repository: `classical-ml` with structure:
```
classical-ml/
├── google-mlcc/
│   ├── notes.md
│   └── colab-notebooks/
├── fastai-part1/
│   ├── lesson1-tabular.ipynb
│   ├── lesson2-rf.ipynb
│   ├── lesson3-gb.ipynb
│   ├── lesson4-embeddings.ipynb
│   └── lesson5-collab.ipynb
├── from-scratch/
│   ├── linear-regression-numpy.py
│   ├── logistic-regression-numpy.py
│   └── gradient-descent-visualization.ipynb
├── kaggle-titanic/
│   ├── submissions/ (3+ CSV files)
│   ├── feature-engineering.ipynb
│   └── best-model-analysis.md
├── kaggle-house-prices/
│   ├── submissions/
│   ├── feature-engineering.ipynb
│   └── best-model-analysis.md
├── deployment-preview/
│   ├── model.joblib
│   ├── main.py (FastAPI)
│   ├── Dockerfile
│   └── requirements.txt
└── README.md
```

---

## Key Updates (2026)

| Change | Details |
|--------|---------|
| **Google MLCC Updated** | Now includes LLM basics, AutoML, responsible AI modules (Nov 2024 refresh) |
| **fast.ai Part 2** | Implements Stable Diffusion from scratch; uses Kaggle/Paperspace free GPUs |
| **ISL Editions** | 2nd Edition (R) and Python Edition (ISLP) both free PDF download |
| **Kaggle Learn** | New "ML Explainability" micro-course (SHAP, permutation importance) |

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Jumping to neural nets too early | **Complete classical ML first** — trees/ensembles beat NNs on tabular data |
| Copying notebooks without understanding | **Reproduce from memory** — close notebook, reimplement |
| Ignoring data leakage | **Audit every split** — no target info in features, no future data in train |
| Only optimizing accuracy | **Use proper metrics** — F1 for imbalanced, RMSE for regression, AUC for ranking |
| Skipping from-scratch implementations | **They build intuition** — required checkpoint, not optional |

---

## Optional Deep-Dives (If Time Permits)

| Topic | Resource | Hours |
|-------|----------|-------|
| Time series forecasting | Kaggle Learn Time Series + Nixtla statsforecast | 15 |
| ML interpretability (SHAP, LIME) | Kaggle ML Explainability + SHAP docs | 10 |
| Automated ML (AutoML) | H2O.ai, Auto-sklearn, Google MLCC AutoML module | 10 |
| Causal inference | CausalML (Uber) + "Causal Inference for ML" (free chapters) | 20 |

---

## Next Phase Preview

**Phase 3: Deep Learning & Transformers** — Karpathy Zero to Hero (build GPT from scratch) → Hugging Face LLM Course (transformers, fine-tuning, RAG) → fast.ai Part 2 (Stable Diffusion, advanced topics).

**Prepare:** Ensure GPU access works (Kaggle 30h/wk, Colab 15–30h/wk). Create Hugging Face account.