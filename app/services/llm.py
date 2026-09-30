from langchain_groq import ChatGroq
from app.config import settings

def get_llm(
    temperature: float = 0.0,
) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=temperature,
    )

def get_filter_llm() -> ChatGroq:
    return get_llm(temperature=0.0)

def get_response_llm() -> ChatGroq:
    return get_llm(temperature=0.2)