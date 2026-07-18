import React, { act, type ReactElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkflowDetailView } from "@/components/workflows/workflow-detail-view";
import { WorkflowListView } from "@/components/workflows/workflow-list-view";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/lib/auth/session";

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

describe("workflow pages", () => {
  it("shows login-required state when no token exists", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    await render(<WorkflowListView />);

    expect(document.body.textContent).toContain("Login required");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("renders loaded workflow rows without fake data", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    mockFetchSequence([
      {
        workflows: [sampleWorkflow("11111111-2222-3333-4444-555555555555")],
        count: 1,
        limit: 100,
        offset: 0,
        status: null,
      },
    ]);

    await render(<WorkflowListView />);

    expect(document.body.textContent).toContain("Demo workflow chooser");
    expect(document.body.textContent).toContain("Run from CREATED");
    expect(document.body.textContent).toContain("procurement_quotation");
    expect(document.body.textContent).toContain("CREATED");
    expect(document.body.textContent).toContain("View detail");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/workflows?limit=100&offset=0",
      expect.objectContaining({
        method: "GET",
      }),
    );
  });

  it("renders an empty workflow state", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    mockFetchSequence([{ workflows: [], count: 0, limit: 100, offset: 0 }]);

    await render(<WorkflowListView />);

    expect(document.body.textContent).toContain("No workflows yet");
  });

  it("renders workflow detail and recent events", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    installMockWebSocket();
    mockFetchSequence([
      { workflow: sampleWorkflow("workflow-123") },
      {
        events: [
          {
            event_id: "event-1",
            workflow_id: "workflow-123",
            event_type: "runtime.started",
            agent_name: "planner",
            status: "completed",
            message: "Runtime started",
            payload: {},
            created_at: "2026-07-13T10:01:00Z",
          },
        ],
        count: 1,
        limit: 25,
        offset: 0,
      },
      {
        workflow_id: "workflow-123",
        approvals: [],
        has_final_decision: false,
        can_resume: false,
      },
      {
        documents: [],
        count: 0,
      },
    ]);

    await render(<WorkflowDetailView workflowId="workflow-123" />);

    expect(document.body.textContent).toContain("What should I do next?");
    expect(document.body.textContent).toContain("This workflow has not run yet.");
    expect(document.body.textContent).toContain("Agent activity");
    expect(document.body.textContent).toContain("Planner Agent");
    expect(document.body.textContent).toContain("workflow-123");
    expect(document.body.textContent).toContain("Request summary");
    expect(document.body.textContent).toContain("Approval history");
    expect(document.body.textContent).toContain("Evidence and citations");
    expect(document.body.textContent).toContain("No retrieved evidence has been attached yet.");
    expect(document.body.textContent).toContain("Search demo knowledge");
    expect(document.body.textContent).toContain("Demo documents");
    expect(document.body.textContent).toContain("Event timeline");
    expect(document.body.textContent).toContain("runtime.started");
    expect(document.body.textContent).toContain("Runtime started");
    expect(MockWebSocket.instances[0].url).toBe(
      "ws://localhost:8000/api/v1/workflows/workflow-123/stream?access_token=access-token",
    );
  });

  it("renders a bounded API error", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Forbidden" }), {
        status: 403,
        statusText: "Forbidden",
        headers: { "Content-Type": "application/json" },
      }),
    );

    await render(<WorkflowListView />);

    expect(document.body.textContent).toContain(
      "Your account does not have workflow read access.",
    );
  });
});

async function render(element: ReactElement) {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);

  await act(async () => {
    root?.render(element);
  });
  await act(async () => {
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

function sampleWorkflow(workflowId: string) {
  return {
    workflow_id: workflowId,
    workflow_type: "procurement_quotation",
    domain: "it_equipment",
    status: "CREATED",
    request: { raw_text: "Need 50 standard laptops" },
    metadata: { state_version: 1 },
    customer: { name: "Acme Manufacturing Group" },
    items: [{ name: "Laptop", quantity: 50 }],
    current_step: "planner",
    retry_count: 0,
    created_at: "2026-07-13T10:00:00Z",
    updated_at: "2026-07-13T10:00:00Z",
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
