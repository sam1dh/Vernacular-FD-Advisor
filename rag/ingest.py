"""Ingestion + chunking.

Reads the markdown corpus (with YAML-style front-matter carrying source
metadata), splits documents into retrieval chunks, and writes a JSONL
dataset that is committed to the repo so anyone can inspect or reuse it.

Chunking strategy (and why):
1. **Heading-aware first.** Documents are written so every `##` section is
   one self-contained topic. Splitting at headings first keeps rules intact
   — a chunk never mixes "what is covered" with "when you get paid".
2. **Fixed character window with overlap inside long sections.** Sections
   longer than CHUNK_MAX_CHARS are split into ~CHUNK_TARGET_CHARS windows
   with CHUNK_OVERLAP_CHARS overlap, always at sentence boundaries, so a
   fact near a boundary appears complete in at least one chunk.
3. **Heading path prepended.** Each chunk carries "Doc title > Section"
   before its text: lexical search matches questions like "kya covered hai"
   against the heading, and the answer generator can cite precisely.
4. **No padding of short sections.** A complete rule is a complete answer
   unit; inflating short sections with neighbours hurts precision.

We use characters, not tokens, because the corpus is multilingual
(English + Devanagari) and tokenizer-dependent sizes would make the
dataset non-reproducible across tokenizers.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import config

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?।])\s+")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("corpus file is missing front-matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[m.end():]


def parse_sections(body: str) -> list[tuple[list[str], str]]:
    """Return [(heading_path, section_text), ...] with an intro section first."""
    sections: list[tuple[list[str], str]] = []
    matches = list(HEADING_RE.finditer(body))
    intro = body[: matches[0].start()] if matches else body
    if intro.strip():
        sections.append(([], intro.strip()))
    for i, m in enumerate(matches):
        level = len(m.group(1))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        heading_path = [s.strip() for s in sections[-1][0]] if sections else []
        heading_path = heading_path[: level - 1]
        heading_path.append(m.group(2).strip())
        sections.append((heading_path, body[m.end(): end].strip()))
    return sections


def split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(text) if p.strip()]
    return parts or [text.strip()]


def window_section(sentences: list[str]) -> list[str]:
    """Slide a window over sentences at the target size, sentence-aligned."""
    windows: list[str] = []
    current: list[str] = []
    size = 0
    for s in sentences:
        if size + len(s) > config.CHUNK_MAX_CHARS and current:
            windows.append(" ".join(current))
            # Rewind by the overlap so boundary facts appear whole somewhere.
            overlap: list[str] = []
            osize = 0
            for prev in reversed(current):
                if osize + len(prev) > config.CHUNK_OVERLAP_CHARS:
                    break
                overlap.insert(0, prev)
                osize += len(prev) + 1
            current = overlap
            size = osize
        current.append(s)
        size += len(s) + 1
        if size >= config.CHUNK_TARGET_CHARS:
            windows.append(" ".join(current))
            overlap = []
            osize = 0
            for prev in reversed(current):
                if osize + len(prev) > config.CHUNK_OVERLAP_CHARS:
                    break
                overlap.insert(0, prev)
                osize += len(prev) + 1
            current = overlap
            size = osize
    if current:
        tail = " ".join(current)
        # Skip a tail that only repeats the overlap of the last emitted window.
        if not windows or tail != windows[-1]:
            windows.append(tail)
    return windows


def chunk_document(path: Path) -> list[dict]:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    title = meta.get("title", path.stem)
    chunks: list[dict] = []
    for heading_path, section_text in parse_sections(body):
        windows = window_section(split_sentences(section_text))
        for j, text in enumerate(windows):
            heading_str = " > ".join([title] + heading_path)
            content = f"{heading_str}\n{text}" if config.PREPEND_HEADING_PATH else text
            chunk_id = hashlib.sha1(
                f"{meta['id']}|{'>'.join(heading_path)}|{j}".encode()
            ).hexdigest()[:12]
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": meta["id"],
                    "doc_title": title,
                    "heading_path": heading_str,
                    "section": heading_path[-1] if heading_path else "(intro)",
                    "window": j,
                    "text": text,
                    "content": content,
                    "chars": len(text),
                    "source_url": meta.get("source", ""),
                    "publisher": meta.get("publisher", ""),
                    "retrieved": meta.get("retrieved", ""),
                }
            )
    return chunks


def run() -> list[dict]:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks: list[dict] = []
    files = sorted(config.CORPUS_DIR.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"no corpus files in {config.CORPUS_DIR}")
    for path in files:
        all_chunks.extend(chunk_document(path))
    with open(config.CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return all_chunks


if __name__ == "__main__":
    chunks = run()
    sizes = [c["chars"] for c in chunks]
    print(f"ingested {len(set(c['doc_id'] for c in chunks))} docs "
          f"-> {len(chunks)} chunks")
    print(f"chunk chars: min={min(sizes)} median={sorted(sizes)[len(sizes)//2]} "
          f"max={max(sizes)}")
    print(f"dataset written to {config.CHUNKS_PATH.relative_to(config.RAG_ROOT)}")
