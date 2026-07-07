"""Qdrant-backed vector store provider."""

from typing import Any, cast

from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings
from app.vectorstore.base import VectorStore
from app.vectorstore.exceptions import VectorStoreOperationError
from app.vectorstore.schemas import VectorPoint, VectorSearchResult


class QdrantVectorStore(VectorStore):
    """VectorStore implementation backed by an async Qdrant client."""

    def __init__(self, client: AsyncQdrantClient) -> None:
        self._client = client

    @classmethod
    def from_url(cls, qdrant_url: str) -> "QdrantVectorStore":
        """Create a provider from a Qdrant URL."""
        return cls(AsyncQdrantClient(url=qdrant_url))

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:
        """Create a vector collection with cosine distance."""
        try:
            await self._client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception as error:
            raise VectorStoreOperationError(
                "Qdrant create_collection operation failed",
            ) from error

    async def collection_exists(self, collection_name: str) -> bool:
        """Return whether a collection exists."""
        try:
            return await self._client.collection_exists(collection_name)
        except Exception as error:
            raise VectorStoreOperationError(
                "Qdrant collection_exists operation failed",
            ) from error

    async def upsert(
        self,
        collection_name: str,
        points: list[VectorPoint],
    ) -> None:
        """Insert or replace vector points in a collection."""
        try:
            await self._client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=dict(point.payload),
                    )
                    for point in points
                ],
            )
        except Exception as error:
            raise VectorStoreOperationError("Qdrant upsert operation failed") from error

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, object] | None = None,
    ) -> list[VectorSearchResult]:
        """Return vector search results ordered by relevance."""
        try:
            response = await self._client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=build_filter(filters),
                limit=limit,
                with_payload=True,
            )
        except Exception as error:
            raise VectorStoreOperationError("Qdrant search operation failed") from error

        return [
            VectorSearchResult(
                id=str(point.id),
                score=point.score,
                payload=dict(point.payload or {}),
            )
            for point in response.points
        ]

    async def delete(
        self,
        collection_name: str,
        point_ids: list[str],
    ) -> None:
        """Delete points by id from a collection."""
        try:
            await self._client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=cast(Any, point_ids)),
            )
        except Exception as error:
            raise VectorStoreOperationError("Qdrant delete operation failed") from error

    async def close(self) -> None:
        """Close the Qdrant client."""
        try:
            await self._client.close()
        except Exception as error:
            raise VectorStoreOperationError("Qdrant close operation failed") from error

    async def health_check(self) -> bool:
        """Return whether Qdrant responds to a health check."""
        try:
            await self._client.get_collections()
        except Exception as error:
            raise VectorStoreOperationError(
                "Qdrant health check failed",
            ) from error
        return True

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection. Intended for test cleanup and maintenance tasks."""
        try:
            if await self._client.collection_exists(collection_name):
                await self._client.delete_collection(collection_name)
        except Exception as error:
            raise VectorStoreOperationError(
                "Qdrant delete_collection operation failed",
            ) from error


def create_qdrant_vector_store(qdrant_url: str | None = None) -> QdrantVectorStore:
    """Create a Qdrant vector store from settings or an explicit URL."""
    settings = get_settings()
    return QdrantVectorStore.from_url(qdrant_url or str(settings.qdrant_url))


def build_filter(filters: dict[str, object] | None) -> models.Filter | None:
    """Convert exact-match metadata filters into a Qdrant filter."""
    if not filters:
        return None

    conditions = [
        models.FieldCondition(
            key=key,
            match=models.MatchValue(value=normalize_filter_value(value)),
        )
        for key, value in filters.items()
    ]
    return models.Filter(must=cast(Any, conditions))


def normalize_filter_value(value: object) -> bool | int | str:
    """Return a Qdrant exact-match filter value."""
    if isinstance(value, bool | int | str):
        return value
    return str(value)
