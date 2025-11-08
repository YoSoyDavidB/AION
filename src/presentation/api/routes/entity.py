"""
API routes for entity management (knowledge graph).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.dtos.entity_dto import (
    EntityGraphResponse,
    EntityResponse,
    EntitySearchRequest,
)
from src.application.use_cases.entity_query_use_cases import (
    GetEntitiesByTypeUseCase,
    GetEntityGraphUseCase,
    SearchEntitiesUseCase,
)
from src.domain.entities.graph_entity import EntityType
from src.shared.exceptions import EntityNotFoundError, UseCaseExecutionError

router = APIRouter(prefix="/entities", tags=["entities"])


def get_search_entities_use_case() -> SearchEntitiesUseCase:
    """Get search entities use case with dependencies."""
    from src.presentation.api.dependencies import get_graph_repository

    return SearchEntitiesUseCase(graph_repo=get_graph_repository())


def get_entity_graph_use_case() -> GetEntityGraphUseCase:
    """Get entity graph use case with dependencies."""
    from src.presentation.api.dependencies import get_graph_repository

    return GetEntityGraphUseCase(graph_repo=get_graph_repository())


def get_entities_by_type_use_case() -> GetEntitiesByTypeUseCase:
    """Get entities by type use case with dependencies."""
    from src.presentation.api.dependencies import get_graph_repository

    return GetEntitiesByTypeUseCase(graph_repo=get_graph_repository())


@router.get("/search", response_model=list[EntityResponse])
async def search_entities(
    query: str = Query(..., min_length=1, description="Search query"),
    entity_type: EntityType | None = Query(None, description="Filter by entity type"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    use_case: SearchEntitiesUseCase = Depends(get_search_entities_use_case),
):
    """
    Search for entities in the knowledge graph.

    Returns entities matching the search query, optionally filtered by type.
    """
    try:
        request = EntitySearchRequest(
            query=query,
            entity_type=entity_type,
            limit=limit,
        )

        entities = await use_case.execute(request)

        return entities

    except UseCaseExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}", response_model=EntityGraphResponse)
async def get_entity(
    entity_id: UUID,
    include_relationships: bool = Query(
        True, description="Include relationships in response"
    ),
    include_related: bool = Query(True, description="Include related entities"),
    max_depth: int = Query(1, ge=1, le=3, description="Maximum depth for related entities"),
    use_case: GetEntityGraphUseCase = Depends(get_entity_graph_use_case),
):
    """
    Get an entity with its relationships and related entities.

    Retrieves comprehensive information about an entity including:
    - Entity details
    - Relationships to other entities
    - Related entities (up to max_depth)
    """
    try:
        entity_graph = await use_case.execute(
            entity_id=entity_id,
            include_relationships=include_relationships,
            include_related=include_related,
            max_depth=max_depth,
        )

        return entity_graph

    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UseCaseExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/type/{entity_type}", response_model=list[EntityResponse])
async def get_entities_by_type(
    entity_type: EntityType,
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    use_case: GetEntitiesByTypeUseCase = Depends(get_entities_by_type_use_case),
):
    """
    Get all entities of a specific type.

    Entity types:
    - person: People mentioned in conversations or documents
    - project: Projects discussed
    - concept: Technical concepts or ideas
    - organization: Companies or organizations
    - document: Documents referenced
    - event: Events or meetings
    - location: Places or locations
    """
    try:
        entities = await use_case.execute(
            entity_type=entity_type,
            limit=limit,
        )

        return entities

    except UseCaseExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))
