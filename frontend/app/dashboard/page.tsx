import { AppShell } from "@/components/layout/app-shell";
import { PlaceholderSection } from "@/components/layout/placeholder-section";

export default function DashboardPage() {
  return (
    <AppShell
      title="Workflow dashboard"
      description="Operational shell for workflow status, runtime monitoring, and event streaming."
    >
      <div className="grid gap-6">
        <PlaceholderSection
          eyebrow="Dashboard"
          title="Ready for workflow operations"
          description="This shell is intentionally static for TASK 009.3. Workflow metrics, backend data, and runtime activity are added in later SPEC-009 tasks."
          items={[
            "Workflow list navigation",
            "Create workflow entry point",
            "Runtime event stream area",
          ]}
        />
        <section className="grid gap-4 md:grid-cols-3">
          {["Workflow creation", "Runtime monitoring", "Event streaming"].map(
            (item) => (
              <div
                className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm"
                key={item}
              >
                <h2 className="text-sm font-semibold">{item}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Placeholder section. No backend data is loaded in this task.
                </p>
              </div>
            ),
          )}
        </section>
      </div>
    </AppShell>
  );
}
