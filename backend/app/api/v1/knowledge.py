"""Knowledge base read/search API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.workflow_errors import workflow_error_detail
from app.auth.rbac import RoleName, require_roles
from app.core.dependencies import provide_knowledge_retrieval_service
from app.knowledge.exceptions import (
    KnowledgeDocumentNotFoundError,
    KnowledgeRetrievalUnavailableError,
)
from app.knowledge.retrieval import KnowledgeRetrievalService
from app.knowledge.schemas import (
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentListResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.models import User

KNOWLEDGE_READ_ROLES: tuple[RoleName, ...] = (
    RoleName.ADMIN,
    RoleName.MANAGER,
    RoleName.SALES,
    RoleName.LEGAL,
    RoleName.FINANCE,
    RoleName.VIEWER,
)

KnowledgeReadAccessDependency = Annotated[
    User,
    Depends(require_roles(*KNOWLEDGE_READ_ROLES)),
]
KnowledgeRetrievalServiceDependency = Annotated[
    KnowledgeRetrievalService,
    Depends(provide_knowledge_retrieval_service),
]

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search knowledge base",
)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    _current_user: KnowledgeReadAccessDependency,
    retrieval_service: KnowledgeRetrievalServiceDependency,
) -> KnowledgeSearchResponse:
    """Search indexed knowledge chunks with safe citation results."""
    try:
        return await retrieval_service.search(payload)
    except KnowledgeRetrievalUnavailableError as error:
        raise knowledge_unavailable_http_exception() from error


@router.get(
    "/documents",
    response_model=KnowledgeDocumentListResponse,
    summary="List knowledge documents",
)
async def list_knowledge_documents(
    _current_user: KnowledgeReadAccessDependency,
    retrieval_service: KnowledgeRetrievalServiceDependency,
) -> KnowledgeDocumentListResponse:
    """Return bounded deterministic knowledge document catalog metadata."""
    return await retrieval_service.list_documents()


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
    summary="Get knowledge document",
)
async def get_knowledge_document(
    document_id: str,
    _current_user: KnowledgeReadAccessDependency,
    retrieval_service: KnowledgeRetrievalServiceDependency,
) -> KnowledgeDocumentDetailResponse:
    """Return bounded metadata and preview for one knowledge document."""
    try:
        return await retrieval_service.get_document(document_id)
    except KnowledgeDocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=workflow_error_detail(
                code="knowledge_document_not_found",
                message=str(error),
            ),
        ) from error


def knowledge_unavailable_http_exception() -> HTTPException:
    """Return a safe unavailable response for retrieval provider failures."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=workflow_error_detail(
            code="knowledge_retrieval_unavailable",
            message="Knowledge retrieval provider is unavailable.",
        ),
    )


__all__ = [
    "KNOWLEDGE_READ_ROLES",
    "KnowledgeReadAccessDependency",
    "KnowledgeRetrievalServiceDependency",
    "knowledge_unavailable_http_exception",
    "router",
]
