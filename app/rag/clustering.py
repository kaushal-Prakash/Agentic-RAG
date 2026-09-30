import json
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

from app.config import settings
from app.services.embeddings import embed_documents

CENTROID_FILE = (
    Path(settings.chroma_persist_directory)
    / "cluster_centroids.json"
)

def create_clusters(
    texts: list[str],
    num_clusters: int,
) -> tuple[list[int], dict[int, list[float]]]:
    if not texts:
        return [], {}
    if num_clusters <= 0:
        raise ValueError("num_clusters must be greater than zero")
    num_clusters = min(num_clusters, len(texts))
    embeddings = np.array(
        embed_documents(texts)
    )
    model = KMeans(
        n_clusters=num_clusters,
        random_state=42,
        n_init="auto",
    )
    labels = model.fit_predict(embeddings)
    centroids = {
        cluster_id: centroid.tolist()
        for cluster_id, centroid in enumerate(
            model.cluster_centers_
        )
    }
    return labels.tolist(), centroids

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