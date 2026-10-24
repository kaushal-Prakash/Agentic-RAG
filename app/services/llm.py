from langchain_groq import ChatGroq
from app.config import settings

# Factory for ChatGroq instances configured with model and API key from settings
def get_llm(
    temperature: float = 0.0,
) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=temperature,
    )

# temperature=0.0: deterministic and strict for document filtering without hallucinations
def get_filter_llm() -> ChatGroq:
    return get_llm(temperature=0.0)

# temperature=0.2: slightly warmer for fluent, natural phrasing while staying factual
def get_response_llm() -> ChatGroq:
    return get_llm(temperature=0.2)