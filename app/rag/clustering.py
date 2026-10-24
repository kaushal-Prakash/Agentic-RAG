import json
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

from app.config import settings
from app.services.embeddings import embed_documents

# Location to persist cluster centroids alongside vector store
CENTROID_FILE = (
    Path(settings.chroma_persist_directory)
    / "cluster_centroids.json"
)

# Groups document chunks into k semantic clusters and calculates their central vectors
def create_clusters(
    texts: list[str],
    num_clusters: int,
) -> tuple[list[int], dict[int, list[float]]]:
    if not texts:
        return [], {}
    if num_clusters <= 0:
        raise ValueError("num_clusters must be greater than zero")
    # Prevent error: clusters cannot exceed the number of available text chunks
    num_clusters = min(num_clusters, len(texts))
    embeddings = np.array(
        embed_documents(texts)
    )
    # Fit KMeans: fixed seed for reproducibility across ingestion runs
    model = KMeans(
        n_clusters=num_clusters,
        random_state=42,
        n_init="auto",
    )
    labels = model.fit_predict(embeddings)  # Cluster assignment per chunk
    # Extract center coordinates of each cluster for semantic gating
    centroids = {
        cluster_id: centroid.tolist()
        for cluster_id, centroid in enumerate(
            model.cluster_centers_
        )
    }
    return labels.tolist(), centroids

# Persist centroids to disk as JSON
def save_cluster_centroids(
    centroids: dict[int, list[float]],
) -> None:
    CENTROID_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    with CENTROID_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            centroids,
            file,
        )

# Load centroids from disk (converts JSON string keys back to integer IDs)
def load_cluster_centroids() -> dict[int, list[float]]:
    if not CENTROID_FILE.exists():
        return {}
    with CENTROID_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)
    return {
        int(cluster_id): centroid
        for cluster_id, centroid in data.items()
    }