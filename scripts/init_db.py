"""
Database initialization script.

This script initializes all databases and creates necessary collections/tables.
Run this after setting up the environment and before starting the application.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.infrastructure.database.connection import get_db_manager
from src.infrastructure.graph_db.neo4j_client import Neo4jClientWrapper
from src.infrastructure.vector_store.document_repository_impl import (
    QdrantDocumentRepository,
)
from src.infrastructure.vector_store.memory_repository_impl import QdrantMemoryRepository
from src.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def initialize_postgresql():
    """Initialize PostgreSQL database and create tables."""
    logger.info("Initializing PostgreSQL database...")

    try:
        db_manager = get_db_manager()
        await db_manager.create_tables()
        logger.info("PostgreSQL tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise


async def initialize_qdrant():
    """Initialize Qdrant collections."""
    logger.info("Initializing Qdrant collections...")

    try:
        # Initialize memory collection
        memory_repo = QdrantMemoryRepository()
        await memory_repo.initialize()
        logger.info("Qdrant memory collection initialized")

        # Initialize document collection
        document_repo = QdrantDocumentRepository()
        await document_repo.initialize()
        logger.info("Qdrant document collection initialized")

    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        raise


async def initialize_neo4j():
    """Initialize Neo4j constraints and indexes."""
    logger.info("Initializing Neo4j database...")

    try:
        async with Neo4jClientWrapper() as neo4j_client:
            await neo4j_client.verify_connectivity()
            await neo4j_client.create_constraints()
            logger.info("Neo4j constraints and indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
        raise


async def main():
    """Main initialization function."""
    settings = get_settings()

    logger.info(
        "Starting database initialization",
        environment=settings.app.environment,
    )

    try:
        # Initialize all databases
        await initialize_postgresql()
        await initialize_qdrant()
        await initialize_neo4j()

        logger.info("All databases initialized successfully!")
        logger.info("You can now start the application with: poetry run python -m src.main")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
