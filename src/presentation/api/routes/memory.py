"""
Memory management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.application.dtos.memory_dto import (
    MemoryCreateRequest,
    MemoryResponse,
    MemorySearchRequest,
)
from src.application.use_cases.memory_use_cases import (
    CreateMemoryUseCase,
    DeleteMemoryUseCase,
    GetMemoryByIdUseCase,
    SearchMemoriesUseCase,
)
from src.presentation.api.dependencies import (
    get_create_memory_use_case,
    get_delete_memory_use_case,
    get_memory_by_id_use_case,
    get_search_memories_use_case,
)
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/memories", response_model=MemoryResponse, status_code=201)
async def create_memory(
    request: MemoryCreateRequest,
    use_case: CreateMemoryUseCase = Depends(get_create_memory_use_case),
):
    """
    Create a new memory.

    Args:
        request: Memory creation request
        use_case: Injected create memory use case

    Returns:
        Created memory

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(
            "create_memory_request",
            type=request.memory_type.value,
            text=request.short_text[:50],
        )

        response = await use_case.execute(request)

        logger.info("memory_created", memory_id=str(response.memory_id))

        return response

    except Exception as e:
        logger.error("create_memory_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create memory: {str(e)}",
        )


@router.post("/memories/search", response_model=list[tuple[MemoryResponse, float]])
async def search_memories(
    request: MemorySearchRequest,
    use_case: SearchMemoriesUseCase = Depends(get_search_memories_use_case),
):
    """
    Search for memories by semantic similarity.

    Args:
        request: Memory search request
        use_case: Injected search memories use case

    Returns:
        List of (Memory, similarity_score) tuples

    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(
            "search_memories_request",
            query=request.query[:50],
            limit=request.limit,
        )

        results = await use_case.execute(request)

        logger.info("memories_search_completed", count=len(results))

        return results

    except Exception as e:
        logger.error("search_memories_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search memories: {str(e)}",
        )


@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    use_case: GetMemoryByIdUseCase = Depends(get_memory_by_id_use_case),
):
    """
    Retrieve a memory by ID.

    Args:
        memory_id: Memory identifier
        use_case: Injected get memory use case

    Returns:
        Memory details

    Raises:
        HTTPException: If memory not found
    """
    try:
        memory = await use_case.execute(memory_id)

        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")

        return memory

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_memory_failed", memory_id=str(memory_id), error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve memory: {str(e)}",
        )


@router.delete("/memories/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: UUID,
    use_case: DeleteMemoryUseCase = Depends(get_delete_memory_use_case),
):
    """
    Delete a memory.

    Args:
        memory_id: Memory identifier
        use_case: Injected delete memory use case

    Raises:
        HTTPException: If deletion fails or memory not found
    """
    try:
        deleted = await use_case.execute(memory_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")

        logger.info("memory_deleted", memory_id=str(memory_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_memory_failed", memory_id=str(memory_id), error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete memory: {str(e)}",
        )
