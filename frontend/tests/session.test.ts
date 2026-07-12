import { beforeEach, describe, expect, it } from "vitest";

import {
  clearSessionTokens,
  getAccessToken,
  getRefreshToken,
  isAuthenticated,
  setAccessToken,
  setRefreshToken,
  setSessionTokens,
} from "@/lib/auth/session";

describe("session token helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("stores and reads access and refresh tokens", () => {
    setSessionTokens({
      access_token: "access-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
    });

    expect(getAccessToken()).toBe("access-token");
    expect(getRefreshToken()).toBe("refresh-token");
    expect(isAuthenticated()).toBe(true);
  });

  it("clears stored tokens", () => {
    setAccessToken("access-token");
    setRefreshToken("refresh-token");

    clearSessionTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });
});
