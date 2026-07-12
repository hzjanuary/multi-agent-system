import { describe, expect, it, vi } from "vitest";

import { apiFetch, buildApiUrl } from "@/lib/api/client";
import { login } from "@/lib/api/auth";

describe("buildApiUrl", () => {
  it("builds URLs with normalized paths and query values", () => {
    const url = buildApiUrl(
      "workflows",
      { limit: 25, offset: 0, status: "CREATED", empty: undefined },
      "http://api.test/api/v1",
    );

    expect(url).toBe(
      "http://api.test/api/v1/workflows?limit=25&offset=0&status=CREATED",
    );
  });
});

describe("apiFetch", () => {
  it("attaches bearer tokens and JSON bodies", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await apiFetch<{ ok: boolean }>("/auth/login", {
      method: "POST",
      body: { email: "sales@example.com", password: "secret" },
      token: "access-token",
      baseUrl: "http://api.test/api/v1",
      fetcher,
    });

    const [, init] = fetcher.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer access-token");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init?.body).toBe(
      JSON.stringify({ email: "sales@example.com", password: "secret" }),
    );
  });

  it("raises safe typed errors for non-2xx responses", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid credentials" }), {
        status: 401,
        statusText: "Unauthorized",
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      apiFetch("/auth/me", {
        baseUrl: "http://api.test/api/v1",
        fetcher,
      }),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 401,
      message: "Invalid credentials",
    });
  });
});

describe("auth API", () => {
  it("uses the backend login endpoint", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "access",
          refresh_token: "refresh",
          token_type: "bearer",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    const response = await login(
      { email: "admin@example.com", password: "password" },
      { baseUrl: "http://api.test/api/v1", fetcher },
    );

    expect(fetcher.mock.calls[0][0]).toBe("http://api.test/api/v1/auth/login");
    expect(response.access_token).toBe("access");
    expect(response.refresh_token).toBe("refresh");
  });
});
