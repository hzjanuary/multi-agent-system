"use client";

import { FormEvent, useState } from "react";

import { ApiClientError } from "@/lib/api/client";
import { login } from "@/lib/api/auth";
import { setSessionTokens } from "@/lib/auth/session";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSignedIn, setIsSignedIn] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setIsSignedIn(false);

    try {
      const tokens = await login({ email, password });
      setSessionTokens(tokens);
      setIsSignedIn(true);
    } catch (caughtError) {
      setError(userFacingError(caughtError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center gap-8 px-6 py-16">
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium text-muted-foreground">
            Enterprise Multi-Agent OS
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Sign in
          </h1>
          <p className="text-sm leading-6 text-muted-foreground">
            Use your backend account credentials to start a local development
            dashboard session.
          </p>
        </div>

        <form
          className="flex flex-col gap-4 rounded-lg border bg-card p-6 text-card-foreground shadow-sm"
          onSubmit={handleSubmit}
        >
          <label className="flex flex-col gap-2 text-sm font-medium">
            Email
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background transition focus-visible:ring-2 focus-visible:ring-ring"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="flex flex-col gap-2 text-sm font-medium">
            Password
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background transition focus-visible:ring-2 focus-visible:ring-ring"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button
            className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          {isSignedIn ? (
            <p className="text-sm text-muted-foreground" role="status">
              Signed in. Dashboard navigation is implemented in a later task.
            </p>
          ) : null}
        </form>
      </section>
    </main>
  );
}

function userFacingError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Unable to sign in. Check your credentials and try again.";
}
