"""SQLAlchemy async engine and transactional session boundary."""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Owns database connections and exposes readiness and session operations."""

    def __init__(self, url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            url, pool_pre_ping=True, pool_recycle=1800, hide_parameters=True
        )
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def healthy(self) -> bool:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._engine.dispose()
