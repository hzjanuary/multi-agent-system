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
    <header className="border-b border-border/70 bg-background/70 px-4 py-3 backdrop-blur sm:px-6 md:py-5 lg:px-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between md:gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-foreground md:text-3xl">
            {title}
          </h1>
          {description ? (
            <p className="mt-1 max-w-4xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="ops-chip">
            Local session
          </div>
          <button
            className="ops-button-secondary min-h-9 px-3"
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
