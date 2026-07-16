"""Provider-independent knowledge retrieval service."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
from math import isfinite

from app.demo.knowledge_documents import DEMO_KNOWLEDGE_DOCUMENTS
from app.knowledge.embeddings import EmbeddingService
from app.knowledge.exceptions import (
    KnowledgeDocumentNotFoundError,
    KnowledgeEmbeddingError,
    KnowledgeRetrievalUnavailableError,
)
from app.knowledge.ingestion import DEFAULT_KNOWLEDGE_COLLECTION_NAME
from app.knowledge.schemas import (
    MAX_CITATION_EXCERPT_CHARS,
    MAX_SEARCH_TOP_K,
    KnowledgeCitation,
    KnowledgeDocument,
    KnowledgeDocumentCatalogItem,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentSourceType,
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    validate_json_metadata,
)
from app.vectorstore import VectorSearchResult, VectorStore
from app.vectorstore.exceptions import VectorStoreError


class KnowledgeRetrievalService:
    """Embed search queries and normalize vector results into citations."""

    def __init__(
        self,
        *,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        collection_name: str = DEFAULT_KNOWLEDGE_COLLECTION_NAME,
        documents: Sequence[KnowledgeDocument] = DEMO_KNOWLEDGE_DOCUMENTS,
    ) -> None:
        if not collection_name.strip():
            raise KnowledgeRetrievalUnavailableError(
                "collection_name must not be blank"
            )
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._collection_name = collection_name
        self._documents = tuple(documents)

    async def search(
        self,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        """Search indexed knowledge chunks and return bounded citation results."""
        try:
            if not await self._vector_store.collection_exists(self._collection_name):
                return KnowledgeSearchResponse(query=request.query, results=())

            embedding = await self._embedding_service.embed_text(request.query)
            raw_results = await self._vector_store.search(
                self._collection_name,
                list(embedding.vector),
                limit=_candidate_limit(request),
                filters=_native_filters(request),
            )
        except (KnowledgeEmbeddingError, VectorStoreError) as error:
            raise KnowledgeRetrievalUnavailableError(
                "Knowledge retrieval provider is unavailable",
            ) from error

        normalized_results = [
            result
            for result in (
                _result_from_vector(raw_result) for raw_result in raw_results
            )
            if result is not None and _matches_request_filters(result, request)
        ]
        return KnowledgeSearchResponse(
            query=request.query,
            results=tuple(normalized_results[: request.top_k]),
        )

    async def list_documents(self) -> KnowledgeDocumentListResponse:
        """Return bounded deterministic demo document catalog metadata."""
        documents = tuple(
            KnowledgeDocumentCatalogItem.from_metadata(document.metadata)
            for document in self._documents
        )
        return KnowledgeDocumentListResponse(
            documents=documents,
            count=len(documents),
        )

    async def get_document(self, document_id: str) -> KnowledgeDocumentDetailResponse:
        """Return one bounded demo document catalog entry by deterministic id."""
        for document in self._documents:
            if document.metadata.document_id == document_id:
                return KnowledgeDocumentDetailResponse(
                    document=KnowledgeDocumentCatalogItem.from_metadata(
                        document.metadata,
                    ),
                    content_preview=_bounded_excerpt(document.content),
                )
        raise KnowledgeDocumentNotFoundError(
            f"Knowledge document {document_id} was not found",
        )


def _candidate_limit(request: KnowledgeSearchRequest) -> int:
    if _requires_service_side_filtering(request):
        return min(MAX_SEARCH_TOP_K, max(request.top_k, request.top_k * 4))
    return request.top_k


def _requires_service_side_filtering(request: KnowledgeSearchRequest) -> bool:
    return len(request.source_types) > 1 or len(request.document_ids) > 1


def _native_filters(request: KnowledgeSearchRequest) -> dict[str, object] | None:
    filters: dict[str, object] = {}
    if len(request.source_types) == 1:
        filters["source_type"] = request.source_types[0].value
    if request.domain is not None:
        filters["domain"] = request.domain
    if len(request.document_ids) == 1:
        filters["document_id"] = request.document_ids[0]
    return filters or None


def _result_from_vector(
    raw_result: VectorSearchResult,
) -> KnowledgeRetrievalResult | None:
    payload = raw_result.payload
    try:
        chunk_id = _payload_string(payload, "chunk_id")
        document_id = _payload_string(payload, "document_id")
        document_title = _payload_string(payload, "title")
        source_type = KnowledgeDocumentSourceType(
            _payload_string(payload, "source_type")
        )
        domain = _payload_string(payload, "domain")
        chunk_text = _bounded_chunk_text(_payload_string(payload, "text"))
        score = _bounded_score(raw_result.score)
        citation = KnowledgeCitation(
            citation_id=_citation_id_for_chunk(chunk_id),
            document_id=document_id,
            document_title=document_title,
            source_type=source_type,
            section=_payload_optional_string(payload, "section"),
            page=_payload_optional_int(payload, "page"),
            excerpt=_bounded_excerpt(chunk_text),
            relevance_score=score,
            citation_label=_payload_string(payload, "citation_label"),
        )
        metadata = _safe_result_metadata(payload)
        return KnowledgeRetrievalResult(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_text=chunk_text,
            score=score,
            source_type=source_type,
            document_title=document_title,
            domain=domain,
            citation=citation,
            metadata=metadata,
        )
    except (TypeError, ValueError):
        return None


def _payload_string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"payload field {key} must be a non-empty string")
    return value.strip()


def _payload_optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _payload_optional_int(payload: dict[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, int) and value >= 1:
        return value
    return None


def _bounded_score(score: float) -> float:
    if not isfinite(score):
        return 0.0
    return min(max(round(float(score), 6), 0.0), 1.0)


def _bounded_chunk_text(text: str) -> str:
    return text[:MAX_CITATION_EXCERPT_CHARS].strip()


def _bounded_excerpt(text: str) -> str:
    return text[:MAX_CITATION_EXCERPT_CHARS].strip()


def _citation_id_for_chunk(chunk_id: str) -> str:
    citation_id = f"citation:{chunk_id}"
    if len(citation_id) <= 160:
        return citation_id
    return f"citation:{sha256(chunk_id.encode('utf-8')).hexdigest()[:24]}"


def _safe_result_metadata(payload: dict[str, object]) -> dict[str, object]:
    allowed_keys = (
        "chunk_index",
        "checksum",
        "embedding_provider",
        "embedding_model",
        "embedding_dimensions",
        "demo_seed",
        "demo_reference_only",
        "version",
    )
    metadata = {key: payload[key] for key in allowed_keys if key in payload}
    return validate_json_metadata(metadata, "retrieval metadata")


def _matches_request_filters(
    result: KnowledgeRetrievalResult,
    request: KnowledgeSearchRequest,
) -> bool:
    if request.source_types and result.source_type not in set(request.source_types):
        return False
    if request.domain is not None and result.domain != request.domain:
        return False
    if request.document_ids and result.document_id not in set(request.document_ids):
        return False
    return not (
        request.minimum_score is not None and result.score < request.minimum_score
    )


__all__ = ["KnowledgeRetrievalService"]
