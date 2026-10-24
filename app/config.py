from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Agentic RAG with Procedural Memory"
    app_version: str = "1.0.0"
    debug: bool = True
    # Async SQLite driver dialect
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    jwt_secret_key: str  # Required from .env (no default)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    groq_api_key: str  # Required API key for LLM calls
    llm_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "company_documents"
    gate_threshold: float = 0.45  # Min confidence to trigger RAG routing
    vector_threshold: float = 0.50  # Min similarity score to accept a chunk
    max_retrieved_chunks: int = 5
    langsmith_tracing: bool = True
    langsmith_api_key: str | None = None
    langsmith_project: str = "agentic-rag"

    # Pydantic config: loads .env, case-insensitive, ignores extra env vars
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

# Cache settings instance so .env is only read once (singleton pattern)
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()