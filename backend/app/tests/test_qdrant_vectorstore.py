"""Integration tests for the Qdrant vector store provider."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from app.config import get_settings
from app.vectorstore import (
    QdrantVectorStore,
    VectorPoint,
    VectorStore,
    create_qdrant_vector_store,
)


@pytest.fixture
async def qdrant_store() -> AsyncIterator[tuple[QdrantVectorStore, str]]:
    """Provide a Qdrant store with an isolated collection name."""
    store = create_qdrant_vector_store(str(get_settings().qdrant_url))
    collection_name = f"test_vectors_{uuid4().hex}"
    try:
        yield store, collection_name
    finally:
        await store.delete_collection(collection_name)
        await store.close()


def test_qdrant_vector_store_satisfies_protocol() -> None:
    vector_store: VectorStore = create_qdrant_vector_store(
        str(get_settings().qdrant_url),
    )

    assert isinstance(vector_store, VectorStore)


@pytest.mark.asyncio
async def test_qdrant_create_collection_and_collection_exists(
    qdrant_store: tuple[QdrantVectorStore, str],
) -> None:
    store, collection_name = qdrant_store

    assert await store.collection_exists(collection_name) is False

    await store.create_collection(collection_name, vector_size=3)

    assert await store.collection_exists(collection_name) is True


@pytest.mark.asyncio
async def test_qdrant_upsert_search_and_delete_behavior(
    qdrant_store: tuple[QdrantVectorStore, str],
) -> None:
    store, collection_name = qdrant_store
    first_point_id = str(uuid4())
    second_point_id = str(uuid4())
    await store.create_collection(collection_name, vector_size=3)

    await store.upsert(
        collection_name,
        [
            VectorPoint(
                id=first_point_id,
                vector=[1.0, 0.0, 0.0],
                payload={"tenant": "alpha"},
            ),
            VectorPoint(
                id=second_point_id,
                vector=[0.0, 1.0, 0.0],
                payload={"tenant": "beta"},
            ),
        ],
    )

    results = await store.search(
        collection_name,
        query_vector=[1.0, 0.0, 0.0],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].id == first_point_id
    assert results[0].payload == {"tenant": "alpha"}

    await store.delete(collection_name, point_ids=[first_point_id])
    results_after_delete = await store.search(
        collection_name,
        query_vector=[1.0, 0.0, 0.0],
        limit=10,
    )

    assert [result.id for result in results_after_delete] == [second_point_id]


@pytest.mark.asyncio
async def test_qdrant_search_filters_payloads(
    qdrant_store: tuple[QdrantVectorStore, str],
) -> None:
    store, collection_name = qdrant_store
    public_point_id = str(uuid4())
    private_point_id = str(uuid4())
    await store.create_collection(collection_name, vector_size=2)
    await store.upsert(
        collection_name,
        [
            VectorPoint(
                id=public_point_id,
                vector=[1.0, 0.0],
                payload={"tag": "public"},
            ),
            VectorPoint(
                id=private_point_id,
                vector=[1.0, 0.0],
                payload={"tag": "private"},
            ),
        ],
    )

    results = await store.search(
        collection_name,
        query_vector=[1.0, 0.0],
        filters={"tag": "private"},
    )

    assert [result.id for result in results] == [private_point_id]


@pytest.mark.asyncio
async def test_qdrant_health_check(
    qdrant_store: tuple[QdrantVectorStore, str],
) -> None:
    store, _collection_name = qdrant_store

    assert await store.health_check() is True
