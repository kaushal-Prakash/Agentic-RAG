from pathlib import Path
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.clustering import (
    create_clusters,
    save_cluster_centroids,
)
from app.services.vector_store import add_documents

# Splits text into 800-char segments with 100-char overlap to preserve boundary context
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
)

# Routes document loading based on file extension (.pdf, .docx, .txt)
def load_document(file_path: str):
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(path))
    elif path.suffix.lower() == ".docx":
        loader = Docx2txtLoader(str(path))
    elif path.suffix.lower() == ".txt":
        loader = TextLoader(
            str(path),
            encoding="utf-8",
        )
    else:
        raise ValueError(
            f"Unsupported file type: {path.suffix}"
        )
    return loader.load()

def split_documents(documents):
    return text_splitter.split_documents(documents)

# Annotates chunks with sequential IDs and preserves document source for citations
def add_metadata(documents):
    for index, document in enumerate(documents):
        document.metadata["chunk_id"] = index
        document.metadata["source"] = document.metadata.get(
            "source",
            "unknown",
        )
    return documents

# Computes KMeans clusters, tags chunks with cluster_id, and saves centroid vectors to disk
def cluster_documents(
    documents,
    num_clusters: int = 5,
):
    texts = [
        document.page_content
        for document in documents
    ]
    labels, centroids = create_clusters(
        texts,
        num_clusters,
    )
    # Tag each chunk with its assigned cluster for partition-filtered retrieval in Chroma
    for document, cluster_id in zip(
        documents,
        labels,
    ):
        document.metadata["cluster_id"] = cluster_id
    save_cluster_centroids(centroids)
    return documents

# End-to-end ingestion: load -> chunk -> tag metadata -> cluster -> store in Chroma
def ingest_document(
    file_path: str,
    num_clusters: int = 5,
) -> list[str]:
    documents = load_document(file_path)
    chunks = split_documents(documents)
    chunks = add_metadata(chunks)
    chunks = cluster_documents(
        chunks,
        num_clusters=num_clusters,
    )
    return add_documents(chunks)