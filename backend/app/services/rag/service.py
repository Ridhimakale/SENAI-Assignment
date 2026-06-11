from pathlib import Path

from app.core.config import get_settings
from app.schemas.rag import RagSearchResponse, RagSearchResult
from app.services.rag.chunker import KnowledgeBaseChunker
from app.services.rag.embeddings import EmbeddingProvider, create_embedding_provider
from app.services.rag.vector_store import VectorStore


class RagService:
    def __init__(
        self,
        *,
        knowledge_base_path: Path,
        embedding_provider: EmbeddingProvider,
        top_k: int,
    ) -> None:
        self.knowledge_base_path = knowledge_base_path
        self.embedding_provider = embedding_provider
        self.top_k = top_k
        self.vector_store = VectorStore()
        self._is_built = False

    def search(self, query: str) -> RagSearchResponse:
        self._ensure_built()
        query_vector = self.embedding_provider.encode([query])
        matches = self.vector_store.search(query_vector, self.top_k)
        return RagSearchResponse(
            query=query,
            results=[
                RagSearchResult(
                    chunk_id=chunk.chunk_id,
                    source_doc=chunk.source_doc,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    score=score,
                )
                for chunk, score in matches
            ],
        )

    def rebuild(self) -> int:
        chunker = KnowledgeBaseChunker()
        chunks = chunker.chunk_directory(self.knowledge_base_path)
        vectors = self.embedding_provider.encode([chunk.chunk_text for chunk in chunks])
        self.vector_store.build(chunks=chunks, vectors=vectors)
        self._is_built = True
        return len(chunks)

    def _ensure_built(self) -> None:
        if not self._is_built:
            self.rebuild()


_rag_service: RagService | None = None


def get_rag_service() -> RagService:
    global _rag_service
    if _rag_service is None:
        settings = get_settings()
        backend_root = Path(__file__).resolve().parents[3]
        knowledge_base_path = (backend_root / settings.knowledge_base_path).resolve()
        _rag_service = RagService(
            knowledge_base_path=knowledge_base_path,
            embedding_provider=create_embedding_provider(settings.embedding_model_name),
            top_k=settings.rag_top_k,
        )
    return _rag_service
