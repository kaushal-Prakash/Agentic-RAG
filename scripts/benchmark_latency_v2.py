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
LANGSMITH_PROJECT = "agentic_rag_tracing"

TOTAL_QUESTIONS = 60

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
    "What time does customer support open?",
    "What time does customer support close?",
    "Does the company provide support on Saturdays?",
    "Does the company provide support on Sundays?",
    "What are the company's customer service hours?",
    "When can I contact the support team?",
    "What days is customer support available?",
    "Are support services available during weekdays?",
    "Can I contact support outside business hours?",
    "Is customer support available 24 hours a day?",
    "How can I submit a support request?",
    "Where can I raise a support ticket?",
    "Can I contact support by email?",
    "Can I contact the company through the customer portal?",
    "Does the customer portal allow support requests?",
    "How do I submit a customer support ticket?",
    "Where should I go for technical support?",
    "How can I get help from the company?",
    "What is the best way to contact customer support?",
    "What channels are available for customer support?",
    "Does the company offer online customer support?",
    "How do enterprise customers get support?",
    "Do enterprise customers have special support services?",
    "Is priority support available for enterprise customers?",
    "What support benefits do enterprise customers receive?",
    "Are enterprise customers given priority assistance?",
    "Does the company prioritize enterprise support requests?",
    "Can enterprise customers contact support directly?",
    "What happens if I contact support after business hours?",
    "Will support requests submitted after hours be answered?",
    "Can I submit a support request outside working hours?",
    "When will an after-hours support request be handled?",
    "Does the company respond to support requests on weekends?",
    "How long are the company's support hours?",
    "What is the support team's working schedule?",
    "What are the operating hours for customer service?",
    "When is the support team available to customers?",
    "What hours can customers receive assistance?",
    "How can I get assistance from the support team?",
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
    "What is the smallest planet in our solar system?",
    "What is the closest planet to the Sun?",
    "What is the hottest planet in our solar system?",
    "How many planets are in the solar system?",
    "What is Earth's natural satellite?",
    "What is the largest continent?",
    "What is the smallest continent?",
    "What is the longest river in the world?",
    "What is the largest desert in the world?",
    "What is the highest mountain in the world?",
    "Who painted the Mona Lisa?",
    "Who wrote Hamlet?",
    "Who wrote The Odyssey?",
    "Who discovered penicillin?",
    "Who developed the theory of relativity?",
    "What is the chemical symbol for oxygen?",
    "What is the chemical symbol for silver?",
    "What is the chemical symbol for iron?",
    "What is the freezing point of water?",
    "How many elements are currently in the periodic table?",
    "How many days are in a normal year?",
    "How many hours are in one day?",
    "How many minutes are in one hour?",
    "How many seconds are in one minute?",
    "What is the largest mammal on Earth?",
    "What is the fastest land animal?",
    "What is the largest bird in the world?",
    "What gas do humans need to breathe?",
    "What gas do plants absorb during photosynthesis?",
    "What is the human body's largest organ?",
    "How many bones are in the adult human body?",
    "What is the primary source of energy for Earth?",
    "What is gravity?",
    "What is electricity?",
    "What is the boiling point of water in Celsius?",
    "What is the approximate age of Earth?",
    "How many sides does a hexagon have?",
    "What is the square root of 144?",
    "What is the largest ocean by area?",
    "What is the capital of Japan?",
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
    print("Pause between questions: 60 seconds")
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
                    f"FAILED | "
                    f"{question} | "
                    f"{exc}"
                )

            # Wait 60 seconds before the next request.
            # The final request does not need a pause.
            if index < len(questions):
                print("Waiting 60 seconds before the next question...")
                await asyncio.sleep(60)

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