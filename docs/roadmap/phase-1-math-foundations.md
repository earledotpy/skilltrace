# Phase 1: Mathematical Foundations — Linear Algebra, Calculus, Statistics

**Estimated Hours:** 60 (Core: 40 | Deep Optional: +60)  
**Weeks at 6h:** 10 | **Weeks at 8h:** 8  
**Prerequisites:** Phase 0 complete (Python, Git, SQL basics)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will be able to:
- Explain vectors, matrices, and linear transformations geometrically
- Compute matrix multiplication, determinants, eigenvalues/eigenvectors by hand (small) and in NumPy
- Understand derivatives as rates of change; explain gradient descent intuition
- Work with probability distributions, expected value, Bayes' theorem
- Implement math concepts in Python (NumPy, Matplotlib, SciPy)
- **Core path:** Intuition-first via 3Blue1Brown + Khan practice
- **Deep path:** Rigorous proofs + ML-targeted math (MIT OCW, DeepLearning.AI)

---

## Resource Table

### Core Path (Required, ~40 Hours)

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **3Blue1Brown: Essence of Linear Algebra** | https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab | YouTube (15 videos, ~3.5h watch) | 15–20 | No | 2026-08-08 |
| **3Blue1Brown: Essence of Calculus** | https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab | YouTube (12 videos, ~4h watch) | 12–15 | No | 2026-08-08 |
| **Khan Academy: Statistics & Probability** | https://www.khanacademy.org/math/statistics-probability | Interactive exercises, video | 15–20 | No | 2026-08-08 |
| **Udacity: Intro to Statistics (Free)** | https://www.udacity.com/course/intro-to-statistics--st101 | Video + exercises | 10–15 | No | 2026-08-08 |
| **Paul's Online Math Notes** | https://tutorial.math.lamar.edu/ | Text notes, practice problems, cheat sheets | Reference | No | 2026-08-08 |

### Deep Path (Optional, +60 Hours)

| Resource | URL | Format | Est. Hours | Certificate | Verified |
|----------|-----|--------|------------|-------------|----------|
| **MIT OCW 18.06SC Linear Algebra** | https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/ | Full self-study: lectures, problem sets, exams | 80–100 | No | 2026-08-08 |
| **MIT OCW 18.06 Linear Algebra (Strang)** | https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/ | Video lectures, problem sets | 60–80 | No | 2026-08-08 |
| **DeepLearning.AI: Mathematics for ML & Data Science (Coursera audit)** | https://www.coursera.org/specializations/mathematics-for-machine-learning-and-data-science | 3 courses: Linear Algebra, Calculus, Probability (Python labs) | 90–100 | No (paid only) | 2026-08-08 |
| **Khan Academy: Differential Calculus** | https://www.khanacademy.org/math/differential-calculus | Practice problems for 3B1B intuition | 20–30 | No | 2026-08-08 |
| **Khan Academy: Linear Algebra** | https://www.khanacademy.org/math/linear-algebra | Practice exercises following 3B1B | 20–30 | No | 2026-08-08 |

---

## Recommended Approach

### Core Path (Default for Most Learners)
1. **Watch 3Blue1Brown Essence of Linear Algebra** (15 videos) — take visual notes, don't just watch
2. **Watch 3Blue1Brown Essence of Calculus** (12 videos) — focus on derivative intuition, chain rule, optimization
3. **Khan Academy Statistics & Probability** — complete units: distributions, expected value, Bayes' theorem
4. **Implement in Python** — after each major concept, write NumPy code (see Checkpoint Exercises)
5. **Use Paul's Notes** as reference when stuck

### Deep Path (If You Want Rigor / Academic Prep)
- Complete MIT OCW 18.06SC (self-contained) or DeepLearning.AI Coursera specialization (audit)
- Do all problem sets, not just watch lectures
- This path replaces Core, not adds to it

**Decision Rule:** If you can explain eigenvectors and gradient descent to a peer after Core, you're ready. If not, do Deep.

---

## Weekly Breakdown

### Core Path at 6 Hours/Week (10 Weeks)

| Week | Focus | Resources | Python Practice |
|------|-------|-----------|-----------------|
| 1 | Vectors, linear combinations, span | 3B1B LA Ep 1–4 | NumPy vector ops, plotting |
| 2 | Linear transformations, matrices | 3B1B LA Ep 5–8 | Matrix multiplication from scratch + NumPy |
| 3 | Determinants, inverse, eigenvalues | 3B1B LA Ep 9–12 | Eigendecomposition in NumPy |
| 4 | Derivatives, chain rule, optimization | 3B1B Calc Ep 1–5 | Gradient descent on simple function |
| 5 | Integrals, backprop intuition | 3B1B Calc Ep 6–12 | Micrograd-style autodiff (Karpathy prep) |
| 6 | Probability distributions, Bayes | Khan Academy Stats Units 1–3 | Simulate distributions, plot PDFs/CDFs |
| 7 | Expected value, variance, CLT | Khan Academy Stats Units 4–6 | Monte Carlo estimation |
| 8 | Hypothesis testing, confidence intervals | Udacity Intro Stats Lessons 1–5 | A/B test simulation |
| 9 | **Consolidation + Python Integration** | Review all, Paul's Notes | Implement: linear regression from scratch |
| 10 | **Checkpoint + Portfolio** | Re-do key exercises from memory | GitHub: `math-foundations` with 5+ notebooks |

### Core Path at 8 Hours/Week (8 Weeks)

| Week | Focus | Resources | Python Practice |
|------|-------|-----------|-----------------|
| 1 | Linear Algebra (3B1B Ep 1–8 + Khan practice) | Vectors → matrix transformations | NumPy matrix ops |
| 2 | Linear Algebra (3B1B Ep 9–15 + Khan practice) | Determinants → eigenvectors | Eigendecomposition, SVD |
| 3 | Calculus (3B1B Ep 1–7 + Khan practice) | Derivatives → chain rule → optimization | Gradient descent implementation |
| 4 | Calculus (3B1B Ep 8–12 + Khan practice) | Integrals → backprop intuition | Autodiff micro-impl |
| 5 | Statistics (Khan + Udacity) | Distributions → Bayes → CLT | Distribution plotting, sampling |
| 6 | Statistics (Udacity + practice) | Hypothesis testing → regression | A/B test, linear regression |
| 7 | Consolidation | Mixed review, Paul's Notes | From-scratch implementations |
| 8 | Checkpoint + Portfolio | Timed exercises, GitHub push | `math-foundations` repo |

---

## Checkpoint Exercises (Must Pass Before Phase 2)

### Linear Algebra
1. **By hand:** Multiply 3×3 × 3×2 matrix; compute 2×2 determinant; find eigenvalues of 2×2
2. **NumPy:** Implement matrix multiplication using loops, then compare to `np.matmul` — explain speed difference
3. **Geometric:** Given transformation matrix, describe what it does to unit square (rotate, scale, shear)
4. **Eigen:** Explain in plain language what an eigenvector is and why it matters for PCA

### Calculus
1. **Derivative:** Compute derivative of `f(x) = 3x^4 - 2x^2 + 5` by hand; explain what it represents
2. **Chain rule:** Differentiate `f(x) = sin(x^2 + 1)` step by step
3. **Gradient descent:** Implement gradient descent for `f(x, y) = x^2 + y^2` from random start; plot trajectory
4. **Backprop intuition:** Explain how chain rule applies to a 2-layer neural network

### Statistics
1. **Distinguish:** When to use normal vs. binomial vs. Poisson — give real example each
2. **Bayes:** Disease test: 1% prevalence, 99% sensitivity, 95% specificity → P(disease | positive)?
3. **Simulation:** Write code to estimate π using Monte Carlo; explain law of large numbers
4. **Hypothesis test:** A/B test two website versions; compute p-value, interpret

---

## Python Integration (Required Throughout)

After each math topic, implement in Python:
```python
# Example: Week 2 - Matrix multiplication
import numpy as np

# Manual implementation
def matmul_manual(A, B):
    result = np.zeros((A.shape[0], B.shape[1]))
    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            for k in range(A.shape[1]):
                result[i, j] += A[i, k] * B[k, j]
    return result

# Compare
A = np.random.randn(100, 100)
B = np.random.randn(100, 100)
# Time both, discuss vectorization
```

**Portfolio:** Each week's implementation → Jupyter notebook → GitHub `math-foundations` repo.

---

## GitHub Portfolio Task

Repository: `math-foundations` with notebooks:
```
math-foundations/
├── 01-vectors-transformations.ipynb
├── 02-matrix-multiplication.ipynb
├── 03-eigenvalues-svd.ipynb
├── 04-gradient-descent.ipynb
├── 05-autodiff-micrograd.ipynb
├── 06-probability-distributions.ipynb
├── 07-bayes-monte-carlo.ipynb
├── 08-hypothesis-testing.ipynb
├── 09-linear-regression-scratch.ipynb
└── README.md
```

Each notebook: explanation, code, visualizations, "what I learned" section.

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Watching 3B1B without pausing | **Pause every 2 min** — predict next step, sketch on paper |
| Skipping Khan practice | **Do 10–15 problems per concept** — intuition ≠ fluency |
| Not coding the math | **Every concept → NumPy code** — dual coding cements learning |
| Memorizing formulas | **Derive from intuition** — if you can't derive, you don't understand |
| Rushing to Phase 2 | **Checkpoints are gates** — if you can't explain eigenvectors, stay here |

---

## Optional Deep-Dives (If Time Permits)

| Topic | Resource | Hours |
|-------|----------|-------|
| Multivariable calculus (gradients, Hessians) | Khan Academy Multivariable Calc | 20 |
| Information theory (entropy, KL divergence) | CMU 15-359 notes (free) | 10 |
| Optimization theory (convexity, Lagrange) | Boyd CVX101 (Stanford, free) | 30 |
| Numerical linear algebra (QR, SVD stability) | Trefethen & Bau (book, not free) | — |

---

## Next Phase Preview

**Phase 2: Classical ML** — Google ML Crash Course (15h) → fast.ai Practical Deep Learning Part 1 (40h). You'll apply linear algebra (matrix ops), calculus (gradient descent), and statistics (evaluation metrics) directly.

**Prepare:** Ensure NumPy, Pandas, Matplotlib, scikit-learn work in your environment (Kaggle/Colab recommended).