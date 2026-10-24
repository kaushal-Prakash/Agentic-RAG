# Architecture & Workflow Notes: Agentic RAG with Procedural Memory

This document provides a deep dive into the design, architectural differences between standard RAG and this Agentic RAG implementation, and a comprehensive breakdown of how a user request is handled step-by-step with all relevant code functions.

---

## 1. Traditional RAG vs. This Agentic RAG

| Architectural Dimension | Traditional (Naive) RAG | This Agentic RAG System |
| :--- | :--- | :--- |
| **Retrieval Decision** | **Always retrieves.** Every user query triggers a vector database query, even for *"hi"*, *"who are you?"*, or arithmetic questions. | **Retrieval Gate.** Evaluates query similarity against semantic cluster centroids (`should_retrieve`). Non-domain questions bypass vector search completely. |
| **Search Space** | Flat search over the entire vector collection (high latency on large document bases). | **Cluster-Partitioned Search.** Narrows vector similarity search to a specific semantic cluster (`filter={"cluster_id": cluster_id}`). |
| **Context Quality** | Concatenates top-$k$ raw retrieved document chunks directly into the prompt (includes irrelevant noise/distractors). | **LLM Context Filtering.** A dedicated deterministic LLM node (`temperature=0.0`) extracts only relevant facts and strips noise before final generation. |
| **Memory System** | None, or basic short-term sliding window chat history. | **Dual-Layer Memory:** <br>1. Short-term chat history (last 4 turns).<br>2. Long-term **Procedural Memory** (extracts and updates user preferences, style, and rules). |
| **Background Processing** | Monolithic synchronous execution; user waits for all LLM calls to finish. | **Non-Blocking Background Tasks.** Procedural memory analysis runs asynchronously via FastAPI `BackgroundTasks`, so chat responses return instantly. |
| **Pipeline Control** | Static sequential pipeline (Input $\to$ Embed $\to$ Retrieve $\to$ LLM $\to$ Output). | **State-Machine Graph (LangGraph).** Execution dynamically branches based on runtime decisions using `AgentState` and conditional edges. |

---

## 2. Visual Request Workflow

```
[Client / Frontend]
        │  HTTP POST /api/chat (Bearer JWT)
        ▼
[app.api.chat: chat]
        │
        ├── 1. Auth & Session Setup
        │      ├── app.auth.dependencies: get_current_user_id()
        │      │      └── app.auth.jwt: verify_access_token()
        │      └── app.database.db: get_db()
        │
        ├── 2. Pre-Graph Context Collection
        │      ├── app.services.chat_history: get_chat_history(limit=4)
        │      ├── app.memory.procedural_memory: get_procedural_memory()
        │      └── app.rag.clustering: load_cluster_centroids()
        │
        ▼
[LangGraph Execution: agent_graph.ainvoke(initial_state)]
        │
        ├── Node 1: app.graph.nodes: embed_query_node
        │      └── app.services.embeddings: embed_text()
        │
        ├── Node 2: app.graph.nodes: retrieval_gate_node
        │      └── app.rag.gate: should_retrieve()
        │             └── app.rag.gate: calculate_cluster_similarities()
        │
        ├── Conditional Router: app.graph.graph: retrieval_router
        │      ├── [should_retrieve == True] ───────┐
        │      │                                     │
        │      │   Node 3: app.graph.nodes: retrieve_node
        │      │        └── app.rag.retrieval: retrieve_from_cluster()
        │      │
        │      │   Node 4: app.graph.nodes: filter_context_node
        │      │        └── app.services.llm: get_filter_llm()
        │      │
        │      └── [should_retrieve == False] ──────┤
        │                                            │
        └── Node 5: app.graph.nodes: generate_response_node ◄───┘
               └── app.services.llm: get_response_llm()
        │
        ▼
[Return to app.api.chat: chat]
        │
        ├── 3. Persist Conversation
        │      ├── app.services.chat_history: save_message(role="user")
        │      └── app.services.chat_history: save_message(role="assistant")
        │
        ├── 4. Immediate HTTP Response Sent to User (ChatResponse)
        │
        ▼
[Asynchronous Background Task: update_memory_in_background]
        │
        ├── app.database.db: AsyncSessionLocal()
        └── app.memory.procedural_memory: update_procedural_memory()
               ├── LLM extraction (MEMORY_UPDATE_PROMPT | get_response_llm())
               ├── app.memory.procedural_memory: normalize_memory_output()
               └── Database Upsert into `procedural_memory` table
```

---

## 3. Step-by-Step Function Execution Guide

### Stage 1: Request Ingress & Security
1. **Endpoint Called:** Client sends a `POST /api/chat` request with JSON payload `{"message": "..."}` and `Authorization: Bearer <token>`.
2. **`get_current_user_id()`** (`app/auth/dependencies.py`):
   - Extracts the Bearer token from headers.
   - Calls **`verify_access_token()`** (`app/auth/jwt.py`) to validate the JWT signature, ensure it has not expired, and extract the `sub` (User ID).
3. **`get_db()`** (`app/database/db.py`):
   - Fast-API dependency yielding a scoped `AsyncSession` from `AsyncSessionLocal()`.

---

### Stage 2: Context Gathering & State Preparation
Before running the graph, the endpoint aggregates three critical pieces of context:
1. **`get_chat_history(db, user_id, limit=4)`** (`app/services/chat_history.py`):
   - Queries the `messages` table for the last 4 messages belonging to this user and orders them chronologically to preserve conversation flow.
2. **`get_procedural_memory(db, user_id)`** (`app/memory/procedural_memory.py`):
   - Fetches long-term instructions or preferences saved for this user (e.g., *"Prefers concise code without explanation"*). Returns an empty string if none exists.
3. **`load_cluster_centroids()`** (`app/rag/clustering.py`):
   - Loads the precomputed JSON mapping of KMeans centroid vectors (`cluster_id -> vector`) from disk (`data/chroma/cluster_centroids.json`).
4. **State Construction**:
   - Assembles `initial_state` matching the **`AgentState`** (`app/graph/state.py`) schema and calls `await agent_graph.ainvoke(initial_state)`.

---

### Stage 3: LangGraph Agent Workflow Execution

The compiled state graph (`app/graph/graph.py`) executes nodes sequentially and conditionally:

#### 1. `embed_query_node` (`app/graph/nodes.py`)
- Calls **`embed_text(query)`** (`app/services/embeddings.py`), using HuggingFace `all-MiniLM-L6-v2` on CPU to turn the query into a normalized 384-dimensional float vector.
- Updates state with `"query_embedding"`.

#### 2. `retrieval_gate_node` (`app/graph/nodes.py`)
- Calls **`should_retrieve(query_embedding, cluster_centroids)`** (`app/rag/gate.py`).
- **`calculate_cluster_similarities()`** computes cosine similarity between the query embedding and each cluster centroid.
- Finds the highest similarity score and checks whether `best_similarity >= settings.gate_threshold` (default 0.45).
- Updates state with:
  - `"should_retrieve"`: `True` or `False`
  - `"selected_cluster_id"`: integer ID of closest document cluster (or `None`)
  - `"gate_similarity"`: floating-point similarity score

#### 3. `retrieval_router(state)` (`app/graph/graph.py`)
- Conditional edge inspects `state["should_retrieve"]`:
  - **If `False`**: Routes immediately to `generate_response_node` (bypassing retrieval and filtering).
  - **If `True`**: Routes to `retrieve_node`.

#### 4. `retrieve_node` (`app/graph/nodes.py`) *(Only if `should_retrieve == True`)*
- Calls **`retrieve_from_cluster(query, cluster_id)`** (`app/rag/retrieval.py`).
- Calls **`similarity_search_with_score()`** (`app/services/vector_store.py`) with Chroma filter `{"cluster_id": cluster_id}`.
- Filters out chunks whose distance exceeds `settings.vector_threshold` (0.50).
- Updates state with `"retrieved_documents"`.

#### 5. `filter_context_node` (`app/graph/nodes.py`) *(Only if `should_retrieve == True`)*
- If no documents retrieved: sets `"filtered_context": ""`.
- **Fast Path:** If only 1 document chunk was retrieved, passes `documents[0].page_content` directly, skipping an extra LLM call.
- If multiple chunks: formats `CONTEXT_FILTER_PROMPT` (`app/rag/prompts.py`) and invokes **`get_filter_llm()`** (`app/services/llm.py`, Groq `llama-3.3-70b-versatile` with `temperature=0.0`) to extract only the facts needed to answer the query.
- Updates state with `"filtered_context"`.

#### 6. `generate_response_node` (`app/graph/nodes.py`)
- Invoked regardless of whether retrieval happened.
- Formats `FINAL_ANSWER_PROMPT` (`app/rag/prompts.py`) injecting:
  - `query`: User's input question.
  - `chat_history`: The last 4 conversation turns.
  - `procedural_memory`: Learned user preferences and instructions.
  - `context`: Filtered knowledge base chunks (or empty string if no retrieval).
- Invokes **`get_response_llm()`** (`app/services/llm.py`, Groq with `temperature=0.2`).
- Updates state with `"response"`.

---

### Stage 4: Response Dispatch & History Persistence
When the graph finishes:
1. The assistant response string is extracted from `result["response"]`.
2. **`save_message(db, user_id, "user", message)`** and **`save_message(db, user_id, "assistant", response)`** (`app/services/chat_history.py`) write both turns to the SQLite database.
3. **`background_tasks.add_task(update_memory_in_background, ...)`** registers the background task with FastAPI.
4. The HTTP 200 response (`ChatResponse`) is returned to the user **immediately**.

---

### Stage 5: Non-Blocking Procedural Memory Update
Runs asynchronously after the HTTP response has already completed:
1. **`update_memory_in_background(user_id, user_message, assistant_response)`** (`app/api/chat.py`):
   - Opens a **new** database session using `AsyncSessionLocal()` (because the request's original DB session has already closed).
2. Calls **`update_procedural_memory()`** (`app/memory/procedural_memory.py`):
   - Fetches existing procedural memory string for this user.
   - Executes `MEMORY_UPDATE_PROMPT | get_response_llm()` to check if the recent exchange contains any new stable preferences, formatting requirements, or guidelines.
   - Calls **`normalize_memory_output()`** to strip meta-labels and handle fallback keywords (like `"unchanged"` or `"none"`).
   - Performs a database upsert: adds a new `ProceduralMemory` record if first interaction, otherwise updates `memory.memory` in place.
   - Commits the transaction.
