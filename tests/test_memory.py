import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.database.db import Base
from app.database.models import User, ProceduralMemory
from app.memory.procedural_memory import get_procedural_memory


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
async def test_procedural_memory_empty_for_new_user(test_db):
    user = User(
        name="Test User",
        username="memory_test_user",
        password_hash="test_hash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    memory = await get_procedural_memory(
        db=test_db,
        user_id=user.id,
    )
    assert memory == ""


@pytest.mark.asyncio
async def test_get_procedural_memory(test_db):
    user = User(
        name="Test User",
        username="memory_test_user_2",
        password_hash="test_hash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    procedural_memory = ProceduralMemory(
        user_id=user.id,
        memory="Explain technical concepts step by step.",
    )
    test_db.add(procedural_memory)
    await test_db.commit()
    memory = await get_procedural_memory(
        db=test_db,
        user_id=user.id,
    )
    assert memory == "Explain technical concepts step by step."


@pytest.mark.asyncio
async def test_memory_is_user_specific(test_db):
    user_1 = User(
        name="User One",
        username="memory_user_one",
        password_hash="test_hash",
    )
    user_2 = User(
        name="User Two",
        username="memory_user_two",
        password_hash="test_hash",
    )
    test_db.add_all([user_1, user_2])
    await test_db.commit()
    await test_db.refresh(user_1)
    await test_db.refresh(user_2)
    memory = ProceduralMemory(
        user_id=user_1.id,
        memory="User one preference.",
    )
    test_db.add(memory)
    await test_db.commit()
    user_1_memory = await get_procedural_memory(
        db=test_db,
        user_id=user_1.id,
    )
    user_2_memory = await get_procedural_memory(
        db=test_db,
        user_id=user_2.id,
    )
    assert user_1_memory == "User one preference."
    assert user_2_memory == ""