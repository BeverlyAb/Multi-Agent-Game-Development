"""Lightweight retrieval-augmented generation (RAG) knowledge base built
directly over the GDD (`gdd.txt`) -- no vector database or embedding
model required. Chunking follows the document's own paragraph structure
(each line in gdd.txt is already one full paragraph or heading); a line
that doesn't end in sentence-ending punctuation is treated as a heading
and attached to the paragraphs that follow it, so a chunk always carries
its section/agent-name context. Retrieval is TF-IDF over those chunks.

This exists so the Dynamic Content Pipeline's generation is demonstrably
grounded in the actual GDD text (Assignment #4's "RAG Implementation"
criterion), not invented from nothing -- every generation call can show
the query, the retrieved chunk(s), and the output side by side.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List

TOKEN_RE = re.compile(r"[a-zA-Z']+")
_SENTENCE_ENDINGS = (".", '"', "”")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


@dataclass
class KBChunk:
    chunk_id: int
    heading: str
    text: str


@dataclass
class RetrievedChunk:
    chunk: KBChunk
    score: float


class GDDKnowledgeBase:
    """Splits gdd.txt into paragraph-level chunks and answers TF-IDF queries against them."""

    def __init__(self, gdd_path: str):
        self.gdd_path = gdd_path
        self.chunks: List[KBChunk] = []
        self._doc_freq = {}
        self._term_freq: List[dict] = []
        self._load()
        self._index()

    def _load(self) -> None:
        with open(self.gdd_path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f]
        current_heading = "(document header)"
        chunk_id = 0
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            is_heading_line = not line.endswith(_SENTENCE_ENDINGS)
            chunk_id += 1
            self.chunks.append(KBChunk(chunk_id=chunk_id, heading=current_heading, text=line))
            if is_heading_line:
                current_heading = line

    def _index(self) -> None:
        doc_freq: dict = {}
        term_freq: List[dict] = []
        for chunk in self.chunks:
            counts: dict = {}
            for term in _tokenize(f"{chunk.heading} {chunk.text}"):
                counts[term] = counts.get(term, 0) + 1
            term_freq.append(counts)
            for term in counts:
                doc_freq[term] = doc_freq.get(term, 0) + 1
        self._term_freq = term_freq
        self._doc_freq = doc_freq

    def _idf(self, term: str) -> float:
        n = len(self.chunks)
        df = self._doc_freq.get(term, 0)
        return math.log((n + 1) / (df + 1)) + 1.0

    def retrieve(self, query: str, k: int = 2) -> List[RetrievedChunk]:
        q_terms = _tokenize(query)
        scored: List[RetrievedChunk] = []
        for chunk, counts in zip(self.chunks, self._term_freq):
            score = sum(counts.get(t, 0) * self._idf(t) for t in q_terms)
            if score > 0:
                scored.append(RetrievedChunk(chunk=chunk, score=round(score, 3)))
        scored.sort(key=lambda r: r.score, reverse=True)
        if not scored:
            return [RetrievedChunk(chunk=self.chunks[0], score=0.0)]
        return scored[:k]
