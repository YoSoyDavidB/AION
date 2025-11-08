"""
Use case for extracting entities and relationships from text.
"""

from datetime import datetime

from src.application.dtos.entity_dto import (
    EntityDTO,
    EntityExtractionRequest,
    EntityExtractionResponse,
    RelationshipDTO,
)
from src.domain.entities.graph_entity import (
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationType,
)
from src.domain.repositories.graph_repository import IGraphRepository
from src.infrastructure.llm.llm_service import LLMService
from src.shared.exceptions import UseCaseExecutionError
from src.shared.logging import LoggerMixin


class EntityExtractionUseCase(LoggerMixin):
    """
    Use case for extracting entities and relationships from text.

    This use case:
    1. Extracts named entities using LLM
    2. Extracts relationships between entities
    3. Stores new entities in Neo4j knowledge graph
    4. Creates or updates relationships
    """

    def __init__(
        self,
        graph_repo: IGraphRepository,
        llm_service: LLMService,
    ) -> None:
        self.graph_repo = graph_repo
        self.llm_service = llm_service

    async def execute(
        self, request: EntityExtractionRequest
    ) -> EntityExtractionResponse:
        """
        Extract entities and relationships from text.

        Args:
            request: Entity extraction request

        Returns:
            Extraction response with created entities and relationships

        Raises:
            UseCaseExecutionError: If extraction fails
        """
        try:
            self.logger.info(
                "extracting_entities_from_text",
                text_length=len(request.text),
                source=request.source,
                user_id=request.user_id,
            )

            # Step 1: Extract entities using LLM
            raw_entities = await self.llm_service.extract_entities(
                text=request.text,
                context=request.metadata.get("context"),
            )

            if not raw_entities:
                self.logger.info("no_entities_extracted")
                return EntityExtractionResponse(
                    entities=[],
                    relationships=[],
                    num_entities_created=0,
                    num_relationships_created=0,
                )

            # Step 2: Store entities in Neo4j
            entity_dtos: list[EntityDTO] = []
            entity_map: dict[str, GraphEntity] = {}  # name -> GraphEntity
            num_created = 0

            for raw_entity in raw_entities:
                # Convert to DTO
                entity_dto = EntityDTO(
                    name=raw_entity["name"],
                    entity_type=EntityType(raw_entity["type"]),
                    description=raw_entity.get("description"),
                    properties=raw_entity.get("properties", {}),
                    confidence=raw_entity.get("confidence", 1.0),
                )

                # Check if entity already exists
                existing = await self.graph_repo.get_entity_by_name(
                    name=entity_dto.name,
                    entity_type=entity_dto.entity_type,
                )

                if existing:
                    # Update existing entity
                    self.logger.debug(
                        "entity_already_exists",
                        name=entity_dto.name,
                        entity_id=str(existing.entity_id),
                    )
                    entity_map[entity_dto.name] = existing
                    entity_dto.entity_id = existing.entity_id
                else:
                    # Create new entity
                    graph_entity = GraphEntity(
                        name=entity_dto.name,
                        entity_type=entity_dto.entity_type,
                        description=entity_dto.description,
                        properties=entity_dto.properties,
                        metadata={
                            "source": request.source,
                            "user_id": request.user_id,
                            "confidence": entity_dto.confidence,
                            **request.metadata,
                        },
                    )

                    created_entity = await self.graph_repo.create_entity(graph_entity)
                    entity_map[entity_dto.name] = created_entity
                    entity_dto.entity_id = created_entity.entity_id
                    num_created += 1

                    self.logger.info(
                        "entity_created",
                        name=entity_dto.name,
                        type=entity_dto.entity_type.value,
                        entity_id=str(created_entity.entity_id),
                    )

                entity_dtos.append(entity_dto)

            # Step 3: Extract relationships using LLM
            relationship_dtos: list[RelationshipDTO] = []
            num_relationships_created = 0

            if len(raw_entities) >= 2:
                raw_relationships = await self.llm_service.extract_relationships(
                    text=request.text,
                    entities=raw_entities,
                )

                # Step 4: Store relationships in Neo4j
                for raw_rel in raw_relationships:
                    source_name = raw_rel["source_name"]
                    target_name = raw_rel["target_name"]

                    # Verify both entities exist in our map
                    if source_name not in entity_map or target_name not in entity_map:
                        self.logger.warning(
                            "relationship_entity_not_found",
                            source=source_name,
                            target=target_name,
                        )
                        continue

                    source_entity = entity_map[source_name]
                    target_entity = entity_map[target_name]

                    # Create relationship
                    rel_dto = RelationshipDTO(
                        source_name=source_name,
                        target_name=target_name,
                        relationship_type=RelationType(raw_rel["type"]),
                        properties=raw_rel.get("properties", {}),
                        strength=raw_rel.get("strength", 0.8),
                    )

                    # Check if relationship already exists
                    relationship_exists = False
                    try:
                        existing_rels = await self.graph_repo.get_entity_relationships(
                            entity_id=source_entity.entity_id,
                            relationship_type=rel_dto.relationship_type,
                            direction="outgoing",
                        )

                        # Check if this specific relationship exists
                        relationship_exists = any(
                            rel.target_entity_id == target_entity.entity_id
                            for rel in existing_rels
                        )
                    except Exception as e:
                        # If checking relationships fails, assume it doesn't exist and create it
                        self.logger.warning(
                            "relationship_check_failed",
                            source_entity=source_entity.name,
                            target_entity=target_entity.name,
                            error=str(e),
                        )

                    if not relationship_exists:
                        graph_relationship = GraphRelationship(
                            source_entity_id=source_entity.entity_id,
                            target_entity_id=target_entity.entity_id,
                            relationship_type=rel_dto.relationship_type,
                            properties=rel_dto.properties,
                            strength=rel_dto.strength,
                            metadata={
                                "source": request.source,
                                "user_id": request.user_id,
                                **request.metadata,
                            },
                        )

                        await self.graph_repo.create_relationship(graph_relationship)
                        num_relationships_created += 1

                        self.logger.info(
                            "relationship_created",
                            source=source_name,
                            target=target_name,
                            type=rel_dto.relationship_type.value,
                        )
                    else:
                        self.logger.debug(
                            "relationship_already_exists",
                            source=source_name,
                            target=target_name,
                            type=rel_dto.relationship_type.value,
                        )

                    relationship_dtos.append(rel_dto)

            response = EntityExtractionResponse(
                entities=entity_dtos,
                relationships=relationship_dtos,
                num_entities_created=num_created,
                num_relationships_created=num_relationships_created,
            )

            self.logger.info(
                "entity_extraction_completed",
                num_entities=len(entity_dtos),
                num_created=num_created,
                num_relationships=len(relationship_dtos),
                num_relationships_created=num_relationships_created,
            )

            return response

        except Exception as e:
            self.logger.error("entity_extraction_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Failed to extract entities: {str(e)}"
            ) from e
