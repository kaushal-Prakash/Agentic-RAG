from langchain_core.documents import Document
from app.config import settings
from app.services.vector_store import similarity_search_with_score

def retrieve_documents(
    query: str,
    k: int | None = None,
) -> list[Document]:
    results = similarity_search_with_score(
        query,
        k=k or settings.max_retrieved_chunks,
    )
    documents = []
    for document, distance in results:
        if distance <= settings.vector_threshold:
            document.metadata["distance"] = distance
            documents.append(document)
    return documents

def retrieve_from_cluster(
    query: str,
    cluster_id: int,
    k: int | None = None,
) -> list[Document]:
    results = similarity_search_with_score(
        query=query,
        k=k or settings.max_retrieved_chunks,
        filter={"cluster_id": cluster_id},
    )
    documents = []
    for document, distance in results:
        if distance <= settings.vector_threshold:
            document.metadata["distance"] = distance
            documents.append(document)
    return documents