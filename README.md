# Agentic RAG with Procedural Memory

An end-to-end Agentic RAG system designed to provide context-aware responses from a company knowledge base while maintaining user-specific procedural memory. The system uses a Retrieval Gate to decide whether retrieval is required, followed by cluster-based retrieval, vector similarity search, LLM-based context filtering, and final response generation. The application is built with FastAPI and LangGraph, uses Chroma for vector storage and SQLite for user data and memory, and is deployed using Docker on AWS EC2.

---

## Table of Contents

- [Project Overview](#project-overview)
- [How This Differs from Normal RAG](#how-this-differs-from-normal-rag)
- [Tools and Technologies](#tools-and-technologies)
- [Project Structure](#project-structure)
- [LangSmith Observability](#langsmith-observability)
- [JMeter Load Testing](#jmeter-load-testing)
- [Deployment](#deployment)
- [License](#license)
- [Contact](#contact)

---

## Project Overview

This project implements an **Agentic Retrieval-Augmented Generation (RAG)** system with **procedural memory**. Instead of retrieving documents for every query, the system first determines whether retrieval is necessary. When retrieval is required, the query is routed through document clusters and vector search before relevant context is filtered by an LLM and passed to the final response model. User-specific procedural memory and recent conversation history are also incorporated into the workflow to provide more personalized and context-aware responses.

---

## How This Differs from Normal RAG

A traditional RAG pipeline generally follows:

```text
User Query
    ↓
Embedding
    ↓
Vector Search
    ↓
Retrieved Context
    ↓
LLM
    ↓
Response
```

This project introduces additional decision-making and memory:

```text
User Query
    ↓
Retrieval Gate
    │
    ├── No Retrieval ──→ LLM
    │
    └── Retrieval
          ↓
      Cluster Search
          ↓
      Vector Search
          ↓
      LLM Context Filtering
          ↓
      Final LLM
          ↓
      Response
          ↓
  Procedural Memory Update
```

### Key Differences

- **Retrieval Gate** – decides whether retrieval is actually required.
- **Cluster-based Retrieval** – narrows the search space before vector search.
- **LLM Context Filtering** – filters retrieved information before final generation.
- **Procedural Memory** – maintains user-specific information across conversations.
- **LangGraph Orchestration** – manages the multi-step agentic workflow.
- **Observability** – LangSmith tracks the complete execution pipeline.

---

## Tools and Technologies

| Category            | Technology                     |
|----------------------|--------------------------------|
| Backend              | FastAPI                        |
| Language             | Python                         |
| LLM Framework        | LangChain                      |
| Agent Orchestration  | LangGraph                      |
| LLM Provider         | Groq                           |
| Embeddings           | HuggingFace `all-MiniLM-L6-v2` |
| Vector Database      | Chroma                         |
| Database             | SQLite                         |
| Authentication       | JWT + bcrypt                   |
| Frontend             | HTML, CSS, JavaScript          |
| Containerization     | Docker                         |
| Cloud Deployment     | AWS EC2                        |
| Observability        | LangSmith                      |
| Load Testing         | Apache JMeter                  |

---

## Project Structure

```text
Agentic-RAG/
│
├── app/
│   ├── api/                  # API routes
│   ├── auth/                 # JWT authentication
│   ├── database/             # SQLite models and database
│   ├── graph/                # LangGraph workflow
│   ├── memory/                # Procedural memory
│   ├── rag/                  # Ingestion, clustering and retrieval
│   ├── services/              # LLM, embeddings, vector store, tracing
│   ├── config.py
│   └── main.py
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── login.html
│   ├── register.html
│   └── chat.html
│
├── scripts/
│   └── benchmark_latency.py
│
├── data/
│   ├── documents/
│   ├── chroma/
│   └── app.db
│
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## LangSmith Observability

LangSmith is used to trace and monitor the application's LangGraph and LLM execution.

### Tracked Metrics

- LLM latency
- End-to-end request latency
- Token usage
- Retrieval frequency
- Retrieval Gate decisions
- Errors
- P50 latency
- P95 latency

### Application Benchmark

A 60-question benchmark was performed using both company-specific and general questions.

| Metric         |   Value |
|----------------|--------:|
| Total Requests |      60 |
| Successful     |      59 |
| Failed         |       1 |
| Success Rate   |  98.33% |
| Mean Latency   | 0.964 s |
| P50 Latency    | 0.649 s |
| P95 Latency    | 1.793 s |
| Min Latency    | 0.253 s |
| Max Latency    | 2.450 s |

LangSmith benchmark project:

```text
agentic_rag_tracing
```

---

## JMeter Load Testing

Apache JMeter was used to test the deployed application running on AWS EC2.

### Test Configuration

```text
Concurrent Users : 5
Loops per User   : 6
Total Requests   : 30
```

### Results

| Metric         |       Value |
|----------------|------------:|
| Total Requests |          30 |
| Successful     |          29 |
| Failed         |           1 |
| Success Rate   |      96.67% |
| Median Latency |     0.921 s |
| P95 Latency    |     6.501 s |
| Throughput     | 1.139 req/s |

During the load test, the external Groq API reached its **8,000 tokens-per-minute limit**, resulting in provider-side rate-limit errors. The observed failed request was therefore associated with the external LLM provider limit rather than a demonstrated failure of the RAG retrieval pipeline.

---

## Deployment

The application is containerized using Docker and deployed on AWS EC2.

```text
User
 ↓
Frontend
 ↓
FastAPI
 ↓
LangGraph
 ↓
Agentic RAG Pipeline
 ↓
Groq LLM
```

### Running with Docker

#### 1. Prepare Environment Variables
Ensure a `.env` file exists in the project root containing your API keys and configuration:

```env
GROQ_API_KEY=your_groq_api_key
JWT_SECRET_KEY=your_secret_key
```

#### 2. Build the Docker Image
```bash
docker build -t agentic-rag .
```

#### 3. Run the Container

**Linux / macOS / PowerShell:**
```bash
docker run -d \
  --name agentic-rag-app \
  -p 8000:8000 \
  --env-file .env \
  -v ${PWD}/data:/project/data \
  agentic-rag
```

**Windows (Command Prompt):**
```cmd
docker run -d --name agentic-rag-app -p 8000:8000 --env-file .env -v "%cd%/data:/project/data" agentic-rag
```

> **Note:** Mounting the `./data` directory ensures that SQLite database records (`app.db`) and Chroma vector store embeddings persist across container restarts.

#### 4. Verify Application
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- API documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

#### 5. Stop the Container
```bash
docker stop agentic-rag-app
docker rm agentic-rag-app
```

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.