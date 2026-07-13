const readinessItems = [
  "Next.js App Router",
  "TypeScript",
  "Tailwind CSS",
  "shadcn/ui-ready structure",
] as const;

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-10 px-6 py-16">
        <div className="flex flex-col gap-5">
          <p className="text-sm font-medium text-muted-foreground">
            Frontend bootstrap
          </p>
          <div className="flex max-w-3xl flex-col gap-4">
            <h1 className="text-4xl font-semibold tracking-tight text-foreground md:text-6xl">
              Enterprise Multi-Agent OS
            </h1>
            <p className="text-lg leading-8 text-muted-foreground">
              A Next.js dashboard foundation for operating procurement
              workflows, runtime progress, and live event streams.
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
            <h2 className="text-xl font-semibold">Bootstrap status</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              The SPEC-009 dashboard foundation is in place with workflow
              browsing, creation, runtime actions, and live event monitoring.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
            <h2 className="text-xl font-semibold">Prepared foundation</h2>
            <ul className="mt-4 flex flex-col gap-3 text-sm text-muted-foreground">
              {readinessItems.map((item) => (
                <li key={item} className="flex items-center gap-3">
                  <span className="size-2 rounded-full bg-primary" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </main>
  );
}
