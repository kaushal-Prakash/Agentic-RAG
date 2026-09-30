import numpy as np

from app.config import settings


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    a = np.array(vector_a)
    b = np.array(vector_b)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def calculate_cluster_similarities(
    query_embedding: list[float],
    cluster_centroids: dict[int, list[float]],
) -> dict[int, float]:
    similarities = {}
    for cluster_id, centroid in cluster_centroids.items():
        similarities[cluster_id] = cosine_similarity(
            query_embedding,
            centroid,
        )
    return similarities


def should_retrieve(
    query_embedding: list[float],
    cluster_centroids: dict[int, list[float]],
) -> tuple[bool, int | None, float]:
    similarities = calculate_cluster_similarities(
        query_embedding,
        cluster_centroids,
    )
    if not similarities:
        return False, None, 0.0
    best_cluster_id = max(
        similarities,
        key=similarities.get,
    )
    best_similarity = similarities[best_cluster_id]
    retrieve = best_similarity >= settings.gate_threshold
    if not retrieve:
        return False, None, best_similarity
    return True, best_cluster_id, best_similarity