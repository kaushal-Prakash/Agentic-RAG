from sqlalchemy import select
from app.database.models import Message

async def save_message(
    db,
    user_id: int,
    role: str,
    content: str,
) -> None:
    message = Message(
        user_id=user_id,
        role=role,
        content=content,
    )

    db.add(message)
    await db.commit()

async def get_chat_history(
    db,
    user_id: int,
    limit: int = 10,
) -> str:
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(
            Message.created_at.desc(),
            Message.id.desc(),
        )
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return "\n".join(
        f"{message.role}: {message.content}"
        for message in messages
    )