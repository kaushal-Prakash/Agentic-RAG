from pathlib import Path

PROJECT_NAME = ""

PROJECT_DIRS = [
    "app",
    "app/api",
    "app/auth",
    "app/database",
    "app/memory",
    "app/rag",
    "app/graph",
    "app/services",
    "frontend",
    "frontend/css",
    "frontend/js",
    "data",
    "data/documents",
    "data/chroma",
    "tests",
    "scripts"
]

PROJECT_FILES = [
    "requirements.txt",
    ".env",
    ".gitignore",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "app/main.py",
    "app/config.py",
    "app/api/auth.py",
    "app/api/chat.py",
    "app/auth/jwt.py",
    "app/auth/dependencies.py",
    "app/database/db.py",
    "app/database/models.py",
    "app/memory/procedural_memory.py",
    "app/rag/ingestion.py",
    "app/rag/retrieval.py",
    "app/rag/gate.py",
    "app/rag/prompts.py",
    "app/graph/state.py",
    "app/graph/nodes.py",
    "app/graph/graph.py",
    "app/services/llm.py",
    "app/services/embeddings.py",
    "app/services/vector_store.py",
    "app/services/langsmith.py",
    "app/services/chat_history.py",
    "frontend/login.html",
    "frontend/register.html",
    "frontend/chat.html",
    "frontend/css/auth.css",
    "frontend/css/chat.css",
    "frontend/js/login.js",
    "frontend/js/register.js",
    "frontend/js/chat.js",
    "tests/test_auth.py",
    "tests/test_rag.py",
    "tests/test_memory.py",
    "tests/test_chat_history.py",
    "tests/test_api_auth.py",
    "tests/test_api_chat.py",
    "scripts/benchmark_latency.py"
]

def create_project():
    root = Path.cwd() / PROJECT_NAME
    root.mkdir(parents=True, exist_ok=True)

    for directory in PROJECT_DIRS:
        path = root / directory
        path.mkdir(parents=True, exist_ok=True)

    for file in PROJECT_FILES:
        path = root / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    print(f"Project created at: {root}")

if __name__ == "__main__":
    create_project()