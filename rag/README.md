# RAG Pipeline — grounded FD answers with citations

Retrieval-augmented generation over a curated Fixed-Deposit knowledge
corpus. Answers are built **only** from retrieved passages, every sentence
carries a source citation, and questions outside the corpus are **refused**
instead of hallucinated. Fully offline and reproducible (no API key
needed); optional LLM mode available.

```
question ──► ingest/chunk ──► hybrid search ──► rerank ──► grounded answer
                              (BM25 + n-gram   (explainable      with [n]
                               vectors, RRF)    features)        citations
                                                    │
                                            adequacy < threshold?
                                                    │ yes
                                              "no evidence" refusal
```

## Quickstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r rag/requirements.txt
.venv/bin/python -m rag.build          # ingest + chunk + index
.venv/bin/python -m rag.eval.run_eval  # reproduce eval results (≈2 s)
.venv/bin/python -m pytest rag/tests   # 22 end-to-end tests
.venv/bin/python -m rag.server         # serve on :8100 (used by Backend)
```

CLI answer (no server needed):

```bash
.venv/bin/python -c "from rag import index, answer; \
  idx,_ = index.load(); \
  print(answer.answer_query(idx, 'How much deposit is insured by DICGC?')['answer'])"
```

## 1. Dataset (shareable)

`rag/corpus/*.md` — 10 documents on Indian fixed deposits (DICGC insurance,
rates, compounding, premature withdrawal, TDS/194A, Section 80TTB, senior
citizens, Small Finance Banks, nomination/KYC, payout vs cumulative),
each with front-matter carrying `source`, `publisher`, `retrieved` — every
fact traces back to a public regulator source (RBI, DICGC, Income Tax Dept).

`rag/data/chunks.jsonl` — the generated chunk dataset (46 chunks) is
**committed to the repo** so it can be inspected, reused, or diffed without
rebuilding. Schema: `chunk_id, doc_id, doc_title, heading_path, section,
text, source_url, publisher, retrieved, chars`.

## 2. Chunking choices

1. **Heading-aware first.** Documents are authored so each `##` section is
   one self-contained rule. Splitting at headings keeps rules intact — a
   chunk never mixes "what is covered" with "when you get paid".
2. **~900-char windows with 140-char overlap** inside long sections,
   always at sentence boundaries, so a fact near a boundary appears whole
   in at least one chunk. Measured result: 46 chunks, median ≈ 500 chars.
3. **Heading path prepended** (`Doc > Section`) to every chunk: lexical
   search can match short questions against section titles, and citations
   can point at a precise section instead of a whole page.
4. **No padding of short sections.** A complete rule is a complete answer
   unit; merging neighbours dilutes precision.
5. **Characters, not tokens**, because the corpus is multilingual
   (English + Devanagari) and tokenizer-dependent sizes would make the
   dataset non-reproducible.

## 3. Retrieval & ranking choices

Two complementary retrievers, fused, then reranked:

| Stage | What | Why |
|---|---|---|
| Lexical | BM25Okapi over Unicode word tokens | exact match on product/legal terms: bank names, "194A", "₹5 lakh", "80TTB" |
| Vector | char_wb 3–5-gram TF-IDF, sublinear TF, L2-normalised, cosine | robust to morphology, typos and code-mixing ("beema"/"बीमा"); fully offline & reproducible — no embedding API, no nondeterministic model updates. Exposes a FAISS-like `.search()` API, so a faiss/SBERT backend drops in without touching callers |
| Fusion | Reciprocal Rank Fusion (k=60) | BM25 has no fixed score scale; RRF fuses ranks, not scores, so it is scale-free and stable (weighted-score fusion was visibly more fragile during tuning) |
| Rerank | linear weighted sum of 6 interpretable features | a cross-encoder is overkill for 10 docs and an unverifiable black box for a project *about* grounding. Features: IDF-weighted term coverage (0.40), bigram overlap (0.15), exact phrase (0.15), numeric match (0.15), heading match (0.10), source authority (0.05) |

**Code-mix handling** (`rag/search.py:HINGLISH_MAP`): users ask in
Latin-script Hinglish ("₹5 lakh se zyada jama karu to kitna safe hai").
A small hand-written normaliser maps such words to corpus equivalents at
*match* time (with word-boundary matching so "invest" never matches
"reinvest"), and numbers are canonicalised (`8.50%` ≡ `8.5%`,
`1,00,000` ≡ `100000`). This was not optional polish: without it, real
Hinglish queries were systematically refused.

## 4. Missing evidence (abstention)

The single most important behaviour for a financial assistant: **if the
evidence isn't there, say so**.

* Signal — *evidence adequacy*: the best **single-sentence** coverage of
  the query's top-8 IDF-weighted **anchor** terms, over the evidence pool
  (top-3 reranked chunks).
  * *anchors* (distinctive words) rather than all words — so "Which credit
    card gives the best cashback?" cannot pass on generic "credit/gives";
  * *single sentence* rather than the whole pool — so "PAN **card**" and
    "rate **cards**" scattered across sentences don't add up into fake
    evidence for a "credit card" question.
* Decision — refuse when adequacy < **0.25**, tuned on the eval dev set:
  every answerable question scores ≥ 0.30, every unanswerable ≤ 0.25, so
  the threshold sits mid-gap with margin on both sides.
* The refusal message states the corpus scope, names the closest topic it
  *does* have, and never guesses. The same gate runs **before** any LLM
  call in `llm` mode, so out-of-domain questions never reach the model.

Honest limitation: adequacy is a calibrated lexical gate, not a semantic
one. Paraphrase gaps ("bank fails" vs "moratorium") and unseen Hinglish
words can push borderline questions below the threshold. Swapping the
anchor coverage for a sentence-embedding similarity (same call site,
`rag/search.py:evidence_adequacy`) is the planned upgrade; the eval
question set already covers this failure mode.

## 5. Answer generation

* **Extractive (default)** — the answer is assembled from the
  highest-coverage sentences of the top chunks, every sentence stamped
  with `[n]` citations resolved to publisher + source URL. Groundedness is
  structural (the answer literally cannot contain an unsourced fact), the
  demo needs no API key, and results are reproducible.
* **LLM mode** (`OPENROUTER_API_KEY` set → `/api/rag/chat` uses it) — the
  LLM sees *only* the numbered retrieved passages, is instructed to mark
  every claim `[n]` and to reply "I don't have evidence" otherwise.
  Responses without citation markers are **discarded** and replaced with
  the extractive answer; LLM failure degrades to extractive, never to
  ungrounded.

## 6. Evaluation

`rag/eval/questions.jsonl` — 28 questions: 22 answerable (English +
Hinglish, each with gold document and key terms) and 6 deliberately
out-of-domain (mutual funds, stocks, crypto, loans, credit cards, weather)
that the pipeline must refuse. Run `python -m rag.eval.run_eval`;
full results in `eval/results.md` / `results.json` (committed).

| Metric | Score |
|---|---|
| Recall@2 / Recall@5 (gold source retrieved) | 100% / 100% |
| MRR@5 | 0.909 |
| nDCG@5 | 0.517 |
| Abstention accuracy (6/6 refusals, 0 false refusals) | 100% |
| Groundedness (every sentence traceable to a cited chunk) | 100% |
| Correct source cited | 100% |
| Latency | ≈ 25 ms/query (single core, no GPU) |

## 7. Wiring into the app

```
Frontend (React) ──► Backend (Node /api/rag/chat) ──► rag.server (FastAPI :8100)
                                                          │
                                              hybrid search + rerank + gates
                                                          │
                                     extractive answer + citations  (no key)
                                     LLM answer over passages       (optional)
```

The frontend chat shows citation chips under grounded answers and silently
falls back to the plain advisor if the RAG service is down.

## Layout

```
rag/
├── corpus/            10 source documents (markdown + source metadata)
├── data/chunks.jsonl  generated chunk dataset (committed)
├── data/index.pkl     hybrid index (committed, rebuilt by rag.build)
├── ingest.py          ingestion + chunking
├── index.py           BM25 + char-ngram vector index
├── search.py          RRF fusion, reranker, adequacy/abstention
├── answer.py          extractive / LLM answers with citations
├── server.py          FastAPI service
├── build.py           one-shot build
├── eval/              questions.jsonl, run_eval.py, results.md/json
├── tests/             22 pytest end-to-end tests
└── config.py          all tunables in one place
```
