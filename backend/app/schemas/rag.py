from pydantic import BaseModel


class RagSearchResult(BaseModel):
    chunk_id: str
    source_doc: str
    chunk_index: int
    chunk_text: str
    score: float


class RagSearchResponse(BaseModel):
    query: str
    results: list[RagSearchResult]
