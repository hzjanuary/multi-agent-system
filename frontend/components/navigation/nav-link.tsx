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
        "flex min-h-10 items-center rounded-md px-3 text-sm font-medium transition hover:bg-accent hover:text-accent-foreground",
        isActive
          ? "bg-accent text-accent-foreground"
          : "text-muted-foreground",
      )}
      href={href}
    >
      {label}
    </Link>
  );
}
