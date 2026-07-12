"use client";

import { useState } from "react";

import { clearSessionTokens } from "@/lib/auth/session";

interface HeaderProps {
  title: string;
  description?: string;
}

export function Header({ title, description }: HeaderProps) {
  const [isSignedOut, setIsSignedOut] = useState(false);

  function handleLogout() {
    clearSessionTokens();
    setIsSignedOut(true);
  }

  return (
    <header className="border-b bg-background px-6 py-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          {description ? (
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-md border bg-card px-3 py-2 text-xs text-muted-foreground">
            Local session
          </div>
          <button
            className="h-9 rounded-md border px-3 text-sm font-medium transition hover:bg-accent"
            type="button"
            onClick={handleLogout}
          >
            Sign out
          </button>
        </div>
      </div>
      {isSignedOut ? (
        <p className="mt-3 text-sm text-muted-foreground" role="status">
          Session cleared. Return to the login page to sign in again.
        </p>
      ) : null}
    </header>
  );
}
