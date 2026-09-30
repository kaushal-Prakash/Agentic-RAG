import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.database.db import Base
from app.database.models import User
from app.services.chat_history import (
    get_chat_history,
    save_message,
)


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_save_and_get_chat_history(test_db):
    user = User(
        name="History User",
        username="history_user",
        password_hash="test_hash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    await save_message(
        db=test_db,
        user_id=user.id,
        role="user",
        content="Hello",
    )
    await save_message(
        db=test_db,
        user_id=user.id,
        role="assistant",
        content="Hello! How can I help?",
    )
    history = await get_chat_history(
        db=test_db,
        user_id=user.id,
    )
    assert "user: Hello" in history
    assert "assistant: Hello! How can I help?" in history


@pytest.mark.asyncio
async def test_chat_history_is_in_correct_order(test_db):
    user = User(
        name="Order User",
        username="order_user",
        password_hash="test_hash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    await save_message(
        db=test_db,
        user_id=user.id,
        role="user",
        content="First message",
    )
    await save_message(
        db=test_db,
        user_id=user.id,
        role="assistant",
        content="First response",
    )
    await save_message(
        db=test_db,
        user_id=user.id,
        role="user",
        content="Second message",
    )
    history = await get_chat_history(
        db=test_db,
        user_id=user.id,
    )
    first_position = history.index("First message")
    response_position = history.index("First response")
    second_position = history.index("Second message")
    assert first_position < response_position
    assert response_position < second_position


@pytest.mark.asyncio
async def test_chat_history_is_user_specific(test_db):
    user_1 = User(
        name="User One",
        username="history_user_one",
        password_hash="test_hash",
    )
    user_2 = User(
        name="User Two",
        username="history_user_two",
        password_hash="test_hash",
    )
    test_db.add_all([user_1, user_2])
    await test_db.commit()
    await test_db.refresh(user_1)
    await test_db.refresh(user_2)
    await save_message(
        db=test_db,
        user_id=user_1.id,
        role="user",
        content="Private message",
    )
    user_1_history = await get_chat_history(
        db=test_db,
        user_id=user_1.id,
    )
    user_2_history = await get_chat_history(
        db=test_db,
        user_id=user_2.id,
    )
    assert "Private message" in user_1_history
    assert "Private message" not in user_2_history