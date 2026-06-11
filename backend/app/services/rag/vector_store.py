from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.services.rag.chunker import KnowledgeChunk


class VectorStore:
    def __init__(self) -> None:
        self.chunks: list[KnowledgeChunk] = []
        self.vectors: np.ndarray | None = None
        self.index = None

    def build(self, *, chunks: list[KnowledgeChunk], vectors: np.ndarray) -> None:
        self.chunks = chunks
        self.vectors = vectors.astype("float32")
        try:
            import faiss

            self.index = faiss.IndexFlatIP(self.vectors.shape[1])
            self.index.add(self.vectors)
        except Exception:
            self.index = None

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[KnowledgeChunk, float]]:
        if self.vectors is None or not self.chunks:
            return []

        query_vector = query_vector.astype("float32")
        if self.index is not None:
            scores, indexes = self.index.search(query_vector, min(top_k, len(self.chunks)))
            return [
                (self.chunks[int(index)], float(score))
                for index, score in zip(indexes[0], scores[0], strict=False)
                if index >= 0
            ]

        scores = np.dot(self.vectors, query_vector[0])
        ranked_indexes = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[int(index)], float(scores[int(index)])) for index in ranked_indexes]

    def metadata(self) -> list[dict]:
        return [asdict(chunk) for chunk in self.chunks]
