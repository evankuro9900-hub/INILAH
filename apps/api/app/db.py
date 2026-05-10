"""Database setup — SQLAlchemy async + SQLite."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class untuk semua ORM models."""

    pass


# Pastikan parent dir untuk SQLite ada
settings.db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Buat semua tables — dipanggil saat startup."""
    # Import models supaya terdaftar ke Base.metadata
    from app.models import (  # noqa: F401
        bankroll,
        fetch_job,
        fixture,
        league,
        odds_snapshot,
        pick,
        team_stats_snapshot,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
