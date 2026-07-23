"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

interface NavLinkProps {
  href: string;
  label: string;
}

export function NavLink({ href, label }: NavLinkProps) {
  const pathname = usePathname();
  const isActive =
    pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`));

  return (
    <Link
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "relative flex min-h-9 shrink-0 items-center rounded-md border border-transparent px-3 text-sm font-medium transition md:min-h-10",
        isActive
          ? "border-primary/30 bg-primary/10 text-foreground shadow-[0_0_18px_hsl(var(--primary)/0.12)] before:absolute before:bottom-0 before:left-3 before:right-3 before:h-0.5 before:rounded-full before:bg-primary md:pl-4 md:before:bottom-auto md:before:left-0 md:before:right-auto md:before:top-2 md:before:h-6 md:before:w-0.5"
          : "text-muted-foreground hover:border-border/70 hover:bg-secondary/50 hover:text-foreground",
      )}
      href={href}
    >
      {label}
    </Link>
  );
}
