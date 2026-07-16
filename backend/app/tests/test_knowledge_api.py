"""API tests for knowledge search and catalog endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password
from app.auth.rbac import RoleName
from app.config import Settings, get_settings
from app.core.dependencies import (
    provide_db_session,
    provide_knowledge_retrieval_service,
)
from app.db import create_database_engine, create_session_factory
from app.knowledge.exceptions import (
    KnowledgeDocumentNotFoundError,
    KnowledgeRetrievalUnavailableError,
)
from app.knowledge.schemas import (
    KnowledgeCitation,
    KnowledgeDocumentCatalogItem,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentSourceType,
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.main import create_app
from app.models import Role, User

TEST_EMAIL_PREFIX = "knowledge-api"
TEST_ROLE_DESCRIPTION = "Knowledge API endpoint test role"


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session and clean committed knowledge API test users."""
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await cleanup_test_records(session)
    finally:
        await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Provide an HTTP client with retrieval dependencies overridden."""
    async with knowledge_client(db_session, FakeKnowledgeRetrievalService()) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
        RoleName.LEGAL,
        RoleName.FINANCE,
        RoleName.VIEWER,
    ],
)
async def test_read_roles_can_search_knowledge(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])

    response = await client.post(
        "/api/v1/knowledge/search",
        headers=auth_headers(user),
        json={
            "query": "manager approval discount",
            "top_k": 1,
            "source_types": ["policy"],
            "domain": "procurement",
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["query"] == "manager approval discount"
    assert len(data["results"]) == 1
    assert data["results"][0]["citation"]["document_title"] == (
        "Demo Procurement Policy"
    )
    assert "embedding" not in data["results"][0]
    assert "raw_prompt" not in str(data).lower()


@pytest.mark.asyncio
async def test_search_empty_results_are_valid(
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])
    async with knowledge_client(
        db_session,
        FakeKnowledgeRetrievalService(empty=True),
    ) as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            headers=auth_headers(user),
            json={"query": "nothing matches"},
        )

    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.asyncio
async def test_search_invalid_payload_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "   ", "top_k": 999},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_search_invalid_payload_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])

    response = await client.post(
        "/api/v1/knowledge/search",
        headers=auth_headers(user),
        json={"query": "   ", "top_k": 999},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "approval"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_retrieval_unavailable_maps_to_503(
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    async with knowledge_client(
        db_session,
        FakeKnowledgeRetrievalService(unavailable=True),
    ) as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            headers=auth_headers(user),
            json={"query": "approval"},
        )
    data = response.json()

    assert response.status_code == 503
    assert data["detail"]["code"] == "knowledge_retrieval_unavailable"


@pytest.mark.asyncio
async def test_document_catalog_list_and_detail(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.LEGAL])

    list_response = await client.get(
        "/api/v1/knowledge/documents",
        headers=auth_headers(user),
    )
    detail_response = await client.get(
        "/api/v1/knowledge/documents/demo-kb-procurement-policy",
        headers=auth_headers(user),
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1
    assert "content_preview" not in list_response.json()["documents"][0]
    assert detail_response.status_code == 200
    assert detail_response.json()["document"]["document_id"] == (
        "demo-kb-procurement-policy"
    )
    assert "Manager approval is required" in detail_response.json()["content_preview"]


@pytest.mark.asyncio
async def test_document_detail_missing_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.FINANCE])

    response = await client.get(
        "/api/v1/knowledge/documents/missing-document",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "knowledge_document_not_found"


@pytest.mark.asyncio
async def test_catalog_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/knowledge/documents")

    assert response.status_code == 401


def test_create_app_registers_knowledge_routes() -> None:
    app = create_app()
    route_paths = route_paths_for(app.routes)

    assert "/api/v1/knowledge/search" in route_paths
    assert "/api/v1/knowledge/documents" in route_paths
    assert "/api/v1/knowledge/documents/{document_id}" in route_paths


class FakeKnowledgeRetrievalService:
    """Retrieval service double for route tests."""

    def __init__(
        self,
        *,
        empty: bool = False,
        unavailable: bool = False,
    ) -> None:
        self.empty = empty
        self.unavailable = unavailable

    async def search(
        self,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        if self.unavailable:
            raise KnowledgeRetrievalUnavailableError("fake unavailable")
        if self.empty:
            return KnowledgeSearchResponse(query=request.query, results=())
        result = KnowledgeRetrievalResult(
            chunk_id="kbchunk:demo-kb-procurement-policy:0:abc123",
            document_id="demo-kb-procurement-policy",
            chunk_text="Manager approval is required for discounts.",
            score=0.91,
            source_type=KnowledgeDocumentSourceType.POLICY,
            document_title="Demo Procurement Policy",
            domain="procurement",
            citation=KnowledgeCitation(
                citation_id="citation:demo-kb-procurement-policy",
                document_id="demo-kb-procurement-policy",
                document_title="Demo Procurement Policy",
                source_type=KnowledgeDocumentSourceType.POLICY,
                excerpt="Manager approval is required for discounts.",
                relevance_score=0.91,
                citation_label="Demo Procurement Policy chunk 1",
            ),
            metadata={"demo_seed": True},
        )
        return KnowledgeSearchResponse(query=request.query, results=(result,))

    async def list_documents(self) -> KnowledgeDocumentListResponse:
        document = _catalog_item()
        return KnowledgeDocumentListResponse(documents=(document,), count=1)

    async def get_document(self, document_id: str) -> KnowledgeDocumentDetailResponse:
        if document_id != "demo-kb-procurement-policy":
            raise KnowledgeDocumentNotFoundError(f"{document_id} missing")
        return KnowledgeDocumentDetailResponse(
            document=_catalog_item(),
            content_preview="Manager approval is required for discounts.",
        )


def _catalog_item() -> KnowledgeDocumentCatalogItem:
    return KnowledgeDocumentCatalogItem(
        document_id="demo-kb-procurement-policy",
        title="Demo Procurement Policy",
        source_type=KnowledgeDocumentSourceType.POLICY,
        domain="procurement",
        version="2026.1",
        owner_team="Procurement Operations",
        checksum="abc123",
        tags=("demo", "policy"),
        attributes={"demo_seed": True},
    )


def knowledge_client(
    session: AsyncSession,
    retrieval_service: FakeKnowledgeRetrievalService,
) -> AsyncClient:
    """Return an API client with knowledge retrieval dependency override."""
    app = create_app(Settings())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    def override_knowledge_retrieval_service() -> FakeKnowledgeRetrievalService:
        return retrieval_service

    app.dependency_overrides[provide_db_session] = override_db_session
    app.dependency_overrides[provide_knowledge_retrieval_service] = (
        override_knowledge_retrieval_service
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


async def create_user_with_roles(
    session: AsyncSession,
    *,
    role_names: list[RoleName],
) -> User:
    """Create and commit a user with the requested exact RBAC role names."""
    roles = [await ensure_role(session, role_name) for role_name in role_names]
    user = User(
        email=f"{TEST_EMAIL_PREFIX}-{uuid4()}@example.test",
        hashed_password=hash_password("not-used-in-knowledge-api-tests"),
        full_name="Knowledge API Test User",
        is_active=True,
        roles=roles,
    )
    session.add(user)
    await session.commit()
    return user


async def ensure_role(session: AsyncSession, role_name: RoleName) -> Role:
    """Return an existing role or create one for endpoint tests."""
    role = await session.scalar(select(Role).where(Role.name == role_name.value))
    if role is not None:
        return role

    role = Role(
        name=role_name.value,
        description=TEST_ROLE_DESCRIPTION,
    )
    session.add(role)
    await session.flush()
    return role


def auth_headers(user: User) -> dict[str, str]:
    """Return bearer token authorization headers for a user."""
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


async def cleanup_test_records(session: AsyncSession) -> None:
    """Remove rows committed by knowledge API endpoint tests."""
    if session.in_transaction():
        await session.rollback()

    await session.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}-%")))
    await session.execute(delete(Role).where(Role.description == TEST_ROLE_DESCRIPTION))
    await session.commit()


def route_paths_for(routes: Iterable[object]) -> set[str]:
    """Return route paths including nested router paths."""
    paths: set[str] = set()
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)

        nested_prefix = ""
        include_context = getattr(route, "include_context", None)
        if include_context is not None:
            context_prefix = getattr(include_context, "prefix", "")
            if isinstance(context_prefix, str):
                nested_prefix = context_prefix

        nested_router = getattr(route, "original_router", route)
        nested_routes = getattr(nested_router, "routes", None)
        if isinstance(nested_routes, Iterable):
            paths.update(
                f"{nested_prefix}{nested_path}"
                for nested_path in route_paths_for(nested_routes)
            )

    return paths
