from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    embed_query_node,
    filter_context_node,
    generate_response_node,
    retrieve_node,
    retrieval_gate_node,
)
from app.graph.state import AgentState


def retrieval_router(state: AgentState) -> str:
    if state.get("should_retrieve", False):
        return "retrieve"
    return "generate_response"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node(
        "embed_query",
        embed_query_node,
    )
    graph.add_node(
        "retrieval_gate",
        retrieval_gate_node,
    )
    graph.add_node(
        "retrieve",
        retrieve_node,
    )
    graph.add_node(
        "filter_context",
        filter_context_node,
    )
    graph.add_node(
        "generate_response",
        generate_response_node,
    )
    graph.add_edge(
        START,
        "embed_query",
    )
    graph.add_edge(
        "embed_query",
        "retrieval_gate",
    )
    graph.add_conditional_edges(
        "retrieval_gate",
        retrieval_router,
        {
            "retrieve": "retrieve",
            "generate_response": "generate_response",
        },
    )
    graph.add_edge(
        "retrieve",
        "filter_context",
    )
    graph.add_edge(
        "filter_context",
        "generate_response",
    )
    graph.add_edge(
        "generate_response",
        END,
    )
    return graph.compile()


agent_graph = build_graph()