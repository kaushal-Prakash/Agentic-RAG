import sys
from unittest.mock import MagicMock

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

from app.database.db import Base
from app.database.db import get_db
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


@pytest.mark.asyncio
async def test_register_endpoint(client):
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "API Test User",
            "username": "api_register_user",
            "password": "Test@12345",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["name"] == "API Test User"
    assert data["username"] == "api_register_user"
    assert isinstance(data["user_id"], int)


@pytest.mark.asyncio
async def test_login_endpoint(client):
    username = "api_login_user"
    password = "Test@12345"
    register_response = await client.post(
        "/api/auth/register",
        json={
            "name": "Login Test User",
            "username": username,
            "password": password,
        },
    )
    assert register_response.status_code == 200
    login_response = await client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == username


@pytest.mark.asyncio
async def test_login_with_wrong_password(client):
    username = "wrong_password_user"
    register_response = await client.post(
        "/api/auth/register",
        json={
            "name": "Wrong Password User",
            "username": username,
            "password": "Correct@12345",
        },
    )
    assert register_response.status_code == 200
    response = await client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": "Wrong@12345",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_duplicate_username(client):
    username = "duplicate_user"
    first_response = await client.post(
        "/api/auth/register",
        json={
            "name": "First User",
            "username": username,
            "password": "Test@12345",
        },
    )
    second_response = await client.post(
        "/api/auth/register",
        json={
            "name": "Second User",
            "username": username,
            "password": "Test@12345",
        },
    )
    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Username already exists"