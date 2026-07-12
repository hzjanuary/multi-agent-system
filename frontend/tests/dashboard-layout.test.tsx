import React, { act, type ReactElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import DashboardPage from "@/app/dashboard/page";
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
});

describe("dashboard shell", () => {
  it("shows a login-required state without a local access token", async () => {
    await render(<DashboardPage />);

    expect(document.body.textContent).toContain("Login required");
    expect(document.body.textContent).toContain("Go to login");
  });

  it("renders dashboard navigation for authenticated sessions", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");

    await render(<DashboardPage />);

    expect(document.body.textContent).toContain("Workflow dashboard");
    expect(document.body.textContent).toContain("Dashboard");
    expect(document.body.textContent).toContain("Workflows");
    expect(document.body.textContent).toContain("Create Workflow");
    expect(document.body.textContent).toContain("Runtime Events");
  });

  it("clears the local session when signing out", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "access-token");

    await render(<DashboardPage />);

    const button = document.querySelector("button");
    expect(button?.textContent).toBe("Sign out");

    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBeNull();
    expect(document.body.textContent).toContain("Session cleared");
  });
});

async function render(element: ReactElement) {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);

  await act(async () => {
    root?.render(element);
  });
}
