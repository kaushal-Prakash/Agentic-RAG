import sys
from unittest.mock import MagicMock, AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

mock_embeddings = MagicMock()
mock_embedding_module = MagicMock()
mock_embedding_module.HuggingFaceEmbeddings.return_value = mock_embeddings
sys.modules["langchain_community.embeddings"] = mock_embedding_module

from app.auth.jwt import create_access_token
from app.database.db import Base, get_db
from app.database.models import User
from app.main import app


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


@pytest_asyncio.fixture
async def client(test_db):
    async def override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db):
    user = User(
        name="Chat Test User",
        username="chat_test_user",
        password_hash="test_hash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_chat_requires_authentication(client):
    response = await client.post(
        "/api/chat",
        json={
            "message": "Hello",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_rejects_invalid_token(client):
    response = await client.post(
        "/api/chat",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "message": "Hello",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_authenticated_chat(client, test_user, monkeypatch):
    token = create_access_token(test_user.id)
    mock_graph_result = {
        "response": "This is a test response.",
    }
    mock_ainvoke = AsyncMock(
        return_value=mock_graph_result
    )
    monkeypatch.setattr(
        "app.api.chat.agent_graph.ainvoke",
        mock_ainvoke,
    )
    response = await client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "message": "Hello",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "This is a test response."
    mock_ainvoke.assert_awaited_once()