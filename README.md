# FD सलाहकार — Vernacular FD Advisor

> **Hackathon Project** | Making Fixed Deposits simple for first-time users through vernacular AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge\&logo=vercel)](https://vernacular-fd-advisor-seven.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Render-purple?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## Retrieval-Augmented Generation (RAG) — grounded answers with citations

The chat is powered by a full **RAG pipeline** (`rag/` — see
[rag/README.md](./rag/README.md) for the deep dive): it retrieves evidence
from a curated FD knowledge corpus, reranks it with an explainable scorer,
answers **only** from retrieved passages, stamps every claim with a source
citation, and **refuses to answer** when the evidence isn't there instead
of hallucinating.

**Measured results** (28 test questions — 22 answerable in English/Hinglish,
6 out-of-domain — reproducible with `python -m rag.eval.run_eval`):

| Metric | Score |
|---|---|
| Recall@2 / Recall@5 — right source retrieved | **100% / 100%** |
| MRR@5 | **0.909** |
| Abstention accuracy — out-of-domain questions refused | **100% (6/6, 0 false refusals)** |
| Groundedness — every answer sentence traceable to a cited chunk | **100%** |
| Correct source cited | **100%** |

What the repo demonstrates:

* **Ingestion + chunking** — heading-aware chunking with justified
  sizes/overlap; the generated dataset (`rag/data/chunks.jsonl`, 10 docs /
  46 chunks with source URLs) is committed and shareable.
* **Hybrid search** — BM25 (lexical) + character n-gram vectors (dense),
  fused with Reciprocal Rank Fusion; handles code-mixed Hinglish queries
  via an auditable query normaliser.
* **Ranking** — transparent, feature-based reranker (coverage, phrase,
  numeric, heading, source authority) instead of a black-box cross-encoder.
* **Missing evidence** — calibrated abstention gate (single-sentence anchor
  coverage) tested directly by the 6 unanswerable eval questions.
* **Evaluation** — test questions + retrieval/answer metrics, per-question
  results committed in `rag/eval/`.

```bash
# reproduce everything (no API key needed):
python3 -m venv .venv && .venv/bin/pip install -r rag/requirements.txt
.venv/bin/python -m rag.build && .venv/bin/python -m rag.eval.run_eval
.venv/bin/python -m pytest rag/tests   # 22 end-to-end tests
```

---

## Problem

A user in Gorakhpur sees:

> **“Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor”**

…but doesn’t understand:

* What **p.a.** means
* Whether the bank is **safe**
* How much money they will **actually get**

---

## Solution

**FD सलाहकार** explains everything in **simple Hindi, Tamil, Telugu** — like a trusted friend:

* Explains jargon (p.a., tenure, DICGC)
* Hows exact maturity amount
* Compares banks clearly
* Guides step-by-step FD booking

---

## Features

* **AI Chat (Vernacular)** — Hindi / Tamil / Telugu
* **FD Comparison** — filter, sort, safety tags
* **FD Calculator** — sliders + visual returns
* **Booking Flow** — step-by-step guided form
* **Multilingual UI** — instant language switch

---

## Demo Video

[![Watch Demo](https://img.youtube.com/vi/YOUR_ID/0.jpg)](https://youtu.be/5MkT9rSK2ds)
---

## Screenshots (Flow)

### Compare & Select

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-20-57.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-24-52.png" width="250"/>
</p>

### Booking Flow

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-25-12.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-25-59.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-26-28.png" width="250"/>
</p>

### Confirmation

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-28-40.png" width="250"/>
</p>

### Calculator

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-29-02.png" width="250"/>
</p>

### AI Chat

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-29-27.png" width="250"/>
</p>

---

## Architecture

```
Frontend (React + Vite)
   ↓
Backend (Node + Express)  ──►  RAG service (Python FastAPI, rag/)
   │                              │
   │                     hybrid search (BM25 + n-gram vectors, RRF)
   │                     rerank → evidence gate → grounded answer
   ↓                              │
OpenRouter API (optional LLM mode) │  ← LLM only ever sees retrieved passages
───────────────────────────────────┘
answers carry [n] citations to RBI / DICGC / Income-Tax sources
```

---

## Local Setup (Step-by-Step)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/Vernacular-FD-Advisor.git
cd Vernacular-FD-Advisor
```

---

## Backend Setup

```bash
cd Backend
npm install
```

### Create `.env` inside Backend

```env
OPENROUTER_API_KEY=your_secret_key_here
PORT=3001
```

> Never push `.env` to GitHub

---

### Run Backend

```bash
npm start
```

Runs on:

```
http://localhost:3001
```

---

## RAG Service (grounded answers)

In a third terminal, from the repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r rag/requirements.txt
.venv/bin/python -m rag.build     # build index (once)
.venv/bin/python -m rag.server    # serves grounded answers on :8100
```

The backend proxies chat to this service (`POST /api/rag/chat`), which
returns answers **with citations**; without the RAG service the chat
falls back to the plain LLM advisor.

---

## Frontend Setup

Open new terminal:

```bash
cd Frontend
npm install
```

### Create `.env` inside Frontend

```env
VITE_API_URL=http://localhost:3001
```

---

### Run Frontend

```bash
npm run dev
```

Runs on:

```
http://localhost:5173
```
---

## Test

Open browser:

http://localhost:5173

Try:

* "Safe hai kya?" — grounded answer with a citation chip to DICGC/RBI
* "8.5% ka matlab kya hai?"
* "Bitcoin mein paisa lagana chahiye?" — the advisor **refuses** (no evidence in corpus)

---
## Final Output

```
User → Frontend → Backend → AI → Response
```

---
