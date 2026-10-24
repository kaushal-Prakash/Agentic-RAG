from langchain_core.prompts import ChatPromptTemplate

from app.graph.state import AgentState
from app.rag.gate import should_retrieve
from app.rag.prompts import (
    CONTEXT_FILTER_PROMPT,
    FINAL_ANSWER_PROMPT,
)
from app.rag.retrieval import retrieve_from_cluster
from app.services.embeddings import embed_text
from app.services.llm import get_filter_llm, get_response_llm


# Node: Generates dense vector embedding for incoming user query
def embed_query_node(state: AgentState) -> AgentState:
    query_embedding = embed_text(state["query"])
    return {
        "query_embedding": query_embedding,
    }


# Node: Evaluates query against cluster centroids to decide if RAG is needed
def retrieval_gate_node(state: AgentState) -> AgentState:
    retrieve, cluster_id, similarity = should_retrieve(
        state["query_embedding"],
        state.get("cluster_centroids", {}),
    )
    return {
        "should_retrieve": retrieve,
        "selected_cluster_id": cluster_id,
        "gate_similarity": similarity,
    }


# Node: Performs vector search narrowed to the selected document cluster
def retrieve_node(state: AgentState) -> AgentState:
    cluster_id = state.get("selected_cluster_id")
    if cluster_id is None:
        return {
            "retrieved_documents": [],
        }
    documents = retrieve_from_cluster(
        query=state["query"],
        cluster_id=cluster_id,
    )
    return {
        "retrieved_documents": documents,
    }


# Node: Uses LLM to filter and extract relevant facts from multiple retrieved chunks
def filter_context_node(state: AgentState) -> AgentState:
    documents = state.get("retrieved_documents", [])
    if not documents:
        return {
            "filtered_context": "",
        }
    # Fast path: single chunk is passed directly without an extra LLM call
    if len(documents) == 1:
        return {
            "filtered_context": documents[0].page_content,
        }
    context = "\n\n".join(
        document.page_content
        for document in documents
    )
    prompt = ChatPromptTemplate.from_template(
        CONTEXT_FILTER_PROMPT
    )
    chain = prompt | get_filter_llm()
    result = chain.invoke(
        {
            "query": state["query"],
            "context": context,
        }
    )
    return {
        "filtered_context": result.content,
    }


# Node: Generates final answer combining RAG context, chat history, and procedural memory
def generate_response_node(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template(
        FINAL_ANSWER_PROMPT
    )
    chain = prompt | get_response_llm()
    result = chain.invoke(
        {
            "query": state["query"],
            "chat_history": state.get(
                "chat_history",
                "",
            ),
            "procedural_memory": state.get(
                "procedural_memory",
                "",
            ),
            "context": state.get(
                "filtered_context",
                "",
            ),
        }
    )
    return {
        "response": result.content,
    }