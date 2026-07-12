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
      <main className="flex min-h-screen items-center justify-center bg-background px-6">
        <p className="text-sm text-muted-foreground">Checking session...</p>
      </main>
    );
  }

  if (!hasSession) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-6">
        <section className="w-full max-w-md rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">
            Login required
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">
            Sign in to open the workflow dashboard.
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            The dashboard shell uses the local development MVP session from the
            login page. Workflow data loading is implemented in later tasks.
          </p>
          <Link
            className="mt-5 inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-95"
            href="/login"
          >
            Go to login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30 md:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Header title={title} description={description} />
        <main className="px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
