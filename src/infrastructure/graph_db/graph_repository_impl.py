"""
Neo4j implementation of Graph repository.
"""

from uuid import UUID

from src.domain.entities.graph_entity import (
    EntitySearchResult,
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationType,
)
from src.domain.repositories.graph_repository import IGraphRepository
from src.infrastructure.graph_db.neo4j_client import Neo4jClientWrapper
from src.shared.exceptions import EntityNotFoundError, GraphDatabaseError
from src.shared.logging import LoggerMixin


class Neo4jGraphRepository(IGraphRepository, LoggerMixin):
    """
    Neo4j implementation of Graph repository.

    Stores entities and relationships in a Neo4j graph database.
    """

    def __init__(self, neo4j_client: Neo4jClientWrapper | None = None) -> None:
        """
        Initialize repository.

        Args:
            neo4j_client: Neo4j client instance (optional)
        """
        self.client = neo4j_client or Neo4jClientWrapper()
        self.logger.info("graph_repository_initialized")

    async def initialize(self) -> None:
        """Initialize database constraints and indexes."""
        await self.client.verify_connectivity()
        await self.client.create_constraints()

    # Entity operations

    async def create_entity(self, entity: GraphEntity) -> GraphEntity:
        """Create a new entity in the graph."""
        try:
            query = """
            CREATE (e:Entity {
                entity_id: $entity_id,
                name: $name,
                entity_type: $entity_type,
                description: $description,
                properties: $properties,
                created_at: datetime($created_at),
                updated_at: datetime($updated_at),
                metadata: $metadata
            })
            RETURN e
            """

            parameters = {
                "entity_id": str(entity.entity_id),
                "name": entity.name,
                "entity_type": entity.entity_type.value,
                "description": entity.description,
                "properties": entity.properties,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
                "metadata": entity.metadata,
            }

            await self.client.execute_write(query, parameters)

            self.logger.info(
                "entity_created",
                entity_id=str(entity.entity_id),
                name=entity.name,
                type=entity.entity_type.value,
            )

            return entity

        except Exception as e:
            self.logger.error(
                "entity_creation_failed",
                entity_id=str(entity.entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to create entity: {str(e)}",
                details={"entity_id": str(entity.entity_id)},
            ) from e

    async def get_entity_by_id(self, entity_id: UUID) -> GraphEntity | None:
        """Retrieve an entity by ID."""
        try:
            query = """
            MATCH (e:Entity {entity_id: $entity_id})
            RETURN e
            """

            results = await self.client.execute_query(
                query, {"entity_id": str(entity_id)}
            )

            if not results:
                return None

            node = results[0]["e"]
            return self._node_to_entity(node)

        except Exception as e:
            self.logger.error(
                "entity_retrieval_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to retrieve entity: {str(e)}"
            ) from e

    async def get_entity_by_name(
        self, name: str, entity_type: EntityType | None = None
    ) -> GraphEntity | None:
        """Retrieve an entity by name."""
        try:
            if entity_type:
                query = """
                MATCH (e:Entity {name: $name, entity_type: $entity_type})
                RETURN e
                """
                parameters = {"name": name, "entity_type": entity_type.value}
            else:
                query = """
                MATCH (e:Entity {name: $name})
                RETURN e
                LIMIT 1
                """
                parameters = {"name": name}

            results = await self.client.execute_query(query, parameters)

            if not results:
                return None

            node = results[0]["e"]
            return self._node_to_entity(node)

        except Exception as e:
            self.logger.error(
                "get_entity_by_name_failed",
                name=name,
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to get entity by name: {str(e)}"
            ) from e

    async def update_entity(self, entity: GraphEntity) -> GraphEntity:
        """Update an existing entity."""
        # Check if exists
        existing = await self.get_entity_by_id(entity.entity_id)
        if existing is None:
            raise EntityNotFoundError("Entity", str(entity.entity_id))

        try:
            query = """
            MATCH (e:Entity {entity_id: $entity_id})
            SET e.name = $name,
                e.entity_type = $entity_type,
                e.description = $description,
                e.properties = $properties,
                e.updated_at = datetime($updated_at),
                e.metadata = $metadata
            RETURN e
            """

            parameters = {
                "entity_id": str(entity.entity_id),
                "name": entity.name,
                "entity_type": entity.entity_type.value,
                "description": entity.description,
                "properties": entity.properties,
                "updated_at": entity.updated_at.isoformat(),
                "metadata": entity.metadata,
            }

            await self.client.execute_write(query, parameters)

            self.logger.info("entity_updated", entity_id=str(entity.entity_id))

            return entity

        except Exception as e:
            self.logger.error(
                "entity_update_failed",
                entity_id=str(entity.entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to update entity: {str(e)}"
            ) from e

    async def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity and all its relationships."""
        try:
            query = """
            MATCH (e:Entity {entity_id: $entity_id})
            DETACH DELETE e
            """

            stats = await self.client.execute_write(
                query, {"entity_id": str(entity_id)}
            )

            deleted = stats["nodes_deleted"] > 0

            if deleted:
                self.logger.info("entity_deleted", entity_id=str(entity_id))

            return deleted

        except Exception as e:
            self.logger.error(
                "entity_deletion_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to delete entity: {str(e)}"
            ) from e

    async def get_entities_by_type(
        self, entity_type: EntityType, limit: int = 100
    ) -> list[GraphEntity]:
        """Get all entities of a specific type."""
        try:
            query = """
            MATCH (e:Entity {entity_type: $entity_type})
            RETURN e
            LIMIT $limit
            """

            results = await self.client.execute_query(
                query, {"entity_type": entity_type.value, "limit": limit}
            )

            entities = [self._node_to_entity(r["e"]) for r in results]

            return entities

        except Exception as e:
            self.logger.error(
                "get_entities_by_type_failed",
                entity_type=entity_type.value,
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to get entities by type: {str(e)}"
            ) from e

    # Relationship operations

    async def create_relationship(
        self, relationship: GraphRelationship
    ) -> GraphRelationship:
        """Create a relationship between two entities."""
        try:
            # Verify both entities exist
            source = await self.get_entity_by_id(relationship.source_entity_id)
            target = await self.get_entity_by_id(relationship.target_entity_id)

            if source is None:
                raise EntityNotFoundError("Entity", str(relationship.source_entity_id))
            if target is None:
                raise EntityNotFoundError("Entity", str(relationship.target_entity_id))

            query = f"""
            MATCH (source:Entity {{entity_id: $source_id}})
            MATCH (target:Entity {{entity_id: $target_id}})
            CREATE (source)-[r:{relationship.relationship_type.value} {{
                relationship_id: $relationship_id,
                properties: $properties,
                strength: $strength,
                created_at: datetime($created_at),
                metadata: $metadata
            }}]->(target)
            RETURN r
            """

            parameters = {
                "source_id": str(relationship.source_entity_id),
                "target_id": str(relationship.target_entity_id),
                "relationship_id": str(relationship.relationship_id),
                "properties": relationship.properties,
                "strength": relationship.strength,
                "created_at": relationship.created_at.isoformat(),
                "metadata": relationship.metadata,
            }

            await self.client.execute_write(query, parameters)

            self.logger.info(
                "relationship_created",
                relationship_id=str(relationship.relationship_id),
                type=relationship.relationship_type.value,
            )

            return relationship

        except EntityNotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                "relationship_creation_failed",
                relationship_id=str(relationship.relationship_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to create relationship: {str(e)}"
            ) from e

    async def get_relationship_by_id(
        self, relationship_id: UUID
    ) -> GraphRelationship | None:
        """Retrieve a relationship by ID."""
        try:
            query = """
            MATCH ()-[r {relationship_id: $relationship_id}]->()
            RETURN r, startNode(r).entity_id as source_id,
                   endNode(r).entity_id as target_id, type(r) as rel_type
            """

            results = await self.client.execute_query(
                query, {"relationship_id": str(relationship_id)}
            )

            if not results:
                return None

            return self._result_to_relationship(results[0])

        except Exception as e:
            self.logger.error(
                "relationship_retrieval_failed",
                relationship_id=str(relationship_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to retrieve relationship: {str(e)}"
            ) from e

    async def update_relationship(
        self, relationship: GraphRelationship
    ) -> GraphRelationship:
        """Update an existing relationship."""
        existing = await self.get_relationship_by_id(relationship.relationship_id)
        if existing is None:
            raise EntityNotFoundError("Relationship", str(relationship.relationship_id))

        try:
            query = """
            MATCH ()-[r {relationship_id: $relationship_id}]->()
            SET r.properties = $properties,
                r.strength = $strength,
                r.metadata = $metadata
            RETURN r
            """

            parameters = {
                "relationship_id": str(relationship.relationship_id),
                "properties": relationship.properties,
                "strength": relationship.strength,
                "metadata": relationship.metadata,
            }

            await self.client.execute_write(query, parameters)

            self.logger.info(
                "relationship_updated",
                relationship_id=str(relationship.relationship_id),
            )

            return relationship

        except Exception as e:
            self.logger.error(
                "relationship_update_failed",
                relationship_id=str(relationship.relationship_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to update relationship: {str(e)}"
            ) from e

    async def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete a relationship."""
        try:
            query = """
            MATCH ()-[r {relationship_id: $relationship_id}]->()
            DELETE r
            """

            stats = await self.client.execute_write(
                query, {"relationship_id": str(relationship_id)}
            )

            deleted = stats["relationships_deleted"] > 0

            if deleted:
                self.logger.info(
                    "relationship_deleted",
                    relationship_id=str(relationship_id),
                )

            return deleted

        except Exception as e:
            self.logger.error(
                "relationship_deletion_failed",
                relationship_id=str(relationship_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to delete relationship: {str(e)}"
            ) from e

    async def get_entity_relationships(
        self,
        entity_id: UUID,
        relationship_type: RelationType | None = None,
        direction: str = "both",
    ) -> list[GraphRelationship]:
        """Get all relationships for an entity."""
        try:
            if direction == "outgoing":
                match_pattern = "(e:Entity {entity_id: $entity_id})-[r]->() "
            elif direction == "incoming":
                match_pattern = "()-[r]->(e:Entity {entity_id: $entity_id})"
            else:  # both
                match_pattern = "(e:Entity {entity_id: $entity_id})-[r]-()"

            type_filter = ""
            if relationship_type:
                type_filter = f":{relationship_type.value}"

            query = f"""
            MATCH {match_pattern.replace('[r]', f'[r{type_filter}]')}
            RETURN r, startNode(r).entity_id as source_id,
                   endNode(r).entity_id as target_id, type(r) as rel_type
            """

            results = await self.client.execute_query(
                query, {"entity_id": str(entity_id)}
            )

            relationships = [self._result_to_relationship(r) for r in results]

            return relationships

        except Exception as e:
            self.logger.error(
                "get_entity_relationships_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to get entity relationships: {str(e)}"
            ) from e

    async def get_related_entities(
        self,
        entity_id: UUID,
        relationship_type: RelationType | None = None,
        max_depth: int = 1,
    ) -> list[GraphEntity]:
        """Get entities related to a given entity."""
        try:
            type_filter = f":{relationship_type.value}" if relationship_type else ""

            query = f"""
            MATCH (e:Entity {{entity_id: $entity_id}})-[r{type_filter}*1..{max_depth}]-(related:Entity)
            RETURN DISTINCT related
            """

            results = await self.client.execute_query(
                query, {"entity_id": str(entity_id)}
            )

            entities = [self._node_to_entity(r["related"]) for r in results]

            return entities

        except Exception as e:
            self.logger.error(
                "get_related_entities_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise GraphDatabaseError(
                f"Failed to get related entities: {str(e)}"
            ) from e

    # Search and query operations

    async def search_entities(
        self,
        query: str,
        entity_type: EntityType | None = None,
        limit: int = 10,
    ) -> list[EntitySearchResult]:
        """Search for entities by text query."""
        try:
            type_filter = f"AND e.entity_type = $entity_type" if entity_type else ""

            cypher_query = f"""
            MATCH (e:Entity)
            WHERE (e.name CONTAINS $query OR e.description CONTAINS $query) {type_filter}
            RETURN e
            LIMIT $limit
            """

            parameters: dict[str, any] = {"query": query, "limit": limit}
            if entity_type:
                parameters["entity_type"] = entity_type.value

            results = await self.client.execute_query(cypher_query, parameters)

            search_results = []
            for r in results:
                entity = self._node_to_entity(r["e"])
                # Simple relevance score based on name match
                relevance = 1.0 if query.lower() in entity.name.lower() else 0.7
                search_results.append(
                    EntitySearchResult(
                        entity=entity,
                        relevance_score=relevance,
                        related_entities=[],
                        relationships=[],
                    )
                )

            return search_results

        except Exception as e:
            self.logger.error("search_entities_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to search entities: {str(e)}"
            ) from e

    async def find_path(
        self,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 5,
        relationship_types: list[RelationType] | None = None,
    ) -> list[GraphRelationship] | None:
        """Find shortest path between two entities."""
        try:
            type_filter = ""
            if relationship_types:
                type_str = "|".join([rt.value for rt in relationship_types])
                type_filter = f":{type_str}"

            query = f"""
            MATCH path = shortestPath(
                (source:Entity {{entity_id: $source_id}})
                -[r{type_filter}*1..{max_depth}]-
                (target:Entity {{entity_id: $target_id}})
            )
            UNWIND relationships(path) as rel
            RETURN rel, startNode(rel).entity_id as source_id,
                   endNode(rel).entity_id as target_id, type(rel) as rel_type
            """

            results = await self.client.execute_query(
                query, {"source_id": str(source_id), "target_id": str(target_id)}
            )

            if not results:
                return None

            relationships = [self._result_to_relationship(r) for r in results]

            return relationships

        except Exception as e:
            self.logger.error("find_path_failed", error=str(e))
            raise GraphDatabaseError(f"Failed to find path: {str(e)}") from e

    async def get_entity_neighbors(
        self,
        entity_id: UUID,
        max_depth: int = 2,
    ) -> list[tuple[GraphEntity, int]]:
        """Get neighboring entities with their distance."""
        try:
            query = f"""
            MATCH path = (e:Entity {{entity_id: $entity_id}})-[*1..{max_depth}]-(neighbor:Entity)
            RETURN DISTINCT neighbor, length(path) as distance
            ORDER BY distance
            """

            results = await self.client.execute_query(
                query, {"entity_id": str(entity_id)}
            )

            neighbors = [
                (self._node_to_entity(r["neighbor"]), r["distance"]) for r in results
            ]

            return neighbors

        except Exception as e:
            self.logger.error("get_neighbors_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to get entity neighbors: {str(e)}"
            ) from e

    async def count_entities(
        self, entity_type: EntityType | None = None
    ) -> int:
        """Count entities, optionally filtered by type."""
        try:
            if entity_type:
                query = """
                MATCH (e:Entity {entity_type: $entity_type})
                RETURN count(e) as count
                """
                parameters = {"entity_type": entity_type.value}
            else:
                query = "MATCH (e:Entity) RETURN count(e) as count"
                parameters = {}

            results = await self.client.execute_query(query, parameters)

            return results[0]["count"] if results else 0

        except Exception as e:
            self.logger.error("count_entities_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to count entities: {str(e)}"
            ) from e

    async def count_relationships(
        self, relationship_type: RelationType | None = None
    ) -> int:
        """Count relationships, optionally filtered by type."""
        try:
            if relationship_type:
                query = f"""
                MATCH ()-[r:{relationship_type.value}]->()
                RETURN count(r) as count
                """
                parameters = {}
            else:
                query = "MATCH ()-[r]->() RETURN count(r) as count"
                parameters = {}

            results = await self.client.execute_query(query, parameters)

            return results[0]["count"] if results else 0

        except Exception as e:
            self.logger.error("count_relationships_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to count relationships: {str(e)}"
            ) from e

    # Bulk operations

    async def bulk_create_entities(
        self, entities: list[GraphEntity]
    ) -> list[GraphEntity]:
        """Create multiple entities at once."""
        try:
            for entity in entities:
                await self.create_entity(entity)

            self.logger.info("bulk_entities_created", count=len(entities))

            return entities

        except Exception as e:
            self.logger.error("bulk_create_entities_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to bulk create entities: {str(e)}"
            ) from e

    async def bulk_create_relationships(
        self, relationships: list[GraphRelationship]
    ) -> list[GraphRelationship]:
        """Create multiple relationships at once."""
        try:
            for relationship in relationships:
                await self.create_relationship(relationship)

            self.logger.info(
                "bulk_relationships_created", count=len(relationships)
            )

            return relationships

        except Exception as e:
            self.logger.error("bulk_create_relationships_failed", error=str(e))
            raise GraphDatabaseError(
                f"Failed to bulk create relationships: {str(e)}"
            ) from e

    # Helper methods

    def _node_to_entity(self, node: dict) -> GraphEntity:
        """Convert Neo4j node to GraphEntity."""
        from datetime import datetime

        return GraphEntity(
            entity_id=UUID(node["entity_id"]),
            name=node["name"],
            entity_type=EntityType(node["entity_type"]),
            description=node.get("description"),
            properties=node.get("properties", {}),
            created_at=node["created_at"]
            if isinstance(node["created_at"], datetime)
            else datetime.fromisoformat(str(node["created_at"])),
            updated_at=node["updated_at"]
            if isinstance(node["updated_at"], datetime)
            else datetime.fromisoformat(str(node["updated_at"])),
            metadata=node.get("metadata", {}),
        )

    def _result_to_relationship(self, result: dict) -> GraphRelationship:
        """Convert query result to GraphRelationship."""
        from datetime import datetime

        rel = result["r"]
        return GraphRelationship(
            relationship_id=UUID(rel["relationship_id"]),
            source_entity_id=UUID(result["source_id"]),
            target_entity_id=UUID(result["target_id"]),
            relationship_type=RelationType(result["rel_type"]),
            properties=rel.get("properties", {}),
            strength=rel.get("strength", 1.0),
            created_at=rel["created_at"]
            if isinstance(rel["created_at"], datetime)
            else datetime.fromisoformat(str(rel["created_at"])),
            metadata=rel.get("metadata", {}),
        )
