from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin


class KnowledgeChunk(TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("source_doc", "chunk_index", name="uq_knowledge_source_chunk"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_doc: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_hash: Mapped[str | None] = mapped_column(String(255))
    faiss_vector_id: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)


Index("ix_knowledge_chunks_source_doc", KnowledgeChunk.source_doc)
Index("ix_knowledge_chunks_faiss_vector_id", KnowledgeChunk.faiss_vector_id)
