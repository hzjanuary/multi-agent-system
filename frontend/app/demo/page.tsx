import Link from "next/link";

import { DemoWorkflowCards } from "@/components/demo/demo-workflow-cards";
import { demoWorkflows, localDemoAccounts, workflowLifecycle } from "@/lib/demo";

export default function DemoPage() {
  return (
    <main className="ops-page">
      <section className="mx-auto grid w-full max-w-7xl gap-8 px-5 py-8 sm:px-6 lg:px-8">
        <div className="ops-panel-strong grid gap-5 p-5 md:p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div className="max-w-4xl">
            <p className="ops-kicker">Evaluator start here</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground md:mt-4 md:text-6xl">
              Start the defense demo.
            </h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              This is not a chatbot. It is a procurement workflow orchestration
              system with deterministic workflow state, specialized runtime
              stages, human approval, evidence/citations, persisted events, and
              production-demo operations.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link className="ops-button-primary" href="/login">
              Go to Login
            </Link>
            <Link className="ops-button-secondary" href="/workflows">
              Open Workflows
            </Link>
            <Link
              className="ops-button-secondary"
              href={`/workflows/${demoWorkflows[0].workflowId}`}
            >
              Full demo: Created workflow
            </Link>
          </div>
        </div>

        <section className="ops-panel p-5 md:p-6">
          <h2 className="text-lg font-semibold">Operation map</h2>
          <div className="mt-5 grid gap-2 md:grid-cols-6">
            {workflowLifecycle.map((step, index) => (
              <div
                className="relative rounded-md border border-primary/20 bg-background/60 p-3 text-center md:p-4"
                key={step}
              >
                <p className="text-xs font-medium text-primary">
                  Step {index + 1}
                </p>
                <p className="mt-2 text-sm font-semibold">{step}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            The runtime intentionally stops at WAITING_APPROVAL. Review the
            workflow details, evidence, and event timeline before submitting a
            human approval decision. Resume is a separate action after approval.
          </p>
        </section>

        <section className="grid gap-4 lg:grid-cols-4">
          {localDemoAccounts.map((account) => (
            <article
              className="ops-panel p-5"
              key={account.email}
            >
              <p className="ops-kicker">
                {account.role}
              </p>
              <h3 className="mt-2 break-all text-base font-semibold">
                {account.email}
              </h3>
              <p className="mt-2 break-all rounded-md border border-border/70 bg-background/70 px-3 py-2 font-mono text-xs text-muted-foreground">
                {account.password}
              </p>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {account.recommendation}
              </p>
            </article>
          ))}
        </section>

        <section className="grid gap-4">
          <div>
            <h2 className="text-lg font-semibold">Choose a seeded workflow</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              These IDs come from the explicit local demo seed. They are links
              to backend workflow records, not fabricated frontend data.
            </p>
          </div>
          <DemoWorkflowCards />
        </section>

        <section className="ops-panel-strong p-5 md:p-6">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="ops-kicker">
                Phone-to-system path
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Telegram Live Demo
              </h2>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                A customer actor sends a Telegram message from a phone. The
                local bridge polls Telegram, creates a backend workflow, calls
                /run, and the deterministic runtime stops at WAITING_APPROVAL.
                Evaluators can then watch the workflow in Agent Monitor, submit
                Manager approval, resume, and verify COMPLETED.
              </p>
              <div className="mt-5 grid gap-2 md:grid-cols-7">
                {[
                  "Phone message",
                  "Telegram bridge",
                  "Create workflow",
                  "/run",
                  "WAITING_APPROVAL",
                  "Agent Monitor",
                  "Approve / Resume / COMPLETED",
                ].map((step) => (
                  <div
                    className="rounded-md border border-primary/20 bg-background/60 p-2.5 text-center text-xs font-semibold leading-5 text-muted-foreground md:p-3"
                    key={step}
                  >
                    {step}
                  </div>
                ))}
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link className="ops-button-primary" href="/agent-monitor">
                  Open Agent Monitor
                </Link>
                <Link className="ops-button-secondary" href="/login">
                  Login as Manager
                </Link>
                <Link className="ops-button-secondary" href="/workflows">
                  View Workflows
                </Link>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="ops-panel-muted p-4">
                <h3 className="text-sm font-semibold">Message to send</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  We would like to purchase 50 standard business laptops for a
                  new operations team. We signed a master agreement in May
                  2026. Please provide your best quotation with the applicable
                  discount.
                </p>
              </div>
              <div className="ops-panel-muted p-4">
                <h3 className="text-sm font-semibold">
                  Local bridge command
                </h3>
                <code className="ops-code mt-3">
                  TELEGRAM_BOT_TOKEN=... python
                  scripts/demo/telegram_inbound_bridge.py
                </code>
                <p className="mt-3 text-xs leading-5 text-muted-foreground">
                  Full setup reference: docs/demo/TELEGRAM_INBOUND_DEMO.md
                </p>
              </div>
              <div className="ops-panel-muted p-4">
                <h3 className="text-sm font-semibold">Safety boundaries</h3>
                <ul className="mt-3 grid gap-2 text-sm leading-6 text-muted-foreground">
                  <li>Telegram token is local only and must not be committed.</li>
                  <li>The bridge does not auto-approve or auto-resume.</li>
                  <li>Human approval is still required before resume.</li>
                  <li>No real email is sent.</li>
                  <li>
                    Deterministic runtime is enough for a stable defense demo.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="ops-panel p-6">
          <h2 className="text-lg font-semibold">Optional RAG evidence mode</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            RAG is off by default. Evidence and citations appear only when
            RAG_ENABLED=true and demo knowledge ingestion has been run. The
            frontend shows attached evidence from workflow state/events and does
            not fabricate evidence when none exists.
          </p>
        </section>
      </section>
    </main>
  );
}
