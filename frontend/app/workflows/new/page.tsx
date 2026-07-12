import { AppShell } from "@/components/layout/app-shell";
import { PlaceholderSection } from "@/components/layout/placeholder-section";

export default function CreateWorkflowPage() {
  return (
    <AppShell
      title="Create Workflow"
      description="Procurement quotation workflow creation placeholder."
    >
      <PlaceholderSection
        eyebrow="Create Workflow"
        title="Creation form arrives in TASK 009.5"
        description="This route keeps the navigation target honest without submitting workflow requests or inventing backend data."
        items={[
          "Manual procurement request text",
          "POST /api/v1/workflows integration",
          "Run workflow action after creation",
        ]}
      />
    </AppShell>
  );
}
