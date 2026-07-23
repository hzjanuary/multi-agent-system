import { NavLink } from "@/components/navigation/nav-link";

const navigationItems = [
  { href: "/demo", label: "Demo Command" },
  { href: "/agent-monitor", label: "Agent Monitor" },
  { href: "/workflows", label: "Workflows" },
  { href: "/workflows/new", label: "Create Workflow" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/events", label: "Runtime Events" },
] as const;

export function Sidebar() {
  return (
    <aside className="border-b border-border/70 bg-card/85 px-3 py-3 text-card-foreground backdrop-blur md:sticky md:top-0 md:min-h-screen md:w-72 md:border-b-0 md:border-r md:px-4 md:py-4">
      <div className="grid gap-3 md:gap-6">
        <div className="rounded-md border border-primary/20 bg-background/45 p-3 md:p-4">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-primary md:text-xs md:tracking-[0.2em]">
            Multi-Agent OS
          </p>
          <p className="mt-1 text-sm font-semibold text-foreground md:mt-2">
            Violet Operations Console
          </p>
          <p className="mt-2 inline-flex rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1 text-[0.68rem] font-medium text-emerald-200 md:mt-3 md:text-xs">
            Deterministic no-key demo
          </p>
        </div>
        <nav
          className="flex gap-1 overflow-x-auto pb-1 md:flex-col md:overflow-visible md:pb-0"
          aria-label="Dashboard navigation"
        >
          {navigationItems.map((item) => (
            <NavLink key={item.href} href={item.href} label={item.label} />
          ))}
        </nav>
      </div>
    </aside>
  );
}
