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
          description="Use the navigation to create workflows, inspect backend workflow records, run deterministic runtime execution, and watch live event timelines."
          items={[
            "Workflow list and detail views",
            "Procurement workflow creation",
            "Runtime run action and live event stream",
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
                  Available through the workflow pages using the existing
                  backend APIs.
                </p>
              </div>
            ),
          )}
        </section>
      </div>
    </AppShell>
  );
}
