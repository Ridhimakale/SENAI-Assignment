from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source_doc: str
    chunk_index: int
    chunk_text: str
    token_count: int


class KnowledgeBaseChunker:
    def __init__(self, *, chunk_size: int = 400, overlap: int = 80) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_directory(self, knowledge_base_path: Path) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for path in sorted(knowledge_base_path.glob("*.md")):
            chunks.extend(self.chunk_document(path))
        return chunks

    def chunk_document(self, path: Path) -> list[KnowledgeChunk]:
        text = path.read_text(encoding="utf-8")
        tokens = text.split()
        if not tokens:
            return []

        chunks: list[KnowledgeChunk] = []
        start = 0
        chunk_index = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"{path.name}:{chunk_index}",
                    source_doc=path.name,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    token_count=len(chunk_tokens),
                )
            )
            if end == len(tokens):
                break
            start = end - self.overlap
            chunk_index += 1
        return chunks
