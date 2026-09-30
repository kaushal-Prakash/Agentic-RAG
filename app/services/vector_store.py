from langchain_chroma import Chroma
from app.config import settings
from app.services.embeddings import get_embedding_model

def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embedding_model(),
        persist_directory=settings.chroma_persist_directory,
    )

vector_store = get_vector_store()

def add_documents(
    documents,
) -> list[str]:
    return vector_store.add_documents(documents)

def similarity_search(
    query: str,
    k: int = 5,
    filter: dict | None = None,
):
    return vector_store.similarity_search(
        query,
        k=k,
        filter=filter,
    )

def similarity_search_with_score(
    query: str,
    k: int = 5,
    filter: dict | None = None,
):
    return vector_store.similarity_search_with_score(
        query,
        k=k,
        filter=filter,
    )