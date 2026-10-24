from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Database engine: echo enables SQL query logging during debug mode
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# Async session factory:
# expire_on_commit=False prevents SQLAlchemy from expiring object attributes after commit.
# In async code, accessing expired attributes would trigger synchronous lazy loading and fail (MissingGreenlet error).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# DeclarativeBase is the modern SQLAlchemy 2.0 base class for ORM models
class Base(DeclarativeBase):
    pass

# FastAPI dependency generator: provides a scoped database session per request
# and automatically closes/cleans up the session when the request finishes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Schema initialization:
# Base.metadata.create_all is a synchronous method, so connection.run_sync is used
# to safely execute synchronous DDL commands inside an async connection
async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

# Application shutdown hook: gracefully closes all connection pool sockets
async def close_db():
    await engine.dispose()