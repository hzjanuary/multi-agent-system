import { NavLink } from "@/components/navigation/nav-link";

const navigationItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/workflows", label: "Workflows" },
  { href: "/workflows/new", label: "Create Workflow" },
  { href: "/events", label: "Runtime Events" },
] as const;

export function Sidebar() {
  return (
    <aside className="border-b bg-card px-4 py-4 text-card-foreground md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm font-semibold text-foreground">
            Enterprise Multi-Agent OS
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Workflow dashboard
          </p>
        </div>
        <nav
          className="grid gap-1 sm:grid-cols-2 md:flex md:flex-col"
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
