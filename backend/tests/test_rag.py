from pathlib import Path

from app.services.rag.chunker import KnowledgeBaseChunker
from app.services.rag.embeddings import HashEmbeddingProvider
from app.services.rag.service import RagService


def test_chunker_creates_overlapping_chunks(tmp_path: Path) -> None:
    kb_file = tmp_path / "sample.md"
    kb_file.write_text(" ".join(f"token{i}" for i in range(900)), encoding="utf-8")

    chunks = KnowledgeBaseChunker(chunk_size=400, overlap=80).chunk_document(kb_file)

    assert len(chunks) == 3
    assert chunks[0].token_count == 400
    assert chunks[1].chunk_text.startswith("token320")


def test_rag_search_returns_source_attribution(tmp_path: Path) -> None:
    (tmp_path / "refund_policy.md").write_text(
        "Refund requests after public review threats require retention escalation.",
        encoding="utf-8",
    )
    (tmp_path / "sla_policy.md").write_text(
        "P0 outage incidents require RCA delivery within 24 hours.",
        encoding="utf-8",
    )

    service = RagService(
        knowledge_base_path=tmp_path,
        embedding_provider=HashEmbeddingProvider(),
        top_k=2,
    )

    response = service.search("refund public review retention")

    assert response.results
    assert response.results[0].source_doc == "refund_policy.md"
    assert response.results[0].score > 0
