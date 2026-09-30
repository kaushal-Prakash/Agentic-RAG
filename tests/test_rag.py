import pytest
from app.rag.gate import (
    calculate_cluster_similarities,
    cosine_similarity,
    should_retrieve,
)
from app.rag.retrieval import retrieve_documents


def test_cosine_similarity_identical_vectors():
    vector_a = [1.0, 0.0, 0.0]
    vector_b = [1.0, 0.0, 0.0]
    similarity = cosine_similarity(vector_a, vector_b)
    assert similarity == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    vector_a = [1.0, 0.0]
    vector_b = [0.0, 1.0]
    similarity = cosine_similarity(vector_a, vector_b)
    assert similarity == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    vector_a = [0.0, 0.0]
    vector_b = [1.0, 0.0]
    similarity = cosine_similarity(vector_a, vector_b)
    assert similarity == 0.0


def test_calculate_cluster_similarities():
    query_embedding = [1.0, 0.0]
    cluster_centroids = {
        0: [1.0, 0.0],
        1: [0.0, 1.0],
    }
    similarities = calculate_cluster_similarities(
        query_embedding,
        cluster_centroids,
    )
    assert similarities[0] == pytest.approx(1.0)
    assert similarities[1] == pytest.approx(0.0)


def test_retrieval_gate_retrieves_relevant_cluster():
    query_embedding = [1.0, 0.0]
    cluster_centroids = {
        0: [1.0, 0.0],
        1: [0.0, 1.0],
    }
    retrieve, cluster_id, similarity = should_retrieve(
        query_embedding,
        cluster_centroids,
    )
    assert retrieve is True
    assert cluster_id == 0
    assert similarity == pytest.approx(1.0)


def test_retrieval_gate_rejects_irrelevant_query(monkeypatch):
    query_embedding = [1.0, 0.0]
    cluster_centroids = {
        0: [0.0, 1.0],
    }
    monkeypatch.setattr(
        "app.rag.gate.settings.gate_threshold",
        0.9,
    )
    retrieve, cluster_id, similarity = should_retrieve(
        query_embedding,
        cluster_centroids,
    )
    assert retrieve is False
    assert cluster_id is None
    assert similarity == pytest.approx(0.0)


def test_empty_cluster_centroids():
    query_embedding = [1.0, 0.0]
    retrieve, cluster_id, similarity = should_retrieve(
        query_embedding,
        {},
    )
    assert retrieve is False
    assert cluster_id is None
    assert similarity == 0.0


def test_retrieve_documents_filters_by_distance(monkeypatch):
    from langchain_core.documents import Document
    documents = [
        Document(page_content="Relevant document"),
        Document(page_content="Irrelevant document"),
    ]
    mock_results = [
        (documents[0], 0.5),
        (documents[1], 1.5),
    ]
    monkeypatch.setattr(
        "app.rag.retrieval.similarity_search_with_score",
        lambda query, k: mock_results,
    )
    monkeypatch.setattr(
        "app.rag.retrieval.settings.max_retrieved_chunks",
        5,
    )
    monkeypatch.setattr(
        "app.rag.retrieval.settings.vector_threshold",
        1.0,
    )
    results = retrieve_documents(
        query="test query",
    )
    assert len(results) == 1
    assert results[0].page_content == "Relevant document"
    assert results[0].metadata["distance"] == 0.5