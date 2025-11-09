"""
API routes for managing system prompts.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.domain.entities.system_prompt import PromptType, SystemPrompt
from src.infrastructure.database.system_prompt_repository import SystemPromptRepository
from src.presentation.schemas.prompt_schemas import (
    PromptsListResponse,
    SystemPromptResponse,
    SystemPromptUpdateRequest,
)
from src.shared.logging import get_logger

router = APIRouter(prefix="/prompts", tags=["prompts"])
logger = get_logger(__name__)


def get_prompt_repository() -> SystemPromptRepository:
    """Dependency to get prompt repository."""
    return SystemPromptRepository()


@router.get("", response_model=PromptsListResponse)
async def list_prompts(
    repo: SystemPromptRepository = Depends(get_prompt_repository),
):
    """
    List all system prompts.

    Returns all configured system prompts with their current values.
    """
    try:
        prompts = await repo.get_all()

        # If no prompts in DB, return defaults
        if not prompts:
            default_prompts = []
            for prompt_type in PromptType:
                default_prompts.append(
                    SystemPrompt(
                        prompt_type=prompt_type,
                        content=SystemPrompt.get_default_prompt(prompt_type),
                        description=f"Default {prompt_type.value} prompt",
                        is_active=True,
                    )
                )
            prompts = default_prompts

        return PromptsListResponse(
            prompts=[
                SystemPromptResponse(
                    prompt_type=p.prompt_type.value,
                    content=p.content,
                    description=p.description,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in prompts
            ],
            total=len(prompts),
        )

    except Exception as e:
        logger.error("list_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/{prompt_type}", response_model=SystemPromptResponse)
async def get_prompt(
    prompt_type: str,
    repo: SystemPromptRepository = Depends(get_prompt_repository),
):
    """
    Get a specific system prompt by type.

    Args:
        prompt_type: Type of prompt to retrieve

    Returns:
        The requested system prompt
    """
    try:
        # Validate prompt type
        try:
            pt = PromptType(prompt_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid prompt type: {prompt_type}. Valid types: {[t.value for t in PromptType]}",
            )

        prompt = await repo.get(pt)

        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_type} not found")

        return SystemPromptResponse(
            prompt_type=prompt.prompt_type.value,
            content=prompt.content,
            description=prompt.description,
            is_active=prompt.is_active,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_prompt_failed", prompt_type=prompt_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.put("/{prompt_type}", response_model=SystemPromptResponse)
async def update_prompt(
    prompt_type: str,
    request: SystemPromptUpdateRequest,
    repo: SystemPromptRepository = Depends(get_prompt_repository),
):
    """
    Update a system prompt.

    Args:
        prompt_type: Type of prompt to update
        request: Update request with new content

    Returns:
        Updated system prompt
    """
    try:
        # Validate prompt type
        try:
            pt = PromptType(prompt_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid prompt type: {prompt_type}. Valid types: {[t.value for t in PromptType]}",
            )

        # Get existing or create new
        existing = await repo.get(pt)

        # Update prompt
        updated_prompt = SystemPrompt(
            prompt_type=pt,
            content=request.content,
            description=request.description or existing.description if existing else f"Updated {pt.value} prompt",
            is_active=True,
        )

        saved_prompt = await repo.save(updated_prompt)

        logger.info("prompt_updated_via_api", prompt_type=prompt_type)

        return SystemPromptResponse(
            prompt_type=saved_prompt.prompt_type.value,
            content=saved_prompt.content,
            description=saved_prompt.description,
            is_active=saved_prompt.is_active,
            created_at=saved_prompt.created_at,
            updated_at=saved_prompt.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_prompt_failed", prompt_type=prompt_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")


@router.post("/{prompt_type}/reset", response_model=SystemPromptResponse)
async def reset_prompt_to_default(
    prompt_type: str,
    repo: SystemPromptRepository = Depends(get_prompt_repository),
):
    """
    Reset a system prompt to its default value.

    Args:
        prompt_type: Type of prompt to reset

    Returns:
        Reset system prompt
    """
    try:
        # Validate prompt type
        try:
            pt = PromptType(prompt_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid prompt type: {prompt_type}. Valid types: {[t.value for t in PromptType]}",
            )

        reset_prompt = await repo.reset_to_default(pt)

        logger.info("prompt_reset_via_api", prompt_type=prompt_type)

        return SystemPromptResponse(
            prompt_type=reset_prompt.prompt_type.value,
            content=reset_prompt.content,
            description=reset_prompt.description,
            is_active=reset_prompt.is_active,
            created_at=reset_prompt.created_at,
            updated_at=reset_prompt.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("reset_prompt_failed", prompt_type=prompt_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to reset prompt: {str(e)}")


@router.post("/initialize-defaults")
async def initialize_default_prompts(
    repo: SystemPromptRepository = Depends(get_prompt_repository),
):
    """
    Initialize all prompts with default values.

    This creates database entries for all prompt types if they don't exist.
    Useful for first-time setup.
    """
    try:
        await repo.initialize_defaults()
        logger.info("defaults_initialized_via_api")
        return {"message": "Default prompts initialized successfully"}

    except Exception as e:
        logger.error("initialize_defaults_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to initialize defaults: {str(e)}")
