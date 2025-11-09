"""
Document management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.application.dtos.document_dto import (
    DocumentSearchRequest,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from src.application.use_cases.document_use_cases import (
    DeleteDocumentUseCase,
    SearchDocumentsUseCase,
    UploadDocumentUseCase,
)
from src.presentation.api.dependencies import (
    get_delete_document_use_case,
    get_document_repository,
    get_search_documents_use_case,
    get_upload_document_use_case,
)
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    user_id: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    tags: str = Form(default=""),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case),
):
    """
    Upload and process a document for the knowledge base.

    Supports: PDF, TXT, MD files.

    Args:
        user_id: User identifier
        title: Document title
        file: File to upload
        tags: Comma-separated tags (optional)
        use_case: Injected upload use case

    Returns:
        Document upload response with chunk count

    Raises:
        HTTPException: If upload fails
    """
    try:
        logger.info(
            "upload_document_request",
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type,
        )

        # Read file content
        file_content = await file.read()

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # Create request
        request = DocumentUploadRequest(
            user_id=user_id,
            title=title,
            tags=tag_list,
        )

        # Execute upload
        response = await use_case.execute(request, file_content, file.filename or "document")

        logger.info(
            "document_uploaded",
            doc_id=str(response.doc_id),
            num_chunks=response.num_chunks,
        )

        return response

    except Exception as e:
        logger.error("upload_document_failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.post("/documents/search")
async def search_documents(
    request: DocumentSearchRequest,
    use_case: SearchDocumentsUseCase = Depends(get_search_documents_use_case),
):
    """
    Search for documents by semantic similarity.

    Args:
        request: Document search request
        use_case: Injected search use case

    Returns:
        List of (DocumentChunkResponse, similarity_score) tuples

    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(
            "search_documents_request",
            query=request.query[:50],
            user_id=request.user_id,
            limit=request.limit,
        )

        results = await use_case.execute(request)

        logger.info("documents_search_completed", count=len(results))

        return results

    except Exception as e:
        logger.error("search_documents_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}",
        )


@router.get("/documents/user/{user_id}")
async def get_user_documents(
    user_id: str,
    limit: int = 100,
    document_repo=Depends(get_document_repository),
):
    """
    Retrieve all documents for a user (grouped by doc_id).

    Args:
        user_id: User identifier
        limit: Maximum number of document chunks to fetch
        document_repo: Injected document repository

    Returns:
        List of unique documents with their metadata
    """
    try:
        logger.info("get_user_documents_request", user_id=user_id, limit=limit)

        # Get recent documents using scroll
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        filter_conditions = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            ]
        )

        results, _ = await document_repo.client.client.scroll(
            collection_name=document_repo.collection_name,
            scroll_filter=filter_conditions,
            limit=limit,
            with_vectors=False,
        )

        # Group chunks by doc_id to get unique documents
        docs_by_id = {}
        for point in results:
            payload = point.payload
            doc_id = payload["doc_id"]

            if doc_id not in docs_by_id:
                docs_by_id[doc_id] = {
                    "doc_id": doc_id,
                    "user_id": payload["user_id"],
                    "title": payload.get("title", ""),
                    "path": payload.get("path", ""),
                    "tags": payload.get("tags", []),
                    "created_at": payload.get("created_at", ""),
                    "updated_at": payload.get("updated_at", ""),
                    "source_type": payload.get("source_type", ""),
                    "chunk_count": 0,
                    "total_chars": 0,
                }

            # Increment counters
            docs_by_id[doc_id]["chunk_count"] += 1
            docs_by_id[doc_id]["total_chars"] += payload.get("char_count", 0)

        # Convert to list and sort by updated_at
        documents = list(docs_by_id.values())
        documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)

        logger.info("user_documents_retrieved", count=len(documents))

        return documents

    except Exception as e:
        logger.error("get_user_documents_failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user documents: {str(e)}",
        )


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    user_id: str,
    use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case),
):
    """
    Delete a document and all its chunks.

    Args:
        doc_id: Document identifier
        user_id: User ID for authorization
        use_case: Injected delete use case

    Raises:
        HTTPException: If deletion fails or document not found
    """
    try:
        deleted = await use_case.execute(doc_id, user_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("document_deleted", doc_id=str(doc_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_document_failed", doc_id=str(doc_id), error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}",
        )
