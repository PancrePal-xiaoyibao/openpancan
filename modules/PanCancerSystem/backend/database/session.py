"""SQLAlchemy session management with async SQLite support."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session.

    Usage as FastAPI dependency:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create all database tables."""
    from backend.database.models import Base  # noqa: F811

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
