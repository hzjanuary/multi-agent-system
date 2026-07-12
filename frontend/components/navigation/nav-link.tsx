"use client";

import Link from "next/link";

interface NavLinkProps {
  href: string;
  label: string;
}

export function NavLink({ href, label }: NavLinkProps) {
  return (
    <Link
      className="flex min-h-10 items-center rounded-md px-3 text-sm font-medium text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
      href={href}
    >
      {label}
    </Link>
  );
}
