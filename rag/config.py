"""Central configuration for the FD-advisor RAG pipeline."""
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parent

# --- Paths ---------------------------------------------------------------
CORPUS_DIR = RAG_ROOT / "corpus"
DATA_DIR = RAG_ROOT / "data"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
INDEX_PATH = DATA_DIR / "index.pkl"
EVAL_DIR = RAG_ROOT / "eval"

# --- Chunking ------------------------------------------------------------
# Target chunk size in characters (~60-180 words). Tuned so that one chunk
# holds exactly one answerable fact: recall of atomic facts beats recall of
# whole documents in retrieval metrics, and keeps prompts small.
CHUNK_TARGET_CHARS = 900
# Hard maximum. Chunks above this are split further; chunks below stay intact
# (we never pad short sections — a complete rule is a complete answer unit).
CHUNK_MAX_CHARS = 1400
# Overlap between consecutive windows of the same section, in characters.
# ~15% of target: enough that a fact split across a boundary appears whole
# in at least one chunk, without doubling the index.
CHUNK_OVERLAP_CHARS = 140
# Heading path (e.g. "DICGC insurance > What is not covered") is prepended
# to every chunk so each chunk is self-contained for lexical search.
PREPEND_HEADING_PATH = True

# --- Hybrid retrieval ----------------------------------------------------
# Reciprocal Rank Fusion constant (standard value from the RRF paper).
RRF_K = 60
BM25_TOP_K = 25       # candidates pulled by lexical search
DENSE_TOP_K = 25      # candidates pulled by character-ngram vectors
CANDIDATE_POOL = 30   # union size fed to the reranker

# --- Reranker weights ----------------------------------------------------
# Linear, hand-tuned, fully explainable. Each feature in [0, 1].
RERANK_WEIGHTS = {
    "term_coverage": 0.40,   # fraction of query terms present in chunk
    "bigram_overlap": 0.15,  # consecutive query-word pairs found (phrase-ness)
    "exact_phrase": 0.15,    # the full query (normalised) appears verbatim
    "numeric_match": 0.15,   # query numbers (₹5 lakh, 8.5%) appear in chunk
    "heading_match": 0.10,   # query terms hit the chunk's heading path
    "source_authority": 0.05,# prior for regulator sources (RBI/DICGC/ITD)
}

# --- Grounded answering --------------------------------------------------
MAX_ANSWER_CHUNKS = 3      # citations shown per answer
ANSWER_MAX_SENTENCES = 4   # sentences extracted into the answer

# --- Missing evidence / abstention ---------------------------------------
# The abstention gate is evidence adequacy: best single-sentence coverage
# of the query's top ANCHOR_K highest-IDF terms, over the evidence pool.
# 0.25 was chosen on eval/questions.jsonl (dev set): every answerable
# question scores >= 0.30 and every unanswerable question <= 0.25, so the
# threshold sits mid-gap (see eval/results.md for per-question scores).
ABSTAIN_THRESHOLD = 0.25
ANCHOR_K = 8

# --- Service -------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 8100
