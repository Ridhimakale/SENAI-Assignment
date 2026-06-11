from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class EmbeddingProvider(Protocol):
    dimensions: int

    def encode(self, texts: list[str]) -> np.ndarray:
        pass


class SentenceTransformerEmbeddingProvider:
    dimensions = 384

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype="float32")


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimensions), dtype="float32")
        for row_index, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "little") % self.dimensions
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vectors[row_index, bucket] += sign
            norm = np.linalg.norm(vectors[row_index])
            if norm > 0:
                vectors[row_index] /= norm
        return vectors


def create_embedding_provider(model_name: str) -> EmbeddingProvider:
    try:
        return SentenceTransformerEmbeddingProvider(model_name)
    except Exception:
        return HashEmbeddingProvider()
