import { AppShell } from "@/components/layout/app-shell";
import { PlaceholderSection } from "@/components/layout/placeholder-section";

export default function RuntimeEventsPage() {
  return (
    <AppShell
      title="Runtime Events"
      description="Event stream viewer placeholder for persisted and live workflow updates."
    >
      <PlaceholderSection
        eyebrow="Runtime Events"
        title="Live timeline arrives in TASK 009.6"
        description="No WebSocket connection is opened in this task. The route only reserves the event monitoring surface."
        items={[
          "Persisted workflow event backlog",
          "WS /api/v1/workflows/{workflow_id}/stream",
          "Disconnected and reconnecting states",
        ]}
      />
    </AppShell>
  );
}
