from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, hash_password, verify_password
from app.database.db import get_db
from app.database.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    username: str

@router.post("/register", response_model=AuthResponse)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),  # Injects request-scoped DB session
):
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    # Returns the single User object, None if not found, or errors if multiple
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = User(
        name=data.name,
        username=data.username,
        password_hash=hash_password(data.password),  # Hash password before persisting
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # Reloads instance to fetch generated fields (e.g., user.id)
    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        username=user.username,
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()
    # Combined check prevents username enumeration attacks
    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        username=user.username,
    )