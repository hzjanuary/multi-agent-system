# RAG Knowledge Flow Diagram

```mermaid
flowchart LR
    Docs["Deterministic demo\nknowledge documents"]
    Chunker["Character chunking\nstable checksums"]
    FakeEmb["Fake embeddings\ndefault/no-key"]
    MinIO[("MinIO source objects")]
    Qdrant[("Qdrant chunk vectors")]
    SearchAPI["Knowledge search/catalog API"]
    Retrieval["KnowledgeRetrievalService"]
    RuntimeGrounding["Runtime grounding adapter\nRAG_ENABLED=true"]
    WorkflowState["Workflow state\nbounded evidence/citations"]
    FrontendEvidence["Workflow evidence panel"]
    FrontendSearch["Knowledge search/catalog panels"]
    Disabled["RAG_ENABLED=false\nno runtime retrieval"]

    Docs --> Chunker
    Chunker --> FakeEmb
    Docs --> MinIO
    FakeEmb --> Qdrant
    SearchAPI --> Retrieval
    Retrieval --> Qdrant
    Retrieval --> FakeEmb
    Retrieval --> FrontendSearch
    Retrieval --> RuntimeGrounding
    RuntimeGrounding --> WorkflowState
    WorkflowState --> FrontendEvidence
    Disabled -. "default behavior" .-> WorkflowState
```

This diagram shows the RAG path from deterministic demo documents through
chunking, fake embeddings, MinIO, Qdrant, retrieval, runtime grounding, and
frontend evidence views. Runtime grounding is optional and disabled by default.

It matters for the report because it explains how compliance, finance, and
approval stages can show citations without requiring live LLM keys or exposing
raw embeddings, vector payloads, prompts, or full documents.

Related docs: `.ai/specs/SPEC-013-rag-document-knowledge-base/spec.md`,
`docs/demo/DATASET_INVENTORY.md`, and
`docs/report/ARCHITECTURE_AND_DESIGN.md`.
