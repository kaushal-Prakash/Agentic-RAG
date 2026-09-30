from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

embedding_model = get_embedding_model()

def embed_text(text: str) -> list[float]:
    return embedding_model.embed_query(text)

def embed_documents(texts: list[str]) -> list[list[float]]:
    return embedding_model.embed_documents(texts)