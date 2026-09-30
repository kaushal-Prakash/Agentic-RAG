from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate

from app.database.models import ProceduralMemory
from app.services.llm import get_response_llm

MEMORY_UPDATE_PROMPT = """
You maintain procedural memory for a user interacting with an AI assistant.

Existing procedural memory:
{existing_memory}

Recent user message:
{user_message}

Assistant response:
{assistant_response}

Update the procedural memory only when the conversation reveals a
stable preference, working style, recurring requirement, or useful
instruction about how the assistant should respond to this user.

Do not store temporary facts.
Do not store sensitive personal information.
Do not store the conversation itself.

Return ONLY the complete updated procedural memory.

If there is nothing useful to add:
- Return the existing procedural memory exactly as it is.
- If the existing procedural memory is empty, return an empty response.

Do not return labels such as:
"Existing procedural memory:"
"Updated procedural memory:"
"Memory:"
"Unchanged"

Keep the memory concise.
"""

def normalize_memory_output(
    updated_memory: str,
    existing_memory: str,
) -> str:
    updated_memory = updated_memory.strip()
    existing_memory = existing_memory.strip()
    if not updated_memory:
        return existing_memory
    prefixes = [
        "Existing procedural memory:",
        "Updated procedural memory:",
        "Procedural memory:",
        "Memory:",
    ]
    for prefix in prefixes:
        if updated_memory.lower().startswith(prefix.lower()):
            updated_memory = updated_memory[len(prefix):].strip()
    unchanged_values = {
        "unchanged",
        "(unchanged)",
        "no change",
        "no changes",
        "none",
        "n/a",
    }
    if updated_memory.lower() in unchanged_values:
        return existing_memory
    if not updated_memory:
        return existing_memory
    return updated_memory

async def get_procedural_memory(
    db: AsyncSession,
    user_id: int,
) -> str:
    result = await db.execute(
        select(ProceduralMemory).where(
            ProceduralMemory.user_id == user_id
        )
    )
    memory = result.scalar_one_or_none()
    if memory is None:
        return ""
    return memory.memory

async def update_procedural_memory(
    db: AsyncSession,
    user_id: int,
    user_message: str,
    assistant_response: str,
) -> str:
    existing_memory = await get_procedural_memory(
        db=db,
        user_id=user_id,
    )
    prompt = ChatPromptTemplate.from_template(
        MEMORY_UPDATE_PROMPT
    )
    chain = prompt | get_response_llm()
    result = await chain.ainvoke(
        {
            "existing_memory": existing_memory,
            "user_message": user_message,
            "assistant_response": assistant_response,
        }
    )
    updated_memory = normalize_memory_output(
        updated_memory=result.content,
        existing_memory=existing_memory,
    )
    query = await db.execute(
        select(ProceduralMemory).where(
            ProceduralMemory.user_id == user_id
        )
    )
    memory = query.scalar_one_or_none()
    if memory is None:
        memory = ProceduralMemory(
            user_id=user_id,
            memory=updated_memory,
        )
        db.add(memory)
    else:
        memory.memory = updated_memory
    await db.commit()
    return updated_memory