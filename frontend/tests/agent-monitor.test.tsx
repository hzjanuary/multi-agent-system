import { act, type ReactElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import AgentMonitorPage from "@/app/agent-monitor/page";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/lib/auth/session";
import type { WorkflowStatus } from "@/lib/api/types";

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
  window.localStorage.clear();
  vi.restoreAllMocks();
  MockWebSocket.instances = [];
});

describe("agent monitor page", () => {
  it("renders login-required without a session", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    await render(await AgentMonitorPage({ searchParams: Promise.resolve({}) }));

    expect(document.body.textContent).toContain("Login required");
    expect(document.body.textContent).toContain("Go to login");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("shows recent workflow and demo shortcut mode with a session", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    window.history.pushState({}, "", "/agent-monitor");
    mockFetchSequence([
      {
        workflows: [sampleWorkflow("workflow-recent-1", "WAITING_APPROVAL")],
        count: 1,
        limit: 8,
        offset: 0,
        status: null,
      },
    ]);

    await render(await AgentMonitorPage({ searchParams: Promise.resolve({}) }));

    expect(document.body.textContent).toContain("Agent Monitor");
    expect(document.body.textContent).toContain("Live demo observer mode");
    expect(document.body.textContent).toContain("Seeded demo shortcuts");
    expect(document.body.textContent).toContain("Run from CREATED");
    expect(document.body.textContent).toContain("Recent workflows");
    expect(document.body.textContent).toContain("workflow-recent-1");
    expect(document.body.textContent).toContain("Agent Monitor");
    expect(
      document.querySelector('a[aria-current="page"]')?.textContent,
    ).toBe("Agent Monitor");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/workflows?limit=8&offset=0",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("renders monitor view for a selected workflow", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    window.history.pushState({}, "", "/agent-monitor?workflowId=workflow-123");
    installMockWebSocket();
    mockFetchSequence([
      { workflow: sampleWorkflow("workflow-123", "WAITING_APPROVAL") },
      {
        events: [
          {
            event_id: "event-1",
            workflow_id: "workflow-123",
            event_type: "workflow.node.completed",
            agent_name: "planner",
            status: "completed",
            message: "Planner completed",
            payload: { stage: "planner" },
            created_at: "2026-07-13T10:01:00Z",
          },
        ],
        count: 1,
        limit: 25,
        offset: 0,
      },
      emptyHistory("workflow-123"),
    ]);

    await render(
      await AgentMonitorPage({
        searchParams: Promise.resolve({ workflowId: "workflow-123" }),
      }),
    );

    expect(document.body.textContent).toContain("Observed workflow");
    expect(document.body.textContent).toContain("workflow-123");
    expect(document.body.textContent).toContain("WAITING_APPROVAL");
    expect(document.body.textContent).toContain("What should I do next?");
    expect(document.body.textContent).toContain("Agent activity");
    expect(document.body.textContent).toContain("Planner Agent");
    expect(document.body.textContent).toContain("Event timeline");
    expect(document.body.textContent).toContain("Planner completed");
    expect(document.body.textContent).toContain("Open full detail");
    expect(document.body.textContent).toContain("Approve / resume");
    expect(MockWebSocket.instances[0].url).toBe(
      "ws://localhost:8000/api/v1/workflows/workflow-123/stream?access_token=access-token",
    );
  });

  it("renders selected workflow reference evidence when explicitly present", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    window.history.pushState({}, "", "/agent-monitor?workflowId=workflow-evidence");
    installMockWebSocket();
    mockFetchSequence([
      {
        workflow: {
          ...sampleWorkflow("workflow-evidence", "WAITING_APPROVAL"),
          outputs: {
            reference_price_research: {
              provider: "rag",
              evidence_label: "reference_price_research",
              confidence: 0.66,
              is_final_quote: false,
              sources: [
                {
                  title: "Internal catalog source",
                  url: "https://catalog.example/source",
                  snippet: "Reference evidence for review.",
                },
              ],
              reference_prices: [
                {
                  label: "Catalog reference",
                  amount: "12000000",
                  currency: "VND",
                  unit: "unit",
                },
              ],
              warnings: ["Manual review required."],
            },
          },
        },
      },
      { events: [], count: 0, limit: 25, offset: 0 },
      emptyHistory("workflow-evidence"),
    ]);

    await render(
      await AgentMonitorPage({
        searchParams: Promise.resolve({ workflowId: "workflow-evidence" }),
      }),
    );

    expect(document.body.textContent).toContain("Reference Price Evidence");
    expect(document.body.textContent).toContain("Provider: rag");
    expect(document.body.textContent).toContain("Catalog reference");
    expect(document.body.textContent).toContain("12000000 VND");
    expect(document.body.textContent).toContain("Internal catalog source");
    expect(document.body.textContent).not.toContain("Reference evidence for review.");
  });

  it("renders selected workflow catalog metadata when explicitly present", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    window.history.pushState({}, "", "/agent-monitor?workflowId=workflow-catalog");
    installMockWebSocket();
    mockFetchSequence([
      {
        workflow: {
          ...sampleWorkflow("workflow-catalog", "WAITING_APPROVAL"),
          metadata: {
            attributes: {
              catalog: sampleCatalogMetadata(),
            },
          },
        },
      },
      { events: [], count: 0, limit: 25, offset: 0 },
      emptyHistory("workflow-catalog"),
    ]);

    await render(
      await AgentMonitorPage({
        searchParams: Promise.resolve({ workflowId: "workflow-catalog" }),
      }),
    );

    expect(document.body.textContent).toContain("Catalog Metadata");
    expect(document.body.textContent).toContain("Office printer");
    expect(document.body.textContent).toContain("office_printer");
    expect(document.body.textContent).toContain("Demo catalog");
    expect(document.body.textContent).toContain("not a final quotation");
  });

  it("does not render sensitive raw fields from workflow state or events", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    installMockWebSocket();
    mockFetchSequence([
      {
        workflow: {
          ...sampleWorkflow("workflow-sensitive", "WAITING_APPROVAL"),
          runtime_context: {
            completed_stages: ["planner"],
            raw_prompt: "hidden runtime prompt",
            token: "hidden-runtime-token",
          },
          stage_outputs: {
            planner: {
              summary: "Safe planner summary.",
              provider_payload: { text: "hidden provider payload" },
              embedding_vector: [0.123, 0.456],
              secret: "hidden-stage-secret",
            },
          },
        },
      },
      {
        events: [
          {
            event_id: "event-sensitive",
            workflow_id: "workflow-sensitive",
            event_type: "workflow.node.completed",
            agent_name: "planner",
            status: "completed",
            message: "Safe event message.",
            payload: {
              stage: "planner",
              raw_prompt: "hidden event prompt",
              vector_payload: [0.1, 0.2],
              access_token: "hidden-event-token",
              safe_label: "visible-label",
            },
            created_at: "2026-07-13T10:01:00Z",
          },
        ],
        count: 1,
        limit: 25,
        offset: 0,
      },
      emptyHistory("workflow-sensitive"),
    ]);

    await render(
      await AgentMonitorPage({
        searchParams: Promise.resolve({ workflowId: "workflow-sensitive" }),
      }),
    );

    expect(document.body.textContent).toContain("Safe planner summary.");
    expect(document.body.textContent).toContain("visible-label");
    expect(document.body.textContent).not.toContain("hidden runtime prompt");
    expect(document.body.textContent).not.toContain("hidden-runtime-token");
    expect(document.body.textContent).not.toContain("hidden provider payload");
    expect(document.body.textContent).not.toContain("hidden-stage-secret");
    expect(document.body.textContent).not.toContain("hidden event prompt");
    expect(document.body.textContent).not.toContain("hidden-event-token");
    expect(document.body.textContent).not.toContain("0.123");
    expect(document.body.textContent).not.toContain("0.1");
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

async function flushEffects() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

function mockFetchSequence(payloads: unknown[]) {
  const responses = payloads.map(
    (payload) =>
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
  );
  vi.spyOn(globalThis, "fetch").mockImplementation(() => {
    const response = responses.shift();
    if (!response) {
      throw new Error("Unexpected fetch call");
    }
    return Promise.resolve(response);
  });
}

function sampleWorkflow(workflowId: string, status: WorkflowStatus) {
  return {
    workflow_id: workflowId,
    workflow_type: "procurement_quotation",
    domain: "it_equipment",
    status,
    request: { raw_text: "Need 50 standard laptops" },
    metadata: { state_version: 1 },
    customer: { name: "Acme Manufacturing Group" },
    items: [{ name: "Laptop", quantity: 50 }],
    current_step: status === "CREATED" ? null : "approval",
    retry_count: 0,
    created_at: "2026-07-13T10:00:00Z",
    updated_at: "2026-07-13T10:00:00Z",
  };
}

function sampleCatalogMetadata() {
  return {
    catalog_version: "demo-catalog-v1",
    item_id: "office_printer",
    display_name: "Office printer",
    normalized_item_name: "Office printer",
    item_family: "office_printer",
    unit: "unit",
    demo_only: true,
    requested_addons: [],
  };
}

function emptyHistory(workflowId: string) {
  return {
    workflow_id: workflowId,
    approvals: [],
    has_final_decision: false,
    can_resume: false,
  };
}

function installMockWebSocket() {
  vi.stubGlobal("WebSocket", MockWebSocket);
}

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  readonly url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}
