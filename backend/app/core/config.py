from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SenAI CRM Intelligence Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/senai_crm",
        description="Async SQLAlchemy database URL.",
    )
    knowledge_base_path: str = "../knowledge_base"
    rag_index_path: str = "storage/faiss_index"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 3
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    classifier_prompt_version: str = "classifier_v1"
    classifier_confidence_threshold: float = 0.70
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-70b-versatile"
    agent_max_tool_calls: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
