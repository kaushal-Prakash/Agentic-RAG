import asyncio
import os
import random
import statistics
import time

import httpx
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

API_BASE_URL = "http://127.0.0.1:8000"
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "tracing")

TOTAL_QUESTIONS = 100
USERNAME = "benchmark_user"
PASSWORD = "BenchmarkPassword123!"
NAME = "Benchmark User"


COMPANY_QUESTIONS = [
    "What are the standard support hours?",
    "When is customer support available?",
    "How can customers contact support?",
    "How do I contact the support team?",
    "Do enterprise customers receive priority support?",
    "What support hours does the company provide?",
    "Is support available on weekends?",
    "What are the company's support timings?",
    "Can customers contact support through the customer portal?",
    "How can I reach customer support?",
]

GENERAL_QUESTIONS = [
    "What is the capital of India?",
    "What is the largest planet in our solar system?",
    "Who wrote Romeo and Juliet?",
    "What is the chemical symbol for gold?",
    "How many continents are there?",
    "What is the boiling point of water at sea level?",
    "What is the largest ocean on Earth?",
    "What is photosynthesis?",
    "How many days are there in a leap year?",
    "What is the speed of light approximately?",
]


def generate_questions(count: int) -> list[str]:
    questions = []

    for _ in range(count // 2):
        questions.append(random.choice(COMPANY_QUESTIONS))
        questions.append(random.choice(GENERAL_QUESTIONS))

    random.shuffle(questions)

    return questions[:count]


def percentile(values: list[float], percentile_value: float) -> float:
    sorted_values = sorted(values)

    index = (len(sorted_values) - 1) * percentile_value / 100

    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)

    weight = index - lower

    return (
        sorted_values[lower]
        + (sorted_values[upper] - sorted_values[lower]) * weight
    )


async def register_or_login(client: httpx.AsyncClient) -> str:
    register_response = await client.post(
        f"{API_BASE_URL}/api/auth/register",
        json={
            "name": NAME,
            "username": USERNAME,
            "password": PASSWORD,
        },
    )

    if register_response.status_code == 200:
        return register_response.json()["access_token"]

    login_response = await client.post(
        f"{API_BASE_URL}/api/auth/login",
        json={
            "username": USERNAME,
            "password": PASSWORD,
        },
    )

    login_response.raise_for_status()

    return login_response.json()["access_token"]


@traceable(
    name="benchmark_chat_request",
    project_name=LANGSMITH_PROJECT,
)
async def send_question(
    client: httpx.AsyncClient,
    token: str,
    question: str,
) -> dict:
    start = time.perf_counter()

    response = await client.post(
        f"{API_BASE_URL}/api/chat",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "message": question,
        },
    )

    elapsed = time.perf_counter() - start

    response.raise_for_status()

    return {
        "question": question,
        "latency": elapsed,
        "response": response.json()["response"],
    }


async def main() -> None:
    questions = generate_questions(TOTAL_QUESTIONS)

    print("=" * 60)
    print("Agentic RAG Latency Benchmark")
    print("=" * 60)
    print(f"Questions: {TOTAL_QUESTIONS}")
    print(f"LangSmith project: {LANGSMITH_PROJECT}")
    print()

    async with httpx.AsyncClient(timeout=120.0) as client:
        token = await register_or_login(client)

        print("Authentication successful.")
        print("Starting benchmark...")
        print()

        results = []

        for index, question in enumerate(questions, start=1):
            try:
                result = await send_question(
                    client=client,
                    token=token,
                    question=question,
                )

                results.append(result)

                print(
                    f"[{index:03d}/{TOTAL_QUESTIONS}] "
                    f"{result['latency']:.3f}s | "
                    f"{question}"
                )

            except Exception as exc:
                print(
                    f"[{index:03d}/{TOTAL_QUESTIONS}] "
                    f"FAILED | {question} | {exc}"
                )

    if not results:
        print("\nNo successful requests.")
        return

    latencies = [result["latency"] for result in results]

    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)

    print()
    print("=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Successful requests : {len(results)}")
    print(f"Failed requests     : {TOTAL_QUESTIONS - len(results)}")
    print(f"Minimum latency     : {min(latencies):.3f}s")
    print(f"Maximum latency     : {max(latencies):.3f}s")
    print(f"Mean latency        : {statistics.mean(latencies):.3f}s")
    print(f"Median / P50        : {p50:.3f}s")
    print(f"P95 latency         : {p95:.3f}s")
    print("=" * 60)

    print()
    print(
        "LangSmith traces are being recorded in project: "
        f"{LANGSMITH_PROJECT}"
    )


if __name__ == "__main__":
    asyncio.run(main())