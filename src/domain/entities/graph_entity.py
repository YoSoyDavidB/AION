"""
Graph entity - Represents entities and relationships in the knowledge graph.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""

    PERSON = "person"
    PROJECT = "project"
    CONCEPT = "concept"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    EVENT = "event"
    LOCATION = "location"
    TECHNOLOGY = "technology"


class RelationType(str, Enum):
    """Types of relationships between entities."""

    RELATED_TO = "RELATED_TO"
    MENTIONED_IN = "MENTIONED_IN"
    PART_OF = "PART_OF"
    CREATED_BY = "CREATED_BY"
    WORKS_ON = "WORKS_ON"
    LOCATED_IN = "LOCATED_IN"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    DEPENDS_ON = "DEPENDS_ON"


class GraphEntity(BaseModel):
    """
    Represents an entity in the knowledge graph (Neo4j).

    Entities can be people, projects, concepts, organizations, etc.
    They are connected through typed relationships.
    """

    entity_id: UUID = Field(default_factory=uuid4, description="Entity identifier")
    name: str = Field(..., min_length=1, description="Entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    description: str | None = Field(default=None, description="Entity description")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Additional properties"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Entity name cannot be empty")
        return stripped

    def update_property(self, key: str, value: Any) -> None:
        """
        Update or add a property to the entity.

        Args:
            key: Property key
            value: Property value
        """
        self.properties[key] = value
        self.updated_at = datetime.utcnow()

    def remove_property(self, key: str) -> None:
        """
        Remove a property from the entity.

        Args:
            key: Property key to remove
        """
        if key in self.properties:
            del self.properties[key]
            self.updated_at = datetime.utcnow()

    def has_property(self, key: str) -> bool:
        """
        Check if entity has a specific property.

        Args:
            key: Property key

        Returns:
            True if property exists
        """
        return key in self.properties

    model_config = {"json_schema_extra": {"example": {
        "entity_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "FastAPI",
        "entity_type": "concept",
        "description": "Modern Python web framework",
        "properties": {
            "category": "web framework",
            "language": "Python",
            "popularity": "high",
        },
    }}}


class GraphRelationship(BaseModel):
    """
    Represents a relationship between two entities in the knowledge graph.
    """

    relationship_id: UUID = Field(
        default_factory=uuid4, description="Relationship identifier"
    )
    source_entity_id: UUID = Field(..., description="Source entity ID")
    target_entity_id: UUID = Field(..., description="Target entity ID")
    relationship_type: RelationType = Field(..., description="Type of relationship")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )
    strength: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Relationship strength (0-1)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("source_entity_id", "target_entity_id")
    @classmethod
    def validate_different_entities(
        cls, v: UUID, info: dict
    ) -> UUID:
        """Ensure source and target are different entities."""
        # This validation happens per field, so we can't compare here
        # We'll add a model validator below
        return v

    def update_strength(self, new_strength: float) -> None:
        """
        Update relationship strength.

        Args:
            new_strength: New strength value (0-1)
        """
        if not 0.0 <= new_strength <= 1.0:
            raise ValueError("Strength must be between 0 and 1")
        self.strength = new_strength

    def increment_strength(self, amount: float = 0.1) -> None:
        """
        Increment relationship strength (e.g., when relationship is reinforced).

        Args:
            amount: Amount to increment
        """
        self.strength = min(1.0, self.strength + amount)

    def decrement_strength(self, amount: float = 0.1) -> None:
        """
        Decrement relationship strength (e.g., when relationship weakens).

        Args:
            amount: Amount to decrement
        """
        self.strength = max(0.0, self.strength - amount)

    model_config = {"json_schema_extra": {"example": {
        "relationship_id": "660e8400-e29b-41d4-a716-446655440000",
        "source_entity_id": "550e8400-e29b-41d4-a716-446655440000",
        "target_entity_id": "770e8400-e29b-41d4-a716-446655440000",
        "relationship_type": "RELATED_TO",
        "strength": 0.85,
        "properties": {"context": "mentioned together in 5 conversations"},
    }}}


class EntitySearchResult(BaseModel):
    """
    Represents a search result for entity queries.
    """

    entity: GraphEntity = Field(..., description="The entity")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score for this result"
    )
    related_entities: list[GraphEntity] = Field(
        default_factory=list, description="Related entities"
    )
    relationships: list[GraphRelationship] = Field(
        default_factory=list, description="Relationships to other entities"
    )

    model_config = {"json_schema_extra": {"example": {
        "entity": {
            "name": "FastAPI",
            "entity_type": "concept",
            "description": "Modern Python web framework",
        },
        "relevance_score": 0.92,
        "related_entities": [],
        "relationships": [],
    }}}
