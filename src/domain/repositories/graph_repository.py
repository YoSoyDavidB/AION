"""
Graph repository interface - Contract for knowledge graph operations.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.graph_entity import (
    EntitySearchResult,
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationType,
)


class IGraphRepository(ABC):
    """
    Interface for graph repository operations (Neo4j).

    This defines the contract for knowledge graph entity and relationship management.
    """

    # Entity operations

    @abstractmethod
    async def create_entity(self, entity: GraphEntity) -> GraphEntity:
        """
        Create a new entity in the graph.

        Args:
            entity: Entity to create

        Returns:
            Created entity

        Raises:
            GraphDatabaseError: If creation fails
        """
        pass

    @abstractmethod
    async def get_entity_by_id(self, entity_id: UUID) -> GraphEntity | None:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_entity_by_name(
        self, name: str, entity_type: EntityType | None = None
    ) -> GraphEntity | None:
        """
        Retrieve an entity by name.

        Args:
            name: Entity name
            entity_type: Filter by type (optional)

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_entity(self, entity: GraphEntity) -> GraphEntity:
        """
        Update an existing entity.

        Args:
            entity: Entity with updated fields

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        pass

    @abstractmethod
    async def delete_entity(self, entity_id: UUID) -> bool:
        """
        Delete an entity and all its relationships.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_entities_by_type(
        self, entity_type: EntityType, limit: int = 100
    ) -> list[GraphEntity]:
        """
        Get all entities of a specific type.

        Args:
            entity_type: Type to filter by
            limit: Maximum number of results

        Returns:
            List of entities
        """
        pass

    # Relationship operations

    @abstractmethod
    async def create_relationship(
        self, relationship: GraphRelationship
    ) -> GraphRelationship:
        """
        Create a relationship between two entities.

        Args:
            relationship: Relationship to create

        Returns:
            Created relationship

        Raises:
            GraphDatabaseError: If creation fails
            EntityNotFoundError: If source or target entity doesn't exist
        """
        pass

    @abstractmethod
    async def get_relationship_by_id(
        self, relationship_id: UUID
    ) -> GraphRelationship | None:
        """
        Retrieve a relationship by ID.

        Args:
            relationship_id: Relationship identifier

        Returns:
            Relationship if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_relationship(
        self, relationship: GraphRelationship
    ) -> GraphRelationship:
        """
        Update an existing relationship.

        Args:
            relationship: Relationship with updated fields

        Returns:
            Updated relationship

        Raises:
            EntityNotFoundError: If relationship doesn't exist
        """
        pass

    @abstractmethod
    async def delete_relationship(self, relationship_id: UUID) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: Relationship identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_entity_relationships(
        self,
        entity_id: UUID,
        relationship_type: RelationType | None = None,
        direction: str = "both",
    ) -> list[GraphRelationship]:
        """
        Get all relationships for an entity.

        Args:
            entity_id: Entity identifier
            relationship_type: Filter by type (optional)
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of relationships
        """
        pass

    @abstractmethod
    async def get_related_entities(
        self,
        entity_id: UUID,
        relationship_type: RelationType | None = None,
        max_depth: int = 1,
    ) -> list[GraphEntity]:
        """
        Get entities related to a given entity.

        Args:
            entity_id: Entity identifier
            relationship_type: Filter by relationship type (optional)
            max_depth: Maximum traversal depth

        Returns:
            List of related entities
        """
        pass

    # Search and query operations

    @abstractmethod
    async def search_entities(
        self,
        query: str,
        entity_type: EntityType | None = None,
        limit: int = 10,
    ) -> list[EntitySearchResult]:
        """
        Search for entities by text query.

        Args:
            query: Search query
            entity_type: Filter by type (optional)
            limit: Maximum number of results

        Returns:
            List of search results with relevance scores
        """
        pass

    @abstractmethod
    async def find_path(
        self,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 5,
        relationship_types: list[RelationType] | None = None,
    ) -> list[GraphRelationship] | None:
        """
        Find shortest path between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_depth: Maximum path length
            relationship_types: Filter by relationship types (optional)

        Returns:
            List of relationships forming the path, or None if no path exists
        """
        pass

    @abstractmethod
    async def get_entity_neighbors(
        self,
        entity_id: UUID,
        max_depth: int = 2,
    ) -> list[tuple[GraphEntity, int]]:
        """
        Get neighboring entities with their distance.

        Args:
            entity_id: Entity identifier
            max_depth: Maximum distance

        Returns:
            List of (Entity, distance) tuples
        """
        pass

    @abstractmethod
    async def count_entities(
        self, entity_type: EntityType | None = None
    ) -> int:
        """
        Count entities, optionally filtered by type.

        Args:
            entity_type: Filter by type (optional)

        Returns:
            Number of entities
        """
        pass

    @abstractmethod
    async def count_relationships(
        self, relationship_type: RelationType | None = None
    ) -> int:
        """
        Count relationships, optionally filtered by type.

        Args:
            relationship_type: Filter by type (optional)

        Returns:
            Number of relationships
        """
        pass

    # Bulk operations

    @abstractmethod
    async def bulk_create_entities(
        self, entities: list[GraphEntity]
    ) -> list[GraphEntity]:
        """
        Create multiple entities at once.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities
        """
        pass

    @abstractmethod
    async def bulk_create_relationships(
        self, relationships: list[GraphRelationship]
    ) -> list[GraphRelationship]:
        """
        Create multiple relationships at once.

        Args:
            relationships: List of relationships to create

        Returns:
            List of created relationships
        """
        pass
