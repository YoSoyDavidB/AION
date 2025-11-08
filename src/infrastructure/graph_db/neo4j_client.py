"""
Neo4j client wrapper for graph database operations.
"""

from typing import Any

from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import Neo4jError

from src.config.settings import get_settings
from src.shared.exceptions import GraphDatabaseError
from src.shared.logging import LoggerMixin


class Neo4jClientWrapper(LoggerMixin):
    """
    Wrapper around Neo4j driver for graph database operations.

    Provides high-level methods for common graph operations
    and handles connection management.
    """

    def __init__(self) -> None:
        """Initialize Neo4j client with configuration."""
        settings = get_settings()
        self.uri = settings.neo4j.neo4j_uri
        self.user = settings.neo4j.neo4j_user
        self.password = settings.neo4j.neo4j_password
        self.database = settings.neo4j.neo4j_database

        # Initialize async driver
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=settings.neo4j.neo4j_max_connection_lifetime,
            max_connection_pool_size=settings.neo4j.neo4j_max_connection_pool_size,
            connection_timeout=settings.neo4j.neo4j_connection_timeout,
        )

        self.logger.info(
            "neo4j_client_initialized",
            uri=self.uri,
            database=self.database,
        )

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        await self.driver.close()
        self.logger.info("neo4j_client_closed")

    async def __aenter__(self) -> "Neo4jClientWrapper":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def verify_connectivity(self) -> bool:
        """
        Verify connection to Neo4j database.

        Returns:
            True if connected successfully

        Raises:
            GraphDatabaseError: If connection fails
        """
        try:
            await self.driver.verify_connectivity()
            self.logger.info("neo4j_connectivity_verified")
            return True
        except Neo4jError as e:
            self.logger.error("neo4j_connection_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to connect to Neo4j: {str(e)}",
                details={"uri": self.uri},
            ) from e

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (optional, uses default)

        Returns:
            List of result records as dictionaries

        Raises:
            GraphDatabaseError: If query execution fails
        """
        parameters = parameters or {}
        database = database or self.database

        try:
            async with self.driver.session(database=database) as session:
                result = await session.run(query, parameters)
                records = await result.data()

                self.logger.debug(
                    "query_executed",
                    num_results=len(records),
                    query_preview=query[:100],
                )

                return records

        except Neo4jError as e:
            self.logger.error(
                "query_execution_failed",
                error=str(e),
                query=query[:200],
            )
            raise GraphDatabaseError(
                f"Failed to execute query: {str(e)}",
                details={"query": query[:200], "error": str(e)},
            ) from e

    async def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a write query (CREATE, UPDATE, DELETE).

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (optional)

        Returns:
            Query statistics

        Raises:
            GraphDatabaseError: If query execution fails
        """
        parameters = parameters or {}
        database = database or self.database

        try:
            async with self.driver.session(database=database) as session:
                result = await session.run(query, parameters)
                summary = await result.consume()

                stats = {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                }

                self.logger.debug(
                    "write_query_executed",
                    stats=stats,
                    query_preview=query[:100],
                )

                return stats

        except Neo4jError as e:
            self.logger.error(
                "write_query_failed",
                error=str(e),
                query=query[:200],
            )
            raise GraphDatabaseError(
                f"Failed to execute write query: {str(e)}",
                details={"query": query[:200], "error": str(e)},
            ) from e

    async def create_constraints(self) -> None:
        """
        Create necessary constraints and indexes.

        This ensures data integrity and query performance.
        """
        constraints = [
            # Unique constraint on entity ID
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
            "FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
            # Index on entity name for faster lookups
            "CREATE INDEX entity_name_idx IF NOT EXISTS "
            "FOR (e:Entity) ON (e.name)",
            # Index on entity type
            "CREATE INDEX entity_type_idx IF NOT EXISTS "
            "FOR (e:Entity) ON (e.entity_type)",
        ]

        try:
            for constraint in constraints:
                await self.execute_write(constraint)

            self.logger.info("neo4j_constraints_created")

        except Exception as e:
            self.logger.error("constraint_creation_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to create constraints: {str(e)}"
            ) from e

    async def clear_database(self) -> None:
        """
        Clear all nodes and relationships from the database.

        WARNING: This is destructive and should only be used in development/testing.
        """
        try:
            await self.execute_write("MATCH (n) DETACH DELETE n")
            self.logger.warning("neo4j_database_cleared")

        except Exception as e:
            self.logger.error("database_clear_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to clear database: {str(e)}"
            ) from e

    async def get_database_stats(self) -> dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with node and relationship counts
        """
        try:
            node_count_query = "MATCH (n) RETURN count(n) as count"
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as count"

            node_result = await self.execute_query(node_count_query)
            rel_result = await self.execute_query(rel_count_query)

            stats = {
                "nodes": node_result[0]["count"] if node_result else 0,
                "relationships": rel_result[0]["count"] if rel_result else 0,
            }

            return stats

        except Exception as e:
            self.logger.error("get_stats_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to get database stats: {str(e)}"
            ) from e
