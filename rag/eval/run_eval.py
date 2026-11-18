"""Evaluation of retrieval and answering quality.

Run:  python -m rag.eval.run_eval

Question set (eval/questions.jsonl):
- 22 answerable questions, each with a gold document and key terms that a
  correct answer must contain (mix of English and Hinglish, mirroring real
  user queries);
- 6 unanswerable questions from outside the corpus domain (mutual funds,
  stocks, crypto, loans, credit cards, weather) that the pipeline must
  REFUSE to answer — this measures the missing-evidence behaviour directly.

Metrics:
- Recall@2 / Recall@5: gold document retrieved in top-k *documents*
  (chunks grouped by doc). Primary retrieval metric: did we find the
  right source at all?
- MRR@5: 1/rank of the first gold-doc chunk. How high the right chunk sits.
- nDCG@5: graded ranking quality (gain 1 for gold doc, log discount).
- Abstention accuracy: fraction of unanswerable questions refused AND
  answerable questions answered (no false refusals).
- Groundedness: by construction every extractive answer sentence carries a
  [n] citation; we verify the cited chunk's text contains the answer
  sentence (structural check, not a judgement call).
- Answer correctness (loose): cited documents cover the gold document
  (citation hits the right source).

Results are written to eval/results.json and eval/results.md (committed to
the repo).
"""
from __future__ import annotations

import json
import math
import sys
import time

from .. import answer, config, index as index_mod

EVAL_QUESTIONS = config.EVAL_DIR / "questions.jsonl"


def load_questions() -> list[dict]:
    return [json.loads(line) for line in open(EVAL_QUESTIONS, encoding="utf-8")]


def doc_rank(results: list[dict], gold_doc: str) -> int:
    """1-based best rank of any chunk from the gold document."""
    for i, r in enumerate(results, start=1):
        if r["doc_id"] == gold_doc:
            return i
    return 0


def ndcg_at_k(results: list[dict], gold_doc: str, k: int = 5) -> float:
    dcg = 0.0
    for i, r in enumerate(results[:k], start=1):
        rel = 1.0 if r["doc_id"] == gold_doc else 0.0
        dcg += rel / math.log2(i + 1)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, k + 1))
    return dcg / ideal


def eval_retrieval(questions: list[dict], index, top_n: int = 5) -> dict:
    rows = []
    for q in questions:
        if q["type"] != "answerable":
            continue
        verdict = index_mod and None  # placeholder to keep flake quiet
        from .. import search
        verdict = search.search_top(index, q["question"])
        results = verdict["results"]
        rank = doc_rank(results, q["gold_doc_id"])
        rows.append({
            "qid": q["qid"],
            "question": q["question"],
            "gold_doc": q["gold_doc_id"],
            "retrieved_doc_ids": [r["doc_id"] for r in results[:top_n]],
            "doc_rank": rank,
            "ndcg@5": round(ndcg_at_k(results, q["gold_doc_id"]), 4),
            "abstained": verdict["abstain"],  # false refusal if True
            "best_score": verdict["best_score"],
        })
    n = len(rows)
    return {
        "n": n,
        "recall@2": round(sum(1 for r in rows if 0 < r["doc_rank"] <= 2) / n, 4),
        "recall@5": round(sum(1 for r in rows if 0 < r["doc_rank"] <= 5) / n, 4),
        "mrr@5": round(sum(1 / r["doc_rank"] for r in rows if r["doc_rank"]) / n, 4),
        "ndcg@5": round(sum(r["ndcg@5"] for r in rows) / n, 4),
        "false_refusals": sum(1 for r in rows if r["abstained"]),
        "rows": rows,
    }


def eval_abstention(questions: list[dict], index) -> dict:
    rows = []
    for q in questions:
        if q["type"] != "unanswerable":
            continue
        from .. import search
        verdict = search.search_top(index, q["question"])
        rows.append({
            "qid": q["qid"],
            "question": q["question"],
            "abstained": verdict["abstain"],
            "best_score": verdict["best_score"],
            "closest_topic": verdict["results"][0]["heading"] if verdict["results"] else None,
        })
    correct_refusals = sum(1 for r in rows if r["abstained"])
    return {
        "n": len(rows),
        "correct_refusals": correct_refusals,
        "abstention_accuracy": round(correct_refusals / len(rows), 4),
        "rows": rows,
    }


def eval_answers(questions: list[dict], index) -> dict:
    """Answer quality: groundedness (structural) + loose correctness."""
    rows = []
    for q in questions:
        if q["type"] != "answerable":
            continue
        out = answer.answer_query(index, q["question"])
        if out["abstained"]:
            rows.append({"qid": q["qid"], "answered": False,
                         "cited_docs": [], "correct_loose": False,
                         "grounded": False})
            continue
        # Structural groundedness: every answer sentence appears in a cited chunk.
        from .. import search
        verdict = search.search_top(index, q["question"])
        chunk_texts = [r["text"] for r in verdict["results"]]
        sentences = [s.strip() for s in
                     search.split_sentences(out["answer"]) if s.strip()]
        grounded = all(any(s[:40] in t for t in chunk_texts) for s in sentences) if sentences else False
        cited_docs = {c["doc_id"] for c in out["citations"]}
        correct_loose = q["gold_doc_id"] in cited_docs
        key_hits = sum(1 for kt in q["key_terms"]
                       if kt.lower() in out["answer"].lower())
        rows.append({
            "qid": q["qid"], "answered": True,
            "cited_docs": sorted(cited_docs),
            "citations_n": len(out["citations"]),
            "grounded": grounded,
            "correct_loose": correct_loose,
            "key_terms_hit": f"{key_hits}/{len(q['key_terms'])}",
        })
    answered = [r for r in rows if r["answered"]]
    return {
        "n": len(rows),
        "answered_n": len(answered),
        "groundedness": round(sum(1 for r in answered if r["grounded"]) / len(rows), 4),
        "correct_loose": round(sum(1 for r in rows if r["correct_loose"]) / len(rows), 4),
        "rows": rows,
    }


def main():
    questions = load_questions()
    index, chunks = index_mod.load()
    print(f"evaluating {len(questions)} questions against {len(chunks)} chunks")

    t0 = time.perf_counter()
    retrieval = eval_retrieval(questions, index)
    abstention = eval_abstention(questions, index)
    answers_eval = eval_answers(questions, index)
    elapsed = time.perf_counter() - t0

    result = {
        "corpus": {"documents": len({c["doc_id"] for c in chunks}),
                    "chunks": len(chunks)},
        "questions": {"answerable": retrieval["n"],
                       "unanswerable": abstention["n"]},
        "retrieval": {k: v for k, v in retrieval.items() if k != "rows"},
        "abstention": {k: v for k, v in abstention.items() if k != "rows"},
        "answers": {k: v for k, v in answers_eval.items() if k != "rows"},
        "latency_ms_per_query": round(elapsed / len(questions) * 1000, 1),
        "detail": {"retrieval_rows": retrieval["rows"],
                    "abstention_rows": abstention["rows"],
                    "answer_rows": answers_eval["rows"]},
    }
    config.EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.EVAL_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Markdown summary table (committed to repo)
    md = []
    md.append("# Retrieval & answer evaluation results")
    md.append("")
    md.append(f"Corpus: **{result['corpus']['documents']} documents / "
              f"{result['corpus']['chunks']} chunks** · "
              f"Questions: **{retrieval['n']} answerable + {abstention['n']} "
              f"unanswerable** · Avg latency: **{result['latency_ms_per_query']} ms/query**")
    md.append("")
    md.append("| Metric | Score | Meaning |")
    md.append("|---|---|---|")
    md.append(f"| Recall@2 (docs) | {retrieval['recall@2']:.0%} | gold source in top-2 retrieved documents |")
    md.append(f"| Recall@5 (docs) | {retrieval['recall@5']:.0%} | gold source in top-5 |")
    md.append(f"| MRR@5 | {retrieval['mrr@5']:.3f} | how high the right chunk ranks |")
    md.append(f"| nDCG@5 | {retrieval['ndcg@5']:.3f} | graded ranking quality |")
    md.append(f"| Abstention accuracy | {abstention['abstention_accuracy']:.0%} "
              f"({abstention['correct_refusals']}/{abstention['n']}) | out-of-domain questions correctly refused |")
    md.append(f"| False refusals | {retrieval['false_refusals']}/{retrieval['n']} | answerable questions we failed to answer |")
    md.append(f"| Answer groundedness | {answers_eval['groundedness']:.0%} | every answer sentence traceable to a cited chunk |")
    md.append(f"| Correct source cited | {answers_eval['correct_loose']:.0%} | citations include the gold document |")
    md.append("")
    md.append("## Per-question detail")
    md.append("")
    md.append("| QID | Type | Question | Gold doc | Doc rank | Abstained? |")
    md.append("|---|---|---|---|---|---|")
    rows = {r["qid"]: r for r in retrieval["rows"]}
    rows.update({r["qid"]: r for r in abstention["rows"]})
    for q in questions:
        r = rows[q["qid"]]
        rank = r.get("doc_rank", "—")
        if q["type"] == "answerable":
            outcome = "❌ false refusal" if r["abstained"] else "✅ answered"
        else:
            outcome = "✅ refused" if r["abstained"] else "❌ answered (!)"
        md.append(f"| {q['qid']} | {q['type']} | {q['question'][:60]} | "
                  f"{q.get('gold_doc_id') or '—'} | {rank} | {outcome} |")
    with open(config.EVAL_DIR / "results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"recall@2={retrieval['recall@2']:.2%} recall@5={retrieval['recall@5']:.2%} "
          f"mrr@5={retrieval['mrr@5']:.3f} ndcg@5={retrieval['ndcg@5']:.3f}")
    print(f"abstention={abstention['abstention_accuracy']:.2%} "
          f"false_refusals={retrieval['false_refusals']}")
    print(f"groundedness={answers_eval['groundedness']:.2%} "
          f"correct_loose={answers_eval['correct_loose']:.2%}")
    return result


if __name__ == "__main__":
    main()
