"""
API routes for Obsidian vault synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.application.agents.obsidian_sync_agent import ObsidianSyncAgent
from src.application.use_cases.document_use_cases import (
    DeleteDocumentUseCase,
    UploadDocumentUseCase,
)
from src.infrastructure.persistence.sync_state_repository import SyncStateRepository
from src.presentation.api.dependencies import (
    get_delete_document_use_case,
    get_upload_document_use_case,
)
from src.config.settings import get_settings
from src.shared.logging import get_logger

router = APIRouter(prefix="/obsidian", tags=["obsidian"])
logger = get_logger(__name__)


class SyncVaultRequest(BaseModel):
    """Request to sync vault."""

    user_id: str = Field(..., description="User ID")
    force: bool = Field(default=False, description="Force sync all files")


class SyncVaultResponse(BaseModel):
    """Response from vault sync."""

    total_files: int
    synced: int
    failed: int
    skipped: int
    vault_path: str


class SyncStatusResponse(BaseModel):
    """Sync status response."""

    vault_path: str
    vault_configured: bool
    total_synced_files: int


def get_sync_agent(
    user_id: str,
    upload_use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case),
    delete_use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case),
) -> ObsidianSyncAgent:
    """Get configured sync agent."""
    settings = get_settings()

    # Validate GitHub configuration
    if not settings.github.github_token:
        raise HTTPException(
            status_code=400,
            detail="GitHub token not configured. Set GITHUB_TOKEN in .env",
        )
    if not settings.github.github_repo_owner or not settings.github.github_repo_name:
        raise HTTPException(
            status_code=400,
            detail="GitHub repository not configured. Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME in .env",
        )

    return ObsidianSyncAgent(
        github_token=settings.github.github_token,
        repo_owner=settings.github.github_repo_owner,
        repo_name=settings.github.github_repo_name,
        branch=settings.github.github_branch,
        user_id=user_id,
        upload_use_case=upload_use_case,
        delete_use_case=delete_use_case,
    )


@router.post("/sync", response_model=SyncVaultResponse)
async def sync_vault(
    request: SyncVaultRequest,
    agent: ObsidianSyncAgent = Depends(
        lambda req=SyncVaultRequest: get_sync_agent(req.user_id)
    ),
):
    """
    Sync Obsidian vault to knowledge base.

    This endpoint scans the configured Obsidian vault and syncs
    all markdown files to the document knowledge base.

    Args:
        request: Sync request with user_id and force flag

    Returns:
        Sync summary with counts
    """
    try:
        logger.info("sync_vault_request", user_id=request.user_id, force=request.force)

        # Get agent with request user_id
        settings = get_settings()
        upload_use_case = get_upload_document_use_case()
        delete_use_case = get_delete_document_use_case()

        agent = ObsidianSyncAgent(
            github_token=settings.github.github_token,
            repo_owner=settings.github.github_repo_owner,
            repo_name=settings.github.github_repo_name,
            branch=settings.github.github_branch,
            user_id=request.user_id,
            upload_use_case=upload_use_case,
            delete_use_case=delete_use_case,
        )

        # Run sync
        summary = await agent.sync_vault(force=request.force)

        # Cleanup deleted files
        await agent.cleanup_deleted_files()

        return SyncVaultResponse(
            **summary,
            vault_path=f"{settings.github.github_repo_owner}/{settings.github.github_repo_name}",
        )

    except ValueError as e:
        logger.error("sync_vault_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sync_vault_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    user_id: str = Query(..., description="User ID"),
):
    """
    Get Obsidian sync status.

    Returns information about vault configuration and sync state.
    """
    try:
        settings = get_settings()

        vault_configured = bool(
            settings.github.github_token
            and settings.github.github_repo_owner
            and settings.github.github_repo_name
        )

        if vault_configured:
            sync_repo = SyncStateRepository()
            states = sync_repo.get_by_user(user_id)
            total_synced = len([s for s in states if s.status.value == "synced"])

            return SyncStatusResponse(
                vault_path=f"{settings.github.github_repo_owner}/{settings.github.github_repo_name}",
                vault_configured=True,
                total_synced_files=total_synced,
            )
        else:
            return SyncStatusResponse(
                vault_path="",
                vault_configured=False,
                total_synced_files=0,
            )

    except Exception as e:
        logger.error("get_sync_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_deleted_files(
    user_id: str = Query(..., description="User ID"),
    agent: ObsidianSyncAgent = Depends(get_sync_agent),
):
    """
    Clean up sync states for deleted files.

    Removes sync state and documents for files that no longer exist in the vault.
    """
    try:
        # Get agent with correct user_id
        settings = get_settings()
        upload_use_case = get_upload_document_use_case()
        delete_use_case = get_delete_document_use_case()

        agent = ObsidianSyncAgent(
            github_token=settings.github.github_token,
            repo_owner=settings.github.github_repo_owner,
            repo_name=settings.github.github_repo_name,
            branch=settings.github.github_branch,
            user_id=user_id,
            upload_use_case=upload_use_case,
            delete_use_case=delete_use_case,
        )

        cleaned = await agent.cleanup_deleted_files()

        return {"cleaned_files": cleaned}

    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
