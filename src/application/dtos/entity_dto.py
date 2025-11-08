"""
DTOs for entity extraction and knowledge graph operations.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.graph_entity import EntityType, RelationType


class EntityDTO(BaseModel):
    """DTO for extracted entity."""

    entity_id: UUID | None = Field(default=None, description="Entity ID if exists")
    name: str = Field(..., min_length=1, description="Entity name")
    entity_type: EntityType = Field(..., description="Entity type")
    description: str | None = Field(default=None, description="Entity description")
    properties: dict[str, str | list[str] | int | float | bool] = Field(
        default_factory=dict, description="Additional properties (strings, lists, numbers, booleans)"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Extraction confidence"
    )


class RelationshipDTO(BaseModel):
    """DTO for extracted relationship."""

    source_name: str = Field(..., description="Source entity name")
    target_name: str = Field(..., description="Target entity name")
    relationship_type: RelationType = Field(..., description="Relationship type")
    properties: dict[str, str | list[str] | int | float | bool] = Field(
        default_factory=dict, description="Relationship properties (strings, lists, numbers, booleans)"
    )
    strength: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Relationship strength"
    )


class EntityExtractionRequest(BaseModel):
    """Request for entity extraction from text."""

    text: str = Field(..., min_length=1, description="Text to extract entities from")
    user_id: str = Field(..., description="User ID")
    source: str = Field(..., description="Source of the text (e.g., 'chat', 'document')")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )


class EntityExtractionResponse(BaseModel):
    """Response from entity extraction."""

    entities: list[EntityDTO] = Field(
        default_factory=list, description="Extracted entities"
    )
    relationships: list[RelationshipDTO] = Field(
        default_factory=list, description="Extracted relationships"
    )
    num_entities_created: int = Field(
        default=0, description="Number of new entities created"
    )
    num_relationships_created: int = Field(
        default=0, description="Number of new relationships created"
    )


class EntitySearchRequest(BaseModel):
    """Request for searching entities."""

    query: str = Field(..., min_length=1, description="Search query")
    entity_type: EntityType | None = Field(
        default=None, description="Filter by entity type"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")


class EntityResponse(BaseModel):
    """Response containing entity information."""

    entity_id: UUID = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    entity_type: EntityType = Field(..., description="Entity type")
    description: str | None = Field(default=None, description="Entity description")
    properties: dict[str, str | list[str] | int | float | bool] = Field(
        default_factory=dict, description="Entity properties"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class RelationshipResponse(BaseModel):
    """Response containing relationship information."""

    relationship_id: UUID = Field(..., description="Relationship ID")
    source_entity: EntityResponse = Field(..., description="Source entity")
    target_entity: EntityResponse = Field(..., description="Target entity")
    relationship_type: RelationType = Field(..., description="Relationship type")
    strength: float = Field(..., description="Relationship strength")
    properties: dict[str, str | list[str] | int | float | bool] = Field(
        default_factory=dict, description="Relationship properties"
    )
    created_at: str = Field(..., description="Creation timestamp")


class EntityGraphResponse(BaseModel):
    """Response containing entity with its relationships."""

    entity: EntityResponse = Field(..., description="The entity")
    relationships: list[RelationshipResponse] = Field(
        default_factory=list, description="Entity relationships"
    )
    related_entities: list[EntityResponse] = Field(
        default_factory=list, description="Related entities"
    )
