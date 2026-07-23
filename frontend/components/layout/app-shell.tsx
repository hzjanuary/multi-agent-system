"use client";

import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";

import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { isAuthenticated } from "@/lib/auth/session";

interface AppShellProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function AppShell({ title, description, children }: AppShellProps) {
  const [hasSession, setHasSession] = useState<boolean | null>(null);

  useEffect(() => {
    setHasSession(isAuthenticated());
  }, []);

  if (hasSession === null) {
    return (
      <main className="ops-page flex items-center justify-center px-6">
        <div className="ops-panel px-6 py-5">
          <p className="ops-kicker">Session check</p>
          <p className="mt-2 text-sm text-muted-foreground">Checking session...</p>
        </div>
      </main>
    );
  }

  if (!hasSession) {
    return (
      <main className="ops-page flex items-center justify-center px-6">
        <section className="ops-panel-strong w-full max-w-md p-6">
          <p className="ops-kicker">
            Login required
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">
            Sign in to open the workflow dashboard.
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            The console uses the local demo session from the login page. Sign
            in to load workflow, agent monitor, approval, and evidence views.
          </p>
          <Link
            className="ops-button-primary mt-5"
            href="/login"
          >
            Go to login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <div className="ops-page md:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Header title={title} description={description} />
        <main className="px-4 py-4 sm:px-6 md:py-5 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
