"""
Chat conversation endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.application.dtos.chat_dto import ChatRequest, ChatResponse
from src.application.use_cases.chat_use_case import ChatUseCase
from src.presentation.api.dependencies import get_chat_use_case
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """
    Send a message and receive a response from the AI assistant (FAST).

    This endpoint uses background processing for optimal performance:
    - Generates quick response using RAG (~4 seconds)
    - Extracts memories and entities in background (async)

    The response is returned immediately while extractions continue.

    Args:
        request: Chat request with user message and parameters
        background_tasks: FastAPI background tasks
        chat_use_case: Injected chat use case

    Returns:
        Chat response with assistant message and metadata

    Raises:
        HTTPException: If chat processing fails
    """
    try:
        logger.info(
            "chat_request_received",
            user_id=request.user_id,
            conversation_id=str(request.conversation_id) if request.conversation_id else None,
        )

        # Execute quick response (without blocking extractions)
        response = await chat_use_case.execute_quick(request)

        # Schedule background extractions
        background_tasks.add_task(
            chat_use_case.extract_background_data,
            conversation_id=str(response.conversation_id),
            user_id=request.user_id,
        )

        logger.info(
            "chat_response_sent",
            conversation_id=str(response.conversation_id),
            background_extraction=True,
        )

        return response

    except Exception as e:
        logger.error(
            "chat_request_failed",
            user_id=request.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}",
        )


@router.get("/conversations/{conversation_id}", status_code=200)
async def get_conversation(conversation_id: UUID):
    """
    Retrieve a conversation by ID.

    Args:
        conversation_id: Conversation identifier

    Returns:
        Conversation details

    Raises:
        HTTPException: If conversation not found
    """
    # TODO: Implement get conversation endpoint
    raise HTTPException(
        status_code=501,
        detail="Get conversation endpoint not yet implemented",
    )


@router.get("/conversations/user/{user_id}", status_code=200)
async def list_user_conversations(user_id: str, limit: int = 10):
    """
    List conversations for a user.

    Args:
        user_id: User identifier
        limit: Maximum number of conversations to return

    Returns:
        List of conversations

    Raises:
        HTTPException: If retrieval fails
    """
    # TODO: Implement list conversations endpoint
    raise HTTPException(
        status_code=501,
        detail="List conversations endpoint not yet implemented",
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID):
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation identifier

    Raises:
        HTTPException: If deletion fails
    """
    # TODO: Implement delete conversation endpoint
    raise HTTPException(
        status_code=501,
        detail="Delete conversation endpoint not yet implemented",
    )
