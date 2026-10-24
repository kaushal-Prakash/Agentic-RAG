from typing import Any, TypedDict

# LangGraph state schema: total=False allows nodes to return partial updates
class AgentState(TypedDict, total=False):
    user_id: int
    query: str
    query_embedding: list[float]
    cluster_centroids: dict[int, list[float]]  # cluster_id -> centroid embedding vector
    selected_cluster_id: int | None
    gate_similarity: float  # Cosine similarity to nearest cluster centroid
    should_retrieve: bool  # Routing flag decided by the retrieval gate
    retrieved_documents: list[Any]  # Raw vector search results from Chroma
    filtered_context: str  # Context distilled by LLM after filtering irrelevant chunks
    chat_history: str  # Recent conversation turns
    procedural_memory: str  # Cross-session user preferences and instructions
    response: str  # Final assistant response generated for user
    error: str | None