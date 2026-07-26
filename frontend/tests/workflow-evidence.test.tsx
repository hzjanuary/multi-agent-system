import React, { act, type ReactElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { KnowledgeDocumentList } from "@/components/knowledge/knowledge-document-list";
import { KnowledgeSearchPanel } from "@/components/knowledge/knowledge-search-panel";
import {
  extractWorkflowCatalogMetadata,
  WorkflowCatalogMetadataPanel,
} from "@/components/workflows/workflow-catalog-metadata-panel";
import {
  extractWorkflowEvidence,
  WorkflowEvidencePanel,
} from "@/components/workflows/workflow-evidence-panel";
import {
  extractReferenceEvidence,
  WorkflowReferenceEvidencePanel,
} from "@/components/workflows/workflow-reference-evidence-panel";
import type {
  WorkflowEvent,
  WorkflowEvidenceCitation,
  WorkflowState,
} from "@/lib/api/types";

let root: Root | null = null;
let container: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => {
      root?.unmount();
    });
  }
  root = null;
  container?.remove();
  container = null;
  vi.restoreAllMocks();
});

describe("workflow evidence UI", () => {
  it("renders an honest empty state without fake citations", async () => {
    await render(<WorkflowEvidencePanel workflow={sampleWorkflow()} />);

    expect(document.body.textContent).toContain(
      "No retrieved evidence has been attached yet.",
    );
    expect(document.body.textContent).not.toContain("Demo citation");
  });

  it("renders runtime_context.rag citations grouped by stage", async () => {
    await render(
      <WorkflowEvidencePanel
        workflow={{
          ...sampleWorkflow(),
          runtime_context: {
            rag: {
              enabled: true,
              stages: {
                compliance: {
                  citations: [sampleCitation("compliance")],
                },
              },
            },
          },
        }}
      />,
    );

    expect(document.body.textContent).toContain("Compliance");
    expect(document.body.textContent).toContain("Procurement Policy");
    expect(document.body.textContent).toContain("POL-1 section 4");
    expect(document.body.textContent).toContain("Score 82%");
  });

  it("renders outputs and stage_outputs evidence", async () => {
    const workflow = {
      ...sampleWorkflow(),
      outputs: {
        evidence: {
          approval: [sampleCitation("approval", "approval-citation")],
        },
      },
      stage_outputs: {
        validation: {
          evidence: [sampleCitation("validation", "validation-citation")],
        },
      },
    };

    await render(<WorkflowEvidencePanel workflow={workflow} />);

    expect(document.body.textContent).toContain("Approval package");
    expect(document.body.textContent).toContain("Validation and finance");
    expect(document.body.textContent).toContain("approval-citation");
    expect(document.body.textContent).toContain("validation-citation");
  });

  it("extracts citations from grounding events only when citation objects exist", () => {
    const events: WorkflowEvent[] = [
      {
        event_id: "event-1",
        workflow_id: "workflow-1",
        event_type: "knowledge.grounding.completed",
        payload: {
          stage: "approval",
          citations: [sampleCitation("approval")],
          citation_ids: ["not-enough-to-render"],
        },
        created_at: "2026-07-13T10:00:00Z",
      },
      {
        event_id: "event-2",
        workflow_id: "workflow-1",
        event_type: "knowledge.grounding.completed",
        payload: { stage: "compliance", citation_ids: ["summary-only"] },
        created_at: "2026-07-13T10:01:00Z",
      },
    ];

    const citations = extractWorkflowEvidence(sampleWorkflow(), events);

    expect(citations).toHaveLength(1);
    expect(citations[0].stage).toBe("approval");
  });

  it("does not render raw embeddings, vector payloads, or prompt fields", async () => {
    await render(
      <WorkflowEvidencePanel
        workflow={{
          ...sampleWorkflow(),
          outputs: {
            evidence: {
              compliance: [
                {
                  ...sampleCitation("compliance"),
                  raw_prompt: "hidden prompt",
                  embedding_vector: [0.1, 0.2],
                  provider_payload: { unsafe: true },
                },
              ],
            },
          },
        }}
      />,
    );

    expect(document.body.textContent).toContain(
      "No retrieved evidence has been attached yet.",
    );
    expect(document.body.textContent).not.toContain("hidden prompt");
    expect(document.body.textContent).not.toContain("0.1");
  });

  it("bounds long excerpts in the rendered panel", async () => {
    const longCitation = {
      ...sampleCitation("compliance"),
      excerpt: "Evidence ".repeat(200),
    };

    await render(
      <WorkflowEvidencePanel
        workflow={{
          ...sampleWorkflow(),
          outputs: { evidence: { compliance: [longCitation] } },
        }}
      />,
    );

    expect(document.body.textContent).toContain("Evidence Evidence");
    expect(document.body.textContent).toContain("...");
  });
});

describe("workflow reference evidence UI", () => {
  it("does not fabricate reference evidence when no explicit field exists", async () => {
    const workflow = sampleWorkflow();

    expect(extractReferenceEvidence(workflow)).toBeNull();

    await render(<WorkflowReferenceEvidencePanel workflow={workflow} />);

    expect(document.body.textContent).not.toContain("Reference Price Evidence");
    expect(document.body.textContent).not.toContain("Reference only");
  });

  it("renders explicit reference evidence safely", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          outputs: {
            reference_price_research: sampleReferenceEvidence(),
          },
        })}
      />,
    );

    expect(document.body.textContent).toContain("Reference Price Evidence");
    expect(document.body.textContent).toContain("Reference evidence only");
    expect(document.body.textContent).toContain("Provider: tavily");
    expect(document.body.textContent).toContain("Confidence 72%");
    expect(document.body.textContent).toContain("Supplier reference listing");
    expect(document.body.textContent).toContain("https://supplier.example/laptops");
    expect(document.body.textContent).toContain("Manual pricing review is required.");
    expect(document.body.textContent).toContain(
      "Final quotation still requires Manager/Admin approval",
    );
  });

  it("renders explicit reference prices with review-only labeling", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          reference_price_research: {
            ...sampleReferenceEvidence(),
            reference_prices: [
              {
                label: "Unit reference",
                amount: "12000000",
                currency: "VND",
                unit: "unit",
                quantity_basis: 1,
              },
            ],
          },
        })}
      />,
    );

    expect(document.body.textContent).toContain("Unit reference");
    expect(document.body.textContent).toContain("12000000 VND");
    expect(document.body.textContent).toContain(
      "Reference only. Not customer-ready pricing.",
    );
    expect(document.body.textContent?.toLowerCase()).not.toContain(
      "approved quote",
    );
  });

  it("downgrades is_final_quote evidence and does not display amount", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          reference_price_research: {
            provider: "manual",
            evidence_label: "reference_price_research",
            is_final_quote: true,
            reference_prices: [
              {
                label: "Approved final quote",
                amount: "12000000",
                currency: "VND",
              },
            ],
          },
        })}
      />,
    );

    expect(document.body.textContent).toContain(
      "Evidence requires internal review",
    );
    expect(document.body.textContent).not.toContain("Approved final quote");
    expect(document.body.textContent).not.toContain("12000000");
  });

  it("bounds source list, titles, URLs, and warnings", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          runtime_context: {
            price_research: {
              ...sampleReferenceEvidence(),
              sources: [
                {
                  title: "Supplier " + "very long ".repeat(80),
                  url: "https://supplier.example/" + "path/".repeat(90),
                  snippet: "<strong>Safe snippet</strong>",
                },
                { title: "Second source", url: "https://supplier.example/2" },
                { title: "Third source", url: "https://supplier.example/3" },
                {
                  title: "Fourth source should not render",
                  url: "https://supplier.example/4",
                },
              ],
              warnings: [
                "Warning ".repeat(80),
                "Second warning",
                "Third warning",
                "Fourth warning should not render",
              ],
            },
          },
        })}
      />,
    );

    expect(document.body.textContent).toContain("Second source");
    expect(document.body.textContent).toContain("Third source");
    expect(document.body.textContent).not.toContain(
      "Fourth source should not render",
    );
    expect(document.body.textContent).not.toContain(
      "Fourth warning should not render",
    );
    expect(document.body.textContent).not.toContain("<strong>");
    expect(document.body.textContent).toContain("...");
  });

  it("redacts sensitive values and skips sensitive source objects", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          reference_evidence: {
            provider: "tavily",
            evidence_label: "reference_price_research",
            reference_prices: [
              {
                label: "raw_prompt chain-of-thought",
                amount: "12000000",
                currency: "VND",
              },
            ],
            sources: [
              {
                title: "provider_payload raw_response secret token",
                url: "https://supplier.example/?api_key=secret",
              },
              {
                title: "Unsafe object",
                provider_payload: { raw: true },
                url: "https://hidden.example",
              },
            ],
            warnings: ["authorization bearer token raw_provider"],
            confidence: 0.9,
          },
        })}
      />,
    );

    const text = document.body.textContent?.toLowerCase() ?? "";
    expect(text).toContain("[redacted]");
    expect(text).not.toContain("provider_payload");
    expect(text).not.toContain("raw_response");
    expect(text).not.toContain("raw_prompt");
    expect(text).not.toContain("api_key");
    expect(text).not.toContain("authorization");
    expect(text).not.toContain("bearer");
    expect(text).not.toContain("chain-of-thought");
    expect(text).not.toContain("https://hidden.example");
  });

  it("does not render forbidden positive claims from safe evidence UI", async () => {
    await render(
      <WorkflowReferenceEvidencePanel
        workflow={workflowWithEvidence({
          reference_price_research: sampleReferenceEvidence(),
        })}
      />,
    );

    const text = document.body.textContent?.toLowerCase() ?? "";
    const forbidden = [
      "approved quote",
      "approved quotation",
      "in stock",
      "stock available",
      "delivery date",
      "will deliver",
      "discount approved",
      "email sent",
    ];
    for (const claim of forbidden) {
      expect(text).not.toContain(claim);
    }
  });
});

describe("workflow catalog metadata UI", () => {
  it("does not fabricate catalog metadata when no explicit field exists", async () => {
    const workflow = sampleWorkflow();

    expect(extractWorkflowCatalogMetadata(workflow)).toBeNull();

    await render(<WorkflowCatalogMetadataPanel workflow={workflow} />);

    expect(document.body.textContent).not.toContain("Catalog Metadata");
    expect(document.body.textContent).not.toContain("Catalog match");
  });

  it("renders explicit catalog metadata safely", async () => {
    await render(
      <WorkflowCatalogMetadataPanel
        workflow={workflowWithEvidence({
          metadata: {
            attributes: {
              catalog: sampleCatalogMetadata(),
            },
          },
        })}
      />,
    );

    expect(document.body.textContent).toContain("Catalog Metadata");
    expect(document.body.textContent).toContain(
      "Deterministic catalog match",
    );
    expect(document.body.textContent).toContain("demo-catalog-v1");
    expect(document.body.textContent).toContain("Standard business laptop");
    expect(document.body.textContent).toContain("business_laptop");
    expect(document.body.textContent).toContain("Office 365");
    expect(document.body.textContent).toContain("not a final quotation");
    expect(document.body.textContent).toContain(
      "Manager/Admin approval",
    );
  });

  it("renders Agent Monitor-compatible catalog candidate paths", async () => {
    const catalog = extractWorkflowCatalogMetadata(
      workflowWithEvidence({
        request: {
          catalog_metadata: {
            itemId: "office_monitor",
            displayName: "Office monitor",
            itemFamily: "office_monitor",
            supportedAddons: [],
            catalogVersion: "demo-catalog-v1",
          },
        },
      }),
    );

    expect(catalog?.itemId).toBe("office_monitor");
    expect(catalog?.displayName).toBe("Office monitor");
    expect(catalog?.catalogVersion).toBe("demo-catalog-v1");
  });

  it("bounds and redacts catalog metadata values", async () => {
    await render(
      <WorkflowCatalogMetadataPanel
        workflow={workflowWithEvidence({
          metadata: {
            catalog: {
              catalog_version: "demo-catalog-v1",
              item_id: "business_desktop_pc",
              display_name: "Business desktop PC " + "safe ".repeat(80),
              normalized_item_name: "<strong>Business desktop PC</strong>",
              item_family: "business_desktop_pc",
              requested_addons: [
                "office_365",
                "microsoft_365",
                "raw_prompt secret token",
                "extra_addon_1",
                "extra_addon_2",
                "extra_addon_3",
                "extra_addon_4",
              ],
            },
          },
        })}
      />,
    );

    const text = document.body.textContent?.toLowerCase() ?? "";
    expect(text).toContain("business desktop pc");
    expect(text).toContain("...");
    expect(text).toContain("[redacted]");
    expect(text).not.toContain("<strong>");
    expect(text).not.toContain("raw_prompt");
    expect(text).not.toContain("secret");
    expect(text).not.toContain("token");
    expect(text).not.toContain("extra_addon_4");
  });

  it("does not render secret-shaped catalog objects", async () => {
    await render(
      <WorkflowCatalogMetadataPanel
        workflow={workflowWithEvidence({
          catalog: {
            item_id: "standard_business_laptop",
            display_name: "Standard business laptop",
            provider_payload: { raw: true },
          },
        })}
      />,
    );

    expect(document.body.textContent).not.toContain("Catalog Metadata");
    expect(document.body.textContent).not.toContain("provider_payload");
  });

  it("does not render forbidden positive claims from catalog metadata UI", async () => {
    await render(
      <WorkflowCatalogMetadataPanel
        workflow={workflowWithEvidence({
          metadata: {
            attributes: {
              catalog: sampleCatalogMetadata(),
            },
          },
        })}
      />,
    );

    const text = document.body.textContent?.toLowerCase() ?? "";
    const forbidden = [
      "final quote",
      "approved quote",
      "in stock",
      "stock available",
      "delivery date",
      "will deliver",
      "discount approved",
      "email sent",
    ];
    for (const claim of forbidden) {
      expect(text).not.toContain(claim);
    }
  });
});

describe("knowledge search and catalog UI", () => {
  it("renders knowledge search success and empty states", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        query: "procurement policy",
        results: [
          {
            chunk_id: "chunk-1",
            document_id: "demo-kb-procurement-policy",
            chunk_text: "Bounded policy evidence.",
            score: 0.91,
            source_type: "policy",
            document_title: "Procurement Policy",
            domain: "procurement",
            citation: sampleCitation("compliance"),
            metadata: {},
          },
        ],
      }),
    );

    await render(<KnowledgeSearchPanel token="access-token" />);
    await clickButton("Search");

    expect(fetchSpy.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/knowledge/search",
    );
    expect(document.body.textContent).toContain("Procurement Policy");
    expect(document.body.textContent).toContain("Score 91%");

    act(() => {
      root?.unmount();
    });
    root = null;
    container?.remove();
    container = null;

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ query: "missing", results: [] }),
    );

    await render(<KnowledgeSearchPanel token="access-token" />);
    await clickButton("Search");

    expect(document.body.textContent).toContain(
      "No knowledge results matched that query.",
    );
  });

  it("shows knowledge search 403 and 503 errors clearly", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: { message: "Forbidden" } }, 403, "Forbidden"),
    );

    await render(<KnowledgeSearchPanel token="access-token" />);
    await clickButton("Search");

    expect(document.body.textContent).toContain(
      "Your account cannot search the knowledge base.",
    );

    act(() => {
      root?.unmount();
    });
    root = null;
    container?.remove();
    container = null;

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        { detail: { message: "Knowledge retrieval provider is unavailable." } },
        503,
        "Service Unavailable",
      ),
    );

    await render(<KnowledgeSearchPanel token="access-token" />);
    await clickButton("Search");

    expect(document.body.textContent).toContain(
      "Knowledge retrieval is unavailable.",
    );
  });

  it("renders document catalog metadata", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        documents: [sampleDocument()],
        count: 1,
      }),
    );

    await render(<KnowledgeDocumentList token="access-token" />);

    expect(document.body.textContent).toContain("Procurement Policy");
    expect(document.body.textContent).toContain("policy / procurement");
    expect(document.body.textContent).toContain("ID: demo-kb-procurement-policy");
  });
});

async function render(element: ReactElement) {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);

  await act(async () => {
    root?.render(element);
  });
  await flushEffects();
}

async function clickButton(label: string) {
  const button = Array.from(document.querySelectorAll("button")).find(
    (candidate) => candidate.textContent === label,
  );
  if (!button) {
    throw new Error(`Expected button ${label} to exist`);
  }
  await act(async () => {
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await flushEffects();
}

async function flushEffects() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

function jsonResponse(
  payload: unknown,
  status = 200,
  statusText = "OK",
): Response {
  return new Response(JSON.stringify(payload), {
    status,
    statusText,
    headers: { "Content-Type": "application/json" },
  });
}

function sampleWorkflow(): WorkflowState {
  return {
    workflow_id: "workflow-1",
    workflow_type: "procurement_quotation",
    domain: "it_equipment",
    status: "WAITING_APPROVAL",
    request: { raw_text: "Need laptops" },
    metadata: {},
    current_step: "approval",
    retry_count: 0,
    created_at: "2026-07-13T10:00:00Z",
    updated_at: "2026-07-13T10:00:00Z",
  };
}

function workflowWithEvidence(extra: Record<string, unknown>): WorkflowState {
  return {
    ...sampleWorkflow(),
    ...extra,
  } as WorkflowState;
}

function sampleReferenceEvidence() {
  return {
    provider: "tavily",
    evidence_label: "reference_price_research",
    confidence: 0.72,
    retrieved_at: "2026-07-26T10:00:00Z",
    is_final_quote: false,
    sources: [
      {
        title: "Supplier reference listing",
        url: "https://supplier.example/laptops",
        snippet: "Reference source for manual review.",
      },
    ],
    reference_prices: [],
    warnings: ["Manual pricing review is required."],
  };
}

function sampleCatalogMetadata() {
  return {
    catalog_version: "demo-catalog-v1",
    item_id: "standard_business_laptop",
    display_name: "Standard business laptop",
    normalized_item_name: "Standard business laptop",
    item_family: "business_laptop",
    unit: "unit",
    demo_only: true,
    requested_addons: ["office_365"],
    supported_addons: ["office_365"],
  };
}

function sampleCitation(
  stage: string,
  citationId = "citation-demo-1",
): WorkflowEvidenceCitation {
  return {
    citation_id: citationId,
    document_id: "demo-kb-procurement-policy",
    document_title: "Procurement Policy",
    source_type: "policy",
    section: "POL-1 section 4",
    page: 2,
    excerpt: "Policy requires manager approval for discounted laptop purchases.",
    relevance_score: 0.82,
    citation_label:
      citationId === "citation-demo-1" ? "POL-1 section 4" : citationId,
    stage,
    reason: "compliance_policy_contract_checklist",
  };
}

function sampleDocument() {
  return {
    document_id: "demo-kb-procurement-policy",
    title: "Procurement Policy",
    source_type: "policy",
    domain: "procurement",
    version: "2026.1",
    effective_date: "2026-01-01",
    owner_team: "Procurement",
    object_storage_key: "demo/knowledge/demo-kb-procurement-policy.txt",
    checksum: "abc123",
    content_type: "text/plain",
    dataset_path: "datasets/policies/POLICY-DISCOUNT-APPROVAL.md",
    tags: ["demo"],
    attributes: {},
  };
}
