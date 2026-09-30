from typing import Any, TypedDict

class AgentState(TypedDict, total=False):
    user_id: int
    query: str
    query_embedding: list[float]
    cluster_centroids: dict[int, list[float]]
    selected_cluster_id: int | None
    gate_similarity: float
    should_retrieve: bool
    retrieved_documents: list[Any]
    filtered_context: str
    chat_history: str
    procedural_memory: str
    response: str
    error: str | None