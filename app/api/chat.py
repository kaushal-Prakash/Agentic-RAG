from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_id
from app.database.db import AsyncSessionLocal, get_db
from app.graph.graph import agent_graph
from app.memory.procedural_memory import (
    get_procedural_memory,
    update_procedural_memory,
)
from app.services.chat_history import (
    get_chat_history,
    save_message,
)
from app.rag.clustering import load_cluster_centroids

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

async def update_memory_in_background(
    user_id: int,
    user_message: str,
    assistant_response: str,
) -> None:
    """
    Update procedural memory using a separate database session.

    This runs in the background after the chat response has been sent,
    so the user does not wait for the procedural-memory LLM call.
    """
    async with AsyncSessionLocal() as db:
        try:
            await update_procedural_memory(
                db=db,
                user_id=user_id,
                user_message=user_message,
                assistant_response=assistant_response,
            )
        except Exception as exc:
            print(f"Procedural memory update failed: {exc}")

@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    chat_history = await get_chat_history(
        db=db,
        user_id=user_id,
        limit=4,
    )
    procedural_memory = await get_procedural_memory(
        db=db,
        user_id=user_id,
    )
    cluster_centroids = load_cluster_centroids()
    initial_state = {
        "user_id": user_id,
        "query": data.message,
        "cluster_centroids": cluster_centroids,
        "chat_history": chat_history,
        "procedural_memory": procedural_memory,
    }
    result = await agent_graph.ainvoke(
        initial_state
    )
    response = result["response"]
    await save_message(
        db=db,
        user_id=user_id,
        role="user",
        content=data.message,
    )
    await save_message(
        db=db,
        user_id=user_id,
        role="assistant",
        content=response,
    )
    background_tasks.add_task(
        update_memory_in_background,
        user_id,
        data.message,
        response,
    )
    return ChatResponse(
        response=response
    )