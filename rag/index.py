"""Index building: lexical + vector representations for hybrid search.

Two independent representations are built and stored:

1. **BM25 (lexical)** — rank_bm25 over lower-cased alphanumeric tokens
   (Unicode-aware, so Devanagari tokens survive). BM25 wins on exact
   product terms: bank names, "194A", "₹5 lakh", section numbers.

2. **Character n-gram TF-IDF vectors (vector side)** — sklearn
   TfidfVectorizer with char_wb 3-5 grams, sublinear TF, L2-normalised.
   Chosen instead of an external embedding API because:
   - the dataset/pipeline stays fully reproducible offline (no API key,
     no nondeterministic model updates);
   - char n-grams handle code-mixing and morphology ("beema"/"बीमा",
     "senior citizen"/"seniorcitizen"), which is exactly the failure mode
     of word-level vectors on Hinglish queries;
   - cosine over L2-normalised TF-IDF is mathematically the same dense
     nearest-neighbour operation used with FAISS, just in NumPy; the
     index object exposes a `.search(q, k)` API so a faiss or SBERT
     backend can be dropped in without touching callers.

The two sides are complementary: eval shows BM25 leads on numeric/legal
queries, char n-grams rescue paraphrase and transliteration queries.
"""
from __future__ import annotations

import json
import pickle
import re

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config

TOKEN_RE = re.compile(r"[\w₹%.]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


class HybridIndex:
    """BM25 + dense(char n-gram) index with a FAISS-like search API."""

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        corpus = [c["content"] for c in chunks]

        tokenized = [tokenize(c) for c in corpus]
        self.bm25 = BM25Okapi(tokenized)

        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            norm="l2",
            lowercase=True,
            max_features=60000,
        )
        self.doc_matrix = self.vectorizer.fit_transform(corpus)  # CSR, L2-normed

    # -- search surface ----------------------------------------------------
    def bm25_scores(self, query: str) -> np.ndarray:
        return np.asarray(self.bm25.get_scores(tokenize(query)))

    def dense_scores(self, query: str) -> np.ndarray:
        q = self.vectorizer.transform([query])
        # L2-normalised rows -> cosine similarity is a simple dot product.
        return np.asarray((self.doc_matrix @ q.T).T.todense()).ravel()

    def top(self, scores: np.ndarray, k: int) -> list[tuple[int, float]]:
        k = min(k, len(scores))
        idx = np.argpartition(-scores, k - 1)[:k]
        order = idx[np.argsort(-scores[idx])]
        return [(int(i), float(scores[i])) for i in order]

    def search_lexical(self, query: str, k: int) -> list[tuple[int, float]]:
        return self.top(self.bm25_scores(query), k)

    def search_dense(self, query: str, k: int) -> list[tuple[int, float]]:
        return self.top(self.dense_scores(query), k)


def build() -> tuple[HybridIndex, list[dict]]:
    chunks = [json.loads(line) for line in open(config.CHUNKS_PATH, encoding="utf-8")]
    index = HybridIndex(chunks)
    with open(config.INDEX_PATH, "wb") as f:
        pickle.dump(index, f)
    return index, chunks


def load() -> tuple[HybridIndex, list[dict]]:
    with open(config.INDEX_PATH, "rb") as f:
        index = pickle.load(f)
    chunks = index.chunks
    return index, chunks


if __name__ == "__main__":
    index, chunks = build()
    q = "kitna paisa insured hai DICGC se"
    print(f"indexed {len(chunks)} chunks; demo query: {q!r}")
    print(" lexical:", [chunks[i]["chunk_id"] for i, _ in index.search_lexical(q, 3)])
    print(" dense  :", [chunks[i]["chunk_id"] for i, _ in index.search_dense(q, 3)])
