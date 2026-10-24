from langchain_core.documents import Document
from app.config import settings
from app.services.vector_store import similarity_search_with_score

# Global vector search across all documents
def retrieve_documents(
    query: str,
    k: int | None = None,
) -> list[Document]:
    results = similarity_search_with_score(
        query,
        k=k or settings.max_retrieved_chunks,
    )
    documents = []
    # Chroma returns distance (lower = more similar); keep chunks within threshold
    for document, distance in results:
        if distance <= settings.vector_threshold:
            document.metadata["distance"] = distance
            documents.append(document)
    return documents

# Partitioned vector search restricted to a single semantic cluster
def retrieve_from_cluster(
    query: str,
    cluster_id: int,
    k: int | None = None,
) -> list[Document]:
    results = similarity_search_with_score(
        query=query,
        k=k or settings.max_retrieved_chunks,
        filter={"cluster_id": cluster_id},  # Chroma metadata filter limits search space
    )
    documents = []
    # Retain only chunks that satisfy similarity threshold
    for document, distance in results:
        if distance <= settings.vector_threshold:
            document.metadata["distance"] = distance
            documents.append(document)
    return documents