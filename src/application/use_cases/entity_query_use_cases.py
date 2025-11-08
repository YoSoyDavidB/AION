"""
Use cases for querying the knowledge graph.
"""

from uuid import UUID

from src.application.dtos.entity_dto import (
    EntityGraphResponse,
    EntityResponse,
    EntitySearchRequest,
    RelationshipResponse,
)
from src.domain.entities.graph_entity import EntityType, RelationType
from src.domain.repositories.graph_repository import IGraphRepository
from src.shared.exceptions import EntityNotFoundError, UseCaseExecutionError
from src.shared.logging import LoggerMixin


class SearchEntitiesUseCase(LoggerMixin):
    """Use case for searching entities in the knowledge graph."""

    def __init__(self, graph_repo: IGraphRepository) -> None:
        self.graph_repo = graph_repo

    async def execute(
        self, request: EntitySearchRequest
    ) -> list[EntityResponse]:
        """
        Search for entities.

        Args:
            request: Entity search request

        Returns:
            List of matching entities

        Raises:
            UseCaseExecutionError: If search fails
        """
        try:
            self.logger.info(
                "searching_entities",
                query=request.query,
                entity_type=request.entity_type.value if request.entity_type else None,
                limit=request.limit,
            )

            search_results = await self.graph_repo.search_entities(
                query=request.query,
                entity_type=request.entity_type,
                limit=request.limit,
            )

            entities = [
                EntityResponse(
                    entity_id=result.entity.entity_id,
                    name=result.entity.name,
                    entity_type=result.entity.entity_type,
                    description=result.entity.description,
                    properties=result.entity.properties,
                    created_at=result.entity.created_at.isoformat(),
                    updated_at=result.entity.updated_at.isoformat(),
                )
                for result in search_results
            ]

            self.logger.info("entities_found", count=len(entities))

            return entities

        except Exception as e:
            self.logger.error("entity_search_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Failed to search entities: {str(e)}"
            ) from e


class GetEntityGraphUseCase(LoggerMixin):
    """Use case for getting an entity with its relationships."""

    def __init__(self, graph_repo: IGraphRepository) -> None:
        self.graph_repo = graph_repo

    async def execute(
        self,
        entity_id: UUID,
        include_relationships: bool = True,
        include_related: bool = True,
        max_depth: int = 1,
    ) -> EntityGraphResponse:
        """
        Get entity with its relationships and related entities.

        Args:
            entity_id: Entity identifier
            include_relationships: Include relationships in response
            include_related: Include related entities
            max_depth: Maximum depth for related entities

        Returns:
            Entity graph response

        Raises:
            EntityNotFoundError: If entity doesn't exist
            UseCaseExecutionError: If retrieval fails
        """
        try:
            self.logger.info(
                "getting_entity_graph",
                entity_id=str(entity_id),
                include_relationships=include_relationships,
                include_related=include_related,
            )

            # Get entity
            entity = await self.graph_repo.get_entity_by_id(entity_id)
            if entity is None:
                raise EntityNotFoundError("Entity", str(entity_id))

            entity_response = EntityResponse(
                entity_id=entity.entity_id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                properties=entity.properties,
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat(),
            )

            # Get relationships
            relationship_responses = []
            if include_relationships:
                relationships = await self.graph_repo.get_entity_relationships(
                    entity_id=entity_id,
                    direction="both",
                )

                # Get source and target entities for each relationship
                for rel in relationships:
                    source_entity = await self.graph_repo.get_entity_by_id(
                        rel.source_entity_id
                    )
                    target_entity = await self.graph_repo.get_entity_by_id(
                        rel.target_entity_id
                    )

                    if source_entity and target_entity:
                        relationship_responses.append(
                            RelationshipResponse(
                                relationship_id=rel.relationship_id,
                                source_entity=EntityResponse(
                                    entity_id=source_entity.entity_id,
                                    name=source_entity.name,
                                    entity_type=source_entity.entity_type,
                                    description=source_entity.description,
                                    properties=source_entity.properties,
                                    created_at=source_entity.created_at.isoformat(),
                                    updated_at=source_entity.updated_at.isoformat(),
                                ),
                                target_entity=EntityResponse(
                                    entity_id=target_entity.entity_id,
                                    name=target_entity.name,
                                    entity_type=target_entity.entity_type,
                                    description=target_entity.description,
                                    properties=target_entity.properties,
                                    created_at=target_entity.created_at.isoformat(),
                                    updated_at=target_entity.updated_at.isoformat(),
                                ),
                                relationship_type=rel.relationship_type,
                                strength=rel.strength,
                                properties=rel.properties,
                                created_at=rel.created_at.isoformat(),
                            )
                        )

            # Get related entities
            related_entity_responses = []
            if include_related:
                related_entities = await self.graph_repo.get_related_entities(
                    entity_id=entity_id,
                    max_depth=max_depth,
                )

                related_entity_responses = [
                    EntityResponse(
                        entity_id=ent.entity_id,
                        name=ent.name,
                        entity_type=ent.entity_type,
                        description=ent.description,
                        properties=ent.properties,
                        created_at=ent.created_at.isoformat(),
                        updated_at=ent.updated_at.isoformat(),
                    )
                    for ent in related_entities
                ]

            response = EntityGraphResponse(
                entity=entity_response,
                relationships=relationship_responses,
                related_entities=related_entity_responses,
            )

            self.logger.info(
                "entity_graph_retrieved",
                entity_id=str(entity_id),
                num_relationships=len(relationship_responses),
                num_related=len(related_entity_responses),
            )

            return response

        except EntityNotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                "get_entity_graph_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise UseCaseExecutionError(
                f"Failed to get entity graph: {str(e)}"
            ) from e


class GetEntitiesByTypeUseCase(LoggerMixin):
    """Use case for getting all entities of a specific type."""

    def __init__(self, graph_repo: IGraphRepository) -> None:
        self.graph_repo = graph_repo

    async def execute(
        self, entity_type: EntityType, limit: int = 100
    ) -> list[EntityResponse]:
        """
        Get entities by type.

        Args:
            entity_type: Entity type to filter by
            limit: Maximum number of results

        Returns:
            List of entities

        Raises:
            UseCaseExecutionError: If retrieval fails
        """
        try:
            self.logger.info(
                "getting_entities_by_type",
                entity_type=entity_type.value,
                limit=limit,
            )

            entities = await self.graph_repo.get_entities_by_type(
                entity_type=entity_type,
                limit=limit,
            )

            responses = [
                EntityResponse(
                    entity_id=ent.entity_id,
                    name=ent.name,
                    entity_type=ent.entity_type,
                    description=ent.description,
                    properties=ent.properties,
                    created_at=ent.created_at.isoformat(),
                    updated_at=ent.updated_at.isoformat(),
                )
                for ent in entities
            ]

            self.logger.info("entities_retrieved", count=len(responses))

            return responses

        except Exception as e:
            self.logger.error(
                "get_entities_by_type_failed",
                entity_type=entity_type.value,
                error=str(e),
            )
            raise UseCaseExecutionError(
                f"Failed to get entities by type: {str(e)}"
            ) from e
