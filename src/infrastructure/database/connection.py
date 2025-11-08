"""
Database connection and session management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings
from src.infrastructure.database.models import Base
from src.shared.exceptions import DatabaseError
from src.shared.logging import LoggerMixin


class DatabaseManager(LoggerMixin):
    """
    Manages database connections and sessions.

    Provides async session management for PostgreSQL using SQLAlchemy.
    """

    def __init__(self) -> None:
        """Initialize database manager with configuration."""
        settings = get_settings()

        # Convert sync URL to async
        database_url = settings.postgres.database_url
        async_database_url = database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        self.engine: AsyncEngine = create_async_engine(
            async_database_url,
            echo=settings.postgres.postgres_echo,
            pool_size=settings.postgres.postgres_pool_size,
            max_overflow=settings.postgres.postgres_max_overflow,
            pool_pre_ping=True,
        )

        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.logger.info(
            "database_manager_initialized",
            host=settings.postgres.postgres_host,
            database=settings.postgres.postgres_db,
        )

    async def create_tables(self) -> None:
        """
        Create all database tables.

        This should only be used in development or for initial setup.
        In production, use Alembic migrations.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.logger.info("database_tables_created")

        except Exception as e:
            self.logger.error("table_creation_failed", error=str(e))
            raise DatabaseError(
                f"Failed to create database tables: {str(e)}"
            ) from e

    async def drop_tables(self) -> None:
        """
        Drop all database tables.

        WARNING: This is destructive and should only be used in development/testing.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            self.logger.warning("database_tables_dropped")

        except Exception as e:
            self.logger.error("table_drop_failed", error=str(e))
            raise DatabaseError(
                f"Failed to drop database tables: {str(e)}"
            ) from e

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session using async context manager.

        Example:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error("session_error", error=str(e))
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database engine and all connections."""
        await self.engine.dispose()
        self.logger.info("database_manager_closed")

    async def __aenter__(self) -> "DatabaseManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database session.

    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
