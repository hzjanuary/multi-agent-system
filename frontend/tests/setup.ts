import { vi } from "vitest";

declare global {
  // React reads this flag in tests to decide whether act() warnings apply.
  // Vitest does not declare it by default.
  var IS_REACT_ACT_ENVIRONMENT: boolean;
}

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("next/navigation", () => ({
  usePathname: () => window.location.pathname,
}));

export {};
