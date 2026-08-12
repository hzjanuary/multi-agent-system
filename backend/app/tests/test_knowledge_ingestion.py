"""Tests for demo knowledge ingestion orchestration."""

from __future__ import annotations

from app.demo.knowledge_documents import DEMO_KNOWLEDGE_DOCUMENTS
from app.knowledge.embeddings import EmbeddingSettings, FakeEmbeddingClient
from app.knowledge.ingestion import DemoKnowledgeIngestionService
from app.storage import StoredObject
from app.vectorstore import VectorPoint, VectorSearchResult


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.upload_calls = 0

    async def bucket_exists(self, bucket_name: str) -> bool:
        return any(bucket == bucket_name for bucket, _object_name in self.objects)

    async def create_bucket(self, bucket_name: str) -> None:
        return None

    async def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        self.upload_calls += 1
        self.objects[(bucket_name, object_name)] = data
        return StoredObject(
            bucket_name=bucket_name,
            object_name=object_name,
            size=len(data),
            content_type=content_type,
            etag="fake-etag",
        )

    async def download_bytes(self, bucket_name: str, object_name: str) -> bytes:
        return self.objects[(bucket_name, object_name)]

    async def delete_object(self, bucket_name: str, object_name: str) -> None:
        self.objects.pop((bucket_name, object_name), None)

    async def object_exists(self, bucket_name: str, object_name: str) -> bool:
        return (bucket_name, object_name) in self.objects

    async def close(self) -> None:
        return None


class FakeVectorStore:
    def __init__(self) -> None:
        self.collections: dict[str, int] = {}
        self.points: dict[str, dict[str, VectorPoint]] = {}
        self.upsert_calls = 0

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:
        self.collections[collection_name] = vector_size
        self.points.setdefault(collection_name, {})

    async def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.collections

    async def upsert(
        self,
        collection_name: str,
        points: list[VectorPoint],
    ) -> None:
        self.upsert_calls += 1
        collection = self.points.setdefault(collection_name, {})
        for point in points:
            collection[point.id] = point

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, object] | None = None,
    ) -> list[VectorSearchResult]:
        return []

    async def delete(self, collection_name: str, point_ids: list[str]) -> None:
        for point_id in point_ids:
            self.points.get(collection_name, {}).pop(point_id, None)

    async def close(self) -> None:
        return None


def _service(
    storage: FakeObjectStorage | None = None,
    vector_store: FakeVectorStore | None = None,
) -> tuple[DemoKnowledgeIngestionService, FakeObjectStorage, FakeVectorStore]:
    resolved_storage = storage or FakeObjectStorage()
    resolved_vector = vector_store or FakeVectorStore()
    service = DemoKnowledgeIngestionService(
        storage=resolved_storage,
        vector_store=resolved_vector,
        embedding_client=FakeEmbeddingClient(
            EmbeddingSettings(dimensions=8, batch_size=64),
        ),
        bucket_name="demo-bucket",
        collection_name="test_demo_knowledge",
    )
    return service, resolved_storage, resolved_vector


async def test_ingestion_dry_run_writes_nothing() -> None:
    service, storage, vector_store = _service()

    summary = await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS, dry_run=True)

    assert summary.dry_run is True
    assert summary.committed is False
    assert summary.documents_seen == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert summary.chunks_seen >= len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert summary.objects_created == 0
    assert summary.vectors_upserted == 0
    assert storage.objects == {}
    assert vector_store.points == {}


async def test_confirmed_ingestion_stores_objects_and_upserts_vectors() -> None:
    service, storage, vector_store = _service()

    summary = await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS)

    assert summary.committed is True
    assert summary.objects_created == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert summary.objects_reused == 0
    assert summary.vectors_upserted == summary.chunks_seen
    assert len(storage.objects) == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert vector_store.collections["test_demo_knowledge"] == 8
    assert len(vector_store.points["test_demo_knowledge"]) == summary.chunks_seen


async def test_repeated_ingestion_is_idempotent_for_objects_and_points() -> None:
    service, storage, vector_store = _service()

    first = await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS)
    second = await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS)

    assert first.chunk_ids == second.chunk_ids
    assert second.objects_created == 0
    assert second.objects_reused == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert len(storage.objects) == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert len(vector_store.points["test_demo_knowledge"]) == first.chunks_seen


async def test_vector_payloads_are_bounded_safe_and_deterministic() -> None:
    service, _storage, vector_store = _service()

    summary = await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS)
    points = list(vector_store.points["test_demo_knowledge"].values())
    first_point = points[0]

    assert len(first_point.vector) == 8
    assert first_point.payload["chunk_id"] in summary.chunk_ids
    assert first_point.payload["demo_seed"] is True
    assert first_point.payload["embedding_provider"] == "fake"
    assert "api_key" not in str(first_point.payload).lower()
    assert "raw_prompt" not in str(first_point.payload).lower()
    assert len(str(first_point.payload["text"])) <= 8000


async def test_vector_payloads_preserve_structured_demo_pricing_metadata() -> None:
    service, _storage, vector_store = _service()

    await service.ingest_documents(DEMO_KNOWLEDGE_DOCUMENTS)
    points = list(vector_store.points["test_demo_knowledge"].values())
    pricing_points = [
        point
        for point in points
        if point.payload.get("document_id") == "demo-kb-office-monitor-price"
    ]

    assert pricing_points
    payload = pricing_points[0].payload
    assert payload["observed_price"] == "3200000"
    assert payload["currency"] == "VND"
    assert payload["quantity_basis"] == 1
    assert payload["price_label"] == "Internal demo catalog unit price"
