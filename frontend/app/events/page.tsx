import { AppShell } from "@/components/layout/app-shell";
import { PlaceholderSection } from "@/components/layout/placeholder-section";

export default function RuntimeEventsPage() {
  return (
    <AppShell
      title="Runtime Events"
      description="Workflow-specific event timelines are available from each workflow detail page."
    >
      <PlaceholderSection
        eyebrow="Runtime Events"
        title="Open a workflow to watch its timeline"
        description="Live event streams are scoped to individual workflows. Choose a workflow from the list, then use its detail page to view persisted backlog and WebSocket updates."
        items={[
          "Persisted event backlog",
          "Live WebSocket updates",
          "Disconnected and reconnecting states",
        ]}
      />
    </AppShell>
  );
}
