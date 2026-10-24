from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},  # Use CPU for portable cross-environment inference
        encode_kwargs={"normalize_embeddings": True},  # Unit-normalizes vectors so dot product equals cosine similarity
    )

# Preload embedding model into memory on startup (singleton)
embedding_model = get_embedding_model()

# Embed single user query (uses query-optimized prompt formatting if supported by model)
def embed_text(text: str) -> list[float]:
    return embedding_model.embed_query(text)

# Batch embed corpus texts
def embed_documents(texts: list[str]) -> list[list[float]]:
    return embedding_model.embed_documents(texts)