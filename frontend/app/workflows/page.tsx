import { AppShell } from "@/components/layout/app-shell";
import { PlaceholderSection } from "@/components/layout/placeholder-section";

export default function WorkflowsPage() {
  return (
    <AppShell
      title="Workflows"
      description="Workflow browsing placeholder for the next SPEC-009 slice."
    >
      <PlaceholderSection
        eyebrow="Workflows"
        title="Workflow list arrives in TASK 009.4"
        description="This route reserves the workflow browsing surface without calling the backend or rendering fake workflow data."
        items={[
          "Load workflows from GET /api/v1/workflows",
          "Show loading, empty, and error states",
          "Open workflow detail pages",
        ]}
      />
    </AppShell>
  );
}
