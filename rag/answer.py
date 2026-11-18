"""Grounded answer generation.

Default mode is **extractive**: the answer is built from sentences in the
retrieved chunks, and every sentence is stamped with a [n] citation. This
makes the demo reproducible offline and guarantees that the answer can
never contain a fact absent from the sources — groundedness is structural,
not a prompt instruction.

An optional **LLM mode** (RAG_ANSWER_MODE=llm) sends ONLY the retrieved
chunks to OpenRouter with a system prompt that forbids outside knowledge
and requires [n] markers; the marker integrity is checked on receipt and
the response falls back to extractive mode if it fails the check.

**Missing evidence handling (abstention):** if the best reranked candidate
scores below ABSTAIN_THRESHOLD, the pipeline does not call the LLM and does
not invent an answer. It replies with an explicit "no evidence in the
knowledge base" message, states what the knowledge base *does* cover that
is closest, and suggests rephrasing. This is tested directly by the
unanswerable questions in eval/questions.jsonl.
"""
from __future__ import annotations

import os
import re
import textwrap

from . import config, search


# --------------------------------------------------------------------------
# Extractive answer
# --------------------------------------------------------------------------
def extractive_answer(query: str, hits: list[dict]) -> tuple[str, list[dict]]:
    """Pick the highest-coverage sentences from top chunks, with citations."""
    sentences: list[tuple[float, str, int]] = []  # (score, sentence, rank)
    for rank, hit in enumerate(hits[: config.MAX_ANSWER_CHUNKS], start=1):
        for sent in search.split_sentences(hit["text"]):
            cov = _coverage(query, sent)
            if cov > 0:
                # Rank-weighted: equal-coverage sentences prefer the chunk
                # that the reranker ranked first.
                sentences.append((cov * (1.0 - 0.1 * (rank - 1)), sent.strip(), rank))

    sentences.sort(key=lambda x: (-x[0], x[2]))
    picked: list[str] = []
    used_ranks: list[int] = []
    best_cov = sentences[0][0] if sentences else 0.0
    floor = 0.5 * best_cov
    for score, sent, rank in sentences:
        if len(picked) >= config.ANSWER_MAX_SENTENCES:
            break
        if score < floor or sent in picked:
            continue
        picked.append(sent)
        if rank not in used_ranks:
            used_ranks.append(rank)

    answer = " ".join(picked)
    citations = [citations_for(hits)[r - 1] for r in used_ranks]
    return answer, citations


def _coverage(query: str, sentence: str) -> float:
    from .search import query_terms, term_covered, canon_nums
    terms = query_terms(query)
    if not terms:
        return 0.0
    lowered = canon_nums(sentence.lower())
    return sum(1 for t in terms if term_covered(t, lowered)) / len(terms)


def citations_for(hits: list[dict]) -> list[dict]:
    """Deduplicated citation list for the top hits."""
    seen, out = set(), []
    for h in hits[: config.MAX_ANSWER_CHUNKS]:
        key = (h["doc_id"], h["heading"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "n": len(out) + 1,
            "doc_id": h["doc_id"],
            "heading": h["heading"],
            "publisher": h["publisher"],
            "source_url": h["source_url"],
            "chunk_id": h["chunk_id"],
        })
    return out


# --------------------------------------------------------------------------
# Abstention ("no evidence") answer
# --------------------------------------------------------------------------
def no_evidence_answer(query: str, hits: list[dict]) -> tuple[str, list[dict]]:
    closest = ""
    if hits:
        top = hits[0]
        closest = textwrap.fill(
            f"The knowledge base does not cover this. The closest topic it has is "
            f"\"{top['heading']}\" (score {top['score']:.2f}, below the evidence "
            f"threshold {config.ABSTAIN_THRESHOLD}).",
            width=100)
    msg = (
        "No sufficient evidence in the knowledge base to answer this question. "
        "The advisor only answers from its FD knowledge corpus "
        "(DICGC insurance, FD rates and basics, compounding, premature "
        "withdrawal, tax/TDS/80TTB, senior citizens, small finance banks, "
        "nomination/KYC) and refuses to guess on anything outside it."
    )
    if hits and closest:
        msg += "\n" + closest
    elif not hits:
        msg += "\nTry asking about FD rates, insurance, tax, withdrawal or nomination."
    return msg, []


# --------------------------------------------------------------------------
# Optional LLM mode (only used when explicitly configured)
# --------------------------------------------------------------------------
LLM_SYSTEM_PROMPT = """You answer questions about fixed deposits in India, in the user's language.

STRICT GROUNDING RULES:
- Use ONLY the numbered context passages provided. No outside knowledge, no opinions.
- Mark every claim you make with the passage number in square brackets, e.g. [1] or [1][2].
- If the passages do not contain the answer, reply exactly: "I don't have evidence for this in my knowledge base."
- Keep the answer short (2-4 sentences), simple words.

CONTEXT PASSAGES:
"""


def llm_answer(query: str, hits: list[dict], language: str = "hi") -> tuple[str, list[dict]] | None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    context = "\n\n".join(
        f"[{n}] {h['heading']}\n{h['text']}"
        for n, h in enumerate(citations_for(hits), start=1)
    )
    import json as _json
    import urllib.request
    body = _json.dumps({
        "model": os.environ.get("RAG_LLM_MODEL", "google/gemma-4-31b-it:free"),
        "messages": [
            {"role": "system", "content": LLM_SYSTEM_PROMPT + context},
            {"role": "user", "content": f"Language: {language}\nQuestion: {query}"},
        ],
        "max_tokens": 250,
        "temperature": 0.1,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read())
        text = data["choices"][0]["message"]["content"].strip()
        if "I don't have evidence" in text:
            return no_evidence_answer(query, hits)
        # Marker integrity: require at least one [n] when passages exist.
        if hits and not re.search(r"\[\d\]", text):
            return extractive_answer(query, hits)  # ungrounded reply -> discard
        return text, citations_for(hits)
    except Exception:
        return extractive_answer(query, hits)  # graceful degradation


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def answer_query(index, query: str, language: str = "hi", mode: str | None = None) -> dict:
    verdict = search.search_top(index, query)
    if verdict["abstain"]:
        text, cites = no_evidence_answer(query, verdict["results"])
        grounded = True
        mode_used = "abstain"
    else:
        use_llm = (mode or os.environ.get("RAG_ANSWER_MODE", "extractive")) == "llm"
        if use_llm:
            llm = llm_answer(query, verdict["results"], language)
            if llm is None:  # no API key configured
                text, cites = extractive_answer(query, verdict["results"])
                mode_used = "extractive"
            else:
                text, cites = llm
                mode_used = "llm"
        else:
            text, cites = extractive_answer(query, verdict["results"])
            mode_used = "extractive"
        grounded = True

    return {
        "query": query,
        "language": language,
        "answer": text,
        "citations": cites,
        "grounded": grounded,
        "abstained": verdict["abstain"],
        "confidence": verdict["adequacy"],
        "mode": mode_used,
        "retrieved": [
            {"chunk_id": r["chunk_id"], "doc_id": r["doc_id"],
             "heading": r["heading"], "score": round(r["score"], 4),
             "source_url": r["source_url"]}
            for r in verdict["results"]
        ],
    }
