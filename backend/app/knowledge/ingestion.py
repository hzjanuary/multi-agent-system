"""Demo knowledge ingestion orchestration for MinIO and Qdrant."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge.chunking import chunk_document
from app.knowledge.embeddings import (
    EmbeddingBatchResult,
    EmbeddingClient,
    EmbeddingSettings,
)
from app.knowledge.exceptions import KnowledgeIngestionConfigurationError
from app.knowledge.schemas import (
    ChunkingConfig,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentSourceType,
    validate_json_metadata,
)
from app.storage import ObjectStorageProvider
from app.vectorstore import VectorPoint, VectorStore

DEFAULT_KNOWLEDGE_COLLECTION_NAME = "demo_procurement_knowledge"
DEMO_KNOWLEDGE_BUCKET_PREFIX = "demo/knowledge"
KNOWLEDGE_POINT_NAMESPACE = UUID("20c844b1-f585-4f1e-8095-73fe09ef0d6c")
MAX_PAYLOAD_TEXT_CHARS = 8000


class KnowledgeIngestionSummary(BaseModel):
    """Bounded summary for demo knowledge ingestion."""

    model_config = ConfigDict(frozen=True)

    demo_only_warning: str = (
        "LOCAL DEMO KNOWLEDGE ONLY - do not use as production ingestion."
    )
    dry_run: bool = False
    committed: bool = False
    collection_name: str = Field(min_length=1, max_length=120)
    embedding_model: str = Field(min_length=1, max_length=200)
    embedding_dimensions: int = Field(ge=1, le=4096)
    documents_seen: int = 0
    chunks_seen: int = 0
    objects_created: int = 0
    objects_reused: int = 0
    vectors_upserted: int = 0
    document_ids: tuple[str, ...] = Field(default_factory=tuple)
    object_keys: tuple[str, ...] = Field(default_factory=tuple)
    chunk_ids: tuple[str, ...] = Field(default_factory=tuple)


class DemoKnowledgeIngestionService:
    """Chunk, embed, store, and upsert deterministic demo knowledge documents."""

    def __init__(
        self,
        *,
        storage: ObjectStorageProvider,
        vector_store: VectorStore,
        embedding_client: EmbeddingClient,
        bucket_name: str,
        collection_name: str = DEFAULT_KNOWLEDGE_COLLECTION_NAME,
        chunking_config: ChunkingConfig | None = None,
    ) -> None:
        if not bucket_name.strip():
            raise KnowledgeIngestionConfigurationError("bucket_name must not be blank")
        if not collection_name.strip():
            raise KnowledgeIngestionConfigurationError(
                "collection_name must not be blank"
            )
        self._storage = storage
        self._vector_store = vector_store
        self._embedding_client = embedding_client
        self._bucket_name = bucket_name
        self._collection_name = collection_name
        self._chunking_config = chunking_config or ChunkingConfig()

    async def ingest_documents(
        self,
        documents: Sequence[KnowledgeDocument],
        *,
        dry_run: bool = False,
    ) -> KnowledgeIngestionSummary:
        """Ingest demo knowledge documents with deterministic chunks and vectors."""
        if not documents:
            raise KnowledgeIngestionConfigurationError(
                "at least one demo knowledge document is required"
            )

        chunks_by_document = [
            chunk_document(document, self._chunking_config) for document in documents
        ]
        chunks = tuple(
            chunk for result in chunks_by_document for chunk in result.chunks
        )
        document_ids = tuple(document.metadata.document_id for document in documents)
        object_keys = tuple(
            _object_key_for_document(document) for document in documents
        )
        chunk_ids = tuple(chunk.metadata.chunk_id for chunk in chunks)

        if dry_run:
            return KnowledgeIngestionSummary(
                dry_run=True,
                committed=False,
                collection_name=self._collection_name,
                embedding_model=self._embedding_client.model,
                embedding_dimensions=self._embedding_client.dimensions,
                documents_seen=len(documents),
                chunks_seen=len(chunks),
                document_ids=document_ids,
                object_keys=object_keys,
                chunk_ids=chunk_ids,
            )

        objects_created = 0
        objects_reused = 0
        for document, object_key in zip(documents, object_keys, strict=True):
            if await self._storage.object_exists(self._bucket_name, object_key):
                objects_reused += 1
            else:
                objects_created += 1
            await self._storage.upload_bytes(
                self._bucket_name,
                object_key,
                document.content.encode("utf-8"),
                content_type=document.metadata.content_type or "text/plain",
            )

        if not await self._vector_store.collection_exists(self._collection_name):
            await self._vector_store.create_collection(
                self._collection_name,
                vector_size=self._embedding_client.dimensions,
            )

        embeddings = await self._embedding_client.embed_texts(
            tuple(chunk.text for chunk in chunks)
        )
        points = [
            VectorPoint(
                id=_point_id_for_chunk(chunk),
                vector=list(embedding.vector),
                payload=_payload_for_chunk(chunk, embedding_settings=embeddings),
            )
            for chunk, embedding in zip(chunks, embeddings.results, strict=True)
        ]
        await self._vector_store.upsert(self._collection_name, points)

        return KnowledgeIngestionSummary(
            dry_run=False,
            committed=True,
            collection_name=self._collection_name,
            embedding_model=self._embedding_client.model,
            embedding_dimensions=self._embedding_client.dimensions,
            documents_seen=len(documents),
            chunks_seen=len(chunks),
            objects_created=objects_created,
            objects_reused=objects_reused,
            vectors_upserted=len(points),
            document_ids=document_ids,
            object_keys=object_keys,
            chunk_ids=chunk_ids,
        )


def _object_key_for_document(document: KnowledgeDocument) -> str:
    if document.metadata.object_storage_key:
        return document.metadata.object_storage_key
    return f"{DEMO_KNOWLEDGE_BUCKET_PREFIX}/{document.metadata.document_id}.txt"


def _point_id_for_chunk(chunk: KnowledgeChunk) -> str:
    return str(uuid5(KNOWLEDGE_POINT_NAMESPACE, chunk.metadata.chunk_id))


def _payload_for_chunk(
    chunk: KnowledgeChunk,
    *,
    embedding_settings: EmbeddingBatchResult,
) -> dict[str, object]:
    metadata = chunk.metadata
    payload: dict[str, object] = {
        "document_id": metadata.document_id,
        "title": metadata.citation_label.rsplit(" chunk ", 1)[0],
        "source_type": metadata.source_type.value,
        "domain": metadata.domain,
        "checksum": metadata.checksum,
        "chunk_id": metadata.chunk_id,
        "chunk_index": metadata.chunk_index,
        "citation_label": metadata.citation_label,
        "character_count": metadata.character_count,
        "text": chunk.text[:MAX_PAYLOAD_TEXT_CHARS],
        "embedding_provider": embedding_settings.provider.value,
        "embedding_model": embedding_settings.model,
        "embedding_dimensions": embedding_settings.dimensions,
        **metadata.attributes,
        "demo_seed": True,
        "demo_reference_only": True,
    }
    if metadata.section:
        payload["section"] = metadata.section
    if metadata.page:
        payload["page"] = metadata.page
    validate_json_metadata(payload, "vector payload")
    return payload


def source_type_counts(
    documents: Sequence[KnowledgeDocument],
) -> dict[KnowledgeDocumentSourceType, int]:
    """Return deterministic source type counts for tests and summaries."""
    counts: dict[KnowledgeDocumentSourceType, int] = {}
    for document in documents:
        source_type = document.metadata.source_type
        counts[source_type] = counts.get(source_type, 0) + 1
    return counts


def default_embedding_settings() -> EmbeddingSettings:
    """Return safe embedding defaults for ingestion tests."""
    return EmbeddingSettings()


__all__ = [
    "DEFAULT_KNOWLEDGE_COLLECTION_NAME",
    "DemoKnowledgeIngestionService",
    "KnowledgeIngestionSummary",
    "default_embedding_settings",
    "source_type_counts",
]
