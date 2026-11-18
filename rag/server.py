"""FastAPI service exposing the RAG pipeline.

Endpoints:
  GET  /health          — liveness + index stats
  GET  /rag/search      — raw hybrid search + rerank (no answer)
  POST /rag/answer      — grounded answer with citations (or abstention)
Run:  python -m rag.server   (serves on :8100 — see config.API_PORT)
"""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import answer, config, index as index_mod

app = FastAPI(title="FD Advisor RAG", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_STATE: dict = {}


@app.on_event("startup")
def load_index():
    try:
        _STATE["index"], _STATE["chunks"] = index_mod.load()
    except FileNotFoundError:
        raise RuntimeError(
            "index not built yet — run `python -m rag.build` first")


class AnswerRequest(BaseModel):
    query: str
    language: str = "hi"
    mode: str | None = None  # "extractive" | "llm"


@app.get("/health")
def health():
    n = len(_STATE.get("chunks", []))
    return {"status": "ok", "chunks": n,
            "docs": len({c["doc_id"] for c in _STATE.get("chunks", [])})}


@app.get("/rag/search")
def rag_search(q: str, top_n: int = 5):
    if "index" not in _STATE:
        raise HTTPException(503, "index not loaded")
    verdict = index_mod and search_verdict(q)
    return verdict


def search_verdict(q: str):
    from . import search
    return search.search_top(_STATE["index"], q)


@app.post("/rag/answer")
def rag_answer(req: AnswerRequest):
    if "index" not in _STATE:
        raise HTTPException(503, "index not loaded")
    if not req.query.strip():
        raise HTTPException(400, "query must not be empty")
    return answer.answer_query(_STATE["index"], req.query.strip(),
                               req.language, req.mode)


def main():
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)


if __name__ == "__main__":
    main()
