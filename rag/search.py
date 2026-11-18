"""Hybrid retrieval + reranking.

Pipeline per query:
  BM25 top-K  ┐
               ├─ union ──► rerank (feature-based linear scorer) ──► top-N
  char-ngram  ┘

**Fusion — why RRF:** lexical BM25 and dense cosine scores live on
incompatible scales, and BM25 has no fixed upper bound. Reciprocal Rank
Fusion (Cormack et al., 2009) fuses *ranks*, not scores, so it is
scale-free, has a single constant (k=60, damping rank dominance), and is
the standard robust choice for small candidate sets.

**Code-mix handling:** user queries are Latin-script Hinglish
("zyada jama karu", "byaj"). The corpus is English. A small hand-written
HINGLISH_MAP expands terms at *match* time: a query term counts as
covered if the term itself, or one of its mapped English equivalents,
appears in the chunk. Expansions are not added as separate query terms,
so coverage stays a faithful measure of the user's actual question.
Matching also canonicalises numbers ("8.50%" == "8.5%").

**Reranking — why a transparent linear scorer instead of a cross-encoder:**
the corpus is 10 documents; a cross-encoder would be overkill, slow to
bootstrap, and — worse — an unverifiable black box for a project that is
itself about grounding. The reranker is a weighted sum of six
interpretable features (see config.RERANK_WEIGHTS), each clamped to
[0, 1]. Coverage is IDF-weighted so that distinctive terms ("loan",
"PAN", "bitcoin") matter more than generic ones ("interest", "bank");
this is what keeps out-of-domain questions from scoring high on shared
generic vocabulary.

**Abstention:** a query is refused when the *evidence pool* (union of the
top-3 reranked candidates) covers too little of the query's IDF weight.
The threshold is tuned on eval/questions.jsonl (treated as a dev set);
per-question scores are in eval/results.md.
"""
from __future__ import annotations

import math
import re

from . import config
from .index import tokenize

WORD_RE = re.compile(r"[\w₹%.]+", re.UNICODE)
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+")
_ABBR = "p.a."
_ABBR_GUARD = "p⟨A⟩"


def split_sentences(text: str) -> list[str]:
    """Sentence split that does not break on abbreviations like 'p.a.'."""
    guarded = text.replace(_ABBR, _ABBR_GUARD)
    parts = [p.strip() for p in SENT_SPLIT.split(guarded) if p.strip()]
    return [p.replace(_ABBR_GUARD, _ABBR) for p in parts]

STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "in", "on", "for", "to", "and",
    "or", "my", "me", "i", "you", "your", "it", "this", "that", "what",
    "how", "do", "does", "hai", "hota", "hain", "ka", "ki", "ke", "ko",
    "se", "mein", "mera", "karu", "karo", "kare", "chahiye", "hoga",
    "kitna", "kitni", "kaise", "kab", "kahan", "kaun", "kya", "which",
    "ya", "ek", "than", "why", "who", "when", "where", "will", "can",
    "should", "would", "instead", "take", "get", "give", "need", "want",
    "also", "much", "many", "any", "some", "je", "te", "hana",
}

# Latin-script Hinglish -> English corpus equivalents. Consulted at match
# time (see term_covered). Small, hand-written, auditable — a lexical
# normaliser, not a translation model: deterministic and reproducible.
HINGLISH_MAP: dict[str, list[str]] = {
    "zyada": ["more", "higher"], "jyada": ["more", "higher"],
    "jama": ["deposit"], "zaroori": ["required", "mandatory"],
    "paisa": ["money"], "paise": ["money"],
    "kamai": ["earnings", "income"],
    "beema": ["insurance"], "bima": ["insurance"],
    "bachat": ["savings"], "bachao": ["save"],
    "todna": ["break", "withdraw"], "toda": ["break"],
    "nivesh": ["invest"], "lagana": ["invest"],
    "matlab": ["means", "meaning"], "arth": ["meaning"],
    "milta": ["get"], "milti": ["get"], "milna": ["get"],
    "faayda": ["benefit"], "fayda": ["benefit"],
    "nuksan": ["loss"], "kam": ["less", "lower"],
    "upar": ["above"], "niche": ["below"],
    "surakshit": ["safe", "protected"], "suraksha": ["protection", "safety"],
    "saath": ["with", "together"],
    "byaj": ["interest"], "byaaj": ["interest"], "sood": ["interest"],
    "daar": ["rate"], "salana": ["annual", "yearly"],
    "saal": ["year"], "varsh": ["year"], "mahina": ["month"],
    "mahine": ["month"], "rakam": ["amount"], "rashi": ["amount"],
    "poora": ["full", "total"], "purna": ["full", "total"],
    "wapas": ["back", "return"], "vaapsi": ["payout", "return"],
    "samay": ["time", "period"], "sabse": ["most"],
    "farak": ["difference", "distinct"],
}


def canon_nums(text: str) -> str:
    """Canonicalise numbers in text: 8.50% -> 8.5%, 1,00,000 -> 100000.
    Spaces between words are preserved (word-boundary matching relies on them)."""
    def fix(m: re.Match) -> str:
        s = m.group(0).replace(",", "")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    return NUM_RE.sub(fix, text)


def query_terms(query: str) -> list[str]:
    """Stopword-filtered query terms, as the user wrote them."""
    out: list[str] = []
    for raw in WORD_RE.findall(query):
        t = raw.lower()
        if t in STOPWORDS or len(t) <= 1:
            continue
        if t not in out:
            out.append(t)
    return out


def _term_pattern(term: str):
    """Word-boundary pattern so 'invest' does not match 'reinvest'."""
    return re.compile(r"(?<![\w₹])" + re.escape(canon_nums(term)) + r"(?![\w₹%])")


def term_covered(term: str, lowered_text: str) -> bool:
    """A term is covered if it (canonically) or a mapped expansion appears."""
    if _term_pattern(term).search(lowered_text):
        return True
    for expansion in HINGLISH_MAP.get(term, []):
        if _term_pattern(expansion).search(lowered_text):
            return True
    return False


def query_numbers(query: str) -> list[str]:
    nums = []
    for m in re.finditer(r"₹?\s?\d[\d,.]*", query):
        token = re.sub(r"[\s,]", "", m.group(0))
        if token and token != "₹":
            nums.append(re.sub(r"[\s,]", "", m.group(0)).lower())
    return nums


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def corpus_df(chunks: list[dict]) -> tuple[dict[str, int], int]:
    """Document frequency of terms across the chunk corpus (for IDF weighting)."""
    df: dict[str, int] = {}
    for c in chunks:
        for t in set(tokenize(c["content"])):
            df[t] = df.get(t, 0) + 1
    return df, len(chunks)


def idf(term: str, df: dict[str, int], n_docs: int) -> float:
    """Smoothed IDF; unseen terms get the maximum weight."""
    return math.log(1 + n_docs / (1 + df.get(term, 0)))


def rerank_score(query: str, chunk_text: str, heading: str,
                 publisher: str, df: dict[str, int] | None = None,
                 n_docs: int = 1) -> tuple[float, dict]:
    """Return (weighted_score, feature_breakdown) — transparent by design."""
    terms = query_terms(query)
    bigrams = query_bigrams(terms)
    lowered = canon_nums(chunk_text.lower())
    heading_l = canon_nums(heading.lower())

    # IDF-weighted coverage: rare, distinctive query terms ("loan", "PAN",
    # "bitcoin", "8.5%") weigh far more than generic ones ("interest",
    # "bank", "rate"). Without this, out-of-domain questions that share
    # only generic vocabulary score high and slip past the abstention gate.
    if df is None:
        weights = {t: 1.0 for t in terms}
    else:
        weights = {t: idf(t, df, n_docs) for t in terms}
    wsum = sum(weights.values())
    term_coverage = _clamp(
        sum(weights[t] for t in terms if term_covered(t, lowered))
        / wsum) if wsum else 0.0
    bigram_overlap = _clamp(
        sum(1 for b in bigrams if canon_nums(b) in lowered)
        / max(len(bigrams), 1))
    # Full normalised phrase match.
    norm_query = " ".join(terms)
    exact_phrase = _clamp(1.0 if norm_query and _term_pattern(norm_query).search(lowered) else 0.0)

    nums = query_numbers(query)
    numeric_match = _clamp(
        sum(1 for n in nums if _term_pattern(n).search(lowered))
        / max(len(nums), 1)) if nums else 0.0

    heading_match = _clamp(
        sum(weights[t] for t in terms if term_covered(t, heading_l))
        / wsum) if wsum else 0.0

    authority_domains = ("dicgc", "rbi", "incometax")
    source_authority = 1.0 if any(d in publisher.lower() for d in authority_domains) else 0.0

    features = {
        "term_coverage": term_coverage,
        "bigram_overlap": bigram_overlap,
        "exact_phrase": exact_phrase,
        "numeric_match": numeric_match,
        "heading_match": heading_match,
        "source_authority": source_authority,
    }
    score = sum(config.RERANK_WEIGHTS[k] * v for k, v in features.items())
    return score, features


def query_bigrams(terms: list[str]) -> list[str]:
    return [f"{a} {b}" for a, b in zip(terms, terms[1:])]


def hybrid_search(index, query: str, candidate_pool: int | None = None):
    """RRF-fused candidates, reranked. Returns list of result dicts."""
    pool = candidate_pool or config.CANDIDATE_POOL
    lex = index.search_lexical(query, config.BM25_TOP_K)
    dens = index.search_dense(query, config.DENSE_TOP_K)

    df, n_docs = corpus_df(index.chunks)

    rrf: dict[int, float] = {}
    for _, hits in (("bm25", lex), ("dense", dens)):
        for rank, (i, _score) in enumerate(hits):
            rrf[i] = rrf.get(i, 0.0) + 1.0 / (config.RRF_K + rank + 1)

    candidates = sorted(rrf, key=rrf.get, reverse=True)[:pool]

    results = []
    for i in candidates:
        c = index.chunks[i]
        score, features = rerank_score(query, c["text"], c["heading_path"],
                                       c["publisher"], df, n_docs)
        results.append({
            "chunk_index": i,
            "chunk_id": c["chunk_id"],
            "doc_id": c["doc_id"],
            "heading": c["heading_path"],
            "text": c["text"],
            "source_url": c["source_url"],
            "publisher": c["publisher"],
            "rrf": rrf[i],
            "score": score,
            "features": features,
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def evidence_adequacy(query: str, hits: list[dict], df: dict[str, int],
                      n_docs: int, anchor_k: int = 5) -> float:
    """Abstention signal: best single-sentence coverage of the anchor terms.

    Anchors are the top-`anchor_k` highest-IDF query terms — the words that
    make this question distinctive ("cashback", "loan", "bitcoin", or for a
    good query "PAN", "premature"). Two checks are combined:
    * anchors, not all terms — so an out-of-domain question cannot pass on
      generic vocabulary ("interest", "bank", "rate") alone;
    * per-sentence maximum — so incidental matches ("PAN **card**" for a
      "credit card" question) scattered across different sentences do not
      add up into fake evidence. Real evidence for one question is
      concentrated in one place; scattered single-word hits are noise.
    """
    terms = query_terms(query)
    if not terms:
        return 0.0
    weighted = sorted(terms, key=lambda t: -idf(t, df, n_docs))
    anchors = weighted[:anchor_k]
    aw = {t: idf(t, df, n_docs) for t in anchors}
    wsum = sum(aw.values())
    if not wsum:
        return 0.0
    pool = canon_nums(" ".join(h["text"].lower()
                               for h in hits[:config.MAX_ANSWER_CHUNKS]))
    best = 0.0
    for sentence in split_sentences(pool):
        sentence = sentence.strip()
        if not sentence:
            continue
        covered = sum(aw[t] for t in anchors if term_covered(t, sentence))
        best = max(best, covered / wsum)
    return _clamp(best)


def evidence_coverage(query: str, hits: list[dict], df: dict[str, int],
                      n_docs: int) -> float:
    """Diagnostic: IDF-weighted query coverage over the whole evidence pool."""
    terms = query_terms(query)
    if not terms:
        return 0.0
    pool = canon_nums(" ".join(h["text"].lower() for h in hits[:config.MAX_ANSWER_CHUNKS]))
    wsum = sum(idf(t, df, n_docs) for t in terms)
    covered = sum(idf(t, df, n_docs) for t in terms if term_covered(t, pool))
    return _clamp(covered / wsum) if wsum else 0.0


def search_top(index, query: str, top_n: int = 5):
    """Full search path: fusion -> rerank -> abstention decision."""
    results = hybrid_search(index, query)
    df, n_docs = corpus_df(index.chunks)
    top = results[:top_n]
    adequacy = evidence_adequacy(query, results, df, n_docs,
                                 anchor_k=config.ANCHOR_K)
    coverage = evidence_coverage(query, results, df, n_docs)
    abstain = adequacy < config.ABSTAIN_THRESHOLD
    return {
        "query": query,
        "abstain": abstain,
        "adequacy": round(adequacy, 4),
        "coverage": round(coverage, 4),
        "best_score": round(top[0]["score"], 4) if top else 0.0,
        "results": top,
    }
